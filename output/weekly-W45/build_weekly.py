# -*- coding: utf-8 -*-
"""把 content.py 渲染为两份一致的「上市公司年报体例」成品：

   1) <stem>.tex   —— 单栏 corporate report + xeCJK，可用 XeLaTeX / 在线 LaTeX 平台编译
   2) <stem>.html  —— A4 单栏年报版式，供 Chrome headless 打印 PDF

版式要点（替换旧版双栏内刊式排版）：
   封面（证券代码 / 重要提示 / 指标速览）→ 目录 → 释义 → 管理层摘要 →
   编号章节（深色章节头 + 全宽表格 + 图表 + 口径说明框）→ 备查文件 → 免责声明；
   @page margin box 负责页眉、页脚与「第 X 页 / 共 Y 页」页码。

内容只写一份（content.py），数字只来自一份（model.py），两份输出永远一致。
用法：
   python build_weekly.py                         # 默认当前目录的 content.py / weekly.*
   python build_weekly.py --stem W-2026-45 --out /path/to/out
   python build_weekly.py --content /path/to/my_content.py --template /path/to/ANNUAL-Template.tex
"""
import argparse
import html as _html
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ---------------------------------------------------------------------------
# 行内标记与转义
# ---------------------------------------------------------------------------
# [[粗体]] ((斜体)) _{下标} ^{上标}
# 上下标用带花括号的形式，避免误伤 make_figs.py 这类含下划线的文件名。
MARK = re.compile(r"(\[\[.*?\]\]|\(\(.*?\)\)|_\{[^}]*\}|\^\{[^}]*\})")


def esc_tex(s):
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("_", r"\_"), ("#", r"\#"), ("$", r"\$"), ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def esc_html(s):
    return _html.escape(s, quote=False)


def inline(text, target):
    out = []
    for part in MARK.split(text):
        if not part:
            continue
        if part.startswith("[[") and part.endswith("]]"):
            inner = part[2:-2]
            out.append(r"\textbf{" + esc_tex(inner) + "}" if target == "tex"
                       else "<strong>" + esc_html(inner) + "</strong>")
        elif part.startswith("((") and part.endswith("))"):
            inner = part[2:-2]
            out.append(r"\textit{" + esc_tex(inner) + "}" if target == "tex"
                       else "<em>" + esc_html(inner) + "</em>")
        elif part.startswith("_{") and part.endswith("}"):
            inner = part[2:-1]
            out.append(r"\textsubscript{" + esc_tex(inner) + "}" if target == "tex"
                       else "<sub>" + esc_html(inner) + "</sub>")
        elif part.startswith("^{") and part.endswith("}"):
            inner = part[2:-1]
            out.append(r"\textsuperscript{" + esc_tex(inner) + "}" if target == "tex"
                       else "<sup>" + esc_html(inner) + "</sup>")
        else:
            out.append(esc_tex(part) if target == "tex" else esc_html(part))
    return "".join(out)


