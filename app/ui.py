import tkinter as tk
from tkinter import ttk as tk_ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import queue
from utils.settings import Settings

class UI:
    def __init__(self):
        self.settings = Settings()
        self.request_queue = queue.Queue()
        self.status_queue = queue.Queue()
        
        # Create main window
        self.root = ttk.Window(
            title="Computer Vision",
            themename="cosmo",
            size=(800, 600),
            resizable=(True, True)
        )
        self.root.minsize(600, 400)
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create header frame
        self.create_header()
        
        # Create settings frame
        self.create_settings_frame()
        
        # Create input frame
        self.create_input_frame()
        
        # Create status frame
        self.create_status_frame()
        
        # Start status update
        self.root.after(100, self.update_status)

    def create_header(self):
        """Create header with title and settings button"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="Computer Vision",
            font=("Helvetica", 24, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side="left", padx=5)
        
        # Settings button
        self.settings_button = ttk.Button(
            header_frame,
            text="⚙️ Settings",
            command=self.toggle_settings,
            bootstyle="secondary-outline",
            width=10
        )
        self.settings_button.pack(side="right", padx=5)

    def create_settings_frame(self):
        """Create collapsible settings frame"""
        self.settings_frame = ttk.LabelFrame(
            self.main_frame,
            text="Settings",
            padding="10",
            bootstyle="primary"
        )
        
        # API Key input
        api_frame = ttk.Frame(self.settings_frame)
        api_frame.pack(fill="x", pady=5)
        
        ttk.Label(
            api_frame,
            text="Gemini API Key:",
            bootstyle="primary"
        ).pack(side="left", padx=5)
        
        self.api_key_var = tk.StringVar(value=self.settings.get_dict().get('gemini_api_key', ''))
        self.api_key_entry = ttk.Entry(
            api_frame,
            textvariable=self.api_key_var,
            show="•",
            bootstyle="primary"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Show/Hide API key button
        self.show_api_key = ttk.Button(
            api_frame,
            text="👁️",
            command=self.toggle_api_key_visibility,
            width=3,
            bootstyle="secondary-outline"
        )
        self.show_api_key.pack(side="left", padx=5)
        
        # Save button
        save_button = ttk.Button(
            api_frame,
            text="Save",
            command=self.save_settings,
            bootstyle="success-outline",
            width=8
        )
        save_button.pack(side="left", padx=5)
        
        # Hide settings frame initially
        self.settings_visible = False

    def create_input_frame(self):
        """Create input area"""
        input_frame = ttk.LabelFrame(
            self.main_frame,
            text="Command Input",
            padding="10",
            bootstyle="primary"
        )
        input_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        # Configure input frame grid
        input_frame.grid_rowconfigure(0, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Text input - using tk.Text instead of ttk.Text
        self.input_text = tk.Text(
            input_frame,
            height=3,
            wrap="word",
            font=("Helvetica", 12),
            bg=self.root.style.colors.bg,  # Match theme background
            fg=self.root.style.colors.fg,  # Match theme foreground
            insertbackground=self.root.style.colors.primary  # Cursor color
        )
        self.input_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        
        # Model selection
        self.model_var = tk.StringVar(value="gemini")
        model_menu = ttk.OptionMenu(
            button_frame,
            self.model_var,
            "gemini",
            "gemini",
            "ollama-llama3.2-vision",
            bootstyle="primary-outline"
        )
        model_menu.pack(side="left", padx=5)
        
        # Stop button
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_request,
            state="disabled",
            bootstyle="danger-outline",
            width=8
        )
        self.stop_button.pack(side="left", padx=5)
        
        # Send button
        self.send_button = ttk.Button(
            button_frame,
            text="Send",
            command=self.send_request,
            bootstyle="success",
            width=8
        )
        self.send_button.pack(side="left", padx=5)

    def create_status_frame(self):
        """Create status area"""
        status_frame = ttk.LabelFrame(
            self.main_frame,
            text="Status",
            padding="10",
            bootstyle="primary"
        )
        status_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        
        # Configure status frame grid
        status_frame.grid_rowconfigure(0, weight=1)
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status text - using tk.Text instead of ttk.Text
        self.status_text = tk.Text(
            status_frame,
            height=8,
            wrap="word",
            font=("Helvetica", 10),
            bg=self.root.style.colors.bg,  # Match theme background
            fg=self.root.style.colors.fg,  # Match theme foreground
            state="disabled"
        )
        self.status_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            status_frame,
            orient="vertical",
            command=self.status_text.yview,
            bootstyle="primary-round"
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.status_text.configure(yscrollcommand=scrollbar.set)

    def toggle_settings(self):
        """Toggle settings frame visibility"""
        if self.settings_visible:
            self.settings_frame.grid_remove()
            self.settings_visible = False
        else:
            self.settings_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
            self.settings_visible = True

    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_entry.cget('show') == '•':
            self.api_key_entry.configure(show='')
            self.show_api_key.configure(text='🔒')
        else:
            self.api_key_entry.configure(show='•')
            self.show_api_key.configure(text='👁️')

    def save_settings(self):
        """Save settings to file"""
        api_key = self.api_key_var.get()
        self.settings.save_settings_to_file({'gemini_api_key': api_key})
        Messagebox.show_info(
            "Settings saved successfully!",
            "Success",
            parent=self.root
        )

    def send_request(self):
        """Send request to processing queue"""
        text = self.input_text.get("1.0", "end-1c").strip()
        if text:
            self.request_queue.put({
                "type": "request",
                "text": text,
                "model": self.model_var.get()
            })
            self.stop_button.configure(state="normal")
            self.send_button.configure(state="disabled")

    def stop_request(self):
        """Stop current request"""
        self.request_queue.put({"type": "stop"})
        self.stop_button.configure(state="disabled")
        self.send_button.configure(state="normal")

    def update_status(self):
        """Update status text with messages from queue"""
        try:
            while True:
                message = self.status_queue.get_nowait()
                self.status_text.configure(state="normal")
                self.status_text.insert("end", f"{message}\n")
                self.status_text.see("end")
                self.status_text.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.update_status)

    def start(self):
        """Start the UI"""
        self.root.mainloop()

    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'root') and self.root:
            self.root.destroy() 