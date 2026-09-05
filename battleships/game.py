"""
The Game class - ties everything together: both boards, both players,
whose turn it is, and whether anyone has won yet.
"""

from enum import Enum, auto
from typing import Optional, Tuple

from . import constants
from .board import Board, Position, ShotResult
from .computer_player import ComputerPlayer
from .player import Player


class GameState(Enum):
    """Which phase the game is currently in."""

    HUMAN_TURN = auto()
    COMPUTER_TURN = auto()
    HUMAN_WON = auto()
    COMPUTER_WON = auto()


class Game:
    """Owns both boards and players, and enforces turn order and win rules."""

    def __init__(self) -> None:
        self.human_board = Board(constants.GRID_SIZE)
        self.computer_board = Board(constants.GRID_SIZE)

        # Both fleets are placed randomly at the start of the game.
        self.human_board.place_ships_randomly(constants.SHIP_SPECS)
        self.computer_board.place_ships_randomly(constants.SHIP_SPECS)

        self.human = Player("Player", self.human_board)
        self.computer = ComputerPlayer(
            "Computer", self.computer_board, constants.GRID_SIZE
        )

        self.state: GameState = GameState.HUMAN_TURN

        # The most recent shot each side made, used by the renderer to show
        # feedback (e.g. flashing the result of the last move).
        self.last_human_shot: Optional[Tuple[Position, ShotResult]] = None
        self.last_computer_shot: Optional[Tuple[Position, ShotResult]] = None

    def human_fire(self, position: Position) -> Optional[ShotResult]:
        """Handle the human player firing at a cell on the computer's board."""
        if self.state != GameState.HUMAN_TURN:
            return None
        if not self.computer_board.is_valid_position(position):
            return None

        result = self.human.take_shot(self.computer_board, position)
        if result == ShotResult.ALREADY_SHOT:
            return result  # ignore repeat clicks, it's still the human's turn

        self.last_human_shot = (position, result)

        if self.computer_board.all_ships_sunk():
            self.state = GameState.HUMAN_WON
        else:
            self.state = GameState.COMPUTER_TURN
        return result

    def computer_turn(self) -> Tuple[Position, ShotResult]:
        """Let the computer take its shot. Only call this in COMPUTER_TURN."""
        position, result = self.computer.play_turn(self.human_board)
        self.last_computer_shot = (position, result)

        if self.human_board.all_ships_sunk():
            self.state = GameState.COMPUTER_WON
        else:
            self.state = GameState.HUMAN_TURN
        return position, result

    def is_over(self) -> bool:
        """True once either side has lost their entire fleet."""
        return self.state in (GameState.HUMAN_WON, GameState.COMPUTER_WON)
