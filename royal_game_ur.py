#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""乌尔王族棋 (Royal Game of Ur) —— Irving Finkel 重构规则。

棋盘 3 行 × 8 列，双方各 7 枚棋子，沿各自 14 格赛道前进。
5 朵玫瑰花格（落上再掷一次），中央玫瑰为安全格（不可被吃、不可共占）。
共享格落子可吃掉对方棋子（打回手中），需精确掷点离盘，
7 枚棋子全部离盘者胜。纯标准库。
"""

import argparse
import copy
import random
import sys

PIECES = 7            # 每方棋子数（Finkel 重构）
TRACK_LEN = 14       # 赛道长度；位置 14 表示已离盘
ROSETTES = (3, 7, 13)       # 玫瑰花格（赛道 0 起编号）
SAFE_ROSETTE = 7     # 中央玫瑰：安全格
NAMES = ("甲", "乙")
GLYPHS = ("甲", "乙")


def track_cell(player, pos):
    """赛道位置 (0..13) -> 棋盘 (行, 列)。"""
    own_row = 2 if player == 0 else 0
    if pos < 4:
        return (own_row, 3 - pos)
    if pos < 12:
        return (1, pos - 4)
    return (own_row, 7 if pos == 12 else 6)


class IllegalMove(Exception):
    """非法走法。"""


class Ur:
    """乌尔王族棋对局。棋子位置：-1=手中，0..13=赛道上，14=已离盘。"""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.pieces = [[-1] * PIECES, [-1] * PIECES]
        self.turn = 0
        self.winner = None
        self.half_moves = 0
        self.knocked = [0, 0]

    def roll(self):
        """掷 4 面骰：返回 0..4（每面 50% 出点）。"""
        return sum(1 for _ in range(4) if self.rng.random() < 0.5)

    def _foe_on_shared(self, player):
        d = {}
        for j, q in enumerate(self.pieces[1 - player]):
            if 4 <= q < 12:
                d.setdefault(q, []).append(j)
        return d

    def legal_moves(self, player, roll):
        """返回 [(子编号, 目标位置)]；目标 14 表示离盘。"""
        if roll <= 0 or self.winner is not None:
            return []
        mine = {p for p in self.pieces[player] if 0 <= p < TRACK_LEN}
        foe_on = self._foe_on_shared(player)
        moves = []
        for i, p in enumerate(self.pieces[player]):
            dest = (p if p >= 0 else -1) + roll
            if dest > TRACK_LEN:
                continue
            if dest == TRACK_LEN:
                moves.append((i, dest))
                continue
            if dest in mine:
                continue
            if dest in foe_on and dest == SAFE_ROSETTE:
                continue  # 中央玫瑰不可共占
            moves.append((i, dest))
        return moves

    def apply_move(self, player, move, roll):
        """执行走法。返回 (是否再掷一次, 是否吃子)。"""
        if self.winner is not None:
            raise IllegalMove("对局已结束")
        i, dest = move
        p = self.pieces[player][i]
        expect = (p if p >= 0 else -1) + roll
        if dest != expect:
            raise IllegalMove(f"走法与掷点不符: 期望 {expect}, 得到 {dest}")
        if not (0 <= dest <= TRACK_LEN):
            raise IllegalMove(f"非法目标: {dest}")
        if dest < TRACK_LEN:
            mine = {q for j, q in enumerate(self.pieces[player])
                    if j != i and 0 <= q < TRACK_LEN}
            if dest in mine:
                raise IllegalMove("落点有己方棋子")
        knocked = False
        if dest < TRACK_LEN and 4 <= dest < 12 and dest != SAFE_ROSETTE:
            for j, q in enumerate(self.pieces[1 - player]):
                if q == dest:
                    self.pieces[1 - player][j] = -1
                    knocked = True
                    self.knocked[player] += 1
        self.pieces[player][i] = dest
        self.half_moves += 1
        if all(q == TRACK_LEN for q in self.pieces[player]):
            self.winner = player
        return (dest in ROSETTES, knocked)

    # ---- AI ----

    def _score_move(self, player, move):
        i, dest = move
        p = self.pieces[player][i]
        s = 0.0
        if dest == TRACK_LEN:
            s += 1000
        if dest in ROSETTES:
            s += 60
        if 4 <= dest < 12 and dest != SAFE_ROSETTE:
            if any(q == dest for q in self.pieces[1 - player]):
                s += 120
        on_board = sum(1 for q in self.pieces[player] if 0 <= q < TRACK_LEN)
        if p == -1 and on_board < 3:
            s += 40
        s += dest * 2
        return s

    def ai_choose(self, player, roll):
        moves = self.legal_moves(player, roll)
        if not moves:
            return None
        scored = [(self._score_move(player, m), self.rng.random(), m)
                  for m in moves]
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return scored[0][2]

    # ---- 展示 ----

    def render(self):
        grid = [["·"] * 8 for _ in range(3)]
        for pos in ROSETTES:
            for pl in (0, 1):
                r, c = track_cell(pl, pos)
                if grid[r][c] == "·":
                    grid[r][c] = "✿"
        for pl in (0, 1):
            for q in self.pieces[pl]:
                if 0 <= q < TRACK_LEN:
                    r, c = track_cell(pl, q)
                    grid[r][c] = GLYPHS[pl]
        lines = ["  " + " ".join(str(c) for c in range(8))]
        for r in range(3):
            lines.append(f"{r} " + " ".join(grid[r]))
        return "\n".join(lines)

    def status(self):
        parts = []
        for pl in (0, 1):
            hand = sum(1 for q in self.pieces[pl] if q == -1)
            off = sum(1 for q in self.pieces[pl] if q == TRACK_LEN)
            parts.append(f"{NAMES[pl]}: 手中{hand} 离盘{off} 吃子{self.knocked[pl]}")
        return " | ".join(parts)


def describe_move(g, player, move):
    i, dest = move
    p = g.pieces[player][i]
    src = "手中" if p == -1 else f"位置{p}"
    dst = "离盘" if dest == TRACK_LEN else f"位置{dest}"
    tags = []
    if dest in ROSETTES:
        tags.append("玫瑰·再掷")
    if 4 <= dest < 12 and any(q == dest for q in g.pieces[1 - player]):
        tags.append("吃子")
    return f"子{i} {src}->{dst}" + (" (" + ",".join(tags) + ")" if tags else "")


def play_game(seed=None, verbose=False, max_half=4000):
    """AI 对 AI 一局。返回 (胜者或 None, 对局对象)。"""
    g = Ur(seed=seed)
    while g.winner is None and g.half_moves < max_half:
        pl = g.turn
        roll = g.roll()
        if verbose:
            print(f"--- {NAMES[pl]} 掷骰: {roll}")
        if roll == 0:
            g.turn = 1 - pl
            continue
        m = g.ai_choose(pl, roll)
        if m is None:
            if verbose:
                print(f"{NAMES[pl]} 无棋可走")
            g.turn = 1 - pl
            continue
        extra, knocked = None, False
        if verbose:
            desc = describe_move(g, pl, m)
        extra, knocked = g.apply_move(pl, m, roll)
        if verbose:
            tail = (" 吃子!" if knocked else "") + (" 再掷!" if extra else "")
            print(f"{NAMES[pl]}: {desc}{tail}")
        if not extra:
            g.turn = 1 - pl
    return g.winner, g


def play_auto(games, seed, verbose):
    wins = [0, 0]
    draws = 0
    total_half = 0
    for n in range(games):
        s = None if seed is None else seed + n
        winner, g = play_game(seed=s, verbose=verbose and games == 1)
        total_half += g.half_moves
        if winner is None:
            draws += 1
            print(f"第 {n + 1}/{games} 局: 和棋 ({g.half_moves} 半回合)")
        else:
            wins[winner] += 1
            print(f"第 {n + 1}/{games} 局: {NAMES[winner]}胜 ({g.half_moves} 半回合)")
    print(f"总计: 甲胜 {wins[0]}, 乙胜 {wins[1]}, 和棋 {draws}, "
          f"平均 {total_half / games:.1f} 半回合/局")


def play_interactive():
    if not sys.stdin.isatty():
        print("交互模式需要终端；无头演示请用 --auto", file=sys.stderr)
        return 2
    g = Ur()
    human = 0
    print("乌尔王族棋：你是甲，对手乙是 AI。输入走法编号，q 退出。")
    while g.winner is None:
        print("\n" + g.render())
        print(g.status())
        pl = g.turn
        roll = g.roll()
        print(f"{NAMES[pl]} 掷骰: {roll}")
        if roll == 0:
            print("掷出 0，跳过本轮")
            g.turn = 1 - pl
            continue
        if pl == human:
            moves = g.legal_moves(pl, roll)
            if not moves:
                print("无棋可走，换手")
                g.turn = 1 - pl
                continue
            for k, m in enumerate(moves):
                print(f"  {k}: {describe_move(g, pl, m)}")
            m = None
            while m is None:
                s = input("选走法编号 (q 退出): ").strip()
                if s.lower() == "q":
                    return 0
                if s.isdigit() and int(s) < len(moves):
                    m = moves[int(s)]
                else:
                    print("输入无效")
        else:
            m = g.ai_choose(pl, roll)
            if m is None:
                print(f"{NAMES[pl]}(AI) 无棋可走")
                g.turn = 1 - pl
                continue
            print(f"{NAMES[pl]}(AI): {describe_move(g, pl, m)}")
        extra, knocked = g.apply_move(pl, m, roll)
        if knocked:
            print("吃子！对方棋子被打回手中")
        if extra:
            print("落在玫瑰花格，再掷一次！")
        else:
            g.turn = 1 - pl
    print("\n" + g.render())
    print(f"胜者: {NAMES[g.winner]}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="乌尔王族棋 (Royal Game of Ur)")
    ap.add_argument("--auto", action="store_true", help="AI 对 AI 自动演示")
    ap.add_argument("--games", type=int, default=10, help="自动演示局数")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    ap.add_argument("--verbose", action="store_true", help="打印每步")
    args = ap.parse_args(argv)
    if args.auto:
        play_auto(args.games, args.seed, args.verbose)
        return 0
    return play_interactive()


if __name__ == "__main__":
    sys.exit(main())
