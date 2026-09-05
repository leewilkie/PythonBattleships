"""
Battleships - entry point.

Run this file to play: `python main.py`
"""

import sys
from typing import Optional

import pygame

from battleships import constants
from battleships.game import Game, GameState
from battleships.renderer import Renderer


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Battleships")
    screen = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    game = Game()
    renderer = Renderer(screen)

    # When the human's shot ends their turn, we schedule the computer's move
    # for a little later (rather than instantly) so it's easy to follow what
    # happened. This holds the tick count (in ms) for when it should fire.
    computer_move_at: Optional[int] = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == GameState.HUMAN_TURN:
                    cell = Renderer.screen_to_grid(
                        event.pos, constants.RIGHT_BOARD_ORIGIN, constants.GRID_SIZE
                    )
                    if cell is not None:
                        game.human_fire(cell)
                        if game.state == GameState.COMPUTER_TURN:
                            computer_move_at = pygame.time.get_ticks() + constants.AI_MOVE_DELAY_MS

        if (
            game.state == GameState.COMPUTER_TURN
            and computer_move_at is not None
            and pygame.time.get_ticks() >= computer_move_at
        ):
            game.computer_turn()
            computer_move_at = None

        renderer.draw(game)
        pygame.display.flip()
        clock.tick(constants.FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
