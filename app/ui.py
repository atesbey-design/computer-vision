import os
import queue
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.settings import Settings

class UI:
    def __init__(self):
        self.request_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.window = MainWindow(self.request_queue, self.status_queue)
        
    def start(self):
        self.window.mainloop()
        
    def cleanup(self):
        self.window.destroy()

class MainWindow(ttk.Window):
    def __init__(self, request_queue, status_queue):
        super().__init__(themename="darkly")
        
        self.request_queue = request_queue
        self.status_queue = status_queue
        self.settings_window = None
        
        self.title("Computer Use Assistant")
        self.geometry("800x600")
        
        self.create_menu()
        self.create_widgets()
        self.configure_grid()
        self.start_status_check()
        
    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Open Settings", command=self.open_settings)
        
    def create_widgets(self):
        # Model selection
        model_frame = ttk.LabelFrame(self, text="Model Selection", padding=10)
        model_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.model_var = tk.StringVar(value="gemini")
        ttk.Radiobutton(model_frame, text="Gemini", variable=self.model_var, value="gemini").pack(side="left", padx=10)
        ttk.Radiobutton(model_frame, text="Ollama", variable=self.model_var, value="ollama-llama3.2-vision").pack(side="left", padx=10)
        
        # Input area
        input_frame = ttk.LabelFrame(self, text="Command Input", padding=10)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        
        self.input_text = ttk.Text(input_frame, height=3, width=50)
        self.input_text.pack(fill="both", expand=True)
        
        # Buttons
        button_frame = ttk.Frame(self, padding=10)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10)
        
        self.send_button = ttk.Button(
            button_frame,
            text="Send Request",
            command=self.send_request,
            style="primary.TButton"
        )
        self.send_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_request,
            style="danger.TButton"
        )
        self.stop_button.pack(side="left", padx=5)
        
        # Status area
        status_frame = ttk.LabelFrame(self, text="Status", padding=10)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        
        self.status_text = ttk.Text(status_frame, height=15, width=50, state="disabled")
        self.status_text.pack(fill="both", expand=True)
        
        # Scrollbar for status
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
    def send_request(self):
        text = self.input_text.get("1.0", "end-1c").strip()
        if text:
            request = {
                "type": "request",
                "model": self.model_var.get(),
                "text": text
            }
            self.request_queue.put(request)
            self.send_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            
    def stop_request(self):
        self.request_queue.put({"type": "stop"})
        self.send_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
    def start_status_check(self):
        self.check_status()
        
    def check_status(self):
        try:
            while True:
                status = self.status_queue.get_nowait()
                self.status_text.configure(state="normal")
                self.status_text.insert("end", f"{status}\n")
                self.status_text.see("end")
                self.status_text.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_status)
            
    def open_settings(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(self)
            
class SettingsWindow(ttk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Settings")
        self.geometry("400x300")
        
        self.settings = Settings()
        self.create_widgets()
        
    def create_widgets(self):
        # API Keys
        api_frame = ttk.LabelFrame(self, text="API Keys", padding=10)
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(api_frame, text="Gemini API Key:").pack(anchor="w")
        self.gemini_key = ttk.Entry(api_frame, show="*")
        self.gemini_key.pack(fill="x", pady=5)
        self.gemini_key.insert(0, self.settings.get_dict().get("gemini_api_key", ""))
        
        # Save button
        save_button = ttk.Button(
            self,
            text="Save Settings",
            command=self.save_settings,
            style="primary.TButton"
        )
        save_button.pack(pady=10)
        
    def save_settings(self):
        settings_dict = self.settings.get_dict()
        settings_dict["gemini_api_key"] = self.gemini_key.get()
        self.settings.save_settings_to_file(settings_dict)
        self.destroy()
        self.master.settings_window = None 