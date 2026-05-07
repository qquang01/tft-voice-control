"""Central configuration for TFT Voice Tool.

Edit this file to change STT engine, language, audio settings, GUI theme,
and command bindings without touching source code.
"""

from typing import Dict, List

# =============================================================================
# STT ENGINE SETTINGS
# =============================================================================

# Supported engines: "vosk", "sherpa_onnx"
STT_ENGINE: str = "vosk"

# Language code. Vosk models must match this (en-us, vi, etc.)
STT_LANGUAGE: str = "en"

# =============================================================================
# MODEL PATHS
# =============================================================================

# Directory name under ./models/ for each engine + language.
# The app resolves: ./models/<MODEL_DIRS[engine][lang]>/
MODEL_DIRS: Dict[str, Dict[str, str]] = {
    "vosk": {
        "en": "vosk-model-small-en-us-0.15",
        "vi": "vosk-model-small-vn-0.4",
    },
    "sherpa_onnx": {
        "en": "sherpa-english",
        "vi": "sherpa-vietnamese",
    },
}

# =============================================================================
# AUDIO SETTINGS
# =============================================================================

AUDIO_CONFIG = {
    "CHUNK": 1024,          # Bytes per read in manual mode
    "CHUNK_VAD": 960,       # 30 ms @ 16 kHz (WebRTC VAD max frame size: 16000*0.03*2=960 bytes)
    "FORMAT": "paInt16",    # PyAudio format string (resolved at runtime)
    "CHANNELS": 1,
    "RATE": 16000,
}

# =============================================================================
# VOICE ACTIVITY DETECTION
# =============================================================================

# Default mode when GUI starts: "manual" or "auto"
VAD_DEFAULT_MODE: str = "manual"

# WebRTC VAD aggressiveness (0=most sensitive, 3=most aggressive)
VAD_AGGRESSIVENESS: int = 1

# Number of silent VAD frames before auto-stopping in auto mode
VAD_MAX_SILENCE_FRAMES: int = 30

# =============================================================================
# GUI SETTINGS
# =============================================================================

GUI_THEME: str = "dark"          # "dark" or "light"
GUI_COLOR_THEME: str = "blue"    # customtkinter color theme
GUI_SIZE: str = "1400x800"      # Width x Height

# =============================================================================
# GAME COMMAND BINDINGS
# =============================================================================

# Each key is the internal action name.
# Each value is a list of voice/text triggers (lower-cased during matching).
COMMANDS: Dict[str, List[str]] = {
    "buy":       ["buy"],
    "sell":      ["sell"],
    "level":     ["level up", "level"],
    "reforge":   ["reforge", "reroll"],
    "screenshot":["screenshot"],
}

# Human-readable descriptions shown in chat for each action.
COMMAND_DESCRIPTIONS: Dict[str, str] = {
    "buy":        "BUY champion",
    "sell":       "SELL champion",
    "level":      "LEVEL UP",
    "reforge":    "REFORGE item",
    "screenshot": "TAKE SCREENSHOT",
}
