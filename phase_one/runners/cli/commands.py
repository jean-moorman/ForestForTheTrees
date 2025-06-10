"""
CLI Command Processing for Phase One

Contains command parsing and execution logic for the interactive CLI debugger.
This module may be extended in the future to support additional CLI commands.
"""

from typing import Dict, List, Tuple


def parse_command(command_line: str) -> Tuple[str, str]:
    """
    Parse a command line into command and arguments.
    
    Args:
        command_line: The raw command line input
        
    Returns:
        Tuple of (command, arguments)
    """
    if not command_line.strip():
        return "", ""
    
    parts = command_line.strip().split(' ', 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    return cmd, args


def get_available_commands() -> Dict[str, str]:
    """
    Get a dictionary of available commands and their descriptions.
    
    Returns:
        Dictionary mapping command names to descriptions
    """
    return {
        'run': 'Execute Phase One workflow with prompt',
        'step': 'Enable step-by-step execution mode',
        'nostep': 'Disable step-by-step execution mode',
        'status': 'Show current workflow status',
        'agents': 'List all agents and their status',
        'metrics': 'Show detailed metrics for an agent',
        'monitor': 'Show real-time system monitoring',
        'breakpoint': 'Set breakpoint at workflow stage',
        'continue': 'Continue execution from breakpoint',
        'history': 'Show execution history',
        'trace': 'Show detailed execution trace',
        'verbose': 'Enable verbose logging (DEBUG level)',
        'quiet': 'Enable quiet mode (WARNING level)',
        'normal': 'Set normal logging (INFO level)',
        'reset': 'Reset debugger state',
        'help': 'Show help message',
        'quit': 'Exit debugger'
    }


def get_command_aliases() -> Dict[str, str]:
    """
    Get a dictionary of command aliases.
    
    Returns:
        Dictionary mapping aliases to canonical command names
    """
    return {
        'q': 'quit',
        'exit': 'quit',
        'h': 'help',
        '?': 'help',
        'c': 'continue',
        's': 'step',
        'ns': 'nostep',
        'st': 'status',
        'ag': 'agents',
        'm': 'metrics',
        'mon': 'monitor',
        'bp': 'breakpoint',
        'hist': 'history',
        'tr': 'trace',
        'v': 'verbose',
        'norm': 'normal',
        'r': 'reset'
    }


def validate_command(command: str) -> bool:
    """
    Validate if a command is recognized.
    
    Args:
        command: The command to validate
        
    Returns:
        True if the command is valid, False otherwise
    """
    available_commands = get_available_commands()
    aliases = get_command_aliases()
    
    return command in available_commands or command in aliases


def resolve_command_alias(command: str) -> str:
    """
    Resolve a command alias to its canonical form.
    
    Args:
        command: The command (potentially an alias)
        
    Returns:
        The canonical command name
    """
    aliases = get_command_aliases()
    return aliases.get(command, command)