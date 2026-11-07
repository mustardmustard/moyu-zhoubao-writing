#!/usr/bin/env bash
#
# compile.sh <weekly.tex> [output_dir]
#
# Compile a Mouyu Weekly annual-report-style .tex to an A4 single-column PDF:
#   1. finds xelatex even if it isn't on PATH (TinyTeX / MacTeX / TeX Live)
#   2. substitutes the template's Noto CJK fonts for whatever CJK fonts the
#      machine actually has (macOS ships Songti SC / PingFang SC, not Noto),
#      so the weekly report renders instead of dying on a missing font
#   3. auto-installs any missing LaTeX packages via tlmgr, in a retry loop
#   4. runs enough passes to resolve cross-references, then drops the PDF
#      next to the source .tex
#
# The source .tex is never modified — all patching happens in a .build/ copy.
# Exit codes: 0 ok · 1 bad args · 2 no xelatex · 3 compile failed after fixes.
# (Same XeLaTeX toolchain as the original report generator; only the layout changed.)

set -uo pipefail

TEX="${1:-}"
[ -n "$TEX" ] && [ -f "$TEX" ] || { echo "usage: compile.sh <report.tex> [output_dir]"; exit 1; }
TEXDIR="$(cd "$(dirname "$TEX")" && pwd)"
TEXNAME="$(basename "$TEX")"
STEM="${TEXNAME%.tex}"
OUTDIR="${2:-$TEXDIR}"
mkdir -p "$OUTDIR"

# ---------------------------------------------------------------------------
# 1. Locate the toolchain
# ---------------------------------------------------------------------------
if ! command -v xelatex >/dev/null 2>&1; then
  for d in "$HOME/Library/TinyTeX/bin/"*/ /usr/local/texlive/*/bin/*/ /Library/TeX/texbin ~/.TinyTeX/bin/*/; do
    if [ -x "$d/xelatex" ]; then export PATH="$d:$PATH"; break; fi
  done
fi
command -v xelatex >/dev/null 2>&1 || {
  echo "✗ XeLaTeX not found. Install TinyTeX (https://yihui.org/tinytex/) or MacTeX,"
  echo "  or hand the .tex to Overleaf (set the compiler to XeLaTeX)."
  exit 2
}
TLMGR="$(command -v tlmgr || true)"

# ---------------------------------------------------------------------------
# 2. Assemble an isolated build dir (source .tex stays untouched)
# ---------------------------------------------------------------------------
BUILD="$TEXDIR/.build_$STEM"
rm -rf "$BUILD"; mkdir -p "$BUILD"
cp "$TEX" "$BUILD/$STEM.tex"
# bring along sibling assets the report may \includegraphics (logos + figures)
for ext in png jpg jpeg pdf eps bib; do
  for f in "$TEXDIR"/*."$ext"; do [ -e "$f" ] && cp "$f" "$BUILD/" 2>/dev/null; done
done

# ---------------------------------------------------------------------------
# 3. CJK font fallback — pick the first installed font from each preference list
# ---------------------------------------------------------------------------
font_available() {
  # true if the family resolves to itself (not a generic fallback)
  fc-match "$1" 2>/dev/null | grep -qiF "\"$1\""
}
pick_font() {
  for f in "$@"; do
    if font_available "$f"; then echo "$f"; return; fi
  done
  echo "$1"   # last resort: leave the original, let XeLaTeX warn
}
SERIF="$(pick_font 'Noto Serif CJK SC' 'Source Han Serif SC' 'Songti SC' 'STSong' 'SimSun' 'PingFang SC')"
SANS="$(pick_font  'Noto Sans CJK SC'  'Source Han Sans SC'  'PingFang SC' 'STHeiti' 'Heiti SC' 'SimHei')"
MONO="$(pick_font  'Noto Sans Mono CJK SC' 'Sarasa Mono SC' 'PingFang SC' 'STHeiti')"

# escape & for sed replacement safety (font names have none, but be safe)
sed -i.bak \
  -e "s/\\\\setCJKmainfont{[^}]*}/\\\\setCJKmainfont{$SERIF}/" \
  -e "s/\\\\setCJKsansfont{[^}]*}/\\\\setCJKsansfont{$SANS}/" \
  -e "s/\\\\setCJKmonofont{[^}]*}/\\\\setCJKmonofont{$MONO}/" \
  "$BUILD/$STEM.tex"
rm -f "$BUILD/$STEM.tex.bak"
echo "→ CJK fonts: main=$SERIF | sans=$SANS | mono=$MONO"

# ---------------------------------------------------------------------------
# 4. Compile with an auto-install retry loop
# ---------------------------------------------------------------------------
cd "$BUILD"
XEL=(xelatex -interaction=nonstopmode -halt-on-error "$STEM.tex")
ok=0
for attempt in $(seq 1 10); do
  if "${XEL[@]}" > compile.log 2>&1; then ok=1; break; fi
  # find the first missing .sty/.cls and try to install its package
  miss="$(grep -oE "File \`[^']+\.(sty|cls|def)' not found" compile.log | head -1 | sed -E "s/File \`([^']+)'.*/\1/")"
  if [ -z "$miss" ]; then
    miss="$(grep -oE "the language definition file [^ ]+\.ldf" compile.log | head -1 | awk '{print $NF}')"
  fi
  if [ -n "$miss" ] && [ -n "$TLMGR" ]; then
    pkg="$("$TLMGR" search --global --file "/$miss" 2>/dev/null | grep -E ':[[:space:]]*$' | head -1 | sed 's/:.*//' | tr -d ' ')"
    if [ -n "$pkg" ]; then
      echo "→ installing missing package: $pkg (provides $miss)"
      "$TLMGR" install "$pkg" >/dev/null 2>&1 && continue
    fi
  fi
  break   # nothing actionable — real error
done

if [ "$ok" -ne 1 ]; then
  echo "✗ Compile failed. Last errors:"
  grep -iE "^!|not found|Undefined|Emergency" compile.log | head -12
  echo "  (full log: $BUILD/compile.log)"
  exit 3
fi

# extra passes to settle table/figure/equation cross-references
"${XEL[@]}" > compile.log 2>&1
"${XEL[@]}" > compile.log 2>&1

# ---------------------------------------------------------------------------
# 5. Deliver
# ---------------------------------------------------------------------------
if [ -f "$STEM.pdf" ]; then
  cp "$STEM.pdf" "$OUTDIR/$STEM.pdf"
  echo "✓ PDF ready: $OUTDIR/$STEM.pdf ($(wc -c < "$STEM.pdf" | tr -d ' ') bytes)"
  # tidy: keep the build dir only if something looks off
  rm -rf "$BUILD"
  exit 0
else
  echo "✗ No PDF produced despite exit 0 — see $BUILD/compile.log"
  exit 3
fi
