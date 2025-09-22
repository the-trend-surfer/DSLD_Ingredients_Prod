#!/usr/bin/env python3
"""
Test each AI component separately
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
from processes.ai_prompts import TablePrompts

def test_components():
    extractor = ExperimentalTableExtractor()

    # Test 1: Prompt generation
    print("=== Test 1: Prompt Generation ===")
    try:
        prompt = TablePrompts.get_table_extraction_prompt(
            "AHCC",
            "AHCC is derived from shiitake mushrooms and contains alpha-glucans. Dose: 3g daily.",
            "https://example.com"
        )
        print(f"Prompt generated successfully: {len(prompt)} chars")
        print(f"Prompt preview: {prompt[:200]}...")
    except Exception as e:
        print(f"Prompt generation failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Direct AI call
    print("\n=== Test 2: Direct AI Call ===")
    try:
        test_prompt = "Extract data about AHCC from: AHCC derived from mushrooms. Return JSON: {'nazva_ukrainska': 'name', 'dzherelo_syrovyny': 'source'}"
        response = extractor._call_ai_direct(test_prompt, "claude")
        print(f"AI response: {response[:200] if response else 'None'}...")
    except Exception as e:
        print(f"AI call failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: JSON extraction
    print("\n=== Test 3: JSON Extraction ===")
    try:
        test_response = '{"nazva_ukr_orig": "test", "dzherelo_syrovyny": "test source"}'
        data = extractor._extract_json_from_response(test_response)
        print(f"JSON extracted: {data}")
    except Exception as e:
        print(f"JSON extraction failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Validation
    print("\n=== Test 4: Data Validation ===")
    try:
        test_data = {
            "nazva_ukr_orig": "AHCC (test)",
            "dzherelo_syrovyny": "test source",
            "aktyvni_spoluky": ["compound1"],
            "dobova_norma": "3g",
            "dzherela_tsytaty": []
        }
        valid = extractor._validate_table_data(test_data)
        print(f"Data validation: {valid}")
    except Exception as e:
        print(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_components()