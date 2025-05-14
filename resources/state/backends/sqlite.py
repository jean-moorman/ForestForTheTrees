import asyncio
import json
import logging
import sqlite3
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from resources.common import ResourceState, InterfaceState, ResourceType
from resources.state.backends.base import StateStorageBackend
from resources.state.models import StateEntry, StateSnapshot

logger = logging.getLogger(__name__)


class SQLiteStateBackend(StateStorageBackend):
    """SQLite-based storage backend for reliable persistence"""
    
    def __init__(self, db_path: str):
        """Initialize with a database path"""
        self.db_path = db_path
        self._connection_pool = {}  # Thread-local connections
        self._lock = threading.RLock()  # Lock for connection management
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema if it doesn't exist"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Create states table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS states (
                resource_id TEXT PRIMARY KEY,
                state_type TEXT,
                state_value TEXT,
                resource_type TEXT,
                timestamp TEXT,
                metadata TEXT,
                version INTEGER,
                previous_state TEXT,
                transition_reason TEXT,
                failure_info TEXT
            )
            ''')
            
            # Create history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS state_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id TEXT,
                state_type TEXT,
                state_value TEXT,
                resource_type TEXT,
                timestamp TEXT,
                metadata TEXT,
                version INTEGER,
                previous_state TEXT,
                transition_reason TEXT,
                failure_info TEXT
            )
            ''')
            
            # Create snapshots table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id TEXT,
                state TEXT,
                timestamp TEXT,
                metadata TEXT,
                resource_type TEXT,
                version INTEGER
            )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_resource_id ON state_history(resource_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_resource_id ON snapshots(resource_id)')
            
            conn.commit()
        finally:
            conn.close()
    
    def _get_connection(self):
        """Get a thread-local database connection"""
        thread_id = threading.get_ident()
        with self._lock:
            if thread_id not in self._connection_pool:
                # Create a new connection
                conn = sqlite3.connect(self.db_path)
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                # Configure connection
                conn.row_factory = sqlite3.Row
                self._connection_pool[thread_id] = conn
            else:
                # Check if connection is valid
                conn = self._connection_pool[thread_id]
                try:
                    # Test if connection is valid with a simple query
                    conn.execute("SELECT 1")
                except sqlite3.Error:
                    # Connection is invalid, create a new one
                    conn = sqlite3.connect(self.db_path)
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.row_factory = sqlite3.Row
                    self._connection_pool[thread_id] = conn
                    
            return self._connection_pool[thread_id]
        
    def __del__(self):
        """Close all connections when object is deleted"""
        try:
            with self._lock:
                for conn in self._connection_pool.values():
                    try:
                        conn.close()
                    except Exception:
                        pass
                self._connection_pool.clear()
        except Exception:
            pass  # Ignore errors during cleanup
    
    @asynccontextmanager
    async def _get_db_cursor(self):
        """Get a database cursor in a context manager"""
        # This runs the SQLite operations in a thread pool since they're blocking
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def _serialize_state_entry(self, entry: StateEntry) -> dict:
        """Convert a StateEntry to a dictionary for database storage"""
        # Handle different state types
        if isinstance(entry.state, (ResourceState, InterfaceState)):
            state_type = type(entry.state).__name__
            state_value = entry.state.name
        else:
            state_type = "dict"
            state_value = json.dumps(entry.state)
        
        return {
            'state_type': state_type,
            'state_value': state_value,
            'resource_type': entry.resource_type.name,
            'timestamp': entry.timestamp.isoformat(),
            'metadata': json.dumps(entry.metadata),
            'version': entry.version,
            'previous_state': entry.previous_state,
            'transition_reason': entry.transition_reason,
            'failure_info': json.dumps(entry.failure_info) if entry.failure_info else None
        }
    
    def _deserialize_state_entry(self, row) -> StateEntry:
        """Convert a database row to a StateEntry"""
        # Convert state based on type
        state_type = row['state_type']
        state_value = row['state_value']
        
        if state_type == 'ResourceState':
            state = ResourceState[state_value]
        elif state_type == 'InterfaceState':
            state = InterfaceState[state_value]
        elif state_type == 'dict':
            state = json.loads(state_value)
        else:
            # Fallback for unknown types
            state = state_value
        
        # Parse metadata and failure_info
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        failure_info = json.loads(row['failure_info']) if row['failure_info'] else None
        
        return StateEntry(
            state=state,
            resource_type=ResourceType[row['resource_type']],
            timestamp=datetime.fromisoformat(row['timestamp']),
            metadata=metadata,
            version=row['version'],
            previous_state=row['previous_state'],
            transition_reason=row['transition_reason'],
            failure_info=failure_info
        )
    
    def _serialize_snapshot(self, snapshot: StateSnapshot) -> dict:
        """Convert a StateSnapshot to a dictionary for database storage"""
        # Deep copy and convert state to ensure all enums are serialized
        serialized_state = self._make_json_serializable(snapshot.state)
        
        return {
            'state': json.dumps(serialized_state),
            'timestamp': snapshot.timestamp.isoformat(),
            'metadata': json.dumps(snapshot.metadata),
            'resource_type': snapshot.resource_type.name,
            'version': snapshot.version
        }
    
    def _make_json_serializable(self, obj):
        """Recursively convert objects to JSON serializable types"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (ResourceState, InterfaceState, ResourceType)):
            return obj.name  # Convert enum to string
        elif hasattr(obj, '__dict__'):  # For custom objects
            return {k: self._make_json_serializable(v) for k, v in obj.__dict__.items()
                    if not k.startswith('_')}
        else:
            return obj  # Return as is (should be JSON serializable)
    
    def _deserialize_snapshot(self, row) -> StateSnapshot:
        """Convert a database row to a StateSnapshot"""
        return StateSnapshot(
            state=json.loads(row['state']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            resource_type=ResourceType[row['resource_type']],
            version=row['version']
        )
    
    async def save_state(self, resource_id: str, state_entry: StateEntry) -> bool:
        """Save a state entry to the database"""
        try:
            # Serialize the state entry
            data = self._serialize_state_entry(state_entry)
            
            async with self._get_db_cursor() as cursor:
                # Insert or replace current state
                cursor.execute('''
                INSERT OR REPLACE INTO states 
                (resource_id, state_type, state_value, resource_type, timestamp, 
                 metadata, version, previous_state, transition_reason, failure_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    resource_id, data['state_type'], data['state_value'], 
                    data['resource_type'], data['timestamp'], data['metadata'],
                    data['version'], data['previous_state'], 
                    data['transition_reason'], data['failure_info']
                ))
                
                # Add to history
                cursor.execute('''
                INSERT INTO state_history 
                (resource_id, state_type, state_value, resource_type, timestamp, 
                 metadata, version, previous_state, transition_reason, failure_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    resource_id, data['state_type'], data['state_value'], 
                    data['resource_type'], data['timestamp'], data['metadata'],
                    data['version'], data['previous_state'], 
                    data['transition_reason'], data['failure_info']
                ))
            
            return True
        except Exception as e:
            logger.error(f"Error saving state to database: {e}")
            return False
    
    async def save_snapshot(self, resource_id: str, snapshot: StateSnapshot) -> bool:
        """Save a state snapshot to the database"""
        try:
            # Serialize the snapshot
            data = self._serialize_snapshot(snapshot)
            
            async with self._get_db_cursor() as cursor:
                cursor.execute('''
                INSERT INTO snapshots 
                (resource_id, state, timestamp, metadata, resource_type, version)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    resource_id, data['state'], data['timestamp'], 
                    data['metadata'], data['resource_type'], data['version']
                ))
            
            return True
        except Exception as e:
            logger.error(f"Error saving snapshot to database: {e}")
            return False
    
    async def load_state(self, resource_id: str) -> Optional[StateEntry]:
        """Load the latest state for a resource from the database"""
        try:
            async with self._get_db_cursor() as cursor:
                cursor.execute('''
                SELECT * FROM states WHERE resource_id = ?
                ''', (resource_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._deserialize_state_entry(row)
        except Exception as e:
            logger.error(f"Error loading state from database: {e}")
            return None
    
    async def load_history(self, resource_id: str, limit: Optional[int] = None) -> List[StateEntry]:
        """Load state history for a resource from the database"""
        try:
            async with self._get_db_cursor() as cursor:
                if limit:
                    cursor.execute('''
                    SELECT * FROM state_history 
                    WHERE resource_id = ? 
                    ORDER BY timestamp DESC LIMIT ?
                    ''', (resource_id, limit))
                else:
                    cursor.execute('''
                    SELECT * FROM state_history 
                    WHERE resource_id = ? 
                    ORDER BY timestamp
                    ''', (resource_id,))
                
                rows = cursor.fetchall()
                
                # Convert rows to StateEntry objects
                history = [self._deserialize_state_entry(row) for row in rows]
                
                # If we fetched in DESC order due to LIMIT, reverse back to chronological
                if limit:
                    history.reverse()
                
                return history
        except Exception as e:
            logger.error(f"Error loading history from database: {e}")
            return []
    
    async def load_snapshots(self, resource_id: str, limit: Optional[int] = None) -> List[StateSnapshot]:
        """Load snapshots for a resource from the database"""
        try:
            async with self._get_db_cursor() as cursor:
                if limit:
                    cursor.execute('''
                    SELECT * FROM snapshots 
                    WHERE resource_id = ? 
                    ORDER BY timestamp DESC LIMIT ?
                    ''', (resource_id, limit))
                else:
                    cursor.execute('''
                    SELECT * FROM snapshots 
                    WHERE resource_id = ? 
                    ORDER BY timestamp
                    ''', (resource_id,))
                
                rows = cursor.fetchall()
                
                # Convert rows to StateSnapshot objects
                snapshots = [self._deserialize_snapshot(row) for row in rows]
                
                # If we fetched in DESC order due to LIMIT, reverse back to chronological
                if limit:
                    snapshots.reverse()
                
                return snapshots
        except Exception as e:
            logger.error(f"Error loading snapshots from database: {e}")
            return []
    
    async def get_all_resource_ids(self) -> List[str]:
        """Get all resource IDs from the database"""
        try:
            async with self._get_db_cursor() as cursor:
                cursor.execute('SELECT DISTINCT resource_id FROM states')
                rows = cursor.fetchall()
                return [row['resource_id'] for row in rows]
        except Exception as e:
            logger.error(f"Error getting resource IDs from database: {e}")
            return []
    
    async def cleanup(self, older_than: Optional[datetime] = None) -> int:
        """
        Clean up old entries, returns count of removed items.
        
        This method:
        1. Removes states for terminated resources older than the specified time
        2. Trims history to prevent excessive growth
        3. Limits the number of snapshots per resource
        """
        items_removed = 0
        
        if not older_than:
            # Default to cleaning up entries older than 30 days
            older_than = datetime.now() - timedelta(days=30)
        
        # Format cutoff timestamp for SQL comparison
        cutoff_timestamp = older_than.isoformat()
        
        try:
            async with self._get_db_cursor() as cursor:
                # 1. Find terminated resources to remove completely
                cursor.execute('''
                SELECT resource_id FROM states 
                WHERE state_type = 'ResourceState' 
                AND state_value = 'TERMINATED' 
                AND timestamp < ?
                ''', (cutoff_timestamp,))
                
                terminated_resources = [row['resource_id'] for row in cursor.fetchall()]
                
                # Remove terminated resources
                for resource_id in terminated_resources:
                    # Delete state
                    cursor.execute('DELETE FROM states WHERE resource_id = ?', (resource_id,))
                    
                    # Delete history
                    cursor.execute('DELETE FROM state_history WHERE resource_id = ?', (resource_id,))
                    
                    # Delete snapshots
                    cursor.execute('DELETE FROM snapshots WHERE resource_id = ?', (resource_id,))
                    
                    items_removed += 1
                    logger.info(f"Cleaned up terminated resource: {resource_id}")
                
                # 2. Trim history for each active resource
                cursor.execute('SELECT DISTINCT resource_id FROM states')
                active_resources = [row['resource_id'] for row in cursor.fetchall()]
                
                for resource_id in active_resources:
                    # Count history entries
                    cursor.execute('''
                    SELECT COUNT(*) as count FROM state_history WHERE resource_id = ?
                    ''', (resource_id,))
                    count = cursor.fetchone()['count']
                    
                    # If more than 1000 entries, keep only the most recent 1000
                    if count > 1000:
                        # Find the ID threshold for deletion
                        cursor.execute('''
                        SELECT id FROM state_history 
                        WHERE resource_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1 OFFSET 1000
                        ''', (resource_id,))
                        result = cursor.fetchone()
                        if result:
                            threshold_id = result['id']
                            
                            # Delete older entries
                            cursor.execute('''
                            DELETE FROM state_history 
                            WHERE resource_id = ? AND id < ?
                            ''', (resource_id, threshold_id))
                            
                            deleted = cursor.rowcount
                            items_removed += deleted
                            logger.info(f"Trimmed history for {resource_id}: removed {deleted} old entries")
                    
                    # 3. Limit snapshots to most recent 10
                    cursor.execute('''
                    SELECT COUNT(*) as count FROM snapshots WHERE resource_id = ?
                    ''', (resource_id,))
                    count = cursor.fetchone()['count']
                    
                    if count > 10:
                        # Find the ID threshold for deletion
                        cursor.execute('''
                        SELECT id FROM snapshots 
                        WHERE resource_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1 OFFSET 10
                        ''', (resource_id,))
                        result = cursor.fetchone()
                        if result:
                            threshold_id = result['id']
                            
                            # Delete older snapshots
                            cursor.execute('''
                            DELETE FROM snapshots 
                            WHERE resource_id = ? AND id < ?
                            ''', (resource_id, threshold_id))
                            
                            deleted = cursor.rowcount
                            items_removed += deleted
                            logger.info(f"Trimmed snapshots for {resource_id}: removed {deleted} old snapshots")
                
                # 4. Vacuum the database periodically to reclaim space
                # Only do this occasionally as it can be expensive
                cursor.execute('PRAGMA auto_vacuum')
                auto_vacuum = cursor.fetchone()[0]
                if auto_vacuum == 0:  # If auto_vacuum is disabled
                    # Get database size in pages
                    cursor.execute('PRAGMA page_count')
                    page_count = cursor.fetchone()[0]
                    cursor.execute('PRAGMA page_size')
                    page_size = cursor.fetchone()[0]
                    
                    # If database is larger than 10MB, vacuum it
                    if page_count * page_size > 10 * 1024 * 1024:
                        cursor.execute('VACUUM')
                        logger.info("Vacuumed SQLite database to reclaim space")
            
            return items_removed
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            return items_removed
    
    async def optimize_database(self) -> bool:
        """
        Optimize the database by running VACUUM and ANALYZE commands.
        This is an expensive operation that should be run during maintenance windows.
        """
        try:
            async with self._get_db_cursor() as cursor:
                # Rebuild the database to defragment and optimize
                cursor.execute('VACUUM')
                # Update statistics for the query planner
                cursor.execute('ANALYZE')
            logger.info("Database optimization completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database for monitoring"""
        stats = {
            "resources_count": 0,
            "history_entries_count": 0,
            "snapshots_count": 0,
            "database_size_bytes": 0,
            "resource_states": {}
        }
        
        try:
            async with self._get_db_cursor() as cursor:
                # Get database file size
                cursor.execute('PRAGMA page_count')
                page_count = cursor.fetchone()[0]
                cursor.execute('PRAGMA page_size')
                page_size = cursor.fetchone()[0]
                stats["database_size_bytes"] = page_count * page_size
                
                # Count resources
                cursor.execute('SELECT COUNT(*) FROM states')
                stats["resources_count"] = cursor.fetchone()[0]
                
                # Count history entries
                cursor.execute('SELECT COUNT(*) FROM state_history')
                stats["history_entries_count"] = cursor.fetchone()[0]
                
                # Count snapshots
                cursor.execute('SELECT COUNT(*) FROM snapshots')
                stats["snapshots_count"] = cursor.fetchone()[0]
                
                # Count by state
                cursor.execute('''
                SELECT state_type, state_value, COUNT(*) as count 
                FROM states 
                GROUP BY state_type, state_value
                ''')
                for row in cursor.fetchall():
                    state_key = f"{row['state_type']}:{row['state_value']}"
                    stats["resource_states"][state_key] = row['count']
            
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return stats