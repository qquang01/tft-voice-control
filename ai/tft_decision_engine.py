import json
from typing import Dict, List, Optional
from .llm_engine import BaseLLM, LLMFactory


class TFTDecisionEngine:
    """Engine ra quyết định game TFT bằng LLM"""
    
    def __init__(self, llm_provider: str = "gemini", **llm_kwargs):
        """
        Khởi tạo Decision Engine
        
        Args:
            llm_provider: 'gemini', 'groq', 'local'
            **llm_kwargs: Additional arguments cho LLM
        """
        self.llm = LLMFactory.create(llm_provider, **llm_kwargs)
    
    def decide_action(self, game_state: Dict) -> Dict:
        """
        Ra quyết định action dựa trên game state
        
        Args:
            game_state: Dict chứa thông tin game
                - gold: int
                - health: int
                - level: int
                - round: str
                - shop: List[str] (champions in shop)
                - bench: List[str] (champions on bench)
                - board: List[Dict] (champions on board)
                - items: List[str] (items in inventory)
                
        Returns:
            Dict với action và parameters
        """
        prompt = self._build_decision_prompt(game_state)
        
        schema = {
            "action": "string (buy/sell/roll/level_up/move/hold)",
            "target": "string (champion name or slot number)",
            "reasoning": "string (why this action)",
            "confidence": "float (0-1)"
        }
        
        response = self.llm.generate_structured(prompt, schema)
        return response
    
    def _build_decision_prompt(self, game_state: Dict) -> str:
        """Build prompt cho decision making"""
        prompt = f"""You are a TFT (Teamfight Tactics) expert player. Analyze the current game state and recommend the best action.

Game State:
- Gold: {game_state.get('gold', 0)}
- Health: {game_state.get('health', 100)}
- Level: {game_state.get('level', 1)}
- Round: {game_state.get('round', '1-1')}
- Shop Champions: {', '.join(game_state.get('shop', []))}
- Bench Champions: {', '.join(game_state.get('bench', []))}
- Board Champions: {len(game_state.get('board', []))} units
- Items: {', '.join(game_state.get('items', []))}

Consider:
1. Current composition and synergies
2. Economy management (save vs spend)
3. Level timing
4. Champion availability
5. Item timing

Recommend ONE best action from: buy, sell, roll, level_up, move, hold.
Be strategic and think long-term.
"""
        return prompt
    
    def get_composition_advice(self, game_state: Dict) -> Dict:
        """
        Đưa ra advice về composition
        
        Args:
            game_state: Current game state
            
        Returns:
            Dict với composition advice
        """
        prompt = f"""Analyze the current TFT game state and provide composition advice.

Game State:
- Level: {game_state.get('level', 1)}
- Board Champions: {', '.join([c.get('name', 'unknown') for c in game_state.get('board', [])])}
- Bench: {', '.join(game_state.get('bench', []))}
- Gold: {game_state.get('gold', 0)}

Provide:
1. Current composition analysis
2. Recommended composition to aim for
3. Key champions to look for
4. Key items to build
5. Positioning advice
"""
        
        schema = {
            "current_comp": "string",
            "recommended_comp": "string",
            "key_champions": "list of strings",
            "key_items": "list of strings",
            "positioning": "string",
            "reasoning": "string"
        }
        
        response = self.llm.generate_structured(prompt, schema)
        return response
    
    def get_item_advice(self, game_state: Dict, champion_name: str) -> Dict:
        """
        Đưa ra advice về item cho champion cụ thể
        
        Args:
            game_state: Current game state
            champion_name: Tên champion
            
        Returns:
            Dict với item advice
        """
        prompt = f"""What are the best items for {champion_name} in TFT?

Game State:
- Level: {game_state.get('level', 1)}
- Available items: {', '.join(game_state.get('items', []))}
- Gold: {game_state.get('gold', 0)}

Provide:
1. Best 3 items for this champion
2. Priority order
3. Alternative items if components unavailable
4. When to build (early/late game)
"""
        
        schema = {
            "best_items": "list of strings",
            "priority": "list of strings (item names in priority order)",
            "alternatives": "list of strings",
            "timing": "string (early/late/mid)",
            "reasoning": "string"
        }
        
        response = self.llm.generate_structured(prompt, schema)
        return response
    
    def evaluate_move(self, game_state: Dict, from_slot: int, to_position: str) -> Dict:
        """
        Đánh giá một move cụ thể
        
        Args:
            game_state: Current game state
            from_slot: Slot trên bench
            to_position: Vị trí trên board
            
        Returns:
            Dict với evaluation
        """
        prompt = f"""Evaluate moving a champion from bench slot {from_slot} to board position {to_position}.

Game State:
- Board: {', '.join([c.get('name', 'unknown') for c in game_state.get('board', [])])}
- Bench: {', '.join(game_state.get('bench', []))}
- Round: {game_state.get('round', '1-1')}

Evaluate:
1. Is this a good move?
2. How does it affect positioning?
3. Does it improve synergies?
4. Any better alternatives?
"""
        
        schema = {
            "is_good_move": "boolean",
            "positioning_impact": "string",
            "synergy_impact": "string",
            "better_alternatives": "list of strings",
            "confidence": "float (0-1)",
            "reasoning": "string"
        }
        
        response = self.llm.generate_structured(prompt, schema)
        return response
    
    def get_general_advice(self, game_state: Dict, question: str) -> str:
        """
        Đưa ra advice chung cho bất kỳ câu hỏi
        
        Args:
            game_state: Current game state
            question: Câu hỏi của người chơi
            
        Returns:
            Advice text
        """
        prompt = f"""TFT Expert Advice Request:

Game State:
- Gold: {game_state.get('gold', 0)}
- Health: {game_state.get('health', 100)}
- Level: {game_state.get('level', 1)}
- Round: {game_state.get('round', '1-1')}
- Shop: {', '.join(game_state.get('shop', []))}
- Board: {len(game_state.get('board', []))} units

Question: {question}

Provide strategic advice based on the game state and question.
"""
        
        response = self.llm.generate(prompt)
        return response


