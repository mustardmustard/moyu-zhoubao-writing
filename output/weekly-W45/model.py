# -*- coding: utf-8 -*-
"""
示意性测算模型：「摸鱼周报自指悖论」的全部数字来源。

⚠️ 本报表所有数值均由本模型测算产生，属示意性推演，未经审计，非真实经营数据。
参数为戏仿设定的假设值，不是经验估计，也不代表任何真实个人或企业的工作表现。

仿写自早期内部报告的 model.py：唯一数字真源 → content.py 引用它填正文/表格，
make_figs.py 引用它画真图，三者永远自洽。改这里的参数，全篇一起变。
"""
import math
import numpy as np

# ---------------------------------------------------------------------------
# 一周的工时预算与注意力分布
# ---------------------------------------------------------------------------
HOURS = 40.0            # 一周名义工时（h）
DAYS = ["周一", "周二", "周三", "周四", "周五"]
CATS = ["会议", "交付", "接水/走动", "刷手机", "写摸鱼周报"]
COLORS = ["#12345A", "#2b6cb0", "#c05621", "#8a8a8a", "#b02424"]

# 基准注意力占比 p_i（示意值，合计 1）
P_BASE = np.array([0.36, 0.30, 0.12, 0.14, 0.08])
# 逐日轻微扰动（写死，保证可复现 / 可 diff）
DAY_WOBBLE = np.array([
    [+0.02, -0.01, +0.00, -0.01, +0.00],
    [-0.04, +0.03, +0.01, +0.01, -0.01],
    [+0.06, -0.05, +0.00, +0.02, -0.03],
    [-0.01, +0.01, -0.02, +0.02, +0.00],
    [+0.08, -0.09, +0.01, +0.04, -0.04],
])

# ---------------------------------------------------------------------------
# 指标模型
# ---------------------------------------------------------------------------
E0 = 0.62               # 无会议、无熵增时的名义有效产出率
LAMBDA = 0.062          # 会议时长对产出的边际侵蚀（每小时）
KAPPA = 0.115           # 摸鱼熵对产出的折减系数
MEETING_H = 7.5         # 本周会议总时长（h，示意）
MEETING_PREV = 6.7      # 上周会议总时长（h，示意）
WRITING_H = 1.5         # 写这份摸鱼周报所耗工时（h，示意）
THETA = 1.0             # 承诺决策噪声温度
U_BASE = -0.35          # 传统摸鱼周报下"兑现"的净效用
OMEGA_REMIND = 0.30     # 只"设个提醒"带来的效用增益（几乎没有牙齿）
OMEGA_PLEDGE = 2.10     # 质押协议带来的效用增益（押金 + 社会可见性）
PLEDGE_YUAN = 5.0       # 每条下周计划的质押金额（元）


def hours_matrix():
    """逐日 × 类别工时矩阵（h）。逐行归一到 8 h，列和即 KPI 里的工时去向。"""
    raw = np.clip(P_BASE[None, :] + DAY_WOBBLE, 0.01, None)
    raw = raw / raw.sum(axis=1, keepdims=True)
    return raw * (HOURS / len(DAYS))


def entropy(p):
    """摸鱼熵 H = -Σ p_i ln p_i。注意力越均匀，越'忙且空转'。"""
    p = np.asarray(p, dtype=float)
    p = p / p.sum()
    return float(-(p * np.log(p)).sum())


def H_week():
    """按一周合计工时分布算出的摸鱼熵。"""
    m = hours_matrix()
    return entropy(m.sum(axis=0) / m.sum())


def H_max():
    """5 类活动完全均分时的熵上界 ln(k)。"""
    return math.log(len(CATS))


def E(m):
    """有效产出率：会议侵蚀 + 摸鱼熵折减。E(m) = E0·exp(-λm) - κH。"""
    return E0 * math.exp(-LAMBDA * m) - KAPPA * H_week()


def E_prev():
    """上周有效产出率（用上周会议时长代入同一模型）。"""
    return E0 * math.exp(-LAMBDA * MEETING_PREV) - KAPPA * (H_week() - 0.18)


def E_selfref():
    """摸鱼周报自指悖论：把'写摸鱼周报'本身计为交付物后，账面产出率的虚高值。"""
    return E(MEETING_H) + WRITING_H / HOURS


def t_for_progress(q, a=0.55):
    """进度感知 P(t)=1-exp(-a t) 达到 q 所需时长（h）。"""
    return -math.log(1.0 - q) / a


def last_leg_share(q_lo=0.90, q_hi=0.99):
    """'最后一点进度'占用的时间比例：(t(q_hi)-t(q_lo))/t(q_hi)。"""
    return (t_for_progress(q_hi) - t_for_progress(q_lo)) / t_for_progress(q_hi)


def R(u):
    """承诺兑现率（logistic 决策）：R(u)=1/(1+exp(-u/θ))。"""
    return 1.0 / (1.0 + math.exp(-u / THETA))


def R0():
    """传统摸鱼周报：承诺零成本。"""
    return R(U_BASE)


def R_remind():
    """温吞方案：设个提醒。"""
    return R(U_BASE + OMEGA_REMIND)


def R_pledge():
    """质押协议：押金 + 罚没 + 全组可见。"""
    return R(U_BASE + OMEGA_PLEDGE)


def meeting_growth():
    """会议密度环比。"""
    return MEETING_H / MEETING_PREV - 1.0


def kpi():
    """KPI 仪表盘：所有显示值集中在这里算，正文与表格引用同一份。"""
    m = hours_matrix()
    return {
        "meeting_h": MEETING_H,
        "meeting_growth": meeting_growth(),
        "delivered_h": float(m[:, 1].sum()),
        "water_h": float(m[:, 2].sum()),
        "phone_h": float(m[:, 3].sum()),
        "writing_h": float(m[:, 4].sum()),
        "entropy": H_week(),
        "entropy_ratio": H_week() / H_max(),
        "E": E(MEETING_H),
        "E_prev": E_prev(),
        "E_selfref": E_selfref(),
        "last_leg": last_leg_share(),
        "R0": R0(),
        "R_remind": R_remind(),
        "R_pledge": R_pledge(),
        "pledge_yuan": PLEDGE_YUAN,
    }


if __name__ == "__main__":
    k = kpi()
    print("== 示意性测算（未经审计、非真实经营数据）==")
    print(f"会议时长        : {k['meeting_h']:.1f} h  (环比 {k['meeting_growth']*100:+.1f}%)")
    print(f"有效产出率 E    : {k['E']*100:.1f}%  (上周 {k['E_prev']*100:.1f}%)")
    print(f"自指虚高后 E    : {k['E_selfref']*100:.1f}%  <- 写摸鱼周报自己算作交付")
    print(f"摸鱼熵 H        : {k['entropy']:.3f} / {H_max():.3f} = {k['entropy_ratio']*100:.1f}%")
    print(f"最后 10% 进度占时: {k['last_leg']*100:.1f}%")
    print(f"承诺兑现率      : 传统 {k['R0']*100:.1f}% -> 提醒 {k['R_remind']*100:.1f}% "
          f"-> 质押 {k['R_pledge']*100:.1f}%")
    print("逐日工时(h):", DAYS)
    print(hours_matrix().round(2))
