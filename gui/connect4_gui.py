"""
Connect-4 AI  -  graphical demo (for the project video)

Needs:  pip install pygame
Run:    python gui/connect4_gui.py        (from the repo root)

Controls
  1 / 2 / 3   choose Easy / Medium / Hard (search depth 2 / 4 / 6)
  Mouse click drop your (red) disc in a column
  C           compare: run plain Minimax vs Alpha-Beta on the current board
  R           restart (back to level select)
  Esc         quit
"""
import math
import sys
import time
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import connect4 as c4  # noqa: E402
from connect4 import AI, EMPTY, HUMAN, ROWS, COLS  # noqa: E402

CELL = 96
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
TOP = 110                       # space above the board for the hover disc
PANEL_W = 470
W, H = BOARD_W + PANEL_W, TOP + BOARD_H + 20
RADIUS = CELL // 2 - 9

NAVY = (31, 58, 95)
BLUE = (36, 86, 166)
BG = (246, 247, 251)
RED = (200, 54, 74)
GOLD = (242, 176, 30)
WHITE = (253, 253, 254)
INK = (27, 42, 61)
MUTED = (90, 105, 125)
GREEN = (29, 122, 92)
CARD = (231, 238, 250)

LEVELS = {1: ("Easy", 2), 2: ("Medium", 4), 3: ("Hard", 6)}


def winning_cells(board, p):
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = [(r + i * dr, c + i * dc) for i in range(4)]
                if all(0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == p for rr, cc in cells):
                    return cells
    return []


def landing_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None


