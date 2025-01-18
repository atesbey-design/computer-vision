import os
import tempfile
from pathlib import Path
import json
import time

import pyautogui
from PIL import Image, ImageDraw


class Screen:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'computer-use-gemini')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Get screen size on initialization
        self.screen_width, self.screen_height = pyautogui.size()
        self.current_highlight = None

    def get_screen_info(self) -> dict:
        """Get current screen and mouse information"""
        current_mouse_x, current_mouse_y = pyautogui.position()
        return {
            "screen_resolution": {
                "width": self.screen_width,
                "height": self.screen_height
            },
            "mouse_position": {
                "x": current_mouse_x,
                "y": current_mouse_y
            },
            "active_highlight": self.current_highlight
        }

    def highlight_region(self, x: int, y: int, width: int, height: int, duration: float = 2.0):
        """Highlight a region of the screen with a blue border"""
        try:
            # Save the region coordinates
            self.current_highlight = {
                "x": x,
                "y": y,
                "width": width,
                "height": height
            }
            
            # Take a screenshot of the region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            # Create a new image with the same size
            highlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(highlight)
            
            # Draw a blue border (3 pixels thick)
            border_color = (0, 120, 255, 255)  # Blue with full opacity
            for i in range(3):  # 3 pixel thickness
                draw.rectangle(
                    [i, i, width-1-i, height-1-i],
                    outline=border_color
                )
            
            # Combine the original screenshot with the highlight
            screenshot = screenshot.convert('RGBA')
            highlighted = Image.alpha_composite(screenshot, highlight)
            
            # Save the highlighted image
            temp_path = os.path.join(self.temp_dir, 'highlight.png')
            highlighted.save(temp_path)
            
            # Keep the highlight visible for the specified duration
            time.sleep(duration)
            
            return True
        except Exception as e:
            print(f"Error highlighting region: {e}")
            return False

    def get_screenshot_file(self) -> str:
        """Take a screenshot and save it with screen information"""
        screenshot = pyautogui.screenshot()
        
        # Create a unique filename for the screenshot
        screenshot_path = os.path.join(self.temp_dir, 'current_screen.png')
        info_path = os.path.join(self.temp_dir, 'screen_info.json')
        
        # If there's an active highlight, add it to the screenshot
        if self.current_highlight:
            # Create a new image with the same size as the screenshot
            highlight = Image.new('RGBA', screenshot.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(highlight)
            
            # Draw the blue border around the highlighted region
            x = self.current_highlight['x']
            y = self.current_highlight['y']
            width = self.current_highlight['width']
            height = self.current_highlight['height']
            
            border_color = (0, 120, 255, 255)  # Blue with full opacity
            for i in range(3):  # 3 pixel thickness
                draw.rectangle(
                    [x+i, y+i, x+width-1-i, y+height-1-i],
                    outline=border_color
                )
            
            # Combine the screenshot with the highlight
            screenshot = screenshot.convert('RGBA')
            screenshot = Image.alpha_composite(screenshot, highlight)
        
        # Save the screenshot
        screenshot.save(screenshot_path, 'PNG')
        
        # Save screen information
        screen_info = self.get_screen_info()
        with open(info_path, 'w') as f:
            json.dump(screen_info, f, indent=2)
        
        return screenshot_path 