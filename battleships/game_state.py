"""
GameState - the phase a game is currently in.

Shared between single-process rendering (Renderer) and the network client's
RemoteGameView, so it lives on its own rather than inside any one of them.
"""

from enum import Enum, auto


class GameState(Enum):
    """Which phase the game is currently in, from the local player's point
    of view."""

    PLAYER_TURN = auto()
    OPPONENT_TURN = auto()
    PLAYER_WON = auto()
    OPPONENT_WON = auto()
