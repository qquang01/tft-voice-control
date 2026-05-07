import json


class StreamingSTTProcessor:
    """Handles streaming STT processing with Vosk"""
    
    def __init__(self, model, rate: int = 16000):
        """Initialize streaming STT processor
        
        Args:
            model: Vosk model instance
            rate: Audio sample rate
        """
        from vosk import KaldiRecognizer
        self.recognizer = KaldiRecognizer(model, rate)
        self.recognizer.SetWords(True)
        self.rate = rate
        self._last_text = ""

    def process_chunk(self, data: bytes) -> tuple:
        """Process audio chunk and return (is_final, text).

        Only returns text when it changes to avoid duplicate callbacks.

        Args:
            data: Audio chunk bytes

        Returns:
            Tuple of (is_final, text)
        """
        if self.recognizer.AcceptWaveform(data):
            res = json.loads(self.recognizer.Result())
            text = res.get("text", "")
            if text and text != self._last_text:
                self._last_text = text
                return (True, text)
            return (False, "")
        else:
            res = json.loads(self.recognizer.PartialResult())
            text = res.get("partial", "")
            if text and text != self._last_text:
                self._last_text = text
                return (False, text)
            return (False, "")
    
    def get_final_result(self) -> str:
        """Get final result after streaming ends
        
        Returns:
            Final transcribed text
        """
        try:
            res = json.loads(self.recognizer.FinalResult())
            return res.get("text", "")
        except Exception:
            return ""
