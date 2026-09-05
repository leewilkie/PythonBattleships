"""
The Ship class - represents a single ship on a Battleships board.
"""

from typing import List, Set, Tuple

# A position on the board is a (row, column) pair of grid coordinates.
Position = Tuple[int, int]


class Ship:
    """A single ship, e.g. the Carrier or the Destroyer."""

    def __init__(self, name: str, size: int) -> None:
        self.name: str = name
        self.size: int = size

        # The cells this ship occupies. Empty until place() is called.
        self.positions: List[Position] = []

        # The subset of self.positions that have been hit so far.
        self.hits: Set[Position] = set()

    def place(self, positions: List[Position]) -> None:
        """Assign this ship to a list of board cells."""
        if len(positions) != self.size:
            raise ValueError(
                f"{self.name} needs {self.size} positions, got {len(positions)}"
            )
        self.positions = positions

    def occupies(self, position: Position) -> bool:
        """Return True if this ship sits on the given cell."""
        return position in self.positions

    def register_hit(self, position: Position) -> None:
        """Record that this ship was hit at the given cell."""
        if position in self.positions:
            self.hits.add(position)

    def is_sunk(self) -> bool:
        """A ship is sunk once every one of its cells has been hit."""
        return len(self.hits) == self.size
