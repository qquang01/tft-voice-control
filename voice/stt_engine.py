import sys
import os
import time
import threading
from typing import Optional, Callable
from abc import ABC, abstractmethod

try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    Model = None
    KaldiRecognizer = None


def _get_default_input_device_index(p: "pyaudio.PyAudio") -> int:
    """Lấy index của default input device, fallback về device đầu tiên khả dụng."""
    try:
        info = p.get_default_input_device_info()
        return int(info["index"])
    except Exception:
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxInputChannels"] > 0:
                return i
        raise OSError("No input device found")


class STTEngine(ABC):
    """Base class cho STT engines"""
    
    @abstractmethod
    def transcribe(self, audio_file: str) -> str:
        """Transcribe audio file thành text"""
        pass
    
    @abstractmethod
    def transcribe_live(self, audio_callback: Callable) -> str:
        """Transcribe live audio stream"""
        pass


class VoskSTT(STTEngine):
    """Vosk STT engine (Streaming support)"""
    
    def __init__(self, model_path: str = None, language: str = "en"):
        """
        Khởi tạo Vosk STT
        
        Args:
            model_path: Đường dẫn đến model folder
            language: Ngôn ngữ (vi, en)
        """
        if Model is None or KaldiRecognizer is None:
            raise ImportError("Install: pip install vosk")
        
        # Import config here to avoid circular imports at module level
        import importlib.util
        import sys
        cfg = None
        try:
            spec = importlib.util.find_spec("config")
            if spec:
                cfg = importlib.import_module("config")
        except Exception:
            pass

        self.language = language
        if model_path:
            self.model_path = model_path
        else:
            # Default path from config or fallback
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if cfg and hasattr(cfg, "MODEL_DIRS"):
                model_dir = cfg.MODEL_DIRS.get("vosk", {}).get(language)
                if model_dir:
                    self.model_path = os.path.join(project_root, "models", model_dir)
                else:
                    self.model_path = os.path.join(project_root, "models", f"vosk-model-small-{language}")
            else:
                self.model_path = os.path.join(project_root, "models", f"vosk-model-small-{language}")
        
        try:
            self.model = Model(self.model_path)
        except Exception as e:
            raise RuntimeError(f"Cannot load Vosk model from {self.model_path}: {e}")
        
        self.recognizer = None
    
    def transcribe(self, audio_file: str) -> str:
        """Transcribe audio file"""
        import wave
        import json
        
        try:
            wf = wave.open(audio_file, "rb")
            
            # Check audio format
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                raise ValueError("Audio must be mono, 16-bit, 16kHz")
            
            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)
            
            result = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    result += res.get("text", "") + " "
            
            # Get final result
            res = json.loads(rec.FinalResult())
            result += res.get("text", "")
            
            wf.close()
            return result.strip()
            
        except Exception as e:
            raise RuntimeError(f"Vosk transcribe error: {e}")
    
    def transcribe_live(self, audio_callback: Callable, partial_callback: Callable = None) -> str:
        """Transcribe live audio stream with true streaming
        
        Args:
            audio_callback: Function to call to stop recording
            partial_callback: Optional callback for partial results (real-time text)
        
        Returns:
            Final transcribed text
        """
        import pyaudio
        import json
        
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        p = pyaudio.PyAudio()
        try:
            device_index = _get_default_input_device_index(p)
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK,
            )
        except Exception as e:
            p.terminate()
            raise RuntimeError(f"Cannot open input device: {e}")
        
        rec = KaldiRecognizer(self.model, RATE)
        rec.SetWords(True)
        
        # Use threading.Event for safe thread control
        stop_event = threading.Event()
        result = ""
        
        def record_and_transcribe():
            """Record audio and transcribe in real-time"""
            nonlocal result
            while not stop_event.is_set():
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    if len(data) == 0:
                        break
                    
                    # Process chunk immediately (true streaming)
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        text = res.get("text", "")
                        if text:
                            result += text + " "
                            if partial_callback:
                                partial_callback(result.strip())
                    else:
                        # Get partial results for real-time feedback
                        if partial_callback:
                            partial_res = json.loads(rec.PartialResult())
                            partial_text = partial_res.get("partial", "")
                            if partial_text:
                                partial_callback(partial_text)
                except Exception:
                    break
        
        # Start recording in thread
        record_thread = threading.Thread(target=record_and_transcribe)
        record_thread.start()
        
        # Wait for callback to stop recording
        audio_callback()
        
        # Signal thread to stop
        stop_event.set()
        record_thread.join(timeout=1.0)
        
        # Clean up stream
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        p.terminate()
        
        # Get final result
        try:
            final_res = json.loads(rec.FinalResult())
            final_text = final_res.get("text", "")
            if final_text:
                result += final_text
        except Exception:
            pass
        
        return result.strip()