def load_content(path):
    spec = importlib.util.spec_from_file_location("weekly_content", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# LaTeX 渲染（单栏 corporate report）
# ---------------------------------------------------------------------------
def preamble(template):
    src = open(template, encoding="utf-8").read()
    pre = src.split(r"\begin{document}")[0]
    # 字体回退：在线平台优先 Noto CJK，本机（Windows）用 SimSun / Microsoft YaHei
    fallback = {
        r"\setCJKmainfont": (r"\IfFontExistsTF{Noto Serif CJK SC}"
                             r"{\setCJKmainfont{Noto Serif CJK SC}}{\setCJKmainfont{SimSun}}"),
        r"\setCJKsansfont": (r"\IfFontExistsTF{Noto Sans CJK SC}"
                             r"{\setCJKsansfont{Noto Sans CJK SC}}"
                             r"{\setCJKsansfont{Microsoft YaHei}}"),
        r"\setCJKmonofont": (r"\IfFontExistsTF{Noto Sans Mono CJK SC}"
                             r"{\setCJKmonofont{Noto Sans Mono CJK SC}}"
                             r"{\setCJKmonofont{SimHei}}"),
    }
    lines = []
    for ln in pre.splitlines():
        hit = next((v for k, v in fallback.items() if ln.strip().startswith(k)), None)
        lines.append(hit if hit else ln)
    return "\n".join(lines)


def tex_cover(C):
    co = C.COMPANY
    kpis = "\n".join(
        r"\begin{minipage}[t]{0.23\textwidth}\centering "
        + r"{\footnotesize " + esc_tex(lbl) + r"}\par "
        + r"{\Large\bfseries\textcolor{navy}{" + esc_tex(val) + r"}}\par "
        + r"{\footnotesize\textcolor{reportred}{" + esc_tex(chg) + r"}}"
        + r"\end{minipage}\hfill"
        for lbl, val, chg in C.HIGHLIGHTS)
    return "\n".join([
        r"\begin{titlepage}",
        r"\centering",
        r"\includegraphics[width=0.42\textwidth]{LOGO1.png}\par\vspace{3mm}",
        r"{\Large\bfseries\textcolor{navy}{" + esc_tex(co["name"]) + r"}}\par",
        r"{\small " + esc_tex(co["en"]) + r"}\par",
        r"\vspace{1mm}\hrule height 1.2pt\vspace{8mm}",
        r"{\Huge\bfseries\textcolor{navy}{" + esc_tex(C.TITLE) + r"}}\par",
        r"\vspace{3mm}{\large\textcolor{reportred}{" + esc_tex(co["week"]) + r"}}\par",
        r"\vspace{6mm}{\small " + esc_tex(C.REPORT_KIND) + r"}\par",
        r"\vspace{8mm}{\normalsize " + esc_tex(C.SUBTITLE) + r"}\par",
        r"\vspace{8mm}{\normalsize 报告期：" + esc_tex(co["period"]) + r"}\par",
        r"\vspace{10mm}",
        kpis,
        r"\vspace{10mm}",
        r"\begin{minipage}{0.88\textwidth}\small ",
        r"\textcolor{reportred}{\bfseries 重要提示}\quad " + inline(C.NOTICE, "tex"),
        r"\end{minipage}\par\vfill",
        r"\begin{minipage}{0.88\textwidth}\footnotesize\raggedright",
        r"编制单位：" + esc_tex(co["dept"]) + r"\quad 编制人：" + esc_tex(co["prepared_by"]) + r"\\",
        r"办公地址：" + esc_tex(co["address"]) + r"\quad 披露日期：" + esc_tex(co["disclose"]) + r"\\",
        r"证券代码：" + esc_tex(co["code"]) + r"\quad 公司简称：" + esc_tex(co["short"])
        + r"\quad 版本：" + esc_tex(co["version"]),
        r"\end{minipage}",
        r"\end{titlepage}",
        r"\newpage",
    ])


def tex_blocks(blocks):
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "p":
            out.append(inline(b[1], "tex") + "\n")
        elif kind == "list":
            out.append(r"\begin{enumerate}")
            for it in b[1]:
                out.append(r"\item " + inline(it, "tex"))
            out.append(r"\end{enumerate}" + "\n")
        elif kind == "sub":
            out.append(r"\subsection{" + inline(b[1], "tex") + "}")
            out.append(tex_blocks(b[2]))
        elif kind == "eq":
            d = b[1]
            out.append(r"\begin{equation}" "\n" + d["tex"] + "\n"
                       + r"\label{" + d["label"] + "}" "\n" + r"\end{equation}" "\n")
        elif kind == "fig":
            d = b[1]
            out.append(r"\begin{figure}[ht]" "\n" r"\centering" "\n"
                       + r"\includegraphics[width=" + d["width"] + r"\textwidth]{./" + d["file"] + "}" "\n"
                       + r"\caption{" + inline(d["caption"], "tex") + "}" "\n"
                       + r"\label{fig:" + d["n"] + "}" "\n" + r"\end{figure}" "\n")
        elif kind == "table":
            d = b[1]
            ncol = len(d["headers"])
            widths = d.get("tex_widths")
            if widths:
                colspec = " ".join(f"m{{{w}\\textwidth}}" for w in widths)
            else:
                w = 0.94 / ncol
                colspec = " ".join(f"m{{{w:.3f}\\textwidth}}" for _ in range(ncol))
            out.append(r"\begin{table}[ht]" "\n" r"\centering" "\n" r"\small" "\n"
                       + r"\caption*{表 " + d["n"] + r"　" + inline(d["title"], "tex") + "}" "\n"
                       + r"\begin{tabular}{ " + colspec + " }" "\n"
                       + r"\hline\hline" "\n"
                       + " & ".join(r"\textbf{" + inline(h, "tex") + "}" for h in d["headers"]) + r" \\" "\n"
                       + r"\hline" "\n")
            for row in d["rows"]:
                out.append(" & ".join(inline(c, "tex") for c in row) + r" \\" "\n")
            out.append(r"\hline\hline" "\n" r"\end{tabular}" "\n"
                       + r"\par\vspace{1mm}\footnotesize " + inline(d["caption"], "tex") + "\n"
                       + r"\end{table}" "\n" + r"\normalsize" "\n")
    return "\n".join(out)


def build_tex(C, template, out_dir, stem):
    parts = [preamble(template), r"\begin{document}", "", tex_cover(C),
             r"\tableofcontents", r"\newpage", ""]
    for sec in C.SECTIONS:
        parts.append(r"\section{" + inline(sec["title"], "tex") + "}")
        parts.append(tex_blocks(sec["blocks"]))
    parts.append(r"\section*{备查文件目录与附录}")
    parts.append(r"\addcontentsline{toc}{section}{备查文件目录与附录}")
    for head, body in C.APPENDIX:
        parts.append(r"\noindent\textbf{" + inline(head, "tex") + r"}\par" + "\n"
                     + inline(body, "tex") + r"\par\vspace{2mm}" + "\n")
    parts.append(r"\noindent\textbf{备查文件}\par")
    parts.append(r"\begin{enumerate}")
    for r in C.DOCUMENTS:
        parts.append(r"\item " + inline(r, "tex"))
    parts.append(r"\end{enumerate}" "\n")
    parts.append(r"\noindent\textit{" + inline(C.DISCLAIMER, "tex") + "}" + "\n")
    parts.append(r"\end{document}")
    txt = "\n".join(parts) + "\n"
    p = os.path.join(out_dir, stem + ".tex")
    open(p, "w", encoding="utf-8").write(txt)
    return p


# ---------------------------------------------------------------------------
# HTML 渲染：A4 单栏 · 上市公司年报版式
# ---------------------------------------------------------------------------
CSS = r"""
@page {
  size: A4;
  margin: 20mm 18mm 18mm 18mm;
  @top-left    { content: "__HEAD_LEFT__";
                 font-family:"SimHei","Microsoft YaHei",sans-serif; font-size:7.4pt; color:#12345a; }
  @top-right   { content: "__HEAD_RIGHT__";
                 font-family:"SimHei","Microsoft YaHei",sans-serif; font-size:7.4pt; color:#7a8798; }
  @bottom-left { content: "示意性测算，未经审计 · 文体性戏仿";
                 font-family:"SimSun",serif; font-size:7.2pt; color:#8b98a8; }
  @bottom-right{ content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
                 font-family:"SimHei","Microsoft YaHei",sans-serif; font-size:7.4pt; color:#12345a; }
}
@page :first {
  margin: 0;
  @top-left { content: none; } @top-right { content: none; }
  @bottom-left { content: none; } @bottom-right { content: none; }
}
* { box-sizing: border-box; }
body { margin:0; padding:0; color:#1c2430; font-size:10pt; line-height:1.75;
       font-family:"SimSun","Songti SC","Noto Serif CJK SC",serif; }
h1,h2,h3,.sans,.cover { font-family:"SimHei","Microsoft YaHei","Noto Sans CJK SC",sans-serif; }
p { margin:0 0 2.3mm; text-align:justify; orphans:2; widows:2; }
strong { font-weight:bold; color:#12345a; }
em { font-style:italic; }

/* ---------------- 封面 ---------------- */
.cover { page-break-after:always; height:297mm; width:210mm; position:relative;
         padding:16mm 20mm 12mm; overflow:hidden;
         display:flex; flex-direction:column; }
.cover-band { height:5mm; background:linear-gradient(90deg,#12345a 0%,#12345a 72%,#b02424 72%); }
.cover-head { display:flex; justify-content:space-between; align-items:flex-start;
              margin-top:9mm; padding-bottom:5mm; border-bottom:1.1pt solid #12345a; }
.cover-head img { height:15mm; width:auto; }
.cover-code { text-align:right; font-size:9pt; line-height:1.9; color:#12345a; }
.cover-code b { color:#b02424; }
.cover-main { text-align:center; margin-top:15mm; }
.cover-company { font-size:21pt; font-weight:bold; color:#12345a; letter-spacing:2.5mm; }
.cover-en { font-size:8.6pt; letter-spacing:1.2mm; color:#7a8798; margin-top:2mm; }
.cover-rule { width:34mm; height:1.4mm; background:#b02424; margin:7mm auto; }
.cover-title { font-size:27pt; font-weight:bold; color:#12345a; margin:0; line-height:1.35; }
.cover-week { font-size:11pt; color:#b02424; margin-top:3mm; }
.cover-kind { font-size:9pt; color:#7a8798; margin-top:4mm; }
.cover-subtitle { max-width:148mm; margin:8mm auto 0; padding:3mm 6mm; font-size:9.2pt;
                  line-height:1.75; color:#33445c; border-top:0.5pt solid #c9d6e5;
                  border-bottom:0.5pt solid #c9d6e5; text-align:center; }
.cover-period { margin-top:5mm; font-size:10pt; color:#12345a; }
.kpi-strip { display:flex; gap:3mm; margin-top:8mm; }
.kpi-card { flex:1; border:0.5pt solid #c9d6e5; border-top:2pt solid #12345a;
            background:#f7f9fc; padding:3.5mm 1.5mm; text-align:center; }
.kpi-card .l { font-size:8pt; color:#66788c; }
.kpi-card .v { font-size:15pt; font-weight:bold; color:#12345a; line-height:1.5; }
.kpi-card .c { font-size:8pt; color:#b02424; }
.notice { margin-top:6mm; border:0.6pt solid #b02424; border-left:2.6pt solid #b02424;
          background:#fdf7f7; padding:2.8mm 4mm; font-size:8.2pt; line-height:1.6; }
.notice .t { color:#b02424; font-weight:bold; margin-right:3mm; }
.cover-foot { margin-top:auto;
              display:flex; justify-content:space-between; align-items:flex-end;
              border-top:1.1pt solid #12345a; padding-top:3mm;
              font-size:8.4pt; line-height:1.75; color:#33445c; }
.cover-foot img { height:20mm; width:auto; }

/* ---------------- 目录 / 释义 / 摘要（前置页） ---------------- */
.front { padding-top:0; }
.fm-title { font-size:16pt; font-weight:bold; color:#12345a; margin:0 0 3mm;
            padding-bottom:2mm; border-bottom:1.4pt solid #12345a; }
.fm-sub { font-size:8pt; color:#8b98a8; letter-spacing:0.5mm; margin-bottom:4mm; }
.toc-row { display:flex; align-items:baseline; font-size:9.6pt; margin-bottom:1.8mm; }
.toc-row .n { color:#b02424; font-weight:bold; flex:0 0 21mm; white-space:nowrap; }
.toc-row .t { color:#1c2430; white-space:nowrap; flex:0 0 auto; }
.toc-row .d { flex:1; border-bottom:1px dotted #9aa8b8; margin:0 2mm; position:relative; top:-1mm; }
.toc-row .e { font-size:8pt; color:#8b98a8; white-space:nowrap; }
.glossary { width:100%; border-collapse:collapse; font-size:8.6pt; margin:1.5mm 0 3mm; }
.glossary th { background:#12345a; color:#fff; text-align:left; padding:1.2mm 2.5mm; font-size:8.8pt; }
.glossary td { border:0.4pt solid #d6dfe9; padding:0.9mm 2.5mm; vertical-align:top; }
.glossary tr:nth-child(even) td { background:#f4f7fb; }
.glossary td:first-child { font-weight:bold; color:#12345a; width:30%; }
.exec { border:0.6pt solid #12345a; border-left:2.8pt solid #12345a;
        background:#f7f9fc; padding:2.5mm 4mm; margin:2.5mm 0 2mm; font-size:9pt;
        line-height:1.7; break-inside:avoid; page-break-inside:avoid; }
.exec .h { font-size:10.5pt; font-weight:bold; color:#12345a; margin-bottom:1.5mm; }
.exec .lbl { color:#b02424; font-weight:bold; }
.exec .attest { font-size:8pt; color:#55677d; line-height:1.6;
                border-top:0.4pt solid #c9d6e5; padding-top:2mm; margin-top:2mm; }

/* ---------------- 编号章节 ---------------- */
.chapter-head { display:flex; align-items:center; gap:5mm; margin:7mm 0 4mm;
                padding-bottom:2mm; border-bottom:1.6pt solid #12345a;
                break-after:avoid; page-break-after:avoid; }
.chapter-head .num { font-family:Arial,sans-serif; font-size:26pt; font-weight:bold;
                     color:#c9d6e5; line-height:1; }
.chapter-head h2 { font-size:14pt; font-weight:bold; color:#12345a; margin:0; }
.chapter-head .en { font-size:7.6pt; color:#8b98a8; letter-spacing:0.5mm; margin-top:1mm; }
h3 { font-size:10.8pt; color:#12345a; margin:5mm 0 2mm; padding-left:2.5mm;
     border-left:2.4pt solid #b02424; break-after:avoid; page-break-after:avoid; }
ol { margin:1.5mm 0 3mm; padding-left:7mm; }
li { margin-bottom:2mm; }
table { width:100%; border-collapse:collapse; font-size:8.9pt; margin:2mm 0 0.5mm;
        break-inside:avoid; page-break-inside:avoid; }
table caption { caption-side:top; text-align:left; font-size:9.2pt; font-weight:bold;
                color:#12345a; margin-bottom:1.5mm; }
thead th { background:#12345a; color:#fff; font-weight:bold; text-align:left;
           padding:1.5mm 2.5mm; border:0.4pt solid #12345a; }
tbody td { padding:1.3mm 2.5mm; border:0.4pt solid #d6dfe9; vertical-align:middle; }
tbody tr:nth-child(even) td { background:#f4f7fb; }
tbody tr:last-child td { border-bottom:1.2pt solid #12345a; }
.tbl-note { font-size:8pt; color:#66788c; margin:0.5mm 0 2.5mm; }
figure { margin:3mm 0; text-align:center; break-inside:avoid; page-break-inside:avoid; }
figure img { max-width:100%; height:auto; display:block; margin:0 auto;
             border:0.4pt solid #e1e7ef; padding:1.2mm; background:#fff; }
figcaption { font-size:8.4pt; color:#44546a; line-height:1.7; margin-top:2mm; text-align:left; }
.formula { border-left:2.8pt solid #12345a; background:#f4f7fb; padding:3mm 4mm;
           margin:3mm 0 4mm; break-inside:avoid; page-break-inside:avoid; }
.formula .lbl { font-size:8pt; font-weight:bold; color:#12345a; letter-spacing:0.5mm; }
.formula .body { font-family:"Times New Roman",serif; font-size:11.5pt; margin-top:1.5mm; }
.appendix-item { margin:3mm 0; font-size:9.2pt; line-height:1.8; }
.appendix-item b { color:#12345a; }
.docs { font-size:9pt; color:#33445c; }
.docs li { margin-bottom:1.5mm; }
.disclaimer { font-size:8.4pt; color:#55677d; margin-top:6mm; padding-top:3mm;
              border-top:0.8pt solid #12345a; line-height:1.8; }
"""


def html_blocks(blocks):
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "p":
            out.append("<p>" + inline(b[1], "html") + "</p>")
        elif kind == "list":
            out.append("<ol>" + "".join("<li>" + inline(i, "html") + "</li>" for i in b[1]) + "</ol>")
        elif kind == "sub":
            out.append("<h3>" + inline(b[1], "html") + "</h3>")
            out.append(html_blocks(b[2]))
        elif kind == "eq":
            d = b[1]
            out.append('<div class="formula"><div class="lbl">计算口径 (' + d["n"] + ')</div>'
                       + '<div class="body">' + d["html"] + '</div></div>')
        elif kind == "fig":
            d = b[1]
            w = int(float(d["width"]) * 100)
            out.append('<figure><img src="' + d["file"] + '" alt="fig' + d["n"] + '"'
                       + ' style="width:' + str(w) + '%">'
                       + '<figcaption>图 ' + d["n"] + '. ' + inline(d["caption"], "html")
                       + '</figcaption></figure>')
        elif kind == "table":
            d = b[1]
            colgroup = ""
            if d.get("widths"):
                colgroup = ("<colgroup>"
                            + "".join('<col style="width:' + w + '">' for w in d["widths"])
                            + "</colgroup>")
            s = ['<table>' + colgroup + '<caption>表 ' + d["n"] + '　'
                 + inline(d["title"], "html") + '</caption>', '<thead><tr>']
            s += ["<th>" + inline(h, "html") + "</th>" for h in d["headers"]]
            s.append("</tr></thead><tbody>")
            for row in d["rows"]:
                s.append("<tr>" + "".join("<td>" + inline(c, "html") + "</td>" for c in row) + "</tr>")
            s.append("</tbody></table>")
            s.append('<div class="tbl-note">注：' + inline(d["caption"], "html") + '</div>')
            out.append("".join(s))
    return "\n".join(out)


def build_html(C, out_dir, stem):
    co = C.COMPANY
    css = (CSS.replace("__HEAD_LEFT__", co["name"] + " · " + C.TITLE)
              .replace("__HEAD_RIGHT__", "证券代码：" + co["code"]))
    head = [
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
        '<title>' + esc_html(co["short"] + " " + C.TITLE) + '</title>',
        '<style>' + css + '</style></head><body>',
    ]

    # ---- 封面 ----
    cards = "".join(
        '<div class="kpi-card"><div class="l">' + esc_html(lbl) + '</div>'
        + '<div class="v">' + esc_html(val) + '</div>'
        + '<div class="c">' + esc_html(chg) + '</div></div>'
        for lbl, val, chg in C.HIGHLIGHTS)
    head += [
        '<section class="cover">',
        '<div class="cover-band"></div>',
        '<div class="cover-head"><img src="LOGO1.png" alt="公司标识">'
        '<div class="cover-code">证券代码：<b>' + esc_html(co["code"]) + '</b><br>'
        '公司简称：<b>' + esc_html(co["short"]) + '</b><br>'
        '披露日期：' + esc_html(co["disclose"]) + '</div></div>',
        '<div class="cover-main">',
        '<div class="cover-company">' + esc_html(co["name"]) + '</div>',
        '<div class="cover-en">' + esc_html(co["en"]) + '</div>',
        '<div class="cover-rule"></div>',
        '<h1 class="cover-title">' + esc_html(C.TITLE) + '</h1>',
        '<div class="cover-week">' + esc_html(co["week"]) + '</div>',
        '<div class="cover-kind">' + esc_html(C.REPORT_KIND) + '</div>',
        '<div class="cover-subtitle">' + esc_html(C.SUBTITLE) + '</div>',
        '<div class="cover-period">报告期：' + esc_html(co["period"]) + '</div>',
        '</div>',
        '<div class="kpi-strip">' + cards + '</div>',
        '<div class="notice"><span class="t">重要提示</span>' + inline(C.NOTICE, "html") + '</div>',
        '<div class="cover-foot"><div>'
        '编制单位：' + esc_html(co["dept"]) + '<br>'
        '编制人：' + esc_html(co["prepared_by"]) + '　联络：' + esc_html(co["contact"]) + '<br>'
        '办公地址：' + esc_html(co["address"]) + '<br>'
        '版本：' + esc_html(co["version"]) + '　密级：' + esc_html(co["class"]) + '<br>'
        '审批链：' + esc_html(co["chain"]) + '　资助：' + esc_html(co["budget"])
        + '</div><img src="LOGO2.png" alt="信息披露专用章"></div>',
        '</section>',
    ]

    # ---- 目录 / 释义 / 管理层摘要 ----
    toc = []
    toc.append('<div class="toc-row"><span class="n">重要提示</span><span class="t">重要提示、目录和释义</span>'
               '<span class="d"></span><span class="e">封面</span></div>')
    toc.append('<div class="toc-row"><span class="n">摘要</span><span class="t">管理层摘要</span>'
               '<span class="d"></span><span class="e">前置页</span></div>')
    for s in C.SECTIONS:
        toc.append('<div class="toc-row"><span class="n">第 ' + s["num"] + ' 节</span>'
                   '<span class="t">' + inline(s["title"], "html") + '</span>'
                   '<span class="d"></span><span class="e">' + esc_html(s["en"]) + '</span></div>')
    toc.append('<div class="toc-row"><span class="n">备查</span><span class="t">备查文件目录与附录</span>'
               '<span class="d"></span><span class="e">APPENDIX</span></div>')

    gloss = "".join('<tr><td>' + esc_html(t) + '</td><td>' + esc_html(d) + '</td></tr>'
                    for t, d in C.GLOSSARY)
    exec_html = inline(C.EXEC_SUMMARY, "html")
    for lbl in ("结论：", "产出：", "风险：", "下周："):
        exec_html = exec_html.replace("<strong>" + lbl + "</strong>",
                                      '<span class="lbl">' + lbl + '</span>')
    head += [
        '<section class="front">',
        '<div class="fm-title">目录</div><div class="fm-sub">CONTENTS</div>',
        "".join(toc),
        '<div class="fm-title" style="margin-top:3mm">释义</div>',
        '<div class="fm-sub">DEFINITIONS　本报告中，除非文义另有所指，下列词语具有如下含义</div>',
        '<table class="glossary"><thead><tr><th>词语</th><th>含义</th></tr></thead><tbody>'
        + gloss + '</tbody></table>',
        '<div class="exec"><div class="h">管理层摘要</div>' + exec_html
        + '<div class="attest">' + inline(C.ATTESTATION, "html") + '</div></div>',
        '</section>',
    ]

    # ---- 编号章节 ----
    for idx, sec in enumerate(C.SECTIONS):
        # 前置页结束后，第一章另起一页：年报体例的章节起页
        start = ' style="page-break-before:always"' if idx == 0 else ''
        head.append('<section class="chapter"' + start + '><div class="chapter-head">'
                    '<div class="num">' + sec["num"] + '</div><div>'
                    '<h2>第 ' + sec["num"] + ' 节　' + inline(sec["title"], "html") + '</h2>'
                    '<div class="en">' + esc_html(sec["en"]) + '</div></div></div>'
                    + html_blocks(sec["blocks"]) + '</section>')

    # ---- 备查文件与附录 ----
    head.append('<section class="chapter"><div class="chapter-head">'
                '<div class="num">07</div><div><h2>第 7 节　备查文件目录与附录</h2>'
                '<div class="en">SECTION 7 · APPENDIX &amp; DOCUMENTS</div></div></div>')
    for h, body in C.APPENDIX:
        head.append('<div class="appendix-item"><b>' + inline(h, "html") + '</b><br>'
                    + inline(body, "html") + '</div>')
    head.append('<h3>备查文件目录</h3><ol class="docs">')
    for r in C.DOCUMENTS:
        head.append('<li>' + inline(r, "html") + '</li>')
    head.append('</ol>')
    head.append('<div class="disclaimer">' + inline(C.DISCLAIMER, "html") + '</div>')
    head.append('</section></body></html>')

    p = os.path.join(out_dir, stem + ".html")
    open(p, "w", encoding="utf-8").write("\n".join(head))
    return p


def main():
    ap = argparse.ArgumentParser(description="一份摸鱼周报内容源 → 年报体例 .tex + A4 单栏 HTML")
    ap.add_argument("--content", default=os.path.join(HERE, "content.py"),
                    help="内容源路径（默认同目录 content.py）")
    ap.add_argument("--template", default=os.path.join(HERE, "ANNUAL-Template.tex"),
                    help="LaTeX 模板路径（只取导言区）")
    ap.add_argument("--out", default=HERE, help="输出目录")
    ap.add_argument("--stem", default="weekly", help="输出文件名主干，默认 weekly")
    a = ap.parse_args()

    content_path = os.path.abspath(a.content)
    out_dir = os.path.abspath(a.out)
    os.makedirs(out_dir, exist_ok=True)
    sys.path.insert(0, os.path.dirname(content_path))
    C = load_content(content_path)

    t = build_tex(C, os.path.abspath(a.template), out_dir, a.stem)
    h = build_html(C, out_dir, a.stem)
    print("TEX :", t, os.path.getsize(t), "bytes")
    print("HTML:", h, os.path.getsize(h), "bytes")
    print("chapters:", len(C.SECTIONS), "| company:", C.COMPANY["name"])


if __name__ == "__main__":
    main()
