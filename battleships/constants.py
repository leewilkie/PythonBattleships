"""
Constants used throughout the game.

Keeping these in one place makes it easy to tweak the look and feel of the
game (grid size, colours, timing, ...) without hunting through every file.
"""

from typing import List, Tuple

# --- Board setup ---------------------------------------------------------

GRID_SIZE: int = 10  # standard Battleships board is 10x10

# (name, length) for each ship in the classic fleet.
SHIP_SPECS: List[Tuple[str, int]] = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]

# --- Layout / sizing (in pixels) -----------------------------------------

CELL_SIZE: int = 32  # each grid square is 32x32 pixels
BOARD_PIXEL_SIZE: int = GRID_SIZE * CELL_SIZE

MARGIN: int = 40  # space between the window edge and the boards
GRID_GAP: int = 80  # horizontal space between the two boards
TITLE_SPACE: int = 40  # space above each board reserved for its title text
STATUS_SPACE: int = 60  # space at the bottom of the window for status text

# Top-left pixel coordinate of each board.
LEFT_BOARD_ORIGIN: Tuple[int, int] = (MARGIN, MARGIN + TITLE_SPACE)
RIGHT_BOARD_ORIGIN: Tuple[int, int] = (
    MARGIN + BOARD_PIXEL_SIZE + GRID_GAP,
    MARGIN + TITLE_SPACE,
)

WINDOW_WIDTH: int = MARGIN * 2 + BOARD_PIXEL_SIZE * 2 + GRID_GAP
WINDOW_HEIGHT: int = MARGIN + TITLE_SPACE + BOARD_PIXEL_SIZE + STATUS_SPACE

# --- Timing ----------------------------------------------------------------

FPS: int = 30

# --- Networking --------------------------------------------------------------

DEFAULT_PORT: int = 5555

# --- Colours (RGB) ---------------------------------------------------------

BACKGROUND: Tuple[int, int, int] = (10, 25, 47)
GRID_LINE: Tuple[int, int, int] = (70, 100, 130)
WATER: Tuple[int, int, int] = (24, 60, 90)
SHIP_COLOR: Tuple[int, int, int] = (120, 120, 120)
HIT_COLOR: Tuple[int, int, int] = (220, 60, 60)
MISS_COLOR: Tuple[int, int, int] = (200, 200, 200)
TEXT_COLOR: Tuple[int, int, int] = (230, 230, 230)