class SherpaONNXSTT(STTEngine):
    """Sherpa-ONNX STT engine (next-gen Kaldi, higher accuracy)"""

    def __init__(self, model_dir: str = None, language: str = "vi"):
        """
        Initialize Sherpa-ONNX STT

        Args:
            model_dir: Path to model directory (contains encoder.onnx, decoder.onnx, joiner.onnx, tokens.txt)
            language: Language code (vi, en)
        """
        try:
            import sherpa_onnx
            self._sherpa = sherpa_onnx
        except ImportError:
            raise ImportError("Install: pip install sherpa-onnx")

        # Import config here to avoid circular imports at module level
        import importlib.util
        cfg = None
        try:
            spec = importlib.util.find_spec("config")
            if spec:
                cfg = importlib.import_module("config")
        except Exception:
            pass

        self.language = language
        if model_dir:
            self.model_dir = model_dir
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if cfg and hasattr(cfg, "MODEL_DIRS"):
                model_dir_name = cfg.MODEL_DIRS.get("sherpa_onnx", {}).get(language)
                if model_dir_name:
                    self.model_dir = os.path.join(project_root, "models", model_dir_name)
                else:
                    self.model_dir = os.path.join(project_root, "models", f"sherpa-{language}")
            else:
                self.model_dir = os.path.join(project_root, "models", f"sherpa-{language}")

        self.recognizer = self._create_recognizer()

    def _create_recognizer(self):
        """Create Sherpa-ONNX recognizer from model files"""
        import glob

        def _find(pattern):
            matches = glob.glob(os.path.join(self.model_dir, pattern))
            return matches[0] if matches else None

        tokens = _find("tokens.txt")
        encoder = _find("*encoder*.onnx")
        decoder = _find("*decoder*.onnx")
        joiner = _find("*joiner*.onnx")

        if tokens and encoder and decoder and joiner:
            # Transducer model
            return self._sherpa.OnlineRecognizer.from_transducer(
                tokens=tokens,
                encoder=encoder,
                decoder=decoder,
                joiner=joiner,
                num_threads=4,
                sample_rate=16000,
                feature_dim=80,
            )

        # Try paraformer
        paraformer = _find("*model*.onnx")
        if tokens and paraformer:
            return self._sherpa.OnlineRecognizer.from_paraformer(
                tokens=tokens,
                encoder=paraformer,
                num_threads=4,
                sample_rate=16000,
                feature_dim=80,
            )

        raise RuntimeError(
            f"Cannot find Sherpa-ONNX model files in {self.model_dir}. "
            "Expected: tokens.txt, *encoder*.onnx, *decoder*.onnx, *joiner*.onnx (transducer) "
            "or tokens.txt, *model*.onnx (paraformer)"
        )

    def transcribe(self, audio_file: str) -> str:
        """Transcribe audio file"""
        import wave
        import numpy as np

        try:
            wf = wave.open(audio_file, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                raise ValueError("Audio must be mono, 16-bit, 16kHz")

            stream = self.recognizer.create_stream()
            while True:
                data = wf.readframes(1024)
                if len(data) == 0:
                    break
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                stream.accept_waveform(16000, samples)
                while self.recognizer.is_ready(stream):
                    self.recognizer.decode_stream(stream)

            # Final decode
            while self.recognizer.is_ready(stream):
                self.recognizer.decode_stream(stream)

            result = self.recognizer.get_result(stream)
            wf.close()
            return result.strip()

        except Exception as e:
            raise RuntimeError(f"Sherpa-ONNX transcribe error: {e}")

    def transcribe_live(self, audio_callback: Callable, partial_callback: Callable = None) -> str:
        """Transcribe live audio stream with true streaming"""
        import pyaudio
        import numpy as np

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()
        try:
            device_index = _get_default_input_device_index(p)
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK,
            )
        except Exception as e:
            p.terminate()
            raise RuntimeError(f"Cannot open input device: {e}")

        sherpa_stream = self.recognizer.create_stream()
        stop_event = threading.Event()
        result_text = ""

        def record_and_transcribe():
            nonlocal result_text
            while not stop_event.is_set():
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    if len(data) == 0:
                        break
                    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    sherpa_stream.accept_waveform(RATE, samples)

                    while self.recognizer.is_ready(sherpa_stream):
                        self.recognizer.decode_stream(sherpa_stream)

                    # Get partial result for real-time feedback
                    if partial_callback:
                        current = self.recognizer.get_result(sherpa_stream)
                        if current and current != result_text:
                            result_text = current
                            partial_callback(current)
                except Exception:
                    break

        record_thread = threading.Thread(target=record_and_transcribe)
        record_thread.start()

        audio_callback()

        stop_event.set()
        record_thread.join(timeout=1.0)

        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        p.terminate()

        # Final result
        while self.recognizer.is_ready(sherpa_stream):
            self.recognizer.decode_stream(sherpa_stream)

        return self.recognizer.get_result(sherpa_stream).strip()


