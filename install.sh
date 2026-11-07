#!/usr/bin/env bash
# 把 skills/ 下的 Skill 链接到 WorkBuddy 的 skills 目录，装完即可在 WorkBuddy 里直接调用。
#
#   默认                       ~/.workbuddy/skills/         （用户级，所有工作区可用）
#   --project                  <本仓库>/.workbuddy/skills/  （仅当前工作区可用）
#   WORKBUDDY_SKILLS_DIR=<dir> 自定义 skills 目录（优先级最高）
#
# macOS / Linux 使用符号链接；Windows(Git Bash) 使用目录 junction（无需管理员权限）。
# 两者都实时指向本仓库，修改仓库里的 SKILL.md 立即生效，不用重装。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
用法: bash install.sh [选项]

  (无参数)      安装到用户级 ~/.workbuddy/skills/（推荐，所有工作区可用）
  --project     安装到本仓库 .workbuddy/skills/（仅当前工作区可用）
  --uninstall   移除本脚本创建的链接
  -h, --help    显示帮助

环境变量:
  WORKBUDDY_SKILLS_DIR=<dir>   自定义 skills 目录，优先级最高
EOF
}

MODE=install
PROJECT=0
for arg in "$@"; do
  case "$arg" in
    --project)   PROJECT=1 ;;
    --uninstall) MODE=uninstall ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "未知参数: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

if [ -n "${WORKBUDDY_SKILLS_DIR:-}" ]; then
  DEST="$WORKBUDDY_SKILLS_DIR"
elif [ "$PROJECT" -eq 1 ]; then
  DEST="$ROOT/.workbuddy/skills"
else
  DEST="$HOME/.workbuddy/skills"
fi

case "$(uname -s)" in
  MINGW*|MSYS*) WIN=1 ;;
  *)            WIN=0 ;;
esac

winpath() {
  if [ "$WIN" -eq 1 ] && command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s' "$1"
  fi
}

# Windows：用 PowerShell 创建/删除目录 junction。
# 只处理 reparse point（链接），遇到实体目录一律退出码 3，绝不覆盖或删除用户数据。
junction() {
  local mode="$1" dst="$2" src="$3"
  WB_MODE="$mode" \
  WB_DST="$(winpath "$dst")" \
  WB_SRC="$(winpath "$src")" \
  MSYS_NO_PATHCONV=1 \
  powershell.exe -NoProfile -NonInteractive -Command '
    $ErrorActionPreference = "Stop"
    $d = $env:WB_DST
    $s = $env:WB_SRC
    $item = Get-Item -LiteralPath $d -Force -ErrorAction SilentlyContinue
    if ($null -ne $item) {
      $isLink = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
      if (-not $isLink) { exit 3 }
      # 用 .NET 直接删 reparse point 本身：不会跟随链接删掉源目录，
      # 也不会像 Remove-Item 那样在 NonInteractive 模式下弹确认提示。
      if ($item.PSIsContainer) { [System.IO.Directory]::Delete($d) }
      else { [System.IO.File]::Delete($d) }
    }
    if ($env:WB_MODE -eq "uninstall") { exit 0 }
    New-Item -ItemType Junction -Path $d -Target $s | Out-Null
  '
}

if [ "$WIN" -eq 1 ] && ! command -v powershell.exe >/dev/null 2>&1; then
  echo "错误：Windows 下需要 powershell.exe 来创建目录 junction（Git Bash 的 PATH 里通常自带）。" >&2
  echo "也可以手动把 skills/ 下的目录复制到：$DEST" >&2
  exit 1
fi

if [ "$MODE" = install ]; then
  mkdir -p "$DEST"
fi

echo "目标目录：$DEST  ($( [ "$WIN" -eq 1 ] && echo 'Windows / junction' || echo 'Unix / symlink' ))"
count=0

for d in "$ROOT"/skills/*/; do
  [ -d "$d" ] || continue
  [ -f "$d/SKILL.md" ] || continue          # 只装真正含 SKILL.md 的 skill
  name="$(basename "$d")"
  src="${d%/}"
  dst="$DEST/$name"

  if [ "$MODE" = uninstall ]; then
    if [ "$WIN" -eq 1 ]; then
      if junction uninstall "$dst" "$src"; then :; else
        rc=$?
        if [ "$rc" -eq 3 ]; then
          echo "  跳过 $name：$dst 是实体目录，未删除" >&2
          continue
        fi
        echo "  移除 $name 失败" >&2; exit 1
      fi
    else
      if [ -L "$dst" ]; then
        rm -f "$dst"
      elif [ -e "$dst" ]; then
        echo "  跳过 $name：$dst 是实体目录，未删除" >&2
        continue
      else
        continue
      fi
    fi
    echo "removed: $name"
    count=$((count + 1))
    continue
  fi

  # ---- 安装 ----
  if [ "$WIN" -eq 0 ]; then
    if [ -L "$dst" ]; then
      rm -f "$dst"
    elif [ -e "$dst" ]; then
      echo "  跳过 $name：$dst 已存在且不是软链（不覆盖实体目录）" >&2
      continue
    fi
    ln -s "$src" "$dst"
    method="符号链接"
  else
    if junction install "$dst" "$src"; then
      method="目录 junction"
    else
      rc=$?
      if [ "$rc" -eq 3 ]; then
        echo "  跳过 $name：$dst 已存在且是实体目录（不覆盖）" >&2
        continue
      fi
      echo "  链接 $name 失败" >&2
      exit 1
    fi
  fi

  echo "linked: $name  [$method]  -> $src"
  count=$((count + 1))
done

echo
if [ "$MODE" = uninstall ]; then
  echo "完成：已移除 $count 个链接。"
else
  if [ "$count" -eq 0 ]; then
    echo "没有找到可安装的 skill（检查 skills/*/SKILL.md 是否存在）。" >&2
    exit 1
  fi
  echo "完成：已链接 $count 个 skill 到 $DEST"
  echo "现在可以在 WorkBuddy 里说「用摸鱼周报写一份关于〈这周干了啥〉的摸鱼周报」来触发。"
  echo "若当前会话还没出现该 skill，新开一个会话（或重启 WorkBuddy）刷新 skill 列表即可。"
fi
