# Sudoku Solver

College assignment for **placement training** — a playable Sudoku app with a visual backtracking solver, built in Python and Pygame.

## Algorithm: Backtracking

The solver uses **backtracking**, a depth-first search that tries values and undoes dead ends.

For each empty cell:

1. Try digits `1` through `9`.
2. Accept a digit only if it does not already appear in the same **row**, **column**, or **3×3 box**.
3. Place it and recurse to the next empty cell.
4. If a later cell has no valid digit, **backtrack**: clear the current cell and try the next option.
5. When no empty cells remain, the board is solved.

This is implemented in `puzzle.py` (`solve_inplace`). Pressing **Space** in the UI runs the same idea with a short delay so you can see placements and backtracks.

### Puzzle generation

1. Fill a full valid board (diagonal boxes first, then backtracking with shuffled digits).
2. Remove cells one by one, keeping the puzzle **uniquely solvable** (`count_solutions` must stay `1`).
3. The app stores that unique solution for checking answers and hints.

## Project structure

| File | Role |
|------|------|
| `main.py` | Starts the app |
| `puzzle.py` | Generate, validate, and solve boards |
| `ui.py` | Pygame UI, input, visual solve, hints |
| `requirements.txt` | Dependencies |

## Setup

Requires Python 3.

```bash
pip install -r requirements.txt
python main.py
```

## How to play

A new medium puzzle loads on start. The top-left cell is selected so you can play with the keyboard only.

| Key | Action |
|-----|--------|
| Arrow keys | Move selection |
| `1`–`9` | Enter a draft value |
| `Enter` | Confirm the draft (wrong guesses count as mistakes) |
| `Backspace` / `Delete` | Clear the cell |
| `Space` | Auto-solve with animated backtracking |
| `H` | Hint — fill one empty cell correctly |
| `R` | New random puzzle |

You can also click a cell with the mouse to select it.

## Learning takeaways

- Recursion and backtracking on a constraint problem
- Validity checks (row / column / box)
- Generating a puzzle that still has exactly one solution
- Simple game loop and keyboard UI with Pygame
