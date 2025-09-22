#!/usr/bin/env python3
"""
Test direct AI extraction
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

from processes.table_extractor_experimental import ExperimentalTableExtractor

def test_ai_extraction():
    extractor = ExperimentalTableExtractor()

    # Create test documents
    test_docs = [
        {
            'title': 'AHCC Study',
            'text': 'AHCC (Active Hexose Correlated Compound) is derived from shiitake mushrooms (Lentinula edodes). It contains alpha-glucans as the main active compounds. The recommended daily dose is 3 grams per day. Studies show AHCC supports immune function.',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/12345'
        }
    ]

    print("Testing _extract_with_table_ai directly...")

    try:
        result = extractor._extract_with_table_ai("AHCC", test_docs, "claude")
        print(f"Result: {result}")

        if result:
            for key, value in result.items():
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_extraction()