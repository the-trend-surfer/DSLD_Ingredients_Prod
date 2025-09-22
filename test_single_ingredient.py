#!/usr/bin/env python3
"""
Test single ingredient processing
"""
import sys
import os

# Fix Windows encoding
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except AttributeError:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processes.pipeline import pipeline

def test_single():
    # Test with minimal data - синоніми з Google Sheets
    result = pipeline.process_ingredient(
        "AHCC",
        [],  # Синоніми беруться з Google Sheets стовпчика E
        []
    )

    print("=== FINAL RESULT ===")
    for key, value in result.items():
        print(f"{key}: '{value}'")

    print(f"\nHas data: {bool(result.get('C_aktyvni_spoluky'))}")

if __name__ == "__main__":
    test_single()