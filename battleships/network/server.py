"""
The authoritative multiplayer server: accepts exactly two players, places
both fleets, and referees the game - it is the only thing that ever calls
Board.receive_shot, so neither client needs to be trusted with the other's
ship positions or with deciding what counts as a hit.
"""

import queue
import socket
import threading
from typing import Any, Dict, List, Optional, Tuple

from .. import constants
from ..board import Board, ShotResult
from . import protocol
from .protocol import MessageStream


class BattleshipServer:
    """Listens for two players and runs one game to completion."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

        self._listener: Optional[socket.socket] = None
        self._streams: List[MessageStream] = []
        self.boards: List[Board] = []
        self.current_turn: int = 0

        # (player_id, message) pairs from both connections' reader threads.
        self._incoming: "queue.Queue[Tuple[int, Dict[str, Any]]]" = queue.Queue()

    def start(self) -> None:
        """Bind and start listening. Safe to call before any client connects."""
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(2)
        self._listener = listener

    def run(self) -> None:
        """Accept both players and referee the game. Blocks until the game
        ends, so this should be run on its own thread."""
        if self._listener is None:
            raise RuntimeError("call start() before run()")

        for player_id in range(2):
            connection, _address = self._listener.accept()
            # See NetworkClient's matching setsockopt call for why this
            # matters: without it, small messages like a single fire can sit
            # in the Nagle buffer instead of going out immediately.
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            stream = MessageStream(connection)
            self._streams.append(stream)

            board = Board(constants.GRID_SIZE)
            board.place_ships_randomly(constants.SHIP_SPECS)
            self.boards.append(board)

            stream.send(protocol.make_welcome(player_id, constants.GRID_SIZE))
            stream.send(
                protocol.make_your_board(
                    [(ship.name, ship.positions) for ship in board.ships]
                )
            )
            threading.Thread(
                target=self._read_loop, args=(player_id, stream), daemon=True
            ).start()

        for stream in self._streams:
            stream.send(protocol.make_start(first_player=0))

        self._referee_loop()

    def _read_loop(self, player_id: int, stream: MessageStream) -> None:
        """Runs on a background thread, one per connection: forwards every
        decoded message onto the shared queue for the referee loop."""
        try:
            for message in stream.read_messages():
                self._incoming.put((player_id, message))
        except OSError:
            pass  # connection dropped - the referee loop simply stops hearing from them

    def _referee_loop(self) -> None:
        """Consumes fire messages in turn order and broadcasts the outcome,
        until one side's fleet is entirely sunk."""
        while True:
            player_id, message = self._incoming.get()
            if message.get("type") != protocol.FIRE or player_id != self.current_turn:
                continue

            position = (message["row"], message["col"])
            defender_id = 1 - player_id
            defender_board = self.boards[defender_id]
            if not defender_board.is_valid_position(position):
                continue

            result = defender_board.receive_shot(position)
            self._broadcast(protocol.make_fire_result(player_id, position, result))

            if result == ShotResult.ALREADY_SHOT:
                continue  # doesn't end their turn, matches single-player behaviour

            if defender_board.all_ships_sunk():
                self._broadcast(protocol.make_game_over(winner=player_id))
                break

            self.current_turn = defender_id

        self._close_all()

    def _broadcast(self, message: Dict[str, Any]) -> None:
        for stream in self._streams:
            stream.send(message)

    def _close_all(self) -> None:
        for stream in self._streams:
            stream.close()
        if self._listener is not None:
            self._listener.close()
