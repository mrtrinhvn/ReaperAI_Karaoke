#!/bin/bash
# ag-kit pack installer
# Usage: ./pack-install.sh [--pack web] [--pack python] [--pack bot]
# Default: installs core pack only

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGKIT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE_SKILLS="$AGKIT_ROOT/template/.agent/skills"
TEMPLATE_PACKS="$AGKIT_ROOT/template/.agent/packs"
TARGET_DIR="${TARGET_DIR:-.}"
TARGET_SKILLS="$TARGET_DIR/.agent/skills"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse args
PACKS=("core")  # Always install core
while [[ $# -gt 0 ]]; do
  case $1 in
    --pack) PACKS+=("$2"); shift 2 ;;
    --target) TARGET_DIR="$2"; TARGET_SKILLS="$TARGET_DIR/.agent/skills"; shift 2 ;;
    --list) echo "Available packs:"; ls "$TEMPLATE_PACKS"/*.pack | xargs -I{} basename {} .pack; exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

mkdir -p "$TARGET_SKILLS"

echo -e "${BLUE}🚀 ag-kit pack installer${NC}"
echo "Target: $TARGET_SKILLS"
echo "Packs: ${PACKS[*]}"
echo ""

TOTAL=0
for pack in "${PACKS[@]}"; do
  pack_file="$TEMPLATE_PACKS/${pack}.pack"
  if [[ ! -f "$pack_file" ]]; then
    echo -e "${YELLOW}⚠️  Pack '$pack' not found, skipping${NC}"
    continue
  fi
  
  echo -e "${GREEN}📦 Installing pack: $pack${NC}"
  
  while IFS= read -r skill; do
    # Skip comments and empty lines
    [[ "$skill" =~ ^#.*$ ]] && continue
    [[ -z "$skill" ]] && continue
    
    src="$TEMPLATE_SKILLS/$skill"
    dst="$TARGET_SKILLS/$skill"
    
    if [[ -d "$src" ]]; then
      cp -r "$src" "$dst"
      echo "  ✅ $skill"
      ((TOTAL++))
    else
      echo "  ⚠️  $skill (not found in template)"
    fi
  done < "$pack_file"
  echo ""
done

echo -e "${GREEN}✅ Done: $TOTAL skills installed${NC}"
echo ""
echo "Installed packs: ${PACKS[*]}"
echo ""
echo "To add more packs later:"
echo "  ./pack-install.sh --pack web --target ."
echo ""
echo "Available packs:"
ls "$TEMPLATE_PACKS"/*.pack | xargs -I{} basename {} .pack | sed 's/^/  - /'
