import os
import json
import time
from typing import Any, Optional

import google.generativeai as genai
from google.generativeai.types import content_types

from utils.screen import Screen
from utils.settings import Settings


class GeminiModel:
    def __init__(self):
        settings = Settings().get_dict()
        api_key = settings.get('gemini_api_key')
        
        if not api_key:
            raise Exception("API key not found in settings")
            
        genai.configure(api_key=api_key)
        
        # Initialize Gemini Pro Vision model
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Set default parameters
        self.generation_config = {
            'temperature': 0.1,
            'top_p': 1,
            'top_k': 32,
            'max_output_tokens': 2048,
        }
        
        # Define system prompt
        self.context = """You are an AI assistant that helps users control their computer by analyzing screenshots and providing step-by-step instructions.
        
        Your task is to:
        1. Analyze the screenshot to understand the current state of the computer
        2. Break down the user's request into specific steps
        3. ALWAYS TRY KEYBOARD SHORTCUTS FIRST
        4. Only use mouse controls when keyboard shortcuts are not possible or would be significantly less efficient
        5. Provide clear feedback about what's happening

        PRIORITY ORDER for actions:
        1. System keyboard shortcuts (Command+Space, Command+Tab, etc.)
        2. Application keyboard shortcuts (Command+C, Command+V, etc.)
        3. Navigation keys (Tab, Arrow keys, Enter, Escape)
        4. Mouse actions (only when above options aren't suitable)

        Available keyboard commands:
        1. Hotkey command:
        {
            "type": "hotkey",
            "value": "command+space",  // Keys joined with '+'
            "description": "Using keyboard shortcut [describe action]"
        }

        2. Single key press:
        {
            "type": "press",
            "value": "enter",  // Single key name
            "description": "Pressing [key name]"
        }

        3. Text typing:
        {
            "type": "type",
            "value": "text to type",
            "description": "Typing [what is being typed]"
        }

        Common keyboard shortcuts to use FIRST:
        - Opening apps: "command+space" then type app name
        - Window management: 
          - "command+tab" (switch apps)
          - "command+`" (switch windows)
          - "command+w" (close window)
          - "command+q" (quit app)
        - Text editing:
          - "command+a" (select all)
          - "command+c" (copy)
          - "command+v" (paste)
          - "command+z" (undo)
        - Navigation:
          - "tab" (move between fields)
          - "space" (select/click buttons)
          - "enter" (confirm/submit)
          - "escape" (cancel/close)
          - Arrow keys for movement

        Only when keyboard shortcuts are not possible, use mouse commands:
        {
            "type": "move",
            "x": number,
            "y": number,
            "description": "Moving mouse to [target]"
        }
        {
            "type": "click",
            "x": number,
            "y": number,
            "description": "Clicking on [target]"
        }
        {
            "type": "drag",
            "x": number,
            "y": number,
            "description": "Dragging to [target]"
        }
        {
            "type": "scroll",
            "value": number,  // positive for up, negative for down
            "description": "Scrolling [direction]"
        }

        Your response MUST be in this format:
        {
            "steps": [
                // Array of command objects as shown above
            ],
            "done": "Task completed successfully" or null,
            "feedback": "Description of what's happening"
        }

        Example response for opening Chrome:
        {
            "steps": [
                {
                    "type": "hotkey",
                    "value": "command+space",
                    "description": "Opening Spotlight Search"
                },
                {
                    "type": "type",
                    "value": "chrome",
                    "description": "Typing Chrome"
                },
                {
                    "type": "press",
                    "value": "enter",
                    "description": "Launching Chrome"
                }
            ],
            "done": null,
            "feedback": "Opening Chrome browser using keyboard shortcuts"
        }

        REMEMBER:
        1. ALWAYS try keyboard shortcuts first
        2. Only use mouse when keyboard shortcuts won't work
        3. If using mouse, always include both move and click commands
        4. Use precise coordinates from screenshot analysis
        """

    def get_instructions_for_objective(self, user_request: str, step_num: int = 0) -> dict[str, Any]:
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Get screenshot and screen info
                screen = Screen()
                screenshot_path = screen.get_screenshot_file()
                screen_info = screen.get_screen_info()
                
                # Format the request with screen information
                request_data = {
                    'original_user_request': user_request,
                    'step_num': step_num,
                    'screen_info': screen_info
                }
                
                # Create prompt with context and screen info
                prompt = f"""
{self.context}

CURRENT SCREEN INFORMATION:
- Screen Resolution: {screen_info['screen_resolution']['width']}x{screen_info['screen_resolution']['height']}
- Current Mouse Position: ({screen_info['mouse_position']['x']}, {screen_info['mouse_position']['y']})

When using mouse coordinates:
1. Ensure coordinates are within screen bounds (0,0) to ({screen_info['screen_resolution']['width']},{screen_info['screen_resolution']['height']})
2. Consider current mouse position at ({screen_info['mouse_position']['x']}, {screen_info['mouse_position']['y']}) for efficient movement
3. Use relative movements when possible for better accuracy

User Request: {json.dumps(request_data)}
"""
                
                # Load and process the image
                image_parts = [
                    {
                        "mime_type": "image/png",
                        "data": open(screenshot_path, "rb").read()
                    }
                ]
                
                # Generate response with retry logic
                try:
                    response = self.model.generate_content(
                        contents=[prompt, image_parts[0]],
                        generation_config=self.generation_config
                    )
                except Exception as e:
                    if "429" in str(e) and retry_count < max_retries - 1:
                        print(f"Rate limit hit, retrying in {(retry_count + 1) * 2} seconds...")
                        time.sleep((retry_count + 1) * 2)
                        retry_count += 1
                        continue
                    raise e
                
                # Extract JSON from response
                response_text = response.text
                print(f"\nDEBUG - Raw Gemini response:\n{response_text}\n")
                
                start_index = response_text.find('{')
                end_index = response_text.rfind('}')
                
                if start_index == -1 or end_index == -1:
                    print("DEBUG - No JSON found in response")
                    return {}
                    
                json_str = response_text[start_index:end_index + 1]
                print(f"\nDEBUG - Extracted JSON:\n{json_str}\n")
                
                try:
                    parsed_response = json.loads(json_str)
                    
                    # Validate coordinates are within screen bounds
                    if 'steps' in parsed_response:
                        for step in parsed_response['steps']:
                            if step.get('type') in ['move', 'click', 'drag']:
                                x = step.get('x', 0)
                                y = step.get('y', 0)
                                if not (0 <= x <= screen_info['screen_resolution']['width'] and 
                                      0 <= y <= screen_info['screen_resolution']['height']):
                                    print(f"DEBUG - Invalid coordinates ({x}, {y}) outside screen bounds")
                                    return {}
                    
                    print(f"\nDEBUG - Parsed response:\n{json.dumps(parsed_response, indent=2)}\n")
                    return parsed_response
                except json.JSONDecodeError as e:
                    print(f"DEBUG - JSON parsing error: {str(e)}")
                    if retry_count < max_retries - 1:
                        print("Retrying with different response format...")
                        retry_count += 1
                        continue
                    return {}
                    
            except Exception as e:
                print(f"DEBUG - Error in getting instructions: {str(e)}")
                if retry_count < max_retries - 1:
                    print(f"Retrying after error... ({retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                return {}
        
        return {}
            
    def cleanup(self):
        """Cleanup any resources if needed"""
        pass 