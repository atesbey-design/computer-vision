import os
import json
from PIL import Image
import base64
from io import BytesIO
from dotenv import load_dotenv
from groq import Groq

class GroqModel:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.2-90b-vision-preview"
        
    def get_instructions_for_objective(self, user_request: str, screenshot_path: str) -> dict:
        try:
            # Load and encode the image
            with Image.open(screenshot_path) as img:
                # Resize image to reduce token size
                max_size = (800, 800)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=85)
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
            }"""
            
            # Create the chat completion
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Request: {user_request}\nImage: {img_str}"}
                ],
                temperature=0.7,
                max_completion_tokens=1024,
                top_p=1,
                stream=False
            )
            
            # Get the response
            response_text = completion.choices[0].message.content.strip()
            print(f"\nDEBUG - Raw Groq response:\n{response_text}\n")
            
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