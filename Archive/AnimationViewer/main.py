#!/usr/bin/env python3
"""
Sprite Animation Tool - Main Entry Point

A professional sprite animation creation tool for 2D game development.
This is the Phase 1 implementation focusing on architecture refactoring
and removing hardcoded dependencies from the original viewer.py.

Usage:
    python main.py

Phase 1 Features:
- Dynamic sprite sheet loading system
- Multi-spritesheet architecture foundation  
- Professional class-based structure
- All original functionality preserved
- File dialog integration
- Project management foundation

Author: AI Assistant (Lead Developer)
Project: 2D Platformer Game Tools
Phase: 1 - Architecture Refactoring
"""

import os
import sys
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.main_window import SpriteAnimationTool
except ImportError as e:
    print(f"Failed to import application modules: {e}")
    print("Make sure you're running from the AnimationViewer directory")
    sys.exit(1)


def main():
    """Main entry point for the sprite animation tool."""
    print("Sprite Animation Tool - Phase 1")
    print("=" * 40)
    print("Features:")
    print("- Dynamic sprite sheet loading (Ctrl+O)")
    print("- Frame selection and animation export (Ctrl+S)")
    print("- Grid navigation and analysis (T key)")
    print("- Multi-spritesheet architecture foundation")
    print("- Professional class-based structure")
    print()
    
    try:
        # Create and run the application
        app = SpriteAnimationTool()
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
