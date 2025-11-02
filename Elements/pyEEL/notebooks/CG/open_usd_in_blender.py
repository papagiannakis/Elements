#!/usr/bin/env python3
"""
Helper script to open USD files in Blender
Usage: python open_usd_in_blender.py [filename.usda]
"""

import sys
import subprocess
from pathlib import Path

BLENDER_PATH = "/Applications/Blender.app/Contents/MacOS/Blender"
USD_OUTPUT_DIR = Path(__file__).parent / "usd_output"

def open_in_blender(usd_file):
    """Open a USD file in Blender"""
    
    if not Path(BLENDER_PATH).exists():
        print(f"❌ Blender not found at: {BLENDER_PATH}")
        print(f"   Install: brew install --cask blender")
        return False
    
    usd_path = USD_OUTPUT_DIR / usd_file
    if not usd_path.exists():
        print(f"❌ USD file not found: {usd_path}")
        print(f"\n📁 Available files:")
        for f in sorted(USD_OUTPUT_DIR.glob("*.usda")):
            print(f"   • {f.name}")
        return False
    
    print(f"🎬 Opening {usd_file} in Blender...")
    print(f"   USD file: {usd_path}")
    print(f"   Blender: {BLENDER_PATH}")
    
    # Create a temporary Blender script to import USD
    script = f'''
import bpy

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import USD
try:
    bpy.ops.wm.usd_import(filepath="{usd_path}")
    print("✅ USD file imported successfully!")
    
    # Frame all objects in viewport
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    override = {{'area': area, 'region': region}}
                    bpy.ops.view3d.view_all(override)
                    break
except Exception as e:
    print(f"❌ Error importing USD: {{e}}")
'''
    
    script_path = USD_OUTPUT_DIR / "blender_import_temp.py"
    with open(script_path, 'w') as f:
        f.write(script)
    
    try:
        # Open Blender with the script
        subprocess.Popen([BLENDER_PATH, "--python", str(script_path)])
        print(f"✅ Blender launched!")
        print(f"\n💡 In Blender:")
        print(f"   • Press numpad 0 for camera view")
        print(f"   • Middle mouse to rotate view")
        print(f"   • Scroll to zoom")
        print(f"   • Spacebar to play animation")
        return True
    except Exception as e:
        print(f"❌ Error launching Blender: {e}")
        return False

def main():
    """Main entry point"""
    print("="*70)
    print("🎨 USD to Blender Viewer")
    print("="*70)
    
    # List available files
    usd_files = sorted(USD_OUTPUT_DIR.glob("*.usda"))
    
    if not usd_files:
        print(f"\n❌ No USD files found in: {USD_OUTPUT_DIR}")
        print(f"   Run the tutorial cells first to create USD files!")
        return
    
    print(f"\n📁 Available USD files:")
    for idx, f in enumerate(usd_files, 1):
        size = f.stat().st_size / 1024
        print(f"   {idx}. {f.name:<25} ({size:>6.2f} KB)")
    
    # Get filename from command line or prompt
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        print(f"\n📝 Enter filename to open (or number 1-{len(usd_files)}):")
        choice = input("   > ").strip()
        
        # Check if it's a number
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(usd_files):
                filename = usd_files[idx].name
            else:
                print(f"❌ Invalid number. Choose 1-{len(usd_files)}")
                return
        else:
            filename = choice
            if not filename.endswith('.usda'):
                filename += '.usda'
    
    # Open in Blender
    open_in_blender(filename)

if __name__ == "__main__":
    main()
