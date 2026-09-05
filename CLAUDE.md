# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A graphical Battleships game built with pygame.

## Commands

Install dependencies:

```
pip install -r requirements.txt
```

Run the game:

```
python main.py
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
  [main.py](main.py). Also converts mouse coordinates to grid cells via `screen_to_grid`.
- [battleships/constants.py](battleships/constants.py) — all tunable values in one place: grid size,
  ship specs, pixel layout/window size, colours, and timing (FPS, AI move delay).
- [main.py](main.py) — the pygame event loop. Reads mouse clicks, delegates to `Game`, and calls
  `Renderer.draw` each frame. The human's shot and the computer's reply are deliberately decoupled by
  `AI_MOVE_DELAY_MS` so the computer's move doesn't happen instantly and is easy to follow on screen.

### Key conventions

- A `Position` is always `(row, col)`, not `(x, y)` — pixel conversion only happens in `Renderer`.
- Game-state transitions live only in `Game`; `Renderer` reads state but never mutates it.
- Two boards are drawn side by side: the human's own fleet (ships revealed) on the left
  (`LEFT_BOARD_ORIGIN`) and the computer's board (ships hidden) on the right (`RIGHT_BOARD_ORIGIN`).
- `Game` is currently built for one human vs. one `ComputerPlayer`, but `Player` is written as a base
  class in anticipation of a future human-vs-human mode (noted in plan.md).
