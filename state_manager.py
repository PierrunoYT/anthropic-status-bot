import json
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self, state_file: str):
        self._state_file = state_file
        self._current_state: Optional[Dict[str, Any]] = None
        self._previous_state: Optional[Dict[str, Any]] = None
        self._load_state()

    def save_state(self, current_state: Optional[Dict[str, Any]]) -> None:
        """Save current state to file."""
        if current_state:
            try:
                with open(self._state_file, 'w') as f:
                    json.dump({
                        'current': current_state,
                        'previous': self._current_state
                    }, f)
                self._previous_state = self._current_state
                self._current_state = current_state
            except Exception as e:
                logger.error(f"Error saving checker state: {str(e)}")

    def _load_state(self) -> None:
        """Load state from file."""
        try:
            with open(self._state_file, 'r') as f:
                data = json.load(f)
                self._current_state = data.get('current')
                self._previous_state = data.get('previous')
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def get_states(self) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Get current and previous states."""
        return self._current_state, self._previous_state

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get current state."""
        return self._current_state

    def get_previous_state(self) -> Optional[Dict[str, Any]]:
        """Get previous state."""
        return self._previous_state