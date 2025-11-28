# *****************************************************************************************************
# scripts/run_terminal.py
import os
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# Import API tools to talk to the Server (Port 8000)
from cerebrum.llm.apis import llm_operate_file
from cerebrum.storage.apis import mount
from list_agents import get_offline_agents, get_online_agents

class AIOSTerminal:
    def __init__(self):
        self.console = Console()
        self.style = Style.from_dict({
            'prompt': '#00ff00 bold',  
            'path': '#0000ff bold',    
            'arrow': '#ff0000',       
        })
        self.session = PromptSession(style=self.style)
        self.current_dir = os.getcwd()

    def get_prompt(self, extra_str = None):
        """Generates the colorful prompt string: 🚀 sysadm ⟹ ... """
        username = os.getenv('USER', 'user')
        path = os.path.basename(self.current_dir)
        prompt_parts = [
            ('class:prompt', f'🚀 {username}'),
            ('class:arrow', ' ⟹  '),
            ('class:path', f'{path}'),
            ('class:arrow', ' ≫ ')
        ]
        if extra_str:
            prompt_parts.append(('class:prompt', extra_str))
        return prompt_parts

    def display_help(self):
            """Shows comprehensive available commands locally."""
            
            # --- Section 1: Local Commands ---
            local_table = Table(show_header=True, header_style="bold magenta", title="🖥️  Local Terminal Commands")
            local_table.add_column("Command", style="cyan")
            local_table.add_column("Description", style="green")
            
            local_table.add_row("help", "Show this user manual")
            local_table.add_row("exit", "Exit the terminal client")
            local_table.add_row("ls / list files", "Instantly list files in the mounted directory")
            local_table.add_row("list agents --online", "List available agents from the hub")
            
            self.console.print(local_table)
            self.console.print("") # Spacing

            # --- Section 2: AI Natural Language Commands ---
            ai_table = Table(show_header=True, header_style="bold yellow", title="🤖 AI Agent Capabilities (Natural Language)")
            ai_table.add_column("Feature", style="cyan")
            ai_table.add_column("Reliable Prompt Format", style="white")
            ai_table.add_column("What it does", style="dim")

            # Core Features
            ai_table.add_row("Code Gen", "Create a file named filename.txt with content HELLO", "Creates & Writes in one step")
            ai_table.add_row("Write Content", "Write a list of fruits into shopping.txt", "Writes text to file")
            ai_table.add_row("Read/Analyze", "Read calc.py and explain the code", "Reads disk & summarizes")
            ai_table.add_row("List (AI)", "List all files in the current folder", "AI-driven directory scan")
            ai_table.add_row("Delete", "Delete the file calc.py", "Permanently removes file")
            
            
            # Security & History
            ai_table.add_section()
            ai_table.add_row("Rollback", "Rollback calc.py to previous version", "Restores from Redis history")
            ai_table.add_row("Share", "Generate a share link for calc.py", "Creates cloud/local link")
            # ai_table.add_row("Lock", "Lock calc.py for 5 minutes", "Restricts OS permissions")

            self.console.print(ai_table)
            self.console.print("[dim]Tip: For code generation, combine the creation and content in one sentence for best results.[/dim]")

    def handle_list_agents(self, args: str):
        """Handles agent listing locally."""
        if '--offline' in args:
            agents = get_offline_agents()
            self.console.print("\nAgents that have been installed:")
            for agent in agents:
                self.console.print(f"- {agent}")
        elif '--online' in args:
            agents = get_online_agents()
            self.console.print("\nAvailable agents on the agenthub:")
            for agent in agents:
                self.console.print(f"- {agent}")
        else:
            self.console.print("[red]Invalid parameter. Use --offline or --online[/red]")

    def run(self):
        """The main loop of the terminal."""
        welcome_msg = Text("Welcome to AIOS Terminal! Type 'help' for commands. But firstly you have to mount this....write [y] ", style="bold cyan")
        self.console.print(Panel(welcome_msg, border_style="green"))
        
        # Default mount point
        root_dir = os.path.join(self.current_dir, "root")
        
        # --- 1. MOUNTING PHASE ---
        while True:
            try:
                mount_choice = self.session.prompt(self.get_prompt(f"Mount FS at {root_dir}? [y/n] "))
                
                if mount_choice.lower() == 'y':
                    # Send mount request to Server
                    mount(agent_name="terminal", root_dir=root_dir)
                    self.console.print(f"[bold cyan]✅ Filesystem mounted at: {root_dir}[/]")
                    break
                elif mount_choice.lower() == 'n':
                    # --- CHANGED HERE: Ask for custom path ---
                    self.console.print("[yellow]Please enter the absolute path you want to mount:[/yellow]")
                    custom_path = self.session.prompt(self.get_prompt("Path: ")).strip()
                    if custom_path:
                        # Ensure the directory exists or try to create it
                        if not os.path.exists(custom_path):
                            try:
                                os.makedirs(custom_path)
                                self.console.print(f"[green]Created new directory: {custom_path}[/green]")
                            except Exception as e:
                                self.console.print(f"[red]Error creating directory: {e}[/red]")
                                continue

                        root_dir = custom_path  # Update global root_dir so 'ls' command works later
                        mount(agent_name="terminal", root_dir=root_dir)
                        self.console.print(f"[bold cyan]✅ Filesystem mounted at: {root_dir}[/]")
                        break
                    else:
                        self.console.print("[red]Path cannot be empty. Try again.[/red]")
                        continue

            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                self.console.print(f"[bold red]❌ Connection Failed![/]")
                self.console.print(f"Is the server running? Run 'python -m uvicorn runtime.launch:app --port 8000' in another window.")
                self.console.print(f"Error details: {e}")
                return # Exit if we can't connect

        # --- 2. COMMAND PHASE ---
        while True:
            try:
                command = self.session.prompt(self.get_prompt())
                command = command.strip()

                # Handle empty input
                if not command:
                    continue

                # --- LOCAL COMMANDS (The Switchboard) ---
                if command == 'exit':
                    self.console.print("[yellow]Goodbye! 👋[/yellow]")
                    break
                    
                elif command == 'help':
                    self.display_help()
                    continue
                
                elif command.startswith('list agents'):
                    args = command[len('list agents'):].strip()
                    self.handle_list_agents(args)
                    continue

                elif command in ['ls', 'list files']:
                    # List files locally to verify what the AI created
                    try:
                        files = os.listdir(root_dir)
                        self.console.print(Panel("\n".join(files), title=f"Files in {os.path.basename(root_dir)}", border_style="blue"))
                    except FileNotFoundError:
                        self.console.print("[red]Root directory not found.[/red]")
                    continue

                # --- SERVER COMMANDS (Send to AI) ---
                # If it's not a local command, send it to the AI Kernel
                try:
                    self.console.print("[dim]Thinking...[/dim]")
                    command_response = llm_operate_file(
                        agent_name="terminal", 
                        messages=[{"role": "user", "content": command}]
                    )
                    
                    if command_response:
                        self.console.print(Text(str(command_response), style="bold green"))
                    else:
                        self.console.print("[yellow]The AI finished but returned no text.[/yellow]")

                except Exception as e:
                    if "500" in str(e):
                        self.console.print("[red]Server Error (500): The AI couldn't process that command.[/red]")
                    elif "Connection refused" in str(e):
                        self.console.print("[red]Connection Lost! Is the server still running?[/red]")
                    else:
                        self.console.print(f"[red]Error: {str(e)}[/red]")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break

if __name__ == "__main__":
    terminal = AIOSTerminal()
    terminal.run()