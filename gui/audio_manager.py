import pyaudio
import webrtcvad
from contextlib import contextmanager
from typing import Optional, List, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

# Resolve audio format string to pyaudio constant
_FORMAT_MAP = {
    "paFloat32": pyaudio.paFloat32,
    "paInt32": pyaudio.paInt32,
    "paInt24": pyaudio.paInt24,
    "paInt16": pyaudio.paInt16,
    "paInt8": pyaudio.paInt8,
    "paUInt8": pyaudio.paUInt8,
}

AUDIO_CONFIG = {
    "CHUNK": cfg.AUDIO_CONFIG["CHUNK"],
    "CHUNK_VAD": cfg.AUDIO_CONFIG["CHUNK_VAD"],
    "FORMAT": _FORMAT_MAP.get(cfg.AUDIO_CONFIG["FORMAT"], pyaudio.paInt16),
    "CHANNELS": cfg.AUDIO_CONFIG["CHANNELS"],
    "RATE": cfg.AUDIO_CONFIG["RATE"],
    "MAX_SILENCE_FRAMES": cfg.VAD_MAX_SILENCE_FRAMES,
}


class AudioManager:
    """Manages audio recording and STT processing"""

    def __init__(self, logger, processor_factory: Callable):
        """Initialize audio manager

        Args:
            logger: DebugLogger instance
            processor_factory: Callable that returns a streaming processor with
                process_chunk(data: bytes) -> (is_final, text) and get_final_result() -> str
        """
        self.logger = logger
        self.processor_factory = processor_factory
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recording = False

        # VAD settings
        self.vad = webrtcvad.Vad(cfg.VAD_AGGRESSIVENESS)
        self.speech_detected = False
        self.silence_duration = 0

    def get_audio_devices(self) -> List[tuple]:
        """Get list of audio input devices with details"""
        devices = []
        seen_names = set()
        try:
            for i in range(self.p.get_device_count()):
                info = self.p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_type = "Unknown"
                    name_lower = info['name'].lower()
                    if 'usb' in name_lower:
                        device_type = "USB"
                    elif 'microphone' in name_lower:
                        device_type = "Mic"
                    elif 'headset' in name_lower:
                        device_type = "Headset"
                    elif 'default' in name_lower:
                        device_type = "Default"

                    display_name = f"[{device_type}] {info['name']}"

                    if display_name not in seen_names:
                        seen_names.add(display_name)
                        devices.append((i, display_name))
        except Exception as e:
            self.logger.log("ERROR", f"Failed to get audio devices: {e}")
            devices = [(0, "Default")]
        return devices

    def _try_open_stream(self, device_index: Optional[int] = None, chunk_size: int = None):
        """Open audio stream, falling back to default device if needed"""
        if chunk_size is None:
            chunk_size = AUDIO_CONFIG['CHUNK']

        try:
            return self.p.open(
                format=AUDIO_CONFIG['FORMAT'],
                channels=AUDIO_CONFIG['CHANNELS'],
                rate=AUDIO_CONFIG['RATE'],
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk_size
            )
        except Exception as e:
            self.logger.log("WARNING", f"Cannot open device {device_index}: {e}")
            return self.p.open(
                format=AUDIO_CONFIG['FORMAT'],
                channels=AUDIO_CONFIG['CHANNELS'],
                rate=AUDIO_CONFIG['RATE'],
                input=True,
                frames_per_buffer=chunk_size
            )

    @contextmanager
    def _audio_stream(self, device_index: Optional[int] = None, chunk_size: int = None):
        """Context manager for audio stream with automatic cleanup"""
        stream = self._try_open_stream(device_index, chunk_size)
        try:
            yield stream
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass

    def record_manual(self, device_index: int, partial_callback: Callable[[str], None]) -> str:
        """Record audio in manual mode with streaming STT

        Args:
            device_index: Audio device index
            partial_callback: Callback for partial results

        Returns:
            Final transcribed text
        """
        with self._audio_stream(device_index, AUDIO_CONFIG['CHUNK']) as stream:
            processor = self.processor_factory()
            self.logger.log("ACTION", "Starting manual streaming STT")

            while self.recording:
                try:
                    data = stream.read(AUDIO_CONFIG['CHUNK'], exception_on_overflow=False)
                    is_final, text = processor.process_chunk(data)
                    if text:
                        partial_callback(text)
                except Exception as e:
                    self.logger.log("ERROR", f"Streaming error: {e}")
                    break

            return processor.get_final_result()

    def record_vad(self, device_index: int, partial_callback: Callable[[str], None], vad_callback: Callable[[bool], None] = None) -> str:
        """Record audio with VAD auto-detection and streaming STT

        Args:
            device_index: Audio device index
            partial_callback: Callback for partial results
            vad_callback: Callback for VAD state changes (True=speech, False=silence)

        Returns:
            Final transcribed text
        """
        with self._audio_stream(device_index, AUDIO_CONFIG['CHUNK_VAD']) as stream:
            processor = self.processor_factory()
            self.speech_detected = False
            self.silence_duration = 0

            self.logger.log("ACTION", "Starting VAD streaming STT")

            chunk_size = AUDIO_CONFIG['CHUNK_VAD']
            chunk_count = 0
            while self.recording:
                try:
                    data = stream.read(chunk_size, exception_on_overflow=False)
                    is_speech = self.vad.is_speech(data, AUDIO_CONFIG['RATE'])
                    chunk_count += 1

                    # Log every 50 chunks to avoid flooding
                    if chunk_count % 50 == 0:
                        self.logger.log("INFO", f"Processed {chunk_count} chunks, speech_detected={self.speech_detected}, is_speech={is_speech}")

                    if is_speech:
                        if not self.speech_detected:
                            self.speech_detected = True
                            self.logger.log("INFO", "Speech detected")
                            if vad_callback:
                                vad_callback(True)

                        is_final, text = processor.process_chunk(data)
                        if text:
                            self.logger.log("INFO", f"STT partial: {text}")
                            partial_callback(text)
                        self.silence_duration = 0
                    else:
                        if self.speech_detected:
                            self.silence_duration += 1
                            if self.silence_duration >= AUDIO_CONFIG['MAX_SILENCE_FRAMES']:
                                self.logger.log("INFO", "Silence detected - stopping")
                                if vad_callback:
                                    vad_callback(False)
                                break
                        elif vad_callback and self.speech_detected:
                            vad_callback(False)
                except Exception as e:
                    self.logger.log("ERROR", f"VAD processing error: {e}")
                    if self.speech_detected:
                        self.silence_duration += 1
                    continue

            return processor.get_final_result()

    def cleanup(self):
        """Cleanup audio resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        self.p.terminate()
