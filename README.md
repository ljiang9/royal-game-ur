# 乌尔王族棋 (Royal Game of Ur)

约 4500 年前美索不达米亚的赛跑棋，按 Irving Finkel 的重构规则实现。
纯 Python 标准库，命令行对战 + AI 自动演示。

## 玩法

- 棋盘 3 行 × 8 列，双方各 7 枚棋子，沿各自 14 格赛道前进。
- 掷 4 面骰（0–4 点），掷出 0 跳过本轮；棋子从手中按掷点入场。
- 5 朵玫瑰花格（✿）：落上可再掷一次；**中央玫瑰是安全格**，不可被吃、不可共占。
- 共享格落子可吃掉对方棋子（打回对方手中）。
- 必须**精确掷点**才能离盘；7 枚棋子全部离盘者胜。

## 运行

需要 Python 3.10+，无第三方依赖。

```bash
# 人机对战（你是甲，乙是 AI）
python3 -m royal_game_ur

# AI 对 AI 自动演示 10 局
python3 royal_game_ur.py --auto --games 10 --seed 7

# 打印每一步
python3 royal_game_ur.py --auto --games 1 --verbose
```

## AI 说明

贪心 AI：按「离盘 > 吃子 > 玫瑰再掷 > 推进 > 派新子」加权选走法，
同分随机打破。**AI 很弱**，只演示规则流程，不做任何前瞻搜索；
人机对战时人类稍加思考即可获胜。

## 已知局限

- 规则采用 Finkel 重构版（7 子、4 面骰），与历史原貌的对应关系学界仍有争议，
  本实现不作考古断言。
- AI 为单层贪心，无多步搜索；无网络对战、无图形界面。

## 文件

- `royal_game_ur.py` — 全部逻辑（规则引擎 + AI + 文本棋盘 + CLI）
- `__main__.py` — `python -m royal_game_ur` 入口
- `LICENSE` — MIT

## 许可证

MIT，Copyright (c) 2026 ljiang9。
