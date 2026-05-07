import customtkinter as ctk
import os
import sys
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as cfg

# Import local modules
from voice.stt_engine import STTFactory, VoskSTT, SherpaONNXSTT
from gui.utils.debug_logger import DebugLogger
from gui.audio_manager import AudioManager
from gui.command_handler import CommandHandler
from gui.voice_controller import VoiceController
from gui.shop_visualizer import ShopVisualizer
from gui.chat_panel import ChatPanel
from gui.device_panel import DevicePanel


class TFTGUI:
    """CustomTkinter GUI cho TFT Tool - Split Window Layout (Coordinator)"""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("TFT Voice Control Tool")
        self.root.geometry(cfg.GUI_SIZE)

        # Initialize components
        self.logger = DebugLogger(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debuglog.md"))
        self.stt_engine = STTFactory.create(cfg.STT_ENGINE, language=cfg.STT_LANGUAGE)
        self.audio_manager = AudioManager(self.logger, self._create_processor_factory())
        self.command_handler = CommandHandler(self.logger, cfg.COMMANDS, cfg.COMMAND_DESCRIPTIONS)

        self.logger.log("INFO", "GUI initialized")

        # Configure theme
        ctk.set_appearance_mode(cfg.GUI_THEME)
        ctk.set_default_color_theme(cfg.GUI_COLOR_THEME)

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Initialize sub-controllers
        self.voice_controller = None
        self.shop_visualizer = None
        self.chat_panel = None
        self.device_panel = None

        self.create_widgets()

    def _create_processor_factory(self):
        """Return a factory callable that creates the right streaming processor for current engine"""
        if isinstance(self.stt_engine, VoskSTT):
            from gui.utils.stt_processor import StreamingSTTProcessor
            return lambda: StreamingSTTProcessor(self.stt_engine.model, 16000)
        elif isinstance(self.stt_engine, SherpaONNXSTT):
            from gui.utils.sherpa_processor import SherpaStreamingProcessor
            return lambda: SherpaStreamingProcessor(self.stt_engine.recognizer, 16000)
        else:
            raise ValueError(f"Unsupported engine type: {type(self.stt_engine)}")

    def create_widgets(self):
        """Tao widgets cho split window layout"""

        # Main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Split panes (Chat + Placeholder)
        self.paned_window = ctk.CTkFrame(self.main_container)
        self.paned_window.pack(fill="both", expand=True)

        # Left side - Chat Window
        self.chat_frame = ctk.CTkFrame(self.paned_window)
        self.chat_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Right side - Placeholder (Game Preview / Controls)
        self.placeholder_frame = ctk.CTkFrame(self.paned_window)
        self.placeholder_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Placeholder header
        placeholder_header = ctk.CTkLabel(
            self.placeholder_frame,
            text="Game Preview / Controls",
            font=("Arial", 16, "bold")
        )
        placeholder_header.pack(pady=10)

        # Tabview for different views
        self.tabview = ctk.CTkTabview(self.placeholder_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initialize sub-controllers
        self._init_chat_panel()
        self._init_device_panel()
        self._init_shop_visualizer()

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Ready",
            anchor="w"
        )
        self.status_bar.pack(fill="x", pady=(10, 0))

        # Initialize voice controller after panels are created
        self._init_voice_controller()

    def _init_chat_panel(self):
        """Initialize chat panel"""
        self.chat_panel = ChatPanel(
            self.logger,
            self.command_handler,
            self.chat_frame,
            self.on_command_processed
        )
        voice_btn = self.chat_panel.create_panel()
        # Store voice button reference for voice controller
        self.voice_btn = voice_btn

    def _init_device_panel(self):
        """Initialize device panel"""
        self.device_panel = DevicePanel(
            self.logger,
            self.audio_manager,
            self.chat_frame,
            self.on_device_change,
            self.on_engine_change,
            self.toggle_vad_mode
        )
        device_names = self.device_panel.create_panel()
        self.selected_device_index = 0
        self.device_names = device_names

    def _init_shop_visualizer(self):
        """Initialize shop visualizer"""
        self.shop_visualizer = ShopVisualizer(self.logger, self.tabview, self.root)
        self.shop_visualizer.create_tab()

    def _init_voice_controller(self):
        """Initialize voice controller"""
        self.voice_controller = VoiceController(
            self.logger,
            self.audio_manager,
            self.stt_engine,
            self._create_processor_factory(),
            self.root,
            self._on_voice_partial,
            self._on_voice_final,
            self.update_status
        )
        # Connect voice button to voice controller
        self.voice_btn.configure(command=self.voice_controller.toggle_voice)


    def _on_voice_partial(self, text: str):
        """Callback for partial transcription results"""
        self.chat_panel.update_text_input(text)
        self.chat_panel.update_streaming_display(text)

    def _on_voice_final(self, final_text: Optional[str], error: Optional[str] = None):
        """Callback for final transcription results"""
        self.chat_panel.clear_streaming_display()
        self.voice_btn.configure(text="Start")

        if error:
            self.chat_panel.add_chat_message("Error", f"Recording error: {error}")
            return

        if not final_text:
            self.chat_panel.add_chat_message("Warning", "No text transcribed")
            return

        self.chat_panel.add_chat_message("Voice", final_text)
        self.chat_panel.process_command(final_text)

    def on_device_change(self, index: int, name: str):
        """Callback khi device thay doi"""
        self.selected_device_index = index
        self.update_status(f"Selected: {name}")
        self.logger.log("ACTION", f"Selected device index: {index}, name: {name}")

    def on_engine_change(self, choice: str):
        """Callback when STT engine changes"""
        engine_map = {
            "Vosk": ("vosk", "vi"),
            "Sherpa-ONNX": ("sherpa_onnx", "vi"),
        }
        engine_name, lang = engine_map.get(choice, ("vosk", "vi"))
        success = self.voice_controller.switch_engine(engine_name, lang)
        if success:
            self.chat_panel.add_chat_message("System", f"Switched to {choice} engine")
        else:
            self.chat_panel.add_chat_message("Error", f"Failed to switch engine")

    def toggle_vad_mode(self):
        """Toggle giua manual va auto VAD mode"""
        mode = self.voice_controller.toggle_vad_mode()
        self.device_panel.update_vad_mode_button(mode)
        if mode == "auto":
            self.voice_btn.configure(text="Start (Auto)")
            self.chat_panel.add_chat_message("System", "Switched to Auto Mode - VAD will auto-detect speech")
            self.update_status("VAD Auto Mode")
        else:
            self.voice_btn.configure(text="Start")
            self.chat_panel.add_chat_message("System", "Switched to Manual Mode - Press button to record")
            self.update_status("VAD Manual Mode")

    def on_command_processed(self, text: str):
        """Callback when command is processed"""
        # Could update placeholder or other UI elements
        pass

    def update_status(self, status: str):
        """Cap nhat status bar"""
        self.status_bar.configure(text=status)
        self.logger.log("STATUS", status)

    def _on_closing(self):
        """Window close handler - cleanup resources"""
        self.logger.log("INFO", "Window closing - cleaning up")
        if self.audio_manager:
            self.audio_manager.cleanup()
        self.root.destroy()

    def run(self):
        """Chay GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = TFTGUI()
        app.run()
    except Exception as e:
        # Log unhandled exceptions without wiping existing log
        logger = DebugLogger(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debuglog.md"),
            clear_on_init=False
        )
        logger.log("CRITICAL", f"Unhandled exception: {str(e)}")
        import traceback
        logger.log("CRITICAL", f"Traceback: {traceback.format_exc()}")
        print(f"Critical error: {e}")
        print(traceback.format_exc())
