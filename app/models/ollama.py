import os
import json
import requests
from PIL import Image
import base64
from io import BytesIO

class OllamaModel:
    def __init__(self):
        self.base_url = "http://localhost:11434/api"
        
    def get_instructions_for_objective(self, user_request: str, screenshot_path: str) -> dict:
        try:
            # Load and encode the image
            with Image.open(screenshot_path) as img:
                # Convert image to RGB if it's not
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Save to bytes
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Prepare the prompt
            system_prompt = """You are a computer control assistant. Your task is to analyze the screenshot and provide step-by-step instructions to achieve the user's objective.
            Always prefer keyboard shortcuts and efficient methods when possible.
            
            Common Mac keyboard shortcuts:
            - Command + Space: Open Spotlight Search
            - Command + Tab: Switch applications
            - Command + C/V/X: Copy/Paste/Cut
            - Command + W: Close window
            - Command + Q: Quit application
            
            Provide instructions in this JSON format:
            {
                "steps": [
                    {
                        "type": "hotkey/click/type/press",
                        "value": "the key combination or text",
                        "description": "Human-readable description of the action",
                        "x": optional_click_x_coordinate,
                        "y": optional_click_y_coordinate
                    }
                ]
            }
            
            Example valid steps:
            1. Opening Chrome:
               {"type": "hotkey", "value": ["command", "space"], "description": "Opening Spotlight Search"}
               {"type": "type", "value": "chrome", "description": "Typing Chrome"}
               {"type": "press", "value": "enter", "description": "Launching Chrome"}
               
            2. Copying text:
               {"type": "click", "value": null, "x": 100, "y": 200, "description": "Clicking text"}
               {"type": "hotkey", "value": ["command", "c"], "description": "Copying text"}
            
            IMPORTANT: Return ONLY the JSON object, without any code blocks, markdown formatting, or additional text."""
            
            # Create the request payload
            payload = {
                "model": "llama2-vision",
                "prompt": f"{system_prompt}\n\nUser Request: {user_request}",
                "images": [img_str],
                "stream": False
            }
            
            # Make the request to Ollama
            response = requests.post(f"{self.base_url}/generate", json=payload)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            response_text = result.get('response', '').strip()
            
            print(f"\nDEBUG - Raw Ollama response:\n{response_text}\n")
            
            # Clean up response text and extract JSON
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            try:
                instructions = json.loads(response_text)
                print(f"\nDEBUG - Parsed instructions:\n{json.dumps(instructions, indent=2)}\n")
                return instructions
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSON parsing error: {str(e)}")
                return {}
                
        except Exception as e:
            print(f"DEBUG - Error in getting instructions: {str(e)}")
            return {}
            
    def cleanup(self):
        """Cleanup resources if needed."""
        pass 