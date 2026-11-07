# moyu-weekly · 摸鱼周报（MOYU WEEKLY）

一句话的一周流水账 → 一份**一本正经胡说八道**的「上市公司年报体例」中文 A4 单栏摸鱼周报 PDF。

沿用原有的输出模式与工具链（公司标识 + 全宽表格 + matplotlib 真图 + 编号口径说明 +
XeLaTeX / Chrome headless 编译），**换掉的是品牌、词汇与版式**：
品牌统一为「摸鱼科技」，场景与措辞全部收敛到公司/职场披露口径，
版式为 A4 单栏年报：封面（证券代码 / 重要提示 / 指标速览）→
目录 → 释义 → 管理层摘要 → 编号章节 → 备查文件，带页眉页脚与「第 X 页 / 共 Y 页」。
风格仍是过分严肃的搞笑。

## 30 秒跑通示例

把 `assets/template/` 的 4 个文件和 `scripts/` 的脚本一起拷进一个输出目录，然后：

```bash
cd <输出目录>
python make_logos.py                    # 可选：重画公司字标 / 披露专用章 / 占位图
python make_figs.py                     # 由 model.py 画 3 张真图（会覆盖占位图）
python build_weekly.py --stem weekly --out .   # 同时产出 weekly.tex + weekly.html
bash compile.sh weekly.tex             # XeLaTeX 编译（需要本地 TeX）
```

没有 XeLaTeX 时，用 Chrome headless 打印等效 A4 年报 PDF（`@page` margin box 自动出
页眉页脚与页码）：

```bash
chrome --headless --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
       --virtual-time-budget=8000 --print-to-pdf="weekly.pdf" "file:///<绝对路径>/weekly.html"
```

`content.py` 是唯一正文来源，`model.py` 是唯一数字来源；改这两份再重跑，
`.tex` 与 `.html` 自动一致。行内标记：`[[粗体]]` `((斜体))` `_{下标}` `^{上标}`。

## 目录

```
moyu-weekly/
├── SKILL.md                      工作流 + 输入规范 + 数据红线 + 交付
├── references/style-guide.md     文体解剖（思考逻辑 / 年报版式 / 流派 / 黑话 / 骨架 / 翻车清单）
├── scripts/
│   ├── compile.sh                XeLaTeX 一键编译（自动找 TeX + 补宏包 + 中文字体降级）
│   ├── figure_helper.py          matplotlib 中文出图助手
│   ├── make_logos.py             公司字标 / 信息披露专用章 / 占位示意图
│   ├── model.py                  示意性测算模型：全部 KPI 的唯一来源
│   ├── make_figs.py              3 张真图（工时堆叠柱 / 机制闭环 / 质押协议流程）
│   ├── content.py                示例摸鱼周报正文（也是给 agent 改写的模板）
│   └── build_weekly.py           一份内容 → 年报体例 .tex + A4 单栏 HTML
└── assets/template/              A4 单栏年报模板 + 公司字标 + 披露专用章 + 占位图
```

## 底线

- **数据诚实**：用户有真实数据就用真的；没有则用明确标注「示意性测算、未经审计」的数字，
  绝不把测算当成真实经营数据或业绩承诺。
- **要有牙齿**：不止汇报，还要给出一个有真实代价、背后是真行为学杠杆的具体制度/协议。
- **戏仿分寸**：调侃普遍职场现象，不指名道姓攻击具体个人 / 公司。