class STTFactory:
    """Factory để tạo STT engine"""
    
    @staticmethod
    def create(engine: str = "vosk", **kwargs) -> STTEngine:
        """
        Tạo STT engine
        
        Args:
            engine: 'vosk'
            **kwargs: Additional arguments
            
        Returns:
            STT engine instance
        """
        engines = {
            "vosk": VoskSTT,
            "sherpa_onnx": SherpaONNXSTT,
        }
        
        if engine not in engines:
            raise ValueError(f"Unsupported engine: {engine}. Supported: {list(engines.keys())}")
        
        return engines[engine](**kwargs)


class VoiceInputCLI:
    """CLI interface cho voice input"""
    
    def __init__(self, stt_engine: STTEngine):
        """
        Khởi tạo CLI voice input
        
        Args:
            stt_engine: STT engine instance
        """
        self.stt = stt_engine
        self.running = False
    
    def record_and_transcribe(self, duration: float = 5.0) -> str:
        """
        Ghi âm và transcribe using live streaming
        
        Args:
            duration: Thời gian ghi âm (giây)
            
        Returns:
            Transcribed text
        """
        print(f"Recording for {duration}s...")
        
        def stop_callback():
            """Callback to stop recording after duration"""
            import time
            time.sleep(duration)
        
        # Use live transcription for better performance
        text = self.stt.transcribe_live(stop_callback)
        
        return text
    
    def interactive_loop(self):
        """Interactive CLI loop"""
        print("=== Voice Input CLI ===")
        print("Press Enter to record, 'q' to quit")
        
        while True:
            cmd = input("> ")
            
            if cmd.lower() == 'q':
                break
            
            if cmd == '':
                text = self.record_and_transcribe()
                print(f"Transcribed: {text}")
        
        print("Exited")


class VoiceInputGUI:
    """GUI interface cho voice input (sử dụng Tkinter)"""
    
    def __init__(self, stt_engine: STTEngine):
        """
        Khởi tạo GUI voice input
        
        Args:
            stt_engine: STT engine instance
        """
        self.stt = stt_engine
        self.recording = False
        self.frames = []
    
    def create_gui(self):
        """Tạo GUI"""
        import tkinter as tk
        from tkinter import ttk
        
        self.root = tk.Tk()
        self.root.title("TFT Voice Input")
        self.root.geometry("400x300")
        
        # Button ghi âm
        self.record_btn = ttk.Button(
            self.root,
            text="Record",
            command=self.toggle_recording
        )
        self.record_btn.pack(pady=20)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="Ready")
        self.status_label.pack(pady=10)
        
        # Transcribed text
        self.text_label = ttk.Label(self.root, text="", wraplength=350)
        self.text_label.pack(pady=20)
        
        return self.root
    
    def toggle_recording(self):
        """Bật/tắt ghi âm"""
        import pyaudio
        import wave
        import tempfile
        
        if not self.recording:
            # Bắt đầu ghi âm
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            self.p = pyaudio.PyAudio()
            try:
                device_index = _get_default_input_device_index(self.p)
                self.stream = self.p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK,
                )
            except Exception as e:
                self.p.terminate()
                self.status_label.config(text=f"Device error: {e}")
                return
            
            self.recording = True
            self.record_btn.config(text="Stop")
            self.status_label.config(text="Recording...")
            
            self.frames = []
            
            def record():
                while self.recording:
                    try:
                        data = self.stream.read(CHUNK, exception_on_overflow=False)
                        self.frames.append(data)
                    except Exception:
                        break
            
            self.record_thread = threading.Thread(target=record)
            self.record_thread.start()
            
        else:
            # Stop recording
            self.recording = False
            self.record_btn.config(text="Record")
            self.status_label.config(text="Transcribing...")
            
            if hasattr(self, 'record_thread') and self.record_thread.is_alive():
                self.record_thread.join(timeout=2.0)
            
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'p') and self.p:
                self.p.terminate()
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            wf = wave.open(tmp_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            # Transcribe
            try:
                text = self.stt.transcribe(tmp_path)
                self.text_label.config(text=f"Transcribed: {text}")
                self.status_label.config(text="Ready")
            except Exception as e:
                self.status_label.config(text=f"Transcribe error: {e}")
            
            # Cleanup
            os.unlink(tmp_path)
    
    def run(self):
        """Chạy GUI"""
        root = self.create_gui()
        root.mainloop()


if __name__ == "__main__":
    # Test
    print("=== Test STT Engine ===\n")
    
    try:
        # Test Vosk
        print("1. Test Vosk...")
        stt = STTFactory.create("vosk", language="en")
        print("OK - Vosk initialized\n")
        
        # Test CLI
        print("2. Test CLI interface...")
        cli = VoiceInputCLI(stt)
        print("OK - CLI initialized\n")
        
        # Test GUI
        print("3. Test GUI interface...")
        gui = VoiceInputGUI(stt)
        print("OK - GUI initialized\n")
        
        print("Select mode:")
        print("1. CLI")
        print("2. GUI")
        choice = input("Choice: ")
        
        if choice == "1":
            cli.interactive_loop()
        elif choice == "2":
            gui.run()
        
    except Exception as e:
        print(f"Error: {e}")
