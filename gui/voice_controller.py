import threading
from typing import Optional, Callable
from voice.stt_engine import STTFactory, VoskSTT, SherpaONNXSTT
from gui.audio_manager import AudioManager
from gui.utils.debug_logger import DebugLogger


class VoiceController:
    """Controller for voice recording and STT functionality"""

    def __init__(
        self,
        logger: DebugLogger,
        audio_manager: AudioManager,
        stt_engine,
        processor_factory: Callable,
        root,
        on_partial_callback: Callable[[str], None],
        on_final_callback: Callable[[Optional[str], Optional[str]], None],
        on_status_callback: Callable[[str], None]
    ):
        self.logger = logger
        self.audio_manager = audio_manager
        self.stt_engine = stt_engine
        self.processor_factory = processor_factory
        self.root = root
        self.on_partial_callback = on_partial_callback
        self.on_final_callback = on_final_callback
        self.on_status_callback = on_status_callback

        self.recording = False
        self.vad_mode = "manual"  # "manual" or "auto"

    def toggle_voice(self):
        """Bat/tat ghi am"""
        self.logger.log("ACTION", f"Toggle voice - recording={self.audio_manager.recording}")
        if not self.audio_manager.recording:
            self._start_recording()
        else:
            self._request_stop_recording()

    def _start_recording(self):
        """Bat dau ghi am trong thread rieng"""
        self.audio_manager.recording = True
        self.on_status_callback("Recording...")
        self.logger.log("ACTION", f"Starting recording in {self.vad_mode} mode")

        method = "vad" if self.vad_mode == "auto" else "manual"
        threading.Thread(target=self._recording_worker, args=(method,), daemon=True).start()

    def _recording_worker(self, method: str):
        """Worker thread: ghi am + streaming STT"""
        device_index = self.audio_manager.get_audio_devices()[0][0]

        # Partial callback: schedule GUI update on main thread via after()
        def partial_callback(text: str):
            if text:
                self.root.after(0, lambda t=text: self._update_partial(t))

        # VAD callback: update indicator on main thread
        def vad_callback(is_speech: bool):
            self.root.after(0, lambda s=is_speech: self._update_vad_indicator(s))

        try:
            if method == "manual":
                final_text = self.audio_manager.record_manual(device_index, partial_callback)
            else:
                final_text = self.audio_manager.record_vad(device_index, partial_callback, vad_callback)

            self.root.after(0, lambda ft=final_text: self._finalize_recording(ft))
        except Exception as e:
            self.logger.log("ERROR", f"Recording error: {e}")
            self.root.after(0, lambda err=str(e): self._finalize_recording(None, err))

    def _request_stop_recording(self):
        """User nhan Stop: chi set flag, khong cham GUI"""
        self.audio_manager.recording = False
        self.on_status_callback("Stopping...")
        self.logger.log("ACTION", "Stop requested by user")

    def _update_partial(self, text: str):
        """Update text input voi partial result (chay tren main thread)"""
        self.on_partial_callback(text)
        self.on_status_callback(f"Transcribing: {text[:30]}...")

    def _update_vad_indicator(self, is_speech: bool):
        """Update VAD indicator based on speech detection"""
        # This will be handled by the UI component
        pass

    def _finalize_recording(self, final_text: Optional[str], error: Optional[str] = None):
        """Hoan tat ghi am, update GUI (chay tren main thread)"""
        self.audio_manager.recording = False

        if error:
            self.on_final_callback(None, error)
            self.on_status_callback("Ready")
            return

        if not final_text:
            self.on_final_callback(None, None)
            self.on_status_callback("Ready")
            return

        self.on_final_callback(final_text, None)
        self.on_status_callback("Ready")
        self.logger.log("ACTION", f"Final transcription: {final_text}")

    def toggle_vad_mode(self):
        """Toggle giua manual va auto VAD mode"""
        self.logger.log("ACTION", f"Toggle VAD mode - Current: {self.vad_mode}")
        if self.vad_mode == "manual":
            self.vad_mode = "auto"
            self.logger.log("ACTION", "Switched to Auto VAD mode")
            return "auto"
        else:
            self.vad_mode = "manual"
            self.logger.log("ACTION", "Switched to Manual VAD mode")
            return "manual"

    def switch_engine(self, engine_name: str, language: str = "vi"):
        """Switch STT engine"""
        try:
            self.stt_engine = STTFactory.create(engine_name, language=language)
            # Recreate audio manager with new processor factory
            self.audio_manager.cleanup()
            self.audio_manager = AudioManager(self.logger, self.processor_factory)
            self.on_status_callback(f"Engine: {engine_name}")
            self.logger.log("ACTION", f"Engine switched successfully to {engine_name}")
            return True
        except Exception as e:
            self.logger.log("ERROR", f"Engine switch failed: {e}")
            self.on_status_callback("Engine switch failed")
            return False
