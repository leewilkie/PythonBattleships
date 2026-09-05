"""
The Renderer class - all pygame drawing code lives here, so the game logic
classes (Board, Ship, Game, ...) don't need to know pygame exists at all.
"""

from typing import Optional, Protocol, Tuple

import pygame

from . import constants
from .board import Board, Position
from .game import GameState


class GameView(Protocol):
    """The shape Renderer needs in order to draw a game: a local Game
    satisfies this naturally, and so does a network-driven RemoteGameView -
    Renderer doesn't care which one it's given, only that state is never
    mutated here."""

    human_board: Board
    computer_board: Board
    state: GameState

    def is_over(self) -> bool: ...


class Renderer:
    """Draws the current game state to a pygame Surface."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self.font = pygame.font.SysFont("arial", 20)
        self.big_font = pygame.font.SysFont("arial", 40, bold=True)

    def draw(self, game: GameView) -> None:
        """Draw everything: both boards, the status text, and game over screen."""
        self.screen.fill(constants.BACKGROUND)

        self._draw_board(
            game.human_board,
            constants.LEFT_BOARD_ORIGIN,
            reveal_ships=True,
            title="Your Fleet",
        )
        self._draw_board(
            game.computer_board,
            constants.RIGHT_BOARD_ORIGIN,
            reveal_ships=False,
            title="Enemy Waters",
        )
        self._draw_status(game)

        if game.is_over():
            self._draw_game_over(game)

    def _draw_board(
        self, board: Board, origin: Position, reveal_ships: bool, title: str
    ) -> None:
        """Draw one 10x10 grid, its ships (if revealed), and shot markers."""
        origin_x, origin_y = origin

        title_surface = self.font.render(title, True, constants.TEXT_COLOR)
        self.screen.blit(title_surface, (origin_x, origin_y - 28))

        for row in range(board.size):
            for col in range(board.size):
                rect = pygame.Rect(
                    origin_x + col * constants.CELL_SIZE,
                    origin_y + row * constants.CELL_SIZE,
                    constants.CELL_SIZE,
                    constants.CELL_SIZE,
                )

                colour = constants.WATER
                if reveal_ships and board.ship_at((row, col)) is not None:
                    colour = constants.SHIP_COLOR

                pygame.draw.rect(self.screen, colour, rect)
                pygame.draw.rect(self.screen, constants.GRID_LINE, rect, width=1)

                self._draw_shot_marker(rect, board.shots.get((row, col)))

    def _draw_shot_marker(self, rect: pygame.Rect, shot: Optional[bool]) -> None:
        """Draw a marker on a cell if it has been shot at: a hit or a miss."""
        if shot is True:
            pygame.draw.circle(
                self.screen, constants.HIT_COLOR, rect.center, constants.CELL_SIZE // 4
            )
        elif shot is False:
            pygame.draw.circle(
                self.screen, constants.MISS_COLOR, rect.center, constants.CELL_SIZE // 6
            )

    def _draw_status(self, game: GameView) -> None:
        """Draw a line of text describing whose turn it is (or who won)."""
        messages = {
            GameState.HUMAN_TURN: "Your turn - click a cell in Enemy Waters",
            GameState.COMPUTER_TURN: "Opponent is thinking...",
            GameState.HUMAN_WON: "You win!",
            GameState.COMPUTER_WON: "Opponent wins!",
        }
        message = messages[game.state]
        surface = self.font.render(message, True, constants.TEXT_COLOR)
        self.screen.blit(surface, (constants.MARGIN, constants.WINDOW_HEIGHT - 40))

    def _draw_game_over(self, game: GameView) -> None:
        """Dim the screen and show a big win/lose message."""
        overlay = pygame.Surface((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        text = "YOU WIN!" if game.state == GameState.HUMAN_WON else "OPPONENT WINS!"
        surface = self.big_font.render(text, True, constants.TEXT_COLOR)
        rect = surface.get_rect(
            center=(constants.WINDOW_WIDTH // 2, constants.WINDOW_HEIGHT // 2)
        )
        self.screen.blit(surface, rect)

    @staticmethod
    def screen_to_grid(
        mouse_pos: Tuple[int, int], origin: Position, grid_size: int
    ) -> Optional[Position]:
        """Convert a mouse click into a (row, col) cell, or None if outside the grid."""
        mouse_x, mouse_y = mouse_pos
        origin_x, origin_y = origin

        col = (mouse_x - origin_x) // constants.CELL_SIZE
        row = (mouse_y - origin_y) // constants.CELL_SIZE

        if 0 <= row < grid_size and 0 <= col < grid_size:
            return (row, col)
        return None
