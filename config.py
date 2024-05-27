from enum import Enum, auto

# Global ROLE_MAP definition
ROLE_MAP = {
    'human': 'user',
    'ai': 'assistant'
}

class APP_MODE(Enum):
    CHAT = auto()
    MENU = auto()