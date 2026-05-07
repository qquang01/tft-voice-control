import customtkinter as ctk
from gui.audio_manager import AudioManager
from gui.utils.debug_logger import DebugLogger


class DevicePanel:
    """Controller for device and engine selection"""

    def __init__(
        self,
        logger: DebugLogger,
        audio_manager: AudioManager,
        parent_frame,
        on_device_change_callback: callable,
        on_engine_change_callback: callable,
        on_vad_toggle_callback: callable
    ):
        self.logger = logger
        self.audio_manager = audio_manager
        self.parent_frame = parent_frame
        self.on_device_change_callback = on_device_change_callback
        self.on_engine_change_callback = on_engine_change_callback
        self.on_vad_toggle_callback = on_vad_toggle_callback

        # UI components
        self.device_dropdown = None
        self.engine_dropdown = None
        self.vad_mode_btn = None
        self.device_names = []

    def create_panel(self):
        """Create device selection panel widgets"""
        # Device selection frame
        device_frame = ctk.CTkFrame(self.parent_frame)
        device_frame.pack(fill="x", padx=10, pady=(0, 5))

        # Device label
        device_label = ctk.CTkLabel(
            device_frame,
            text="Input Device:",
            font=("Arial", 10)
        )
        device_label.pack(side="left", padx=(0, 5))

        # Device dropdown
        audio_devices = self.audio_manager.get_audio_devices()
        self.device_names = [dev[1] for dev in audio_devices]
        self.device_dropdown = ctk.CTkOptionMenu(
            device_frame,
            values=self.device_names,
            command=self.on_device_change,
            width=300
        )
        if self.device_names:
            self.device_dropdown.set(self.device_names[0])
        self.device_dropdown.pack(side="left", padx=(0, 10))

        # Engine selection
        engine_label = ctk.CTkLabel(
            device_frame,
            text="Engine:",
            font=("Arial", 10)
        )
        engine_label.pack(side="left", padx=(10, 5))

        engine_names = ["Vosk", "Sherpa-ONNX"]
        self.engine_dropdown = ctk.CTkOptionMenu(
            device_frame,
            values=engine_names,
            command=self.on_engine_change,
            width=150
        )
        self.engine_dropdown.set(engine_names[0])
        self.engine_dropdown.pack(side="left", padx=(0, 10))

        # VAD mode toggle
        self.vad_mode_btn = ctk.CTkButton(
            device_frame,
            text="Mode: Manual",
            command=self.on_vad_toggle_callback,
            width=120
        )
        self.vad_mode_btn.pack(side="right")

        return self.device_names

    def on_device_change(self, choice: str):
        """Callback khi device thay doi"""
        self.logger.log("ACTION", f"Device changed to: {choice}")
        audio_devices = self.audio_manager.get_audio_devices()
        for i, (index, name) in enumerate(audio_devices):
            if name == choice:
                if self.on_device_change_callback:
                    self.on_device_change_callback(i, name)
                break

    def on_engine_change(self, choice: str):
        """Callback when STT engine changes"""
        self.logger.log("ACTION", f"Engine changed to: {choice}")
        if self.on_engine_change_callback:
            self.on_engine_change_callback(choice)

    def update_vad_mode_button(self, mode: str):
        """Update VAD mode button text"""
        if mode == "auto":
            self.vad_mode_btn.configure(text="Mode: Auto")
        else:
            self.vad_mode_btn.configure(text="Mode: Manual")
