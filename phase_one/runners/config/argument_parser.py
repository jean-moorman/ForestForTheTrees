"""
Argument Parser for Phase One Runners

Handles command-line argument parsing for both GUI and CLI modes
of the Phase One application.
"""

import argparse


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Phase One Standalone Runner - GUI and CLI modes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_phase_one.py                    # Run GUI mode (default)
  python run_phase_one.py --cli              # Run CLI interactive mode
  python run_phase_one.py --debug            # Run CLI debug mode
  python run_phase_one.py -p "Create a web app"  # Single prompt execution
  python run_phase_one.py -f prompt.txt      # Execute prompt from file
  python run_phase_one.py -p "..." -o result.json  # Save result to file
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--gui', action='store_true', 
                           help='Run in GUI mode (default)')
    mode_group.add_argument('--cli', action='store_true',
                           help='Run in CLI interactive mode')
    mode_group.add_argument('--debug', action='store_true',
                           help='Run in CLI debug mode with step-by-step execution')
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('-p', '--prompt', type=str,
                            help='Execute a single prompt')
    input_group.add_argument('-f', '--file', type=str,
                            help='Execute prompt from file')
    input_group.add_argument('-i', '--interactive', action='store_true',
                            help='Run in interactive mode')
    
    # Output options
    parser.add_argument('-o', '--output', type=str,
                       help='Save result to output file (JSON format)')
    
    # Logging options
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    parser.add_argument('--log-file', type=str, default='run_phase_one.log',
                       help='Log file path')
    
    return parser.parse_args()


def determine_mode(args):
    """
    Determine the execution mode based on parsed arguments.
    
    Returns:
        tuple: (is_cli_mode, mode_description)
    """
    # CLI takes precedence over GUI
    cli_mode = args.cli or args.debug or args.interactive or args.prompt or args.file
    
    if cli_mode:
        if args.debug:
            mode_desc = "CLI Debug Mode"
        elif args.interactive:
            mode_desc = "CLI Interactive Mode"
        elif args.prompt:
            mode_desc = "CLI Single Prompt Mode"
        elif args.file:
            mode_desc = "CLI File Prompt Mode"
        else:
            mode_desc = "CLI Mode"
    else:
        mode_desc = "GUI Mode"
    
    return cli_mode, mode_desc