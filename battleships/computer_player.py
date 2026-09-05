"""
The ComputerPlayer class - a simple AI opponent.

Strategy ("hunt and target"):
  * Fire at random unshot cells until a hit lands.
  * Once a ship is hit, queue up its orthogonal neighbours and try those
    next, to home in on and sink the rest of the ship.
  * Once the ship is sunk, go back to firing randomly.
"""

import random
from typing import List, Set, Tuple

from .board import Board, Position, ShotResult
from .player import Player


class ComputerPlayer(Player):
    """AI opponent that hunts randomly, then targets around a hit."""

    def __init__(self, name: str, board: Board, grid_size: int) -> None:
        super().__init__(name, board)
        self.grid_size: int = grid_size

        self._shot_positions: Set[Position] = set()  # every cell fired at so far
        self._target_queue: List[Position] = []  # candidates to try next

    def play_turn(self, enemy_board: Board) -> Tuple[Position, ShotResult]:
        """Choose a cell, fire at it, and update the AI's memory."""
        position = self._choose_target()
        result = self.take_shot(enemy_board, position)
        self._record_result(position, result)
        return position, result

    def _choose_target(self) -> Position:
        """Pick the next cell to fire at."""
        # Prefer a cell queued up from a previous hit, if one is still valid.
        while self._target_queue:
            candidate = self._target_queue.pop()
            if candidate not in self._shot_positions and self._in_bounds(candidate):
                return candidate

        # Otherwise fall back to a random cell that hasn't been shot yet.
        return self._random_unshot_position()

    def _random_unshot_position(self) -> Position:
        while True:
            position = (
                random.randint(0, self.grid_size - 1),
                random.randint(0, self.grid_size - 1),
            )
            if position not in self._shot_positions:
                return position

    def _in_bounds(self, position: Position) -> bool:
        row, col = position
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size

    def _record_result(self, position: Position, result: ShotResult) -> None:
        self._shot_positions.add(position)

        if result == ShotResult.SUNK:
            # The ship is gone, so any queued guesses about it are useless.
            self._target_queue.clear()
        elif result == ShotResult.HIT:
            self._queue_neighbours(position)

    def _queue_neighbours(self, position: Position) -> None:
        """Add the up/down/left/right cells around a hit to the queue."""
        row, col = position
        neighbours = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        for neighbour in neighbours:
            if self._in_bounds(neighbour) and neighbour not in self._shot_positions:
                self._target_queue.append(neighbour)
