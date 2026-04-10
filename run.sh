#!/bin/bash
echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║       🖐️  HAND VIZ PRO           ║"
echo "  ║   Real-time Hand Visualizer      ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install from https://python.org"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Install packages
echo ""
echo "📦 Installing dependencies..."
pip3 install mediapipe opencv-python numpy --quiet

echo ""
echo "✅ Dependencies ready!"
echo ""
echo "  ┌──────────────────────────────────┐"
echo "  │  CONTROLS                        │"
echo "  ├──────────────────────────────────┤"
echo "  │  Q  ─  Quit                      │"
echo "  │  D  ─  Toggle Dark/Light Mode    │"
echo "  │  P  ─  Toggle Particles          │"
echo "  │  G  ─  Toggle Background Grid    │"
echo "  │  M  ─  Toggle Distance Measure   │"
echo "  │  H  ─  Show/Hide Help Overlay    │"
echo "  └──────────────────────────────────┘"
echo ""
echo "⚠️  macOS Camera Permission:"
echo "   If the app fails to open camera, go to:"
echo "   System Settings → Privacy & Security → Camera"
echo "   → Enable Terminal (or iTerm2, or your app)"
echo ""
echo "🚀 Launching..."
echo ""
python3 handviz_pro.py
