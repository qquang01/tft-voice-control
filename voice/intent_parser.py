import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class Intent:
    """Kết quả parse intent"""
    action: str
    parameters: Dict[str, Any]
    confidence: float
    raw_text: str


class RuleBasedIntentParser:
    """Parser intent dựa trên rules (regex patterns)"""
    
    def __init__(self):
        self.rules: List[Dict] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load rules mặc định cho TFT"""
        self.rules = [
            # BUY actions
            {
                'pattern': r'(mua|buy)\s+(\w+)',
                'action': 'BUY',
                'params': {'champion': 2},
                'confidence': 0.9
            },
            {
                'pattern': r'(mua|buy)\s+tướng\s+(\w+)',
                'action': 'BUY',
                'params': {'champion': 2},
                'confidence': 0.95
            },
            
            # SELL actions
            {
                'pattern': r'(bán|sell)\s+tướng\s+(\d+)',
                'action': 'SELL',
                'params': {'slot': 2},
                'confidence': 0.9
            },
            {
                'pattern': r'(bán|sell)\s+(\d+)',
                'action': 'SELL',
                'params': {'slot': 2},
                'confidence': 0.85
            },
            
            # MOVE actions
            {
                'pattern': r'(đặt|put)\s+(\w+)\s+(trên|on)\s+(\d+)',
                'action': 'MOVE',
                'params': {'champion': 2, 'position': 4},
                'confidence': 0.9
            },
            {
                'pattern': r'(di chuyển|move)\s+(\w+)\s+(đến|to)\s+(\d+)',
                'action': 'MOVE',
                'params': {'champion': 2, 'position': 4},
                'confidence': 0.9
            },
            {
                'pattern': r'(kéo|drag)\s+(\w+)\s+(lên|up)\s+bàn',
                'action': 'MOVE_TO_BOARD',
                'params': {'champion': 2},
                'confidence': 0.85
            },
            
            # ROLL actions
            {
                'pattern': r'(làm mới|refresh|roll)\s+shop',
                'action': 'ROLL',
                'params': {},
                'confidence': 0.95
            },
            {
                'pattern': r'(làm mới|refresh|roll)',
                'action': 'ROLL',
                'params': {},
                'confidence': 0.85
            },
            
            # LEVEL actions
            {
                'pattern': r'(lên\s+cấp|level\s+up)',
                'action': 'LEVEL',
                'params': {},
                'confidence': 0.95
            },
            
            # ITEM actions
            {
                'pattern': r'(lên\s+đồ|buy\s+item|equip)',
                'action': 'BUY_ITEM',
                'params': {},
                'confidence': 0.85
            },
            
            # INFO actions
            {
                'pattern': r'(kiểm\s+tra|check|what\'?s)\s+(gold|tiền)',
                'action': 'INFO_GOLD',
                'params': {},
                'confidence': 0.9
            },
            {
                'pattern': r'(kiểm\s+tra|check|what\'?s)\s+(health|máu|hp)',
                'action': 'INFO_HEALTH',
                'params': {},
                'confidence': 0.9
            },
            {
                'pattern': r'(kiểm\s+tra|check|what\'?s)\s+(level|cấp)',
                'action': 'INFO_LEVEL',
                'params': {},
                'confidence': 0.9
            },
            
            # NAVIGATION
            {
                'pattern': r'(trở\s+về|quay\s+lại|back)',
                'action': 'BACK',
                'params': {},
                'confidence': 0.95
            },
            {
                'pattern': r'(về\s+nhà|home)',
                'action': 'HOME',
                'params': {},
                'confidence': 0.95
            },
            
            # GAME CONTROL
            {
                'pattern': r'(mở\s+game|open\s+game)',
                'action': 'OPEN_GAME',
                'params': {},
                'confidence': 0.9
            },
            {
                'pattern': r'(đóng\s+game|close\s+game)',
                'action': 'CLOSE_GAME',
                'params': {},
                'confidence': 0.9
            },
        ]
    
    def add_rule(self, pattern: str, action: str, params: Dict, confidence: float = 0.9):
        """
        Thêm rule mới
        
        Args:
            pattern: Regex pattern
            action: Tên action
            params: Dict mapping param name -> group index
            confidence: Confidence score (0-1)
        """
        self.rules.append({
            'pattern': pattern,
            'action': action,
            'params': params,
            'confidence': confidence
        })
    
    def parse(self, text: str) -> Optional[Intent]:
        """
        Parse text thành intent
        
        Args:
            text: Text cần parse
            
        Returns:
            Intent object hoặc None nếu không match
        """
        text = text.strip().lower()
        
        for rule in self.rules:
            match = re.search(rule['pattern'], text, re.IGNORECASE)
            if match:
                # Extract parameters
                params = {}
                for param_name, group_idx in rule['params'].items():
                    try:
                        value = match.group(group_idx)
                        # Try convert to int
                        if value.isdigit():
                            value = int(value)
                        params[param_name] = value
                    except (IndexError, AttributeError):
                        continue
                
                return Intent(
                    action=rule['action'],
                    parameters=params,
                    confidence=rule['confidence'],
                    raw_text=text
                )
        
        return None
    
    def parse_with_context(self, text: str, context: Dict) -> Optional[Intent]:
        """
        Parse text với context bổ sung
        
        Args:
            text: Text cần parse
            context: Context từ game state (gold, health, etc.)
            
        Returns:
            Intent object hoặc None
        """
        intent = self.parse(text)
        
        if intent:
            # Enrich với context
            intent.parameters['context'] = context
        
        return intent
    
    def get_all_actions(self) -> List[str]:
        """Lấy danh sách tất cả actions có thể"""
        actions = set()
        for rule in self.rules:
            actions.add(rule['action'])
        return sorted(list(actions))


class ContextResolver:
    """Giải quyết context và disambiguation"""
    
    def __init__(self):
        self.game_state = {}
        self.champion_positions = {}  # champion_name -> (x, y)
        self.board_positions = {}  # position_id -> (x, y)
    
    def update_game_state(self, state: Dict):
        """Cập nhật game state"""
        self.game_state = state
    
    def update_champion_position(self, champion: str, position: Tuple[int, int]):
        """Cập nhật vị trí tướng"""
        self.champion_positions[champion.lower()] = position
    
    def resolve_champion_position(self, champion_name: str) -> Optional[Tuple[int, int]]:
        """
        Giải quyết vị trí tướng
        
        Args:
            champion_name: Tên tướng
            
        Returns:
            Tọa độ (x, y) hoặc None
        """
        return self.champion_positions.get(champion_name.lower())
    
    def resolve_board_position(self, position_id: str or int) -> Optional[Tuple[int, int]]:
        """
        Giải quyết vị trí trên bàn
        
        Args:
            position_id: ID vị trí (1-9 hoặc tên)
            
        Returns:
            Tọa độ (x, y) hoặc None
        """
        # Map position ID sang tọa độ (cần tùy chỉnh)
        position_map = {
            1: (200, 300),
            2: (300, 300),
            3: (400, 300),
            4: (500, 300),
            5: (600, 300),
            6: (200, 400),
            7: (300, 400),
            8: (400, 400),
            9: (500, 400),
        }
        
        if isinstance(position_id, str) and position_id.isdigit():
            position_id = int(position_id)
        
        return position_map.get(position_id)
    
    def disambiguate_move(self, champion: str, position: Any) -> Dict:
        """
        Giải quyết lệnh move với context
        
        Args:
            champion: Tên tướng
            position: Vị trí đích
            
        Returns:
            Dict với from_pos và to_pos
        """
        from_pos = self.resolve_champion_position(champion)
        to_pos = self.resolve_board_position(position)
        
        if from_pos and to_pos:
            return {
                'from': from_pos,
                'to': to_pos,
                'resolved': True
            }
        else:
            return {
                'resolved': False,
                'reason': 'Cannot resolve positions'
            }


class ActionPlanner:
    """Lập kế hoạch action từ intent"""
    
    def __init__(self, context_resolver: ContextResolver):
        self.context = context_resolver
        self.action_handlers = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Đăng ký handlers mặc định"""
        self.action_handlers = {
            'BUY': self._handle_buy,
            'SELL': self._handle_sell,
            'MOVE': self._handle_move,
            'MOVE_TO_BOARD': self._handle_move_to_board,
            'ROLL': self._handle_roll,
            'LEVEL': self._handle_level,
            'BUY_ITEM': self._handle_buy_item,
            'INFO_GOLD': self._handle_info_gold,
            'INFO_HEALTH': self._handle_info_health,
            'INFO_LEVEL': self._handle_info_level,
            'BACK': self._handle_back,
            'HOME': self._handle_home,
            'OPEN_GAME': self._handle_open_game,
            'CLOSE_GAME': self._handle_close_game,
        }
    
    def plan(self, intent: Intent) -> Dict:
        """
        Lập kế hoạch action từ intent
        
        Args:
            intent: Intent đã parse
            
        Returns:
            Action plan dict
        """
        if intent.action not in self.action_handlers:
            return {
                'success': False,
                'reason': f'Unknown action: {intent.action}'
            }
        
        return self.action_handlers[intent.action](intent)
    
    def _handle_buy(self, intent: Intent) -> Dict:
        """Handle BUY action"""
        champion = intent.parameters.get('champion')
        if not champion:
            return {'success': False, 'reason': 'Missing champion name'}
        
        return {
            'success': True,
            'action': 'buy_champion',
            'champion': champion,
            'method': 'ocr_find_and_tap'  # hoặc 'shop_slot'
        }
    
    def _handle_sell(self, intent: Intent) -> Dict:
        """Handle SELL action"""
        slot = intent.parameters.get('slot')
        if slot is None:
            return {'success': False, 'reason': 'Missing slot number'}
        
        return {
            'success': True,
            'action': 'sell_champion',
            'slot': slot,
            'method': 'bench_slot_drag_to_sell'
        }
    
    def _handle_move(self, intent: Intent) -> Dict:
        """Handle MOVE action"""
        champion = intent.parameters.get('champion')
        position = intent.parameters.get('position')
        
        if not champion or not position:
            return {'success': False, 'reason': 'Missing champion or position'}
        
        # Resolve positions
        resolved = self.context.disambiguate_move(champion, position)
        
        if resolved['resolved']:
            return {
                'success': True,
                'action': 'move_champion',
                'from': resolved['from'],
                'to': resolved['to'],
                'method': 'swipe'
            }
        else:
            return {
                'success': False,
                'reason': resolved['reason']
            }
    
    def _handle_move_to_board(self, intent: Intent) -> Dict:
        """Handle MOVE_TO_BOARD action"""
        champion = intent.parameters.get('champion')
        if not champion:
            return {'success': False, 'reason': 'Missing champion name'}
        
        from_pos = self.context.resolve_champion_position(champion)
        if not from_pos:
            return {'success': False, 'reason': f'Cannot find {champion} position'}
        
        return {
            'success': True,
            'action': 'move_champion_to_board',
            'from': from_pos,
            'to': 'auto',  # Tự động tìm vị trí trống
            'method': 'swipe'
        }
    
    def _handle_roll(self, intent: Intent) -> Dict:
        """Handle ROLL action"""
        return {
            'success': True,
            'action': 'refresh_shop',
            'method': 'tap_button'
        }
    
    def _handle_level(self, intent: Intent) -> Dict:
        """Handle LEVEL action"""
        return {
            'success': True,
            'action': 'level_up',
            'method': 'tap_button'
        }
    
    def _handle_buy_item(self, intent: Intent) -> Dict:
        """Handle BUY_ITEM action"""
        return {
            'success': True,
            'action': 'buy_item',
            'method': 'tap_item'
        }
    
    def _handle_info_gold(self, intent: Intent) -> Dict:
        """Handle INFO_GOLD action"""
        return {
            'success': True,
            'action': 'get_info',
            'info_type': 'gold',
            'method': 'ocr_read'
        }
    
    def _handle_info_health(self, intent: Intent) -> Dict:
        """Handle INFO_HEALTH action"""
        return {
            'success': True,
            'action': 'get_info',
            'info_type': 'health',
            'method': 'ocr_read'
        }
    
    def _handle_info_level(self, intent: Intent) -> Dict:
        """Handle INFO_LEVEL action"""
        return {
            'success': True,
            'action': 'get_info',
            'info_type': 'level',
            'method': 'ocr_read'
        }
    
    def _handle_back(self, intent: Intent) -> Dict:
        """Handle BACK action"""
        return {
            'success': True,
            'action': 'press_back',
            'method': 'keyevent'
        }
    
    def _handle_home(self, intent: Intent) -> Dict:
        """Handle HOME action"""
        return {
            'success': True,
            'action': 'press_home',
            'method': 'keyevent'
        }
    
    def _handle_open_game(self, intent: Intent) -> Dict:
        """Handle OPEN_GAME action"""
        return {
            'success': True,
            'action': 'open_app',
            'package': 'com.riotgames.league.wildrift',
            'method': 'adb_shell'
        }
    
    def _handle_close_game(self, intent: Intent) -> Dict:
        """Handle CLOSE_GAME action"""
        return {
            'success': True,
            'action': 'close_app',
            'package': 'com.riotgames.league.wildrift',
            'method': 'adb_shell'
        }


if __name__ == "__main__":
    # Test
    parser = RuleBasedIntentParser()
    
    test_inputs = [
        "mua Ahri",
        "bán tướng 1",
        "đặt Darius trên 4",
        "làm mới shop",
        "lên cấp",
        "kiểm tra gold",
        "trở về",
    ]
    
    print("=== Test Intent Parser ===\n")
    for text in test_inputs:
        intent = parser.parse(text)
        if intent:
            print(f"Input: '{text}'")
            print(f"  Action: {intent.action}")
            print(f"  Params: {intent.parameters}")
            print(f"  Confidence: {intent.confidence}")
        else:
            print(f"Input: '{text}' -> No match")
        print()
    
    print(f"Tất cả actions: {parser.get_all_actions()}")
