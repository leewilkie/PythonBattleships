"""
Battleships - network multiplayer entry point.

One side hosts (this also starts the server, and the host plays as
player 0):

    python network_main.py --host

The other side connects to the host's IP to join as player 1:

    python network_main.py --connect <host-ip>

The server referees the game and is the only side that knows both fleets;
each client only ever sees its own ships plus the shots fired so far.
"""

import argparse
import os
import queue
import sys
import threading
from typing import NoReturn

# Must be set before pygame.init(): with two game windows on one machine,
# each turn means clicking into whichever window doesn't currently have
# focus. SDL's default behaviour is to spend that click purely on focusing
# the window (dropping it as input), which reads as "the first click did
# nothing" - this hint makes the focusing click also register normally.
os.environ.setdefault("SDL_MOUSE_FOCUS_CLICKTHROUGH", "1")

import pygame

from battleships import constants
from battleships.board import ShotResult
from battleships.game_state import GameState
from battleships.network import protocol
from battleships.network.client import NetworkClient, RemoteGameView
from battleships.network.server import BattleshipServer
from battleships.renderer import Renderer

HANDSHAKE_TIMEOUT_SECONDS = 10.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Battleships over the network.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--host", action="store_true", help="Host the game and play as player 0."
    )
    mode.add_argument(
        "--connect", metavar="HOST", help="Connect to a host's IP/hostname, as player 1."
    )
    parser.add_argument("--port", type=int, default=constants.DEFAULT_PORT)
    return parser.parse_args()


def connect(args: argparse.Namespace) -> NetworkClient:
    """Set up the network connection: start a server thread first if we're
    hosting, then connect a client (to ourselves, or to the remote host)."""
    if args.host:
        server = BattleshipServer("0.0.0.0", args.port)
        server.start()  # bind before returning, so our own connect() below can't race it
        threading.Thread(target=server.run, daemon=True).start()
        return NetworkClient("127.0.0.1", args.port)
    return NetworkClient(args.connect, args.port)


def handshake(client: NetworkClient) -> RemoteGameView:
    """Block for the server's opening messages and build the initial view.
    Only used once, before the pygame loop starts."""
    welcome = client.recv(HANDSHAKE_TIMEOUT_SECONDS)
    your_board = client.recv(HANDSHAKE_TIMEOUT_SECONDS)
    start = client.recv(HANDSHAKE_TIMEOUT_SECONDS)
    return RemoteGameView(
        player_id=welcome["player_id"],
        grid_size=welcome["grid_size"],
        own_ships=your_board["ships"],
        first_player=start["first_player"],
    )


def apply_messages(view: RemoteGameView, client: NetworkClient) -> None:
    """Drain whatever the server has sent since last frame and fold it into
    the local view."""
    for message in client.poll():
        if message["type"] == protocol.FIRE_RESULT:
            position = (message["row"], message["col"])
            view.apply_fire_result(message["by"], position, ShotResult[message["result"]])
        elif message["type"] == protocol.GAME_OVER:
            view.apply_game_over(message["winner"])


def _fail(message: str) -> NoReturn:
    """Print a one-line error and exit, instead of an unhandled traceback."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    args = parse_args()

    if args.host:
        print(f"Waiting for the other player to connect on port {args.port}...", flush=True)
    else:
        print(f"Connecting to {args.connect}:{args.port}...", flush=True)

    try:
        client = connect(args)
    except OSError as exc:
        if args.host:
            _fail(f"Could not start the server on port {args.port} - {exc}")
        else:
            _fail(f"Could not connect to {args.connect}:{args.port} - {exc}")

    try:
        view = handshake(client)
    except queue.Empty:
        if args.host:
            _fail(
                f"Timed out after {HANDSHAKE_TIMEOUT_SECONDS:.0f}s waiting for the other "
                "player to connect."
            )
        else:
            _fail(
                f"Timed out after {HANDSHAKE_TIMEOUT_SECONDS:.0f}s waiting for the host to "
                "start the game."
            )

    print("Both players connected - the game begins now!", flush=True)

    pygame.init()
    pygame.display.set_caption("Battleships - Multiplayer")
    screen = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    renderer = Renderer(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if view.state == GameState.PLAYER_TURN:
                    cell = Renderer.screen_to_grid(
                        event.pos, constants.RIGHT_BOARD_ORIGIN, constants.GRID_SIZE
                    )
                    if cell is not None:
                        client.send_fire(cell)

        apply_messages(view, client)

        renderer.draw(view)
        pygame.display.flip()
        clock.tick(constants.FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
