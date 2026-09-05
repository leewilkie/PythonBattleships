"""
The Player class - base class for anyone playing the game (human or
computer). It just knows its own board and how to fire at an enemy board.
"""

from .board import Board, Position, ShotResult


class Player:
    """A participant in the game. Subclassed by ComputerPlayer for the AI."""

    def __init__(self, name: str, board: Board) -> None:
        self.name: str = name
        self.own_board: Board = board  # this player's own ships live here

    def take_shot(self, enemy_board: Board, position: Position) -> ShotResult:
        """Fire at a cell on the enemy's board and return what happened."""
        return enemy_board.receive_shot(position)
