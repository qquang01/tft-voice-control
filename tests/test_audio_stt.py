"""
Test script để kiểm tra audio input và STT signal
"""
import sys
import os
import pyaudio
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from voice.stt_engine import VoskSTT
from gui.audio_manager import AudioManager
from gui.utils.debug_logger import DebugLogger


def test_audio_devices():
    """Test danh sách audio input devices"""
    print("=== Test Audio Devices ===\n")
    
    try:
        p = pyaudio.PyAudio()
        print(f"Số lượng devices: {p.get_device_count()}\n")
        
        input_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append((i, info))
                print(f"Device {i}: {info['name']}")
                print(f"  - Channels: {info['maxInputChannels']}")
                print(f"  - Sample Rate: {info['defaultSampleRate']}")
                print()
        
        p.terminate()
        return input_devices
        
    except Exception as e:
        print(f"✗ Lỗi khi lấy audio devices: {e}\n")
        return []


def test_audio_stream(device_index=0):
    """Test đọc audio stream từ device"""
    print("=== Test Audio Stream ===\n")
    
    try:
        p = pyaudio.PyAudio()
        
        # Mở stream
        print(f"Đang mở stream từ device {device_index}...")
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        print("✓ Stream đã mở\n")
        
        # Đọc một số chunk
        print("Đang đọc 5 chunks audio (giả sử 1 giây)...")
        chunks_read = 0
        for i in range(5):
            try:
                data = stream.read(1024, exception_on_overflow=False)
                chunks_read += 1
                print(f"  Chunk {i+1}: {len(data)} bytes")
            except Exception as e:
                print(f"  ✗ Lỗi đọc chunk {i+1}: {e}")
        
        print(f"\n✓ Đã đọc thành công {chunks_read}/5 chunks")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test audio stream: {e}\n")
        return False


def test_stt_initialization():
    """Test khởi tạo STT engine"""
    print("=== Test STT Initialization ===\n")
    
    try:
        print("Đang khởi tạo VoskSTT...")
        stt = VoskSTT(language="en")
        print("✓ STT engine đã khởi tạo")
        print(f"  - Model: {stt.model}")
        print(f"  - Language: en\n")
        return stt
        
    except Exception as e:
        print(f"✗ Lỗi khi khởi tạo STT: {e}\n")
        return None


def test_stt_with_audio_stream(stt, device_index=0):
    """Test STT với audio stream thực tế"""
    print("=== Test STT với Audio Stream ===\n")
    
    try:
        p = pyaudio.PyAudio()
        
        # Mở stream
        print(f"Đang mở stream từ device {device_index}...")
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        print("✓ Stream đã mở\n")
        
        # Khởi tạo Vosk recognizer
        from vosk import KaldiRecognizer
        recognizer = KaldiRecognizer(stt.model, 16000)
        recognizer.SetWords(True)
        print("✓ KaldiRecognizer đã khởi tạo\n")
        
        # Test streaming
        print("Đang test streaming STT (đọc 10 chunks)...")
        chunks_processed = 0
        partial_results = 0
        final_results = 0
        
        for i in range(10):
            try:
                data = stream.read(1024, exception_on_overflow=False)
                chunks_processed += 1
                
                # Process với STT
                if recognizer.AcceptWaveform(data):
                    result = __import__('json').loads(recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        final_results += 1
                        print(f"  Chunk {i+1}: [FINAL] {text}")
                else:
                    result = __import__('json').loads(recognizer.PartialResult())
                    text = result.get("partial", "")
                    if text:
                        partial_results += 1
                        print(f"  Chunk {i+1}: [PARTIAL] {text}")
                        
            except Exception as e:
                print(f"  ✗ Lỗi xử lý chunk {i+1}: {e}")
        
        print(f"\n✓ Đã xử lý {chunks_processed}/10 chunks")
        print(f"  - Partial results: {partial_results}")
        print(f"  - Final results: {final_results}")
        
        # Get final result
        final_result = __import__('json').loads(recognizer.FinalResult())
        final_text = final_result.get("text", "")
        if final_text:
            print(f"  - Final text: {final_text}\n")
        else:
            print("  - Không có final text (có thể chưa có giọng nói)\n")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test STT với audio: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_audio_manager():
    """Test AudioManager với audio thực"""
    print("=== Test AudioManager ===\n")
    
    try:
        logger = DebugLogger("test_audio.log")
        print("✓ DebugLogger đã khởi tạo\n")
        
        stt = VoskSTT(language="en")
        print("✓ VoskSTT đã khởi tạo\n")
        
        audio_manager = AudioManager(logger, stt.model)
        print("✓ AudioManager đã khởi tạo\n")
        
        # Test get devices
        devices = audio_manager.get_audio_devices()
        print(f"✓ Đã lấy {len(devices)} audio devices")
        for idx, name in devices:
            print(f"  - [{idx}] {name}")
        print()
        
        # Test open stream
        if devices:
            device_index = devices[0][0]
            print(f"Đang test mở stream từ device {device_index}...")
            stream = audio_manager._try_open_stream(device_index)
            print("✓ Stream đã mở\n")
            
            stream.stop_stream()
            stream.close()
        
        audio_manager.cleanup()
        print("✓ AudioManager đã cleanup\n")
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test AudioManager: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Chạy tất cả tests"""
    print("=" * 60)
    print("AUDIO & STT SIGNAL TEST SUITE")
    print("=" * 60)
    print()
    
    # Test 1: Audio Devices
    devices = test_audio_devices()
    if not devices:
        print("⚠ Không tìm thấy audio input device. Hãy kết nối microphone.\n")
        return
    
    # Test 2: Audio Stream
    print("\n" + "=" * 60)
    test_audio_stream(devices[0][0])
    
    # Test 3: STT Initialization
    print("\n" + "=" * 60)
    stt = test_stt_initialization()
    if not stt:
        print("⚠ Không thể khởi tạo STT engine. Kiểm tra model path.\n")
        return
    
    # Test 4: STT với Audio Stream
    print("\n" + "=" * 60)
    test_stt_with_audio_stream(stt, devices[0][0])
    
    # Test 5: AudioManager
    print("\n" + "=" * 60)
    test_audio_manager()
    
    print("\n" + "=" * 60)
    print("TEST HOÀN TẤT")
    print("=" * 60)
    print("\nKết luận:")
    print("1. Nếu tất cả tests pass → Audio & STT hoạt động bình thường")
    print("2. Nếu audio stream fail → Microphone không hoạt động")
    print("3. Nếu STT fail → Model Vosk không tải được")
    print("4. Nếu STT không có text → Không có giọng nói hoặc volume quá thấp")


if __name__ == "__main__":
    run_all_tests()
