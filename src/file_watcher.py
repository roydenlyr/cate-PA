import os
import time
import glob

class FileWatcher:
    def __init__(self, watch_folder, callback):
        self.watch_folder = watch_folder
        self.callback = callback
        self.processed = set()

    def is_file_ready(self, file_path):
        """Check if the file is fully written by comparing its size over a short interval.
        """
        try:
            initial_size = os.path.getsize(file_path)
            time.sleep(0.5)  # Wait a bit before checking again
            final_size = os.path.getsize(file_path)
            return initial_size == final_size and initial_size > 0
        except OSError:
            return False
        
    def start(self):
        os.makedirs(self.watch_folder, exist_ok=True)
        print(f"Watching folder: {self.watch_folder}")
        
        while True:
            files = glob.glob(os.path.join(self.watch_folder, '*.wav'))
            for file_path in files:
                if file_path not in self.processed and self.is_file_ready(file_path):
                    self.processed.add(file_path)
                    try:
                        self.callback(file_path)
                        os.remove(file_path) 
                        print(f"Processed and removed: {file_path}")
                    except Exception as e:
                        print(f"Error processing {os.path.basename(file_path)}: {e}")
                    finally:
                        self.processed.discard(file_path)
            time.sleep(1) # Check for new files every second
