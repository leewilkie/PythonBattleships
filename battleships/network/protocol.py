"""
The wire protocol for network multiplayer: one JSON object per line, sent
over a plain TCP socket. This module only knows how to build and frame
messages - it has no opinion about who sends what to whom (see server.py
and client.py for that).
"""

import json
import socket
from typing import Any, Dict, Iterator, List, Tuple

from ..board import ShotResult
from ..ship import Position

# A message is just a JSON-able dict with a "type" field naming one of these.
WELCOME = "welcome"
YOUR_BOARD = "your_board"
START = "start"
FIRE = "fire"
FIRE_RESULT = "fire_result"
GAME_OVER = "game_over"


def encode(message: Dict[str, Any]) -> bytes:
    """Serialise a message dict to a single newline-terminated JSON line."""
    return (json.dumps(message) + "\n").encode("utf-8")


def make_welcome(player_id: int, grid_size: int) -> Dict[str, Any]:
    return {"type": WELCOME, "player_id": player_id, "grid_size": grid_size}


def make_your_board(ships: List[Tuple[str, List[Position]]]) -> Dict[str, Any]:
    return {
        "type": YOUR_BOARD,
        "ships": [{"name": name, "positions": positions} for name, positions in ships],
    }


def make_start(first_player: int) -> Dict[str, Any]:
    return {"type": START, "first_player": first_player}


def make_fire(position: Position) -> Dict[str, Any]:
    row, col = position
    return {"type": FIRE, "row": row, "col": col}


def make_fire_result(by: int, position: Position, result: ShotResult) -> Dict[str, Any]:
    row, col = position
    return {"type": FIRE_RESULT, "by": by, "row": row, "col": col, "result": result.name}


def make_game_over(winner: int) -> Dict[str, Any]:
    return {"type": GAME_OVER, "winner": winner}


class MessageStream:
    """Buffers bytes off a socket and yields one decoded message dict per
    complete line, since a single recv() can return a partial line, several
    lines at once, or anything in between."""

    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._buffer = b""

    def send(self, message: Dict[str, Any]) -> None:
        self._sock.sendall(encode(message))

    def close(self) -> None:
        self._sock.close()

    def read_messages(self) -> Iterator[Dict[str, Any]]:
        """Block on recv() until the connection closes, yielding each
        complete message as it arrives. Intended to be run on its own
        thread, one per connection."""
        while True:
            chunk = self._sock.recv(4096)
            if not chunk:
                return  # the other end closed the connection
            self._buffer += chunk
            while b"\n" in self._buffer:
                line, self._buffer = self._buffer.split(b"\n", 1)
                if line:
                    yield json.loads(line.decode("utf-8"))
