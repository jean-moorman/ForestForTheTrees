"""
Phase One Interactive Debugger

Provides step-by-step execution, agent state inspection, and real-time monitoring
of the Phase One workflow for debugging and verification purposes.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any


class PhaseOneDebugger:
    """
    Interactive command-line debugger for Phase One workflow.
    
    Provides step-by-step execution, agent state inspection, and real-time monitoring
    of the Phase One workflow for debugging and verification purposes.
    """
    
    def __init__(self, phase_one_orchestrator: 'PhaseOneOrchestrator'):
        self.phase_one = phase_one_orchestrator
        self.logger = logging.getLogger(f"{__name__}.debugger")
        self.current_operation_id = None
        self.workflow_state = {}
        self.agent_metrics = {}
        self.step_mode = False
        self.break_points = set()
        
    async def start_interactive_session(self):
        """Start an interactive debugging session."""
        print("🌲 Phase One Interactive Debugger")
        print("=" * 50)
        print("Commands:")
        print("  run <prompt>     - Execute Phase One workflow with prompt")
        print("  step            - Enable step-by-step execution mode")
        print("  nostep          - Disable step-by-step execution mode")
        print("  status          - Show current workflow status")
        print("  agents          - List all agents and their status")
        print("  metrics <agent> - Show detailed metrics for an agent")
        print("  monitor         - Show real-time system monitoring")
        print("  breakpoint <stage> - Set breakpoint at workflow stage")
        print("  continue        - Continue execution from breakpoint")
        print("  history         - Show execution history")
        print("  trace           - Show detailed execution trace")
        print("  verbose         - Enable verbose logging (DEBUG level)")
        print("  quiet           - Enable quiet mode (WARNING level)")
        print("  normal          - Set normal logging (INFO level)")
        print("  reset           - Reset debugger state")
        print("  help            - Show this help message")
        print("  quit            - Exit debugger")
        print("=" * 50)
        
        while True:
            try:
                # Get user input
                command = input("\n🐛 > ").strip()
                
                if not command:
                    continue
                    
                # Parse command
                parts = command.split(' ', 1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                # Handle commands
                if cmd in ('quit', 'exit', 'q'):
                    print("Exiting debugger...")
                    break
                elif cmd == 'help':
                    await self._cmd_help()
                elif cmd == 'run':
                    await self._cmd_run(args)
                elif cmd == 'step':
                    await self._cmd_step()
                elif cmd == 'nostep':
                    await self._cmd_nostep()
                elif cmd == 'status':
                    await self._cmd_status()
                elif cmd == 'agents':
                    await self._cmd_agents()
                elif cmd == 'metrics':
                    await self._cmd_metrics(args)
                elif cmd == 'monitor':
                    await self._cmd_monitor()
                elif cmd == 'breakpoint':
                    await self._cmd_breakpoint(args)
                elif cmd == 'continue':
                    await self._cmd_continue()
                elif cmd == 'history':
                    await self._cmd_history()
                elif cmd == 'trace':
                    await self._cmd_trace()
                elif cmd == 'verbose':
                    await self._cmd_verbose()
                elif cmd == 'quiet':
                    await self._cmd_quiet()
                elif cmd == 'normal':
                    await self._cmd_normal()
                elif cmd == 'reset':
                    await self._cmd_reset()
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
            except Exception as e:
                self.logger.error(f"Debugger error: {e}", exc_info=True)
                print(f"Error: {str(e)}")
    
    async def _cmd_help(self):
        """Show help information."""
        print("\n📖 Phase One Workflow Steps:")
        print("1. User prompt submission/storage")
        print("2. Garden Planner agent (strategy → reflection → revision)")
        print("3. Earth agent validation (recursion with Garden Planner)")
        print("4. Water agent coordination between sequential agents")
        print("5. Environmental Analysis agent")
        print("6. Root System agent")
        print("7. Tree Placement Planner agent")
        print("8. Air agent historical summary")
        print("9. Fire agent complexity decomposition")
        print("10. Phase Zero parallel analysis")
        print("11. Phase Zero Evolution agent synthesis")
        print("12. Phase One refinement operations")
        
    async def _cmd_run(self, prompt: str):
        """Execute Phase One workflow with the given prompt."""
        if not prompt:
            print("Error: Please provide a prompt. Usage: run <your prompt here>")
            return
            
        print(f"\n🚀 Starting Phase One execution with prompt: {prompt[:100]}...")
        self.current_operation_id = f"debug_{datetime.now().isoformat().replace(':', '-')}"
        
        try:
            if self.step_mode:
                result = await self._execute_with_stepping(prompt)
            else:
                result = await self.phase_one.process_task(prompt, self.current_operation_id)
                
            self._print_execution_result(result)
            
        except Exception as e:
            self.logger.error(f"Execution error: {e}", exc_info=True)
            print(f"❌ Execution failed: {str(e)}")
    
    async def _execute_with_stepping(self, prompt: str):
        """Execute workflow with step-by-step debugging."""
        print("\n🔍 Step-by-step execution mode enabled")
        print("Press Enter to continue to next step, 'c' to continue without stepping, 'q' to quit")
        
        # This would require modifications to the orchestrator to support stepping
        # For now, we'll simulate stepping by showing progress
        steps = [
            "Initializing workflow",
            "Garden Planner processing",
            "Earth Agent validation",
            "Water Agent coordination",
            "Environmental Analysis",
            "Root System Architect",
            "Tree Placement Planner",
            "Phase Zero analysis",
            "Refinement processing"
        ]
        
        for i, step in enumerate(steps):
            print(f"\n📍 Step {i+1}: {step}")
            
            if step in self.break_points:
                print(f"🛑 Breakpoint hit at: {step}")
                
            choice = input("Next? (Enter/c/q): ").strip().lower()
            if choice == 'q':
                print("Execution aborted.")
                return {"status": "aborted", "message": "User aborted execution"}
            elif choice == 'c':
                self.step_mode = False
                print("Continuing without stepping...")
                break
        
        # Execute the actual workflow
        return await self.phase_one.process_task(prompt, self.current_operation_id)
    
    async def _cmd_step(self):
        """Enable step-by-step execution mode."""
        self.step_mode = True
        print("✅ Step-by-step execution mode enabled")
    
    async def _cmd_nostep(self):
        """Disable step-by-step execution mode."""
        self.step_mode = False
        print("✅ Step-by-step execution mode disabled")
    
    async def _cmd_status(self):
        """Show current workflow status."""
        if not self.current_operation_id:
            print("No active operation")
            return
            
        try:
            status = await self.phase_one.get_workflow_status(self.current_operation_id)
            print(f"\n📊 Workflow Status (Operation: {self.current_operation_id})")
            print(f"Status: {status.get('status', 'unknown')}")
            print(f"Current Agent: {status.get('current_agent', 'none')}")
            print(f"Start Time: {status.get('start_time', 'unknown')}")
            if status.get('end_time'):
                print(f"End Time: {status.get('end_time')}")
            if status.get('failure_stage'):
                print(f"❌ Failed at: {status.get('failure_stage')}")
            if status.get('error'):
                print(f"Error: {status.get('error')}")
                
        except Exception as e:
            print(f"Error getting status: {str(e)}")
    
    async def _cmd_agents(self):
        """List all agents and their status."""
        agents = [
            ("garden_planner", "Garden Planner Agent"),
            ("earth_agent", "Earth Agent (Validation)"),
            ("environmental_analysis", "Environmental Analysis Agent"),
            ("root_system_architect", "Root System Architect Agent"),
            ("tree_placement_planner", "Tree Placement Planner Agent")
        ]
        
        print("\n🤖 Phase One Agents:")
        for agent_id, description in agents:
            try:
                metrics = await self.phase_one.get_agent_metrics(agent_id)
                status = "✅ Ready" if metrics.get('status') == 'success' else "❌ Error"
                print(f"  {agent_id}: {description} - {status}")
            except Exception as e:
                print(f"  {agent_id}: {description} - ❓ Unknown ({str(e)})")
    
    async def _cmd_metrics(self, agent_id: str):
        """Show detailed metrics for an agent."""
        if not agent_id:
            print("Error: Please specify an agent ID. Usage: metrics <agent_id>")
            return
            
        try:
            metrics = await self.phase_one.get_agent_metrics(agent_id)
            print(f"\n📈 Metrics for {agent_id}:")
            print(json.dumps(metrics, indent=2))
        except Exception as e:
            print(f"Error getting metrics for {agent_id}: {str(e)}")
    
    async def _cmd_monitor(self):
        """Show real-time system monitoring."""
        try:
            # Get system health information
            if hasattr(self.phase_one, '_health_tracker') and self.phase_one._health_tracker:
                print("\n💚 System Health Monitor:")
                # This would require accessing health tracker data
                print("Health tracking is active")
            else:
                print("❌ Health tracking not available")
                
            if hasattr(self.phase_one, '_memory_monitor') and self.phase_one._memory_monitor:
                print("Memory monitoring is active")
            else:
                print("❌ Memory monitoring not available")
                
        except Exception as e:
            print(f"Error accessing monitoring: {str(e)}")
    
    async def _cmd_breakpoint(self, stage: str):
        """Set a breakpoint at a workflow stage."""
        if not stage:
            print("Current breakpoints:", list(self.break_points))
            return
            
        valid_stages = {
            "garden_planner", "earth_validation", "water_coordination",
            "environmental_analysis", "root_system", "tree_placement",
            "air_summary", "fire_decomposition", "phase_zero", "refinement"
        }
        
        if stage in valid_stages:
            self.break_points.add(stage)
            print(f"✅ Breakpoint set at: {stage}")
        else:
            print(f"Invalid stage. Valid stages: {', '.join(valid_stages)}")
    
    async def _cmd_continue(self):
        """Continue execution from breakpoint."""
        print("Continuing execution...")
        # This would be used during step-by-step execution
    
    async def _cmd_history(self):
        """Show execution history."""
        print("\n📚 Execution History:")
        if self.current_operation_id:
            print(f"Current operation: {self.current_operation_id}")
        else:
            print("No execution history available")
    
    async def _cmd_trace(self):
        """Show detailed execution trace."""
        if not self.current_operation_id:
            print("No active operation to trace")
            return
            
        print(f"\n🔍 Execution Trace for {self.current_operation_id}:")
        # This would require storing and retrieving detailed trace information
        print("Trace functionality would show detailed step-by-step execution logs")
    
    async def _cmd_verbose(self):
        """Enable verbose logging (DEBUG level)."""
        logging.getLogger().setLevel(logging.DEBUG)
        # Also set specific loggers that were optimized
        logging.getLogger("agent").setLevel(logging.DEBUG)
        logging.getLogger("resources.monitoring.circuit_breakers").setLevel(logging.DEBUG)
        logging.getLogger("resources.events.queue").setLevel(logging.DEBUG)
        logging.getLogger("interfaces.agent.interface").setLevel(logging.DEBUG)
        print("✅ Verbose logging enabled (DEBUG level)")
    
    async def _cmd_quiet(self):
        """Enable quiet mode (WARNING level)."""
        logging.getLogger().setLevel(logging.WARNING)
        # Also set specific loggers that were optimized
        logging.getLogger("agent").setLevel(logging.WARNING)
        logging.getLogger("resources.monitoring.circuit_breakers").setLevel(logging.WARNING)
        logging.getLogger("resources.events.queue").setLevel(logging.WARNING)
        logging.getLogger("interfaces.agent.interface").setLevel(logging.WARNING)
        print("✅ Quiet mode enabled (WARNING level)")
    
    async def _cmd_normal(self):
        """Set normal logging (INFO level)."""
        logging.getLogger().setLevel(logging.INFO)
        # Also set specific loggers that were optimized
        logging.getLogger("agent").setLevel(logging.INFO)
        logging.getLogger("resources.monitoring.circuit_breakers").setLevel(logging.INFO)
        logging.getLogger("resources.events.queue").setLevel(logging.INFO)
        logging.getLogger("interfaces.agent.interface").setLevel(logging.INFO)
        print("✅ Normal logging enabled (INFO level)")
    
    async def _cmd_reset(self):
        """Reset debugger state."""
        self.current_operation_id = None
        self.workflow_state = {}
        self.agent_metrics = {}
        self.step_mode = False
        self.break_points.clear()
        print("✅ Debugger state reset")
    
    def _print_execution_result(self, result: Dict[str, Any]):
        """Print execution result in a readable format."""
        print("\n" + "="*60)
        print("🌲 PHASE ONE EXECUTION RESULT")
        print("="*60)
        
        status = result.get('status', 'unknown')
        status_emoji = "✅" if status == 'success' else "❌" if status == 'error' else "⚠️"
        print(f"Status: {status_emoji} {status.upper()}")
        
        if result.get('execution_time'):
            print(f"Execution Time: {result['execution_time']:.2f} seconds")
        
        if status == 'error':
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
            return
        
        # Print structural components
        if 'structural_components' in result:
            print(f"\n🏗️  Structural Components ({len(result['structural_components'])}):")
            for i, component in enumerate(result['structural_components'], 1):
                name = component.get('name', f'Component {i}')
                desc = component.get('description', 'No description')
                deps = component.get('dependencies', [])
                print(f"  {i}. {name}")
                print(f"     📝 {desc}")
                if deps:
                    print(f"     🔗 Dependencies: {', '.join(deps)}")
        
        # Print system requirements summary
        if 'system_requirements' in result:
            requirements = result['system_requirements']
            print(f"\n⚙️  System Requirements:")
            
            if 'task_analysis' in requirements:
                task = requirements['task_analysis']
                goal = task.get('interpreted_goal', 'Unknown goal')
                print(f"  🎯 Goal: {goal}")
                
                if 'technical_requirements' in task:
                    tech = task['technical_requirements']
                    languages = tech.get('languages', [])
                    frameworks = tech.get('frameworks', [])
                    if languages or frameworks:
                        tech_stack = ', '.join(languages + frameworks)
                        print(f"  💻 Tech Stack: {tech_stack}")
        
        # Print refinement information if available
        if 'refinement_analysis' in result:
            refinement = result['refinement_analysis']
            print(f"\n🔄 Refinement Analysis:")
            if refinement.get('status') == 'refinement_executed':
                print(f"  ✅ Refinement applied to: {refinement.get('target_agent')}")
                print(f"  🔄 Cycle: {refinement.get('cycle')}")
            else:
                print(f"  ℹ️  No refinement required")
        
        print("="*60)