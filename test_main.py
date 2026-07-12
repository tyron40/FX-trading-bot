#!/usr/bin/env python3
"""
Test script for main_final.py functionality
"""

import sys
import os
from io import StringIO

def test_main_menu():
    """Test the main menu selection"""
    print("Testing main_final.py menu...")

    # Mock inputs for practice account, auto trading
    inputs = ["1", "1"]  # Practice account, Auto trading

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    try:
        # Import and run main
        from main_final import main

        # Mock input function
        def mock_input(prompt):
            if inputs:
                response = inputs.pop(0)
                print(f"Input: {response}")
                return response
            return ""

        # Replace input with mock
        import builtins
        builtins.input = mock_input

        main()

    except SystemExit:
        pass  # Expected when program ends
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Restore stdout
        sys.stdout = old_stdout

    output = captured_output.getvalue()
    print("Menu test output:")
    print(output)

    # Check for expected outputs
    success_indicators = [
        "Using PRACTICE account",
        "Starting Smart Auto Trader",
        "Account Balance",
        "Trading EUR_USD"
    ]

    for indicator in success_indicators:
        if indicator in output:
            print(f"✓ Found: {indicator}")
        else:
            print(f"✗ Missing: {indicator}")

if __name__ == "__main__":
    test_main_menu()
