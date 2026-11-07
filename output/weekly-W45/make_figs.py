# -*- coding: utf-8 -*-
"""生成年报体例摸鱼周报的三张真实插图。所有数值均由 model.py 的示意性测算模型算出。

仿写自早期内部报告流水线：测算模型 → 真图 → 正文/表格，三者共用一份数字。
配色为公司披露文件的深蓝 / 红，替换掉旧版内刊风的紫色。
运行前确保 figure_helper.py 与 model.py 同目录（SKILL.md 步骤 3 已把它们拷进来）。
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from figure_helper import setup_cjk
import model as M

FONT = setup_cjk(9)
print("CJK font:", FONT)

INK = "#1C2430"
NAVY = "#12345A"
GREY = "#8A8A8A"
RED = "#B02424"
BLUE = "#2B6CB0"
ORANGE = "#C05621"
PAL = [NAVY, BLUE, ORANGE, GREY, RED]

K = M.kpi()

# ---------------------------------------------------------------------------
# fig1.png — 主结果图：(a) 逐日工时去向堆叠柱  (b) 有效产出率随会议时长衰减
# ---------------------------------------------------------------------------
mat = M.hours_matrix()
fig, axes = plt.subplots(2, 1, figsize=(3.45, 4.9))

ax = axes[0]
bottom = np.zeros(len(M.DAYS))
for j, (cat, col) in enumerate(zip(M.CATS, PAL)):
    vals = mat[:, j]
    ax.bar(M.DAYS, vals, bottom=bottom, width=0.62, color=col,
           edgecolor="white", linewidth=0.6, label=cat)
    bottom += vals
ax.set_ylim(0, 9.2)
ax.set_ylabel("工时 (h)", fontsize=8.5)
ax.set_title("(a) 逐日工时去向（示意性测算，未经审计）", fontsize=9, loc="left")
ax.legend(fontsize=6.8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.13),
          columnspacing=0.8, handlelength=1.1, handletextpad=0.35)
ax.tick_params(labelsize=7.5)
ax.grid(axis="x", alpha=0.0)

ax = axes[1]
ms = np.linspace(0, 14, 400)
es = [M.E(float(m)) * 100 for m in ms]
ax.plot(ms, es, color=NAVY, lw=2.0, label="有效产出率 E(m)")
ax.axhline(0, color=INK, lw=0.8, ls="--")
ax.scatter([M.MEETING_H], [K["E"] * 100], color=BLUE, zorder=5, s=26)
ax.annotate(f"本期 {M.MEETING_H:.1f} h\nE = {K['E']*100:.1f}%",
            xy=(M.MEETING_H, K["E"] * 100), xytext=(1.0, 13.0),
            fontsize=7.6, color=BLUE,
            arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9))
ax.scatter([M.MEETING_H], [K["E_selfref"] * 100], color=RED, zorder=5, s=26,
           marker="^")
ax.annotate(f"把写摸鱼周报算成交付\n账面 {K['E_selfref']*100:.1f}%",
            xy=(M.MEETING_H, K["E_selfref"] * 100),
            xytext=(8.8, 40.0),
            fontsize=7.4, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
ax.text(0.4, 51.0, "会开得越多，事动得越少", fontsize=7.8, color=GREY)
ax.set_xlim(0, 14)
ax.set_ylim(min(es) - 4, max(es) + 14)
ax.set_xlabel("本期会议时长 m (h)", fontsize=8.5)
ax.set_ylabel("有效产出率 E (%)", fontsize=8.5)
ax.set_title("(b) 会议侵蚀与摸鱼周报自指悖论", fontsize=9, loc="left")
ax.tick_params(labelsize=7.5)

fig.tight_layout(h_pad=2.6)
fig.savefig(os.path.join(HERE, "fig1.png"), dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------------------
# 图 2 —「写满推进中」恶性闭环示意
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(3.45, 3.25))
ax.set_xlim(0, 10)
ax.set_ylim(0, 9.2)
ax.axis("off")

HALF_W, HALF_H = 1.42, 0.66
nodes = [
    (5.0, 7.9, "摸鱼周报写满\n「持续推进中」", NAVY),
    (8.3, 5.7, "下期照抄上期\n进度 99%", NAVY),
    (7.1, 2.4, "承诺无成本\n无质押无核验", BLUE),
    (3.0, 2.4, "无人追问\n验收口径留白", ORANGE),
    (1.7, 5.7, "兑现率 " + f"{K['R0']*100:.1f}%" + "\n下期期初归零", RED),
]
centers = [(x, y) for x, y, _, _ in nodes]
for x, y, txt, col in nodes:
    b = FancyBboxPatch((x - HALF_W, y - HALF_H), 2 * HALF_W, 2 * HALF_H,
                       boxstyle="round,pad=0.10,rounding_size=0.18",
                       linewidth=1.1, edgecolor=col, facecolor="white", zorder=2)
    ax.add_patch(b)
    ax.text(x, y, txt, ha="center", va="center", fontsize=7.0, color=INK, zorder=3)


def edge_point(p1, p2, pad=0.14):
    """沿 p1->p2 射线求与矩形框边界的交点，再外推 pad，避免箭头被白底框盖住。"""
    ux, uy = p2[0] - p1[0], p2[1] - p1[1]
    tx = HALF_W / abs(ux) if abs(ux) > 1e-9 else float("inf")
    ty = HALF_H / abs(uy) if abs(uy) > 1e-9 else float("inf")
    t = min(tx, ty)
    n = math.hypot(ux, uy)
    return (p1[0] + ux * t + pad * ux / n,
            p1[1] + uy * t + pad * uy / n)


for i in range(5):
    a = edge_point(centers[i], centers[(i + 1) % 5])
    b = edge_point(centers[(i + 1) % 5], centers[i])
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11,
                                 lw=1.1, color=GREY, zorder=1,
                                 connectionstyle="arc3,rad=0.20"))

ax.text(5.0, 4.45, "自强化闭环", ha="center", va="center",
        fontsize=9.5, color=RED, fontweight="bold")
ax.text(5.0, 0.42, "编制摸鱼周报本身，成了本期唯一可验证的交付物",
        ha="center", fontsize=7.4, color=GREY)
fig.savefig(os.path.join(HERE, "fig2.png"), dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------------------
# 图 3 — 摸鱼周报质押协议 WDP 流程（带牙齿的那一步）
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(3.45, 4.5))
ax.set_xlim(0, 10)
ax.set_ylim(-0.4, 13.0)
ax.axis("off")


def box(x, y, w, h, txt, col, fs=7.5):
    b = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.10,rounding_size=0.14",
                       linewidth=1.1, edgecolor=col, facecolor="white", zorder=2)
    ax.add_patch(b)
    ax.text(x, y, txt, ha="center", va="center", fontsize=fs, color=INK, zorder=3)


def arrow(p1, p2, col=GREY, rad=0.0, txt=None, tx=None, ty=None):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=10,
                                 lw=1.0, color=col, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))
    if txt:
        ax.text(tx, ty, txt, fontsize=7.0, color=col, ha="center")


box(5, 12.0, 6.8, 1.18, "提交下周计划\n（须带 owner / due / 验收口径）", NAVY, 7.4)
box(5, 10.0, 6.8, 1.02, "每条自动质押 " + f"{M.PLEDGE_YUAN:.0f}" + " 元 · 生成存证编号", NAVY, 7.8)
arrow((5, 11.40), (5, 10.52))

box(5, 8.0, 6.8, 1.02, "下周五 17:00 自动复盘对账", GREY, 7.8)
arrow((5, 9.48), (5, 8.52))

box(2.4, 5.7, 4.3, 1.35, "兑现\n退还押金 + 累积\n闭环积分", BLUE, 7.5)
box(7.7, 5.7, 4.3, 1.35, "未兑现\n押金立即罚没\n（不设申诉通道）", RED, 7.5)
arrow((4.4, 7.48), (2.8, 6.4), col=BLUE, rad=0.10, txt="验收通过", tx=2.7, ty=7.05)
arrow((5.6, 7.48), (7.3, 6.4), col=RED, rad=-0.10, txt="逾期", tx=7.8, ty=7.05)

box(2.4, 3.4, 4.3, 1.35, "每月兑换 1 张\n「免写摸鱼周报券」", BLUE, 7.4)
box(7.7, 3.4, 4.3, 1.35, "强制转存\n20 年定期存单", RED, 7.4)
arrow((2.4, 5.0), (2.4, 4.1), col=BLUE)
arrow((7.7, 5.0), (7.7, 4.1), col=RED)

box(7.7, 1.3, 4.3, 1.15, "未兑现清单\n自动抄送全组页脚", RED, 7.3)
arrow((7.7, 2.7), (7.7, 1.9), col=RED)

ax.text(5, 0.35, "牙齿 = 真实损失 + 社会可见性（示意性机制设计）",
        ha="center", fontsize=7.6, color=INK)
fig.savefig(os.path.join(HERE, "fig3.png"), dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

for f in ("fig1.png", "fig2.png", "fig3.png"):
    p = os.path.join(HERE, f)
    print(f, os.path.getsize(p), "bytes")
