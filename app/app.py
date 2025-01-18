import sys
import threading
from multiprocessing import freeze_support
import queue

from core import Core
from ui import UI


class App:
    """
    +----------------------------------------------------+
    | App                                                |
    |                                                    |
    |    +-------+                                       |
    |    |  GUI  |                                       |
    |    +-------+                                       |
    |        ^                                           |
    |        | (via MP Queues)                           |
    |        v                                           |
    |  +-----------+  (Screenshot + Goal)  +-----------+ |
    |  |           | --------------------> |           | |
    |  |    Core   |                       |  Gemini   | |
    |  |           | <-------------------- |           | |
    |  +-----------+    (Instructions)     +-----------+ |
    |        |                                           |
    |        v                                           |
    |  +-------------+                                   |
    |  | Interpreter |                                   |
    |  +-------------+                                   |
    |        |                                           |
    |        v                                           |
    |  +-------------+                                   |
    |  |   Executer  |                                   |
    |  +-------------+                                   |
    +----------------------------------------------------+
    """

    def __init__(self):
        # Initialize UI first to get the queues
        self.ui = UI()
        
        # Initialize core with status queue from UI
        self.core = Core(self.ui.status_queue)
        
        # Start core thread
        self.core_thread = threading.Thread(target=self.process_requests)
        self.core_thread.daemon = True
        self.core_thread.start()
        
    def process_requests(self):
        """Process requests from the UI in a separate thread"""
        while True:
            try:
                request = self.ui.request_queue.get()
                self.core.execute_user_request(request)
            except queue.Empty:
                continue
            except Exception as e:
                self.ui.status_queue.put(f"Error processing request: {str(e)}")
                
    def run(self):
        """Start the application"""
        try:
            self.ui.start()
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'ui'):
            self.ui.cleanup()
            

if __name__ == '__main__':
    freeze_support()
    app = App()
    app.run()
    sys.exit(0) 