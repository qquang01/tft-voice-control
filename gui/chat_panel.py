import customtkinter as ctk
from gui.command_handler import CommandHandler
from gui.utils.debug_logger import DebugLogger


class ChatPanel:
    """Controller for chat display and message handling"""

    def __init__(
        self,
        logger: DebugLogger,
        command_handler: CommandHandler,
        parent_frame,
        on_command_callback: callable
    ):
        self.logger = logger
        self.command_handler = command_handler
        self.parent_frame = parent_frame
        self.on_command_callback = on_command_callback

        # UI components
        self.chat_display = None
        self.streaming_display = None
        self.streaming_label = None
        self.vad_indicator = None
        self.text_input = None
        self.send_btn = None
        self.voice_btn = None

    def create_panel(self):
        """Create chat panel widgets"""
        # Chat header
        chat_header = ctk.CTkLabel(
            self.parent_frame,
            text="Chat / Voice Input",
            font=("Arial", 16, "bold")
        )
        chat_header.pack(pady=10)

        # Streaming display (real-time STT)
        streaming_frame = ctk.CTkFrame(self.parent_frame)
        streaming_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Streaming header with VAD indicator
        streaming_header = ctk.CTkFrame(streaming_frame, fg_color="transparent")
        streaming_header.pack(fill="x", padx=5, pady=(5, 0))

        self.streaming_label = ctk.CTkLabel(
            streaming_header,
            text="Live Transcription:",
            font=("Arial", 10, "bold")
        )
        self.streaming_label.pack(side="left")

        # VAD indicator (dot that lights up when speech detected)
        self.vad_indicator = ctk.CTkLabel(
            streaming_header,
            text="●",
            font=("Arial", 20),
            text_color="#555555"  # Gray when inactive
        )
        self.vad_indicator.pack(side="right", padx=5)

        self.streaming_display = ctk.CTkLabel(
            streaming_frame,
            text="",
            font=("Arial", 14),
            wraplength=500,
            anchor="w"
        )
        self.streaming_display.pack(fill="x", padx=5, pady=(0, 5))

        # Chat display (read-only)
        self.chat_display = ctk.CTkTextbox(
            self.parent_frame,
            font=("Arial", 12),
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Input frame
        input_frame = ctk.CTkFrame(self.parent_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Voice button
        self.voice_btn = ctk.CTkButton(
            input_frame,
            text="Start",
            height=40
        )
        self.voice_btn.pack(side="left", padx=(0, 10))

        # Text input
        self.text_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type command or press Start...",
            height=40
        )
        self.text_input.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Send button
        self.send_btn = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_message,
            height=40
        )
        self.send_btn.pack(side="right")

        return self.voice_btn

    def send_message(self):
        """Gui message"""
        message = self.text_input.get()
        if message:
            self.add_chat_message("User", message)
            self.text_input.delete(0, "end")
            self.process_command(message)

    def add_chat_message(self, sender: str, message: str):
        """Them message vao chat display"""
        # Only log to debuglog, don't display in chat (except for user/voice messages)
        if sender not in ["System", "Status", "Action", "INFO", "ERROR", "WARNING"]:
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", f"{sender}: {message}\n\n")
            self.chat_display.see("end")
            self.chat_display.configure(state="disabled")

        # Log to debuglog
        self.logger.log("CHAT", f"{sender}: {message}")

    def process_command(self, command: str):
        """Xu ly command tu user"""
        result = self.command_handler.process_command(command)

        if result['action']:
            action_desc = self.command_handler.get_action_description(result['action'])
            self.add_chat_message("System", f"Command: {action_desc}")
            if self.on_command_callback:
                self.on_command_callback(f"Command: {command}\nAction: {result['action'].upper()}")
        else:
            self.add_chat_message("System", f"Command not recognized: {command}")
            if self.on_command_callback:
                self.on_command_callback(f"Command: {command}\nStatus: Unknown")

    def update_text_input(self, text: str):
        """Update text input with transcribed text"""
        self.text_input.delete(0, "end")
        self.text_input.insert(0, text)

    def update_streaming_display(self, text: str):
        """Update streaming display with partial transcription"""
        self.streaming_display.configure(text=text)

    def update_vad_indicator(self, is_speech: bool):
        """Update VAD indicator based on speech detection"""
        if is_speech:
            # Green when speech detected
            self.vad_indicator.configure(text_color="#00FF00")
        else:
            # Gray when silence
            self.vad_indicator.configure(text_color="#555555")

    def clear_streaming_display(self):
        """Clear streaming display"""
        self.streaming_display.configure(text="")
        self.vad_indicator.configure(text_color="#555555")

    def set_voice_button_text(self, text: str):
        """Update voice button text"""
        self.voice_btn.configure(text=text)
