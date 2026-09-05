"""
The Board class - a single player's 10x10 grid, holding their ships and
recording the shots that have been fired at it.
"""

import random
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from .ship import Position, Ship


class ShotResult(Enum):
    """The outcome of firing at a single cell."""

    MISS = auto()
    HIT = auto()
    SUNK = auto()  # a hit that also finished off the ship
    ALREADY_SHOT = auto()  # that cell has already been fired at


class Board:
    """One player's board: its ships, and every shot fired at it so far."""

    def __init__(self, size: int) -> None:
        self.size: int = size
        self.ships: List[Ship] = []

        # Every cell that has been shot at, mapped to whether it was a hit.
        self.shots: Dict[Position, bool] = {}

    def place_ships_randomly(self, ship_specs: List[Tuple[str, int]]) -> None:
        """Place every ship in ship_specs at a random, non-overlapping spot."""
        for name, length in ship_specs:
            ship = Ship(name, length)
            while True:
                positions = self._random_positions(length)
                if positions and not self._overlaps(positions):
                    ship.place(positions)
                    self.ships.append(ship)
                    break

    def _random_positions(self, length: int) -> List[Position]:
        """Pick a random horizontal or vertical run of cells for a ship."""
        horizontal = random.choice([True, False])

        if horizontal:
            max_col = self.size - length
            if max_col < 0:
                return []
            row = random.randint(0, self.size - 1)
            col = random.randint(0, max_col)
            return [(row, col + offset) for offset in range(length)]
        else:
            max_row = self.size - length
            if max_row < 0:
                return []
            row = random.randint(0, max_row)
            col = random.randint(0, self.size - 1)
            return [(row + offset, col) for offset in range(length)]

    def _overlaps(self, positions: List[Position]) -> bool:
        """Check whether any of positions already belongs to a placed ship."""
        occupied = {pos for ship in self.ships for pos in ship.positions}
        return any(pos in occupied for pos in positions)

    def is_valid_position(self, position: Position) -> bool:
        """Check whether a (row, col) pair actually lies on this board."""
        row, col = position
        return 0 <= row < self.size and 0 <= col < self.size

    def ship_at(self, position: Position) -> Optional[Ship]:
        """Return the ship occupying a cell, or None if it's empty water."""
        for ship in self.ships:
            if ship.occupies(position):
                return ship
        return None

    def receive_shot(self, position: Position) -> ShotResult:
        """Fire at a cell on this board and record/return the result."""
        if position in self.shots:
            return ShotResult.ALREADY_SHOT

        ship = self.ship_at(position)
        if ship is None:
            self.shots[position] = False
            return ShotResult.MISS

        ship.register_hit(position)
        self.shots[position] = True
        return ShotResult.SUNK if ship.is_sunk() else ShotResult.HIT

    def all_ships_sunk(self) -> bool:
        """True once every ship on this board has been sunk."""
        return all(ship.is_sunk() for ship in self.ships)
