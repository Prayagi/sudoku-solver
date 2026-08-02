"""Sudoku puzzle generation and backtracking solver."""

from __future__ import annotations

import copy
import random
from typing import Iterator, Optional


Grid = list[list[int]]


def empty_grid() -> Grid:
    return [[0] * 9 for _ in range(9)]


def clone_grid(grid: Grid) -> Grid:
    return copy.deepcopy(grid)


def iter_empty(grid: Grid) -> Iterator[tuple[int, int]]:
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                yield row, col


def first_empty(grid: Grid) -> Optional[tuple[int, int]]:
    return next(iter_empty(grid), None)


def is_placement_ok(grid: Grid, row: int, col: int, value: int) -> bool:
    if any(grid[row][c] == value for c in range(9)):
        return False
    if any(grid[r][col] == value for r in range(9)):
        return False

    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if grid[r][c] == value:
                return False
    return True


def solve_inplace(grid: Grid, shuffle_choices: bool = False) -> bool:
    spot = first_empty(grid)
    if spot is None:
        return True

    row, col = spot
    options = list(range(1, 10))
    if shuffle_choices:
        random.shuffle(options)

    for value in options:
        if is_placement_ok(grid, row, col, value):
            grid[row][col] = value
            if solve_inplace(grid, shuffle_choices=shuffle_choices):
                return True
            grid[row][col] = 0
    return False


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """Count solutions up to `limit` (used to enforce uniqueness)."""
    spot = first_empty(grid)
    if spot is None:
        return 1

    row, col = spot
    found = 0
    for value in range(1, 10):
        if is_placement_ok(grid, row, col, value):
            grid[row][col] = value
            found += count_solutions(grid, limit)
            grid[row][col] = 0
            if found >= limit:
                return found
    return found


def solved_copy(grid: Grid) -> Optional[Grid]:
    result = clone_grid(grid)
    if solve_inplace(result):
        return result
    return None


def _fill_diagonal_boxes(grid: Grid) -> None:
    for box in range(0, 9, 3):
        digits = list(range(1, 10))
        random.shuffle(digits)
        for r in range(3):
            for c in range(3):
                grid[box + r][box + c] = digits[r * 3 + c]


def _carve_unique(grid: Grid, target_removals: int) -> None:
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    removed = 0

    for row, col in cells:
        if removed >= target_removals:
            break
        backup = grid[row][col]
        if backup == 0:
            continue
        grid[row][col] = 0
        probe = clone_grid(grid)
        if count_solutions(probe, limit=2) != 1:
            grid[row][col] = backup
        else:
            removed += 1


def make_puzzle(difficulty: str = "medium") -> tuple[Grid, Grid]:
    """
    Build a playable puzzle with a unique solution.

    Returns (puzzle, solution). Empty cells are 0.
    """
    removals = {
        "easy": random.randint(35, 40),
        "medium": random.randint(42, 48),
        "hard": random.randint(50, 55),
    }.get(difficulty, random.randint(42, 48))

    solution = empty_grid()
    _fill_diagonal_boxes(solution)
    if not solve_inplace(solution, shuffle_choices=True):
        return make_puzzle(difficulty)

    puzzle = clone_grid(solution)
    _carve_unique(puzzle, removals)
    return puzzle, clone_grid(solution)


def boards_equal(a: Grid, b: Grid) -> bool:
    return all(a[r][c] == b[r][c] for r in range(9) for c in range(9))
