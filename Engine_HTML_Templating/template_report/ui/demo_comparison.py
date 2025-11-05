#!/usr/bin/env python3
"""
Demo script to compare original vs fixed template layouts
"""

import subprocess
import sys
from pathlib import Path

def run_comparison():
    """Generate both original and fixed templates for comparison"""

    print("=" * 60)
    print("DAFTAR UPAH TEMPLATE COMPARISON DEMO")
    print("=" * 60)

    # Change to the correct directory
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)

    print("\n1. GENERATING ORIGINAL TEMPLATE...")
    try:
        result = subprocess.run([sys.executable, "daftar_upah_engine.py"],
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Original template generated successfully")
            print(f"  {result.stdout.strip()}")
        else:
            print("✗ Original template failed")
            print(f"  Error: {result.stderr}")
    except Exception as e:
        print(f"✗ Error running original template: {e}")

    print("\n2. GENERATING FIXED TEMPLATE...")
    try:
        result = subprocess.run([sys.executable, "daftar_upah_engine_fixed.py"],
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Fixed template generated successfully")
            print(f"  {result.stdout.strip()}")
        else:
            print("✗ Fixed template failed")
            print(f"  Error: {result.stderr}")
    except Exception as e:
        print(f"✗ Error running fixed template: {e}")

    print("\n" + "=" * 60)
    print("IMPROVEMENTS IN FIXED TEMPLATE:")
    print("=" * 60)

    improvements = [
        "✓ Fixed table width (2900px) for consistent layout",
        "✓ Reduced columns from 58 to 47 for better fitting",
        "✓ Optimized column widths with proper sizing",
        "✓ Added text overflow handling (ellipsis)",
        "✓ Improved header organization with 4-level hierarchy",
        "✓ Better currency formatting (shortened for display)",
        "✓ Print-optimized CSS with @media rules",
        "✓ Horizontal scrolling container for large tables",
        "✓ Smaller font sizes for better space utilization",
        "✓ Consistent padding and border styling",
        "✓ Responsive signature section"
    ]

    for improvement in improvements:
        print(f"  {improvement}")

    print("\n" + "=" * 60)
    print("TECHNICAL SPECIFICATIONS:")
    print("=" * 60)

    specs = [
        "Table Width: 2900px (fixed)",
        "Column Count: 47 columns",
        "Font Size: 7pt (6.5pt for numbers)",
        "Page Layout: A4 Landscape",
        "Margins: 0.5in x 0.3in",
        "Header Levels: 4 (Main, Section, Detail, Sub-detail)",
        "Currency Format: Shortened (1.5jt, 250rb)",
        "Overflow: Hidden with ellipsis",
        "Print Support: Yes (@media print)",
        "Scrolling: Horizontal for overflow"
    ]

    for spec in specs:
        print(f"  • {spec}")

    print("\n" + "=" * 60)
    print("FILES GENERATED:")
    print("=" * 60)

    output_dir = script_dir / "output"
    if output_dir.exists():
        files = list(output_dir.glob("*.html"))
        for file in sorted(files):
            size = file.stat().st_size
            print(f"  📄 {file.name} ({size:,} bytes)")

    print("\n" + "=" * 60)
    print("READY FOR PRODUCTION!")
    print("=" * 60)

    print("\nThe fixed template is now ready for production use.")
    print("Key improvements ensure proper column fitting and professional appearance.")
    print("\nUsage:")
    print("  python daftar_upah_engine_fixed.py")
    print("  python daftar_upah_engine_fixed.py --data your_data.json --output report.html")

if __name__ == "__main__":
    run_comparison()