class TFTAutoPlayer:
    """Auto-play loop với LLM decision making"""
    
    def __init__(self, llm_provider: str = "gemini", **llm_kwargs):
        """
        Khởi tạo Auto Player
        
        Args:
            llm_provider: LLM provider
            **llm_kwargs: LLM arguments
        """
        self.decision_engine = TFTDecisionEngine(llm_provider, **llm_kwargs)
        self.running = False
    
    def auto_play_turn(self, game_state: Dict, execute_action_callback) -> Dict:
        """
        Auto-play một turn
        
        Args:
            game_state: Current game state
            execute_action_callback: Function để execute action
            
        Returns:
            Decision result
        """
        # Lấy decision từ LLM
        decision = self.decision_engine.decide_action(game_state)
        
        print(f"Decision: {decision.get('action')} - {decision.get('target')}")
        print(f"Reasoning: {decision.get('reasoning')}")
        
        # Execute action
        if execute_action_callback:
            result = execute_action_callback(decision)
            decision['execution_result'] = result
        
        return decision
    
    def start_auto_play(self, get_game_state_callback, execute_action_callback, 
                       interval: float = 5.0):
        """
        Bắt đầu auto-play loop
        
        Args:
            get_game_state_callback: Function để lấy game state
            execute_action_callback: Function để execute action
            interval: Thời gian giữa các turn (giây)
        """
        import time
        
        self.running = True
        print("Bắt đầu auto-play...")
        
        while self.running:
            try:
                # Lấy game state
                game_state = get_game_state_callback()
                
                # Auto-play turn
                self.auto_play_turn(game_state, execute_action_callback)
                
                # Wait
                time.sleep(interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Lỗi auto-play: {e}")
                time.sleep(1)
        
        self.running = False
        print("Đã dừng auto-play")
    
    def stop_auto_play(self):
        """Dừng auto-play"""
        self.running = False


if __name__ == "__main__":
    # Test
    print("=== Test TFT Decision Engine ===\n")
    
    try:
        engine = TFTDecisionEngine("gemini")
        
        # Test decision
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
        
        print("Test decision making...")
        decision = engine.decide_action(test_state)
        print(f"Decision: {json.dumps(decision, indent=2)}\n")
        
        # Test composition advice
        print("Test composition advice...")
        advice = engine.get_composition_advice(test_state)
        print(f"Advice: {json.dumps(advice, indent=2)}\n")
        
    except Exception as e:
        print(f"Test skipped: {e}")
