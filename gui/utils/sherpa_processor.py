import numpy as np


class SherpaStreamingProcessor:
    """Handles streaming STT processing with Sherpa-ONNX"""

    def __init__(self, recognizer, rate: int = 16000):
        """Initialize streaming processor

        Args:
            recognizer: Sherpa-ONNX OnlineRecognizer instance
            rate: Audio sample rate
        """
        self.recognizer = recognizer
        self.rate = rate
        self.stream = recognizer.create_stream()
        self._last_text = ""

    def process_chunk(self, data: bytes) -> tuple:
        """Process audio chunk and return (is_final, text)

        Args:
            data: Audio chunk bytes (int16 PCM)

        Returns:
            Tuple of (is_final, text). is_final is always False for Sherpa-ONNX
        """
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        self.stream.accept_waveform(self.rate, samples)

        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        text = self.recognizer.get_result(self.stream)
        if text and text != self._last_text:
            self._last_text = text
            return (False, text)
        return (False, "")

    def get_final_result(self) -> str:
        """Get final result after streaming ends

        Returns:
            Final transcribed text
        """
        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)
        return self.recognizer.get_result(self.stream).strip()
