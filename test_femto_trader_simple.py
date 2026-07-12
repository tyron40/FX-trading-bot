#!/usr/bin/env python3
"""
Simple test for FemtoTrader to verify basic functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that FemtoTrader can be imported"""
    try:
        from FemtoTrader_new import FemtoTrader
        print("✓ FemtoTrader imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import FemtoTrader: {e}")
        return False

def test_instantiation():
    """Test that FemtoTrader can be instantiated (without real config)"""
    try:
        from FemtoTrader_new import FemtoTrader

        # Try to create with a dummy config file that doesn't exist
        # This should fail gracefully
        try:
            trader = FemtoTrader("nonexistent.cfg")
            print("✗ FemtoTrader should have failed with nonexistent config")
            return False
        except Exception as e:
            print(f"✓ FemtoTrader correctly failed with nonexistent config: {type(e).__name__}")
            return True

    except Exception as e:
        print(f"✗ Failed to test instantiation: {e}")
        return False

def test_callbacks():
    """Test that GUI callbacks can be set"""
    try:
        from FemtoTrader_new import FemtoTrader

        # Create a mock trader instance (this will fail but we can test the callback setup)
        trader = FemtoTrader.__new__(FemtoTrader)  # Create without calling __init__

        # Initialize the callbacks dict manually since __init__ wasn't called
        trader._gui_callbacks = {
            'price': None,
            'signal': None,
            'news': None,
            'technical': None,
            'position': None,
            'history': None
        }

        # Test callback setup
        trader.set_gui_callbacks(
            price_callback=lambda x: None,
            signal_callback=lambda x: None,
            news_callback=lambda x: None,
            technical_callback=lambda x: None,
            position_callback=lambda x: None,
            history_callback=lambda x: None
        )

        print("✓ GUI callbacks set successfully")
        return True

    except Exception as e:
        print(f"✗ Failed to test callbacks: {e}")
        return False
    
def main():
    """Run all tests"""
    print("Running FemtoTrader simple tests...\n")

    tests = [
        test_import,
        test_instantiation,
        test_callbacks
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
