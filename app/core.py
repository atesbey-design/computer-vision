import time
import queue
import os
from models.gemini import GeminiModel
from models.ollama import OllamaModel
from models.groq import GroqModel
from utils.screen import Screen
from utils.settings import Settings
from interpreter import Interpreter
import threading

class Core:
    def __init__(self, status_queue):
        self.status_queue = status_queue
        self.settings = Settings().get_dict()
        self.screen = Screen()
        self.current_model = None
        self.stop_requested = False
        self.process_lock = threading.Lock()
        self.interpreter = Interpreter(self.status_queue)
        
    def execute_user_request(self, request):
        with self.process_lock:
            self.stop_requested = False
            
            if request["type"] == "stop":
                self.stop_requested = True
                self.send_status("Task interrupted by user")
                if self.current_model:
                    self.current_model.cleanup()
                    self.current_model = None
                return
                
            if request["type"] == "request":
                try:
                    # Initialize model if needed or different
                    if not self.current_model or self.current_model.__class__.__name__.lower() != request["model"]:
                        if self.current_model:
                            self.current_model.cleanup()
                            
                        if request["model"] == "gemini":
                            self.current_model = GeminiModel()
                        elif request["model"] == "ollama-llama3.2-vision":
                            self.current_model = OllamaModel()
                        elif request["model"] == "groq":
                            self.current_model = GroqModel()
                            
                    self.execute(request["text"])
                    
                except Exception as e:
                    self.send_status(f"Error: {str(e)}")
                    if self.current_model:
                        self.current_model.cleanup()
                        self.current_model = None
                        
    def execute(self, text):
        """Execute the user's request by getting instructions from the model and running them."""
        try:
            # Get screenshot
            self.send_status("📸 Capturing screen...")
            screenshot_path = self.screen.get_screenshot_file()
            if screenshot_path is None:
                self.send_status("❌ Failed to capture screen")
                return

            self.send_status("🤖 Analyzing screen and processing request...")
            instructions = self.current_model.get_instructions_for_objective(text, screenshot_path)
            
            if not instructions:
                self.send_status("❌ No instructions received from model")
                return
                
            if instructions.get('done', False):
                self.send_status(f"✅ {instructions.get('done', 'Task completed')}")
                return
                
            commands = instructions.get('commands', [])
            if not commands:
                commands = instructions.get('steps', [])  # Try alternative key
            
            if not commands:
                self.send_status("❌ No commands to execute")
                return
                
            # Execute each command
            for cmd_idx, command in enumerate(commands, 1):
                if self.stop_requested:
                    break
                    
                # Show command description in status
                description = command.get('description', 'Executing command...')
                self.send_status(f"🔄 Step {cmd_idx}/{len(commands)}: {description}")
                    
                # Validate command has required fields
                if not isinstance(command, dict) or 'type' not in command:
                    self.send_status(f"❌ Step {cmd_idx}: Invalid command format")
                    continue
                    
                # Add validation for mouse control commands
                if command['type'] in ['move', 'click', 'drag']:
                    if 'x' not in command or 'y' not in command:
                        self.send_status(f"❌ Step {cmd_idx}: Missing coordinates for {command['type']} command")
                        continue
                    if not isinstance(command['x'], (int, float)) or not isinstance(command['y'], (int, float)):
                        self.send_status(f"❌ Step {cmd_idx}: Invalid coordinates for {command['type']} command")
                        continue
                        
                if command['type'] == 'scroll' and ('value' not in command or not isinstance(command['value'], (int, float))):
                    self.send_status(f"❌ Step {cmd_idx}: Invalid scroll value")
                    continue
                    
                # Execute the command
                success = self.interpreter.process_command(command)
                if not success:
                    self.send_status(f"❌ Step {cmd_idx} failed: {description}")
                    break
                else:
                    self.send_status(f"✅ Step {cmd_idx} completed: {description}")
                    
                # Add small delay between commands for stability
                time.sleep(0.5)
                
            if not self.stop_requested:
                self.send_status("🎉 All tasks completed successfully!")
                
        except Exception as e:
            self.send_status(f"❌ Error: {str(e)}")
        finally:
            if self.current_model:
                self.current_model.cleanup()
                
    def send_status(self, message):
        try:
            self.status_queue.put(message, block=False)
        except queue.Full:
            pass  # Skip status update if queue is full 