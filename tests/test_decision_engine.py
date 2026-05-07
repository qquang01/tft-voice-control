"""
Test script cho TFT Decision Engine
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.tft_decision_engine import TFTDecisionEngine


def test_decision_engine():
    print("=== Test TFT Decision Engine ===\n")
    
    try:
        engine = TFTDecisionEngine("gemini")
        print("✓ Đã khởi tạo Decision Engine\n")
    except Exception as e:
        print(f"✗ Không thể khởi tạo: {e}")
        return
    
    # Test game state
    test_state = {
        "gold": 50,
        "health": 80,
        "level": 4,
        "round": "3-2",
        "shop": ["Ahri", "Syndra", "Garen", "Ashe", "Nasus"],
        "bench": ["Ahri", "Garen"],
        "board": [{"name": "Ahri", "star": 1}],
        "items": ["B.F. Sword", "Needlessly Large Rod"]
    }
    
    # Test decision
    print("1. Test decision making...")
    try:
        decision = engine.decide_action(test_state)
        print(f"✓ Decision: {decision.get('action')} - {decision.get('target')}")
        print(f"  Reasoning: {decision.get('reasoning')}")
        print(f"  Confidence: {decision.get('confidence')}\n")
    except Exception as e:
        print(f"✗ Decision test failed: {e}\n")
    
    # Test composition advice
    print("2. Test composition advice...")
    try:
        advice = engine.get_composition_advice(test_state)
        print(f"✓ Current comp: {advice.get('current_comp')}")
        print(f"  Recommended: {advice.get('recommended_comp')}")
        print(f"  Key champions: {advice.get('key_champions')}\n")
    except Exception as e:
        print(f"✗ Composition advice failed: {e}\n")
    
    # Test item advice
    print("3. Test item advice...")
    try:
        item_advice = engine.get_item_advice(test_state, "Ahri")
        print(f"✓ Best items: {item_advice.get('best_items')}")
        print(f"  Priority: {item_advice.get('priority')}\n")
    except Exception as e:
        print(f"✗ Item advice failed: {e}\n")
    
    # Test general advice
    print("4. Test general advice...")
    try:
        advice = engine.get_general_advice(test_state, "Should I roll now?")
        print(f"✓ Advice: {advice[:200]}...\n")
    except Exception as e:
        print(f"✗ General advice failed: {e}\n")
    
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_decision_engine()
