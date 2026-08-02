"""Pygame UI for playing and visualizing Sudoku."""

from __future__ import annotations

import random
import sys
import time
from typing import Optional

import pygame

from puzzle import (
    Grid,
    boards_equal,
    clone_grid,
    first_empty,
    is_placement_ok,
    make_puzzle,
)


# Layout
CELL = 56
GRID = CELL * 9
PAD = 24
STATUS_H = 72
WIDTH = GRID + PAD * 2
HEIGHT = GRID + PAD * 2 + STATUS_H

# Colors — slate board, teal selection
BG = (232, 236, 241)
BOARD_BG = (248, 250, 252)
INK = (30, 41, 59)
GIVEN = (15, 23, 42)
PENCIL = (100, 116, 139)
LINE = (148, 163, 184)
BOX_LINE = (51, 65, 85)
TEAL = (13, 148, 136)
OK = (22, 163, 74)
BAD = (220, 38, 38)
STATUS = (71, 85, 105)


class SudokuApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Sudoku")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 28)
        self.small = pygame.font.SysFont("segoeui", 20)
        self.big = pygame.font.SysFont("segoeui", 36)

        self.puzzle: Grid = []
        self.solution: Grid = []
        self.grid: Grid = []
        self.given: set[tuple[int, int]] = set()
        self.selected: Optional[tuple[int, int]] = None
        self.draft: dict[tuple[int, int], int] = {}
        self.flash_ok: set[tuple[int, int]] = set()
        self.flash_bad: set[tuple[int, int]] = set()
        self.mistakes = 0
        self.started_at = 0.0
        self.finished = False
        self.animating = False

        self.new_game()

    def new_game(self) -> None:
        self.puzzle, self.solution = make_puzzle("medium")
        self.grid = clone_grid(self.puzzle)
        self.given = {
            (r, c) for r in range(9) for c in range(9) if self.puzzle[r][c] != 0
        }
        self.selected = (0, 0)
        self.draft.clear()
        self.flash_ok.clear()
        self.flash_bad.clear()
        self.mistakes = 0
        self.started_at = time.time()
        self.finished = False
        self.animating = False

    def cell_at(self, pos: tuple[int, int]) -> Optional[tuple[int, int]]:
        x, y = pos
        ox, oy = PAD, PAD
        if not (ox <= x < ox + GRID and oy <= y < oy + GRID):
            return None
        col = (x - ox) // CELL
        row = (y - oy) // CELL
        return int(row), int(col)

    def elapsed_label(self) -> str:
        seconds = int(time.time() - self.started_at)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def draw(self) -> None:
        self.screen.fill(BG)
        board = pygame.Rect(PAD, PAD, GRID, GRID)
        pygame.draw.rect(self.screen, BOARD_BG, board, border_radius=4)

        for r in range(9):
            for c in range(9):
                rect = pygame.Rect(PAD + c * CELL, PAD + r * CELL, CELL, CELL)
                key = (r, c)

                if key in self.flash_ok:
                    pygame.draw.rect(self.screen, (220, 252, 231), rect)
                elif key in self.flash_bad:
                    pygame.draw.rect(self.screen, (254, 226, 226), rect)
                elif self.selected == key:
                    pygame.draw.rect(self.screen, (204, 251, 241), rect)

                value = self.grid[r][c]
                draft = self.draft.get(key)
                if value:
                    color = GIVEN if key in self.given else INK
                    text = self.font.render(str(value), True, color)
                    self.screen.blit(text, text.get_rect(center=rect.center))
                elif draft:
                    text = self.font.render(str(draft), True, PENCIL)
                    self.screen.blit(text, text.get_rect(center=rect.center))

        for i in range(10):
            thick = 3 if i % 3 == 0 else 1
            color = BOX_LINE if i % 3 == 0 else LINE
            x = PAD + i * CELL
            y = PAD + i * CELL
            pygame.draw.line(self.screen, color, (x, PAD), (x, PAD + GRID), thick)
            pygame.draw.line(self.screen, color, (PAD, y), (PAD + GRID, y), thick)

        if self.selected is not None:
            r, c = self.selected
            rect = pygame.Rect(PAD + c * CELL, PAD + r * CELL, CELL, CELL)
            pygame.draw.rect(self.screen, TEAL, rect, 3, border_radius=2)

        status_y = PAD + GRID + 18
        mist = self.small.render(f"Mistakes: {self.mistakes}", True, BAD if self.mistakes else STATUS)
        timer = self.small.render(self.elapsed_label(), True, STATUS)
        help_txt = self.small.render(
            "Arrows move | Enter confirm | Space solve | H hint | R new", True, STATUS
        )
        self.screen.blit(mist, (PAD, status_y))
        self.screen.blit(timer, (WIDTH - PAD - timer.get_width(), status_y))
        self.screen.blit(help_txt, (PAD, status_y + 28))

        if self.finished:
            banner = self.big.render("Solved", True, OK)
            self.screen.blit(banner, banner.get_rect(center=(WIDTH // 2, status_y + 14)))

        pygame.display.flip()

    def commit_draft(self) -> None:
        if self.selected is None or self.finished:
            return
        r, c = self.selected
        if (r, c) in self.given or self.grid[r][c] != 0:
            return
        if (r, c) not in self.draft:
            return

        value = self.draft.pop((r, c))
        if value == self.solution[r][c]:
            self.grid[r][c] = value
            if boards_equal(self.grid, self.solution):
                self.finished = True
        else:
            self.mistakes += 1
            self.flash_bad.add((r, c))
            pygame.time.set_timer(pygame.USEREVENT + 1, 350, True)

    def clear_cell(self) -> None:
        if self.selected is None or self.finished:
            return
        r, c = self.selected
        if (r, c) in self.given:
            return
        self.draft.pop((r, c), None)
        self.grid[r][c] = 0

    def give_hint(self) -> None:
        if self.finished:
            return
        empties = [(r, c) for r in range(9) for c in range(9) if self.grid[r][c] == 0]
        if not empties:
            return
        r, c = random.choice(empties)
        self.draft.pop((r, c), None)
        self.grid[r][c] = self.solution[r][c]
        self.flash_ok.add((r, c))
        pygame.time.set_timer(pygame.USEREVENT + 2, 450, True)
        if boards_equal(self.grid, self.solution):
            self.finished = True

    def visual_solve(self) -> bool:
        """Animate backtracking. Returns True when the board is solved."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

        spot = first_empty(self.grid)
        if spot is None:
            return True

        row, col = spot
        self.selected = (row, col)
        for value in range(1, 10):
            if is_placement_ok(self.grid, row, col, value):
                self.grid[row][col] = value
                self.flash_ok.add((row, col))
                self.flash_bad.discard((row, col))
                self.draw()
                pygame.time.delay(40)
                if self.visual_solve():
                    return True
                self.grid[row][col] = 0
                self.flash_ok.discard((row, col))
                self.flash_bad.add((row, col))
                self.draw()
                pygame.time.delay(40)
        return False

    def move_selection(self, d_row: int, d_col: int) -> None:
        if self.selected is None:
            self.selected = (0, 0)
            return
        row, col = self.selected
        self.selected = ((row + d_row) % 9, (col + d_col) % 9)

    def handle_keydown(self, key: int) -> None:
        if key == pygame.K_r:
            self.new_game()
            return
        if key == pygame.K_LEFT:
            self.move_selection(0, -1)
            return
        if key == pygame.K_RIGHT:
            self.move_selection(0, 1)
            return
        if key == pygame.K_UP:
            self.move_selection(-1, 0)
            return
        if key == pygame.K_DOWN:
            self.move_selection(1, 0)
            return
        if key == pygame.K_h:
            self.give_hint()
            return
        if key == pygame.K_SPACE and not self.finished:
            self.animating = True
            self.draft.clear()
            self.selected = None
            self.visual_solve()
            self.flash_ok.clear()
            self.flash_bad.clear()
            self.finished = True
            self.animating = False
            self.selected = (0, 0)
            return

        if self.selected is None or self.finished:
            return

        r, c = self.selected
        if (r, c) in self.given:
            return

        if key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self.clear_cell()
            return
        if key == pygame.K_RETURN:
            self.commit_draft()
            return

        digit = None
        if pygame.K_1 <= key <= pygame.K_9:
            digit = key - pygame.K_0
        elif pygame.K_KP1 <= key <= pygame.K_KP9:
            digit = key - pygame.K_KP0

        if digit is not None:
            if self.grid[r][c] != 0:
                self.grid[r][c] = 0
            self.draft[(r, c)] = digit

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.selected = self.cell_at(event.pos)
                if event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                if event.type == pygame.USEREVENT + 1:
                    self.flash_bad.clear()
                if event.type == pygame.USEREVENT + 2:
                    self.flash_ok.clear()

            if not self.finished and boards_equal(self.grid, self.solution):
                self.finished = True

            self.draw()
            self.clock.tick(60)
