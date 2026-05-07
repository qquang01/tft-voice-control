"""
Test script cho STT Engine
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from voice.stt_engine import STTFactory, VoiceInputCLI, VoiceInputGUI


def test_stt():
    print("=== Test STT Engine ===\n")
    
    # Test Vosk
    print("1. Test Vosk initialization...")
    try:
        stt = STTFactory.create("vosk", language="en")
        print("OK - Vosk initialized\n")
    except Exception as e:
        print(f"Error: {e}")
        print("Install: pip install vosk\n")
        return
    
    # Test CLI
    print("2. Test CLI interface...")
    try:
        cli = VoiceInputCLI(stt)
        print("OK - CLI initialized\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Test GUI
    print("3. Test GUI interface...")
    try:
        gui = VoiceInputGUI(stt)
        print("OK - GUI initialized\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    print("=== Test completed ===")
    print("\nUsage:")
    print("CLI: cli.interactive_loop()")
    print("GUI: gui.run()")


if __name__ == "__main__":
    test_stt()
