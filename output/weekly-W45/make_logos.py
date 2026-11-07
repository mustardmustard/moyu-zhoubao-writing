# -*- coding: utf-8 -*-
"""生成公司披露文件用的三张图片资产（沿用 figure_helper.py 的中文出图助手）：

   LOGO1.png  公司字标（封面 / 页眉用）
   LOGO2.png  信息披露专用章（封面右下角用）
   fig1.png   占位示意图，运行 make_figs.py 后会被真图覆盖

品牌统一为「摸鱼科技」；图片用于上市公司年报封面的公司标识与信息披露专用章。
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon

from figure_helper import setup_cjk

setup_cjk(10)
NAVY = "#12345A"
RED = "#B02424"
GREY = "#7A8798"
INK = "#1C2430"


def wordmark():
    fig, ax = plt.subplots(figsize=(6.4, 1.05), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 2.1)
    ax.axis("off")
    # 企业标记：深蓝圆角方块 + 一条「摸鱼」波浪
    ax.add_patch(FancyBboxPatch((0.18, 0.30), 1.5, 1.5,
                                boxstyle="round,pad=0.02,rounding_size=0.25",
                                linewidth=0, facecolor=NAVY, zorder=1))
    xs = [0.42, 0.72, 1.02, 1.32]
    for i, x in enumerate(xs):
        ax.plot([x - 0.22, x + 0.22], [1.05 + (0.22 if i % 2 == 0 else -0.22),
                                       1.05 - (0.22 if i % 2 == 0 else -0.22)],
                color="white", lw=2.2, solid_capstyle="round", zorder=2)
    ax.text(2.05, 1.18, "摸鱼科技", fontsize=25, fontweight="bold",
            color=NAVY, va="center", ha="left")
    ax.text(2.10, 0.48, "MOYU TECHNOLOGY CO., LTD.", fontsize=8.2,
            color=GREY, va="center", ha="left", family="DejaVu Sans")
    # 右侧只放摸鱼周报产品标识；证券代码在封面右上方单独披露，避免重复小字
    ax.plot([9.9, 12.5], [1.62, 1.62], color=RED, lw=1.6)
    ax.text(12.5, 1.28, "MOYU WEEKLY", fontsize=10.5, color=NAVY,
            va="center", ha="right", family="DejaVu Sans", fontweight="bold")
    fig.savefig(os.path.join(HERE, "LOGO1.png"), dpi=300,
                bbox_inches="tight", pad_inches=0.06, facecolor="white")
    plt.close(fig)


def seal():
    fig, ax = plt.subplots(figsize=(2.6, 2.6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Circle((5, 5), 4.55, fill=False, edgecolor=RED, linewidth=7))
    ax.add_patch(Circle((5, 5), 4.05, fill=False, edgecolor=RED, linewidth=1.4))
    ax.text(5, 6.75, "摸鱼科技", fontsize=17, fontweight="bold",
            color=RED, ha="center", va="center")
    ax.text(5, 5.55, "信息披露专用章", fontsize=10.5, color=RED,
            ha="center", va="center")
    # 五角星：交替内外半径
    pts = []
    for i in range(10):
        r = 0.86 if i % 2 == 0 else 0.38
        a = math.pi / 2 + i * math.pi / 5
        pts.append((5 + r * math.cos(a), 4.15 + r * math.sin(a)))
    ax.add_patch(Polygon(pts, closed=True, facecolor=RED, edgecolor="none", alpha=0.9))
    ax.text(5, 2.55, "NO. 002520", fontsize=8, color=RED,
            ha="center", va="center", family="DejaVu Sans")
    ax.text(5, 1.85, "未经审计", fontsize=8, color=RED,
            ha="center", va="center")
    fig.savefig(os.path.join(HERE, "LOGO2.png"), dpi=300,
                bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)


def placeholder():
    fig, ax = plt.subplots(figsize=(6.2, 3.4), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.3, 0.3), 9.4, 4.9,
                                boxstyle="round,pad=0.02,rounding_size=0.12",
                                linewidth=1.0, edgecolor="#C9D6E5",
                                facecolor="#F7F9FC"))
    ax.plot([1.0, 9.0], [4.2, 4.2], color=NAVY, lw=2.0)
    ax.text(5, 3.0, "指标示意图（占位）", fontsize=15, color=NAVY,
            ha="center", va="center", fontweight="bold")
    ax.text(5, 2.1, "运行 make_figs.py 后由测算模型生成真图替换", fontsize=10,
            color=GREY, ha="center", va="center")
    ax.text(5, 1.2, "示意图 · 未经审计", fontsize=9, color=RED,
            ha="center", va="center")
    fig.savefig(os.path.join(HERE, "fig1.png"), dpi=200,
                bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    wordmark()
    seal()
    placeholder()
    for f in ("LOGO1.png", "LOGO2.png", "fig1.png"):
        print(f, os.path.getsize(os.path.join(HERE, f)), "bytes")
