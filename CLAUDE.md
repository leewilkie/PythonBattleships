# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A graphical Battleships game built with pygame.

## Commands

Install dependencies:

```
pip install -r requirements.txt
```

Run the game (single player vs. the computer):

```
python main.py
```

Run network multiplayer (two humans, one game each side):

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
- [battleships/player.py](battleships/player.py) — `Player`: base class holding a name and its own
  `Board`, with `take_shot` to fire at an enemy board.
- [battleships/computer_player.py](battleships/computer_player.py) — `ComputerPlayer(Player)`: "hunt and
  target" AI — fires randomly until a hit, then queues orthogonal neighbours to home in on the rest of
  the ship, clearing the queue once it's sunk.
- [battleships/game.py](battleships/game.py) — `Game`: owns both boards and players, and the `GameState`
  enum (`HUMAN_TURN` / `COMPUTER_TURN` / `HUMAN_WON` / `COMPUTER_WON`). `human_fire()` and
  `computer_turn()` are the only ways state advances; both boards are randomly populated in `__init__`.
- [battleships/renderer.py](battleships/renderer.py) — `Renderer`: all pygame drawing (boards, ships,
  shot markers, status text, game-over overlay). The only class that imports `pygame` besides
  [main.py](main.py) and [network_main.py](network_main.py). Also converts mouse coordinates to grid
  cells via `screen_to_grid`. `draw` takes a `GameView` — a `Protocol` (`human_board`,
  `computer_board`, `state`, `is_over()`) satisfied by both `Game` and the network `RemoteGameView`,
  so rendering is identical in single-player and multiplayer.
- [battleships/constants.py](battleships/constants.py) — all tunable values in one place: grid size,
  ship specs, pixel layout/window size, colours, timing (FPS, AI move delay), and `DEFAULT_PORT` for
  networking.
- [main.py](main.py) — the pygame event loop for single player. Reads mouse clicks, delegates to
  `Game`, and calls `Renderer.draw` each frame. The human's shot and the computer's reply are
  deliberately decoupled by `AI_MOVE_DELAY_MS` so the computer's move doesn't happen instantly and is
  easy to follow on screen.

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
  `RemoteGameView` — a `Game`-shaped object built entirely from server messages. Its `computer_board`
  stays ship-less; `.shots` is written directly from `fire_result` rather than through `receive_shot`.
- [network_main.py](network_main.py) — the multiplayer entry point and pygame loop: `--host` starts a
  server thread then connects a local client; both do a blocking handshake, then each frame send
  clicks as `fire` and fold incoming messages into the `RemoteGameView`.

### Key conventions

- A `Position` is always `(row, col)`, not `(x, y)` — pixel conversion only happens in `Renderer`.
- Game-state transitions live only in `Game` (single player) or are driven by server messages in
  `RemoteGameView` (multiplayer); `Renderer` reads state but never mutates it.
- Two boards are drawn side by side: the local player's own fleet (ships revealed) on the left
  (`LEFT_BOARD_ORIGIN`) and the opponent's board (ships hidden) on the right (`RIGHT_BOARD_ORIGIN`).
- The `GameState` enum still uses `HUMAN_*` / `COMPUTER_*` names in multiplayer, read as
  "local player" / "opponent"; `Renderer`'s status text says "Opponent" rather than "Computer".
- `Game` is built for one human vs. one `ComputerPlayer`; human-vs-human is a separate path via the
  network server rather than a second local `Player`.
