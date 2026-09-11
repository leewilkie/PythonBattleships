# Battleships

A graphical version of the classic Battleships game, built in Python with pygame.

This game has been developed with Claude code to demonstrate a simple implementation using classes
to establish a good separation of concerns - e.g. game logic, UI rendering etc.

## How to play

Battleships is a two-player guessing game. Each player has a fleet of ships hidden on a grid.
You take turns firing shots at your opponent's grid, trying to sink their ships before they
sink yours. This version is played over the network between two humans.

- Your fleet is shown on the left, with your ships visible.
- Your opponent's grid is shown on the right, with its ships hidden.
- Click a cell on your opponent's grid to fire a shot there.
- Hits, misses, and sunk ships are marked on the grid as you play.
- The first player to sink the other's entire fleet wins!

## Getting started

You'll need Python installed. Then, from the project folder:

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
2. Run the game — one side hosts, the other connects to their IP:
   ```
   python network_main.py --host
   python network_main.py --connect <host-ip>
   ```

## Status

This is a work in progress and features may be added or changed over time.
