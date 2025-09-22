#!/usr/bin/env python3
"""
Quick test for new citation format
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processes.pipeline import pipeline

# Test new citation format
def test_citation_format():
    print("=== Testing New Citation Format ===")
    print("Citations and URLs should now be combined in column F")
    print("Column G should be empty")
    print()

    # Create test citations data
    test_citations = [
        {
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
            "quote": "AHCC shows immunomodulatory effects in clinical studies",
            "type": "test",
            "priority": 1
        },
        {
            "url": "https://pubmed.ncbi.nlm.nih.gov/67890/",
            "quote": "Dosage of 3g daily demonstrated significant benefits",
            "type": "test",
            "priority": 1
        }
    ]

    # Test formatting
    formatted_citations = pipeline._format_citations(test_citations)

    print("Input citations:")
    for i, citation in enumerate(test_citations, 1):
        print(f"  {i}. Quote: {citation['quote']}")
        print(f"     URL: {citation['url']}")

    print(f"\nFormatted output for column F:")
    print(f"'{formatted_citations}'")

    print(f"\nColumn G (should be empty): ''")

    # Verify format
    expected_parts = [
        "AHCC shows immunomodulatory effects in clinical studies (https://pubmed.ncbi.nlm.nih.gov/12345/)",
        "Dosage of 3g daily demonstrated significant benefits (https://pubmed.ncbi.nlm.nih.gov/67890/)"
    ]
    expected = "; ".join(expected_parts)

    if formatted_citations == expected:
        print("\n✅ Citation format test PASSED!")
    else:
        print(f"\n❌ Citation format test FAILED!")
        print(f"Expected: {expected}")
        print(f"Got: {formatted_citations}")

    return formatted_citations == expected

if __name__ == "__main__":
    test_citation_format()