class Demo:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Connect-4 AI  |  Minimax + Alpha-Beta")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.f_big = pygame.font.SysFont("arial", 40, bold=True)
        self.f_mid = pygame.font.SysFont("arial", 26, bold=True)
        self.f_txt = pygame.font.SysFont("arial", 22)
        self.f_small = pygame.font.SysFont("arial", 19)
        self.reset()

    # ------------------------------------------------------------- state
    def reset(self):
        self.board = c4.new_board()
        self.level = None
        self.turn = HUMAN
        self.over = None            # "You win!", "AI wins!", "Draw"
        self.win_cells = []
        self.hover = 3
        self.last = None            # stats of the AI's last move
        self.compare = None         # result of the C comparison
        self.total_nodes = 0
        self.moves = 0

    # ---------------------------------------------------------- drawing
    def text(self, s, font, color, x, y, center=False):
        img = font.render(s, True, color)
        rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
        self.screen.blit(img, rect)

    def draw_board(self, falling=None):
        pygame.draw.rect(self.screen, BLUE, (0, TOP, BOARD_W, BOARD_H), border_radius=22)
        for r in range(ROWS):
            for c in range(COLS):
                v = self.board[r][c]
                if falling and (r, c) == falling[:2]:
                    v = EMPTY
                col = {EMPTY: BG, HUMAN: RED, AI: GOLD}[v]
                centre = (c * CELL + CELL // 2, TOP + r * CELL + CELL // 2)
                pygame.draw.circle(self.screen, col, centre, RADIUS)
        if falling:
            r, c, y, piece = falling
            pygame.draw.circle(self.screen, RED if piece == HUMAN else GOLD,
                               (c * CELL + CELL // 2, int(y)), RADIUS)
        for r, c in self.win_cells:
            pygame.draw.circle(self.screen, WHITE, (c * CELL + CELL // 2, TOP + r * CELL + CELL // 2),
                               RADIUS + 3, 6)

    def draw_panel(self):
        x0 = BOARD_W + 24
        pygame.draw.rect(self.screen, NAVY, (BOARD_W + 10, 0, PANEL_W - 10, H))
        self.text("CONNECT-4 AI", self.f_big, WHITE, x0, 20)
        self.text("Minimax + Alpha-Beta pruning", self.f_txt, (210, 220, 235), x0, 68)
        y = 115
        if self.level:
            name, depth = LEVELS[self.level]
            self.text(f"Level: {name}   (search depth {depth})", self.f_mid, GOLD, x0, y)
        y += 50
        self.text("You = RED      AI = YELLOW", self.f_txt, WHITE, x0, y)
        y += 45
        pygame.draw.rect(self.screen, CARD, (x0, y, PANEL_W - 58, 190), border_radius=14)
        self.text("AI's last move", self.f_mid, NAVY, x0 + 16, y + 12)
        if self.last:
            col, nodes, secs, val = self.last
            self.text(f"Column played:  {col + 1}", self.f_txt, INK, x0 + 16, y + 55)
            self.text(f"Positions searched:  {nodes:,}", self.f_txt, INK, x0 + 16, y + 87)
            self.text(f"Thinking time:  {secs * 1000:.0f} ms", self.f_txt, INK, x0 + 16, y + 119)
            self.text(f"Evaluation:  {val:+,}" if abs(val) < 1e6 else
                      ("Evaluation:  AI can force a WIN" if val > 0 else "Evaluation:  AI is losing"),
                      self.f_txt, INK, x0 + 16, y + 151)
        else:
            self.text("Waiting for the first move...", self.f_txt, MUTED, x0 + 16, y + 60)
        y += 210
        pygame.draw.rect(self.screen, CARD, (x0, y, PANEL_W - 58, 200), border_radius=14)
        self.text("C key: Minimax vs Alpha-Beta", self.f_mid, NAVY, x0 + 16, y + 12)
        if self.compare == "busy":
            self.text("Running plain minimax... please wait", self.f_txt, RED, x0 + 16, y + 60)
        elif self.compare:
            d, mm, ab = self.compare
            self.text(f"Depth {d} on this exact board:", self.f_txt, INK, x0 + 16, y + 55)
            self.text(f"Minimax:     {mm[1]:>9,} nodes  {mm[2] * 1000:>6.0f} ms", self.f_small, RED, x0 + 16, y + 90)
            self.text(f"Alpha-Beta: {ab[1]:>9,} nodes  {ab[2] * 1000:>6.0f} ms", self.f_small, GREEN, x0 + 16, y + 118)
            saved = 100 * (1 - ab[1] / max(mm[1], 1))
            same = "SAME move" if mm[0] == ab[0] else "different move (equal score)"
            self.text(f"{saved:.0f}% fewer nodes, {same}", self.f_txt, NAVY, x0 + 16, y + 155)
        else:
            self.text("Shows how much work pruning saves", self.f_txt, MUTED, x0 + 16, y + 60)
        y += 220
        self.text(f"Moves played: {self.moves}    Total AI nodes: {self.total_nodes:,}",
                  self.f_small, (210, 220, 235), x0, y)
        self.text("R = restart    Esc = quit", self.f_small, (210, 220, 235), x0, H - 40)

    def draw_top(self):
        pygame.draw.rect(self.screen, BG, (0, 0, BOARD_W, TOP))
        if self.over:
            self.text(self.over + "   (press R to play again)", self.f_mid, NAVY, BOARD_W // 2, TOP // 2, True)
        elif self.turn == HUMAN:
            pygame.draw.circle(self.screen, RED, (self.hover * CELL + CELL // 2, TOP // 2 + 5), RADIUS)
        else:
            self.text("AI is thinking...", self.f_mid, NAVY, BOARD_W // 2, TOP // 2, True)

    def frame(self, falling=None):
        self.screen.fill(BG)
        self.draw_top()
        self.draw_board(falling)
        self.draw_panel()
        pygame.display.flip()

    def level_screen(self):
        self.screen.fill(NAVY)
        self.text("CONNECT-4 AI", self.f_big, WHITE, W // 2, 150, True)
        self.text("Adversarial search with Minimax + Alpha-Beta pruning", self.f_txt, (210, 220, 235), W // 2, 200, True)
        for i, (k, (name, d)) in enumerate(LEVELS.items()):
            rect = pygame.Rect(W // 2 - 220, 270 + i * 110, 440, 84)
            pygame.draw.rect(self.screen, GOLD if k == 2 else CARD, rect, border_radius=16)
            self.text(f"{k}.  {name}   (looks {d} moves ahead)", self.f_mid, NAVY, rect.centerx, rect.centery, True)
        self.text("Press 1, 2 or 3 (or click) to start   ·   you play RED and move first",
                  self.f_txt, (210, 220, 235), W // 2, 640, True)
        pygame.display.flip()

    # ---------------------------------------------------------- actions
    def animate_drop(self, col, piece):
        row = landing_row(self.board, col)
        target = TOP + row * CELL + CELL // 2
        y, v = TOP // 2.0, 0.0
        while y < target:
            v += 2.2
            y = min(target, y + v)
            self.frame(falling=(row, col, y, piece))
            self.clock.tick(60)
        self.board = c4.drop(self.board, col, piece)

    def after_move(self, piece):
        self.moves += 1
        if c4.is_win(self.board, piece):
            self.win_cells = winning_cells(self.board, piece)
            self.over = "You win!" if piece == HUMAN else "AI wins!"
        elif not c4.valid_moves(self.board):
            self.over = "Draw"
        else:
            self.turn = AI if piece == HUMAN else HUMAN

    def ai_move(self):
        depth = LEVELS[self.level][1]
        c4.Stats.nodes = 0
        t = time.perf_counter()
        col, val = c4.alphabeta(self.board, depth, -math.inf, math.inf, True, ordered=True)
        secs = time.perf_counter() - t
        nodes = c4.Stats.nodes
        pygame.time.wait(max(0, 350 - int(secs * 1000)))   # short pause so viewers see "thinking"
        self.last = (col, nodes, secs, int(val))
        self.total_nodes += nodes
        self.animate_drop(col, AI)
        self.after_move(AI)

    def run_compare(self):
        if self.over or not self.level:
            return
        d = min(LEVELS[self.level][1], 5)   # plain minimax at depth 6 takes several seconds
        self.compare = "busy"
        self.frame()
        res = []
        for fn in ("minimax", "alphabeta_ordered"):
            t = time.perf_counter()
            col = c4.best_move(self.board, d, fn)
            res.append((col, c4.Stats.nodes, time.perf_counter() - t))
        self.compare = (d, res[0], res[1])

    # -------------------------------------------------------------- loop
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    self.reset()
                if self.level is None:
                    if e.type == pygame.KEYDOWN and e.unicode in "123" and e.unicode:
                        self.level = int(e.unicode)
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        for i in range(3):
                            if pygame.Rect(W // 2 - 220, 270 + i * 110, 440, 84).collidepoint(e.pos):
                                self.level = i + 1
                    continue
                if e.type == pygame.KEYDOWN and e.key == pygame.K_c:
                    self.run_compare()
                if e.type == pygame.MOUSEMOTION and e.pos[0] < BOARD_W:
                    self.hover = e.pos[0] // CELL
                if (e.type == pygame.MOUSEBUTTONDOWN and e.pos[0] < BOARD_W and not self.over
                        and self.turn == HUMAN):
                    col = e.pos[0] // CELL
                    if col in c4.valid_moves(self.board):
                        self.compare = None
                        self.animate_drop(col, HUMAN)
                        self.after_move(HUMAN)
            if self.level is None:
                self.level_screen()
            else:
                self.frame()
                if self.turn == AI and not self.over:
                    self.ai_move()
            self.clock.tick(60)


if __name__ == "__main__":
    Demo().run()
