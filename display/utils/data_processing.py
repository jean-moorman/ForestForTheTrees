"""
Data transformation utilities for the display system.
"""
from typing import List, Tuple, Dict, Any
from datetime import datetime


class DataProcessor:
    """Utility class for processing display data."""
    
    @staticmethod
    def decimate_data(data_points: List[Tuple[float, float]], 
                     threshold: int = 1000, 
                     epsilon: float = 0.1) -> List[Tuple[float, float]]:
        """
        Reduce data points using Ramer-Douglas-Peucker algorithm.
        
        Args:
            data_points: List of (timestamp, value) tuples
            threshold: Maximum number of points before decimation
            epsilon: Decimation precision
            
        Returns:
            Decimated data points
        """
        if len(data_points) <= threshold:
            return data_points
            
        return DataProcessor._rdp_reduce(data_points, epsilon)
    
    @staticmethod
    def _rdp_reduce(points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
        """Implement Ramer-Douglas-Peucker algorithm."""
        if len(points) <= 2:
            return points
            
        # Find point with max distance
        dmax = 0
        index = 0
        for i in range(1, len(points) - 1):
            d = DataProcessor._point_line_distance(points[i], points[0], points[-1])
            if d > dmax:
                index = i
                dmax = d
                
        if dmax > epsilon:
            # Recursive call
            rec_results1 = DataProcessor._rdp_reduce(points[:index + 1], epsilon)
            rec_results2 = DataProcessor._rdp_reduce(points[index:], epsilon)
            return rec_results1[:-1] + rec_results2
        else:
            return [points[0], points[-1]]
    
    @staticmethod
    def _point_line_distance(point: Tuple[float, float], 
                           line_start: Tuple[float, float], 
                           line_end: Tuple[float, float]) -> float:
        """Calculate perpendicular distance from point to line."""
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        numerator = abs((y2-y1)*x - (x2-x1)*y + x2*y1 - y2*x1)
        denominator = ((y2-y1)**2 + (x2-x1)**2)**0.5
        
        return numerator/denominator if denominator != 0 else 0
    
    @staticmethod
    def format_error_message(error_msg: str, error_data: Dict[str, Any]) -> str:
        """Format error message with details."""
        detailed_error = f"Error: {error_msg}"
        if error_data and 'traceback' in error_data:
            detailed_error += f"\n\nTraceback:\n{error_data['traceback']}"
        return detailed_error
    
    @staticmethod
    def format_time_duration(seconds: float) -> str:
        """Format time duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"