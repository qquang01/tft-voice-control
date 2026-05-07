import os
from datetime import datetime


class DebugLogger:
    """Debug logger for TFT Tool"""
    
    def __init__(self, log_file: str = "debuglog.md", clear_on_init: bool = True):
        self.log_file = log_file
        if clear_on_init:
            self.clear_log()  # Clear previous session
    
    def clear_log(self):
        """Clear log file for new session"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"# TFT Tool Debug Log\n")
                f.write(f"# Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Auto-cleared on new session\n\n")
        except Exception as e:
            print(f"Failed to clear log: {e}")
    
    def log(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write log: {e}")
        
        # Also print to console
        print(log_entry.strip())
