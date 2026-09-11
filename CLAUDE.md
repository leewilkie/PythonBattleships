# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A graphical Battleships game built with pygame, played over the network between two humans.

## Commands

Install dependencies:

```
pip install -r requirements.txt
```

Run the game (two humans, one game each side):

```
python network_main.py --host            # host: also starts the server, plays as player 0
python network_main.py --connect <host-ip>   # opponent: joins as player 1
```

Install dev tools (ruff + mypy) and lint/type-check:

```
pip install -r requirements-dev.txt
python -m ruff check .
python -m mypy .
```

`ruff format .` is also available but is not enforced — some lines are wrapped by hand for
readability and `ruff format` would collapse them; run it manually only if you want that style.

There is no test suite or build step configured in this repository.

## Architecture

The game separates pure game logic from pygame rendering so the logic classes have no drawing
dependencies:

- [battleships/ship.py](battleships/ship.py) — `Ship`: a fleet member's cells and hit tracking. Also
  defines `Position = Tuple[int, int]`, the `(row, col)` type used throughout the codebase.
- [battleships/board.py](battleships/board.py) — `Board`: one player's 10x10 grid. Owns ship placement
  (random, non-overlapping) and records shots via `receive_shot`, returning a `ShotResult` enum
  (`MISS` / `HIT` / `SUNK` / `ALREADY_SHOT`).
- [battleships/game_state.py](battleships/game_state.py) — the `GameState` enum (`PLAYER_TURN` /
  `OPPONENT_TURN` / `PLAYER_WON` / `OPPONENT_WON`), shared by `Renderer` and the network
  `RemoteGameView`.
- [battleships/renderer.py](battleships/renderer.py) — `Renderer`: all pygame drawing (boards, ships,
  shot markers, status text, game-over overlay). The only class that imports `pygame` besides
  [network_main.py](network_main.py). Also converts mouse coordinates to grid cells via
  `screen_to_grid`. `draw` takes a `GameView` — a `Protocol` (`player_board`, `opponent_board`,
  `state`, `is_over()`) satisfied by the network `RemoteGameView`.
- [battleships/constants.py](battleships/constants.py) — all tunable values in one place: grid size,
  ship specs, pixel layout/window size, colours, timing (FPS), and `DEFAULT_PORT` for networking.

### Networking (`battleships/network/`)

Multiplayer is authoritative-server: the server places both fleets and is the only side that ever
calls `Board.receive_shot`, so neither client is trusted with the other's ship positions or with
deciding hits. Messages are one JSON object per line over a plain TCP socket (`TCP_NODELAY` on both
ends so a single fire isn't held by Nagle's algorithm).

- [battleships/network/protocol.py](battleships/network/protocol.py) — the wire format: `make_*`
  builders for the six message types (`welcome` / `your_board` / `start` / `fire` / `fire_result` /
  `game_over`) and `MessageStream`, which frames/buffers a socket into decoded message dicts. Knows
  nothing about who sends what.
- [battleships/network/server.py](battleships/network/server.py) — `BattleshipServer`: accepts exactly
  two players, sends each its own fleet, then runs `_referee_loop` — consumes `fire` messages in turn
  order, broadcasts each `fire_result`, and ends on `game_over` when a fleet is fully sunk. One reader
  thread per connection feeds a shared queue.
- [battleships/network/client.py](battleships/network/client.py) — `NetworkClient` (socket wrapper with
  a background reader thread; `recv` blocks for handshake, `poll` drains per frame) and
  `RemoteGameView` — a game-shaped object built entirely from server messages, satisfying the
  `GameView` protocol `Renderer` expects. Its `opponent_board` stays ship-less; `.shots` is written
  directly from `fire_result` rather than through `receive_shot`.
- [network_main.py](network_main.py) — the entry point and pygame loop: `--host` starts a server
  thread then connects a local client; both do a blocking handshake, then each frame send clicks as
  `fire` and fold incoming messages into the `RemoteGameView`.

### Key conventions

- A `Position` is always `(row, col)`, not `(x, y)` — pixel conversion only happens in `Renderer`.
- Game-state transitions are driven entirely by server messages folded into `RemoteGameView`;
  `Renderer` reads state but never mutates it.
- Two boards are drawn side by side: the local player's own fleet (ships revealed) on the left
  (`LEFT_BOARD_ORIGIN`) and the opponent's board (ships hidden) on the right (`RIGHT_BOARD_ORIGIN`).
- `Renderer`'s status text refers to the two sides as "you" and "Opponent".
