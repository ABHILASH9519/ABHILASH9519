#!/usr/bin/env python3
"""Apply the Mono Steel palette to every SVG used by the profile README."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

# Map the existing Aurora Teal palette to the Mono Steel palette.
PALETTE = {
    "#021A1F": "#05070D",  # deepest background
    "#052E35": "#0D1320",  # raised background
    "#14B8A6": "#64748B",  # primary steel
    "#2DD4BF": "#E2E8F0",  # bright steel
    "#5EEAD4": "#94A3B8",  # muted steel
    "#CCFBF1": "#FFFFFF",  # highlight
}

changed = []
for path in sorted(ASSETS.glob("*.svg")):
    original = path.read_text(encoding="utf-8")
    updated = original
    for old, new in PALETTE.items():
        updated = updated.replace(old, new)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        changed.append(path.name)

print(f"Applied Mono Steel palette to {len(changed)} SVG assets:")
for name in changed:
    print(f" - {name}")
