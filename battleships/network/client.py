"""
The network client side: a thin socket wrapper that hands decoded messages
to the pygame loop, plus RemoteGameView - a stand-in for Game that Renderer
can draw without any changes, built entirely from what the server tells us.
"""

import queue
import socket
import threading
from typing import Any, Dict, List

from ..board import Board, ShotResult
from ..game import GameState
from ..ship import Position, Ship
from . import protocol
from .protocol import MessageStream


class NetworkClient:
    """Connects to a BattleshipServer and ferries messages to/from it."""

    def __init__(self, host: str, port: int) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        # Without this, Nagle's algorithm can sit on a small outgoing message
        # (like a single fire) until more data follows or a delayed ACK fires,
        # which reads as needing a second click before a shot "takes".
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._stream = MessageStream(sock)

        self._incoming: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self) -> None:
        try:
            for message in self._stream.read_messages():
                self._incoming.put(message)
        except OSError:
            pass  # server connection dropped

    def recv(self, timeout: float) -> Dict[str, Any]:
        """Block for the next message, up to timeout seconds. Used only
        during the initial handshake, before the pygame loop starts."""
        return self._incoming.get(timeout=timeout)

    def poll(self) -> List[Dict[str, Any]]:
        """Drain every message that's arrived so far, without blocking.
        Meant to be called once per frame from the pygame loop."""
        messages = []
        while True:
            try:
                messages.append(self._incoming.get_nowait())
            except queue.Empty:
                break
        return messages

    def send_fire(self, position: Position) -> None:
        self._stream.send(protocol.make_fire(position))


class RemoteGameView:
    """A Game-shaped object driven entirely by server messages: exposes
    human_board, computer_board, state and is_over() so Renderer.draw can
    render it exactly like a local Game."""

    def __init__(
        self,
        player_id: int,
        grid_size: int,
        own_ships: List[Dict[str, Any]],
        first_player: int,
    ) -> None:
        self.player_id = player_id

        self.human_board = Board(grid_size)
        for ship_data in own_ships:
            positions: List[Position] = [tuple(p) for p in ship_data["positions"]]
            ship = Ship(ship_data["name"], len(positions))
            ship.place(positions)
            self.human_board.ships.append(ship)

        # The enemy board's real ship layout is never sent to us - only shot
        # outcomes - so this mirror stays ship-less; its .shots dict is
        # written directly from fire_result messages instead of going
        # through receive_shot (which would have nothing to hit).
        self.computer_board = Board(grid_size)

        self.state = (
            GameState.HUMAN_TURN if first_player == player_id else GameState.COMPUTER_TURN
        )

    def is_over(self) -> bool:
        return self.state in (GameState.HUMAN_WON, GameState.COMPUTER_WON)

    def apply_fire_result(self, by: int, position: Position, result: ShotResult) -> None:
        if result == ShotResult.ALREADY_SHOT:
            return  # nothing changed, doesn't end anyone's turn

        if by == self.player_id:
            self.computer_board.shots[position] = result in (
                ShotResult.HIT,
                ShotResult.SUNK,
            )
            self.state = GameState.COMPUTER_TURN
        else:
            self.human_board.receive_shot(position)
            self.state = GameState.HUMAN_TURN

    def apply_game_over(self, winner: int) -> None:
        self.state = GameState.HUMAN_WON if winner == self.player_id else GameState.COMPUTER_WON
