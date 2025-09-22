#!/usr/bin/env python3
"""
Debug test for pipeline to see why data extraction fails
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
from modules.multi_ai_client import multi_ai_client

def test_ai_direct():
    """Test AI direct call"""
    extractor = ExperimentalTableExtractor()

    # Test simple prompt
    test_prompt = """
    Витягни дані про AHCC:
    1. Назва українською
    2. Джерело сировини
    3. Активні сполуки
    4. Добова норма

    Текст: AHCC is derived from shiitake mushrooms. It contains alpha-glucans as active compounds. Recommended dose is 3g daily.

    Поверни у JSON форматі:
    {
        "nazva_ukr_orig": "українська назва",
        "dzherelo_syrovyny": "джерело",
        "aktyvni_spoluky": ["сполука1", "сполука2"],
        "dobova_norma": "доза",
        "dzherela_tsytaty": []
    }
    """

    print("Testing AI direct call...")
    print("=" * 50)

    try:
        response = extractor._call_ai_direct(test_prompt, "claude")
        print(f"AI Response length: {len(response) if response else 0}")
        print(f"AI Response preview: {response[:200] if response else 'None'}...")

        if response and '{' in response:
            data = extractor._extract_json_from_response(response)
            print(f"Extracted data: {data}")

            if data:
                valid = extractor._validate_table_data(data)
                print(f"Data is valid: {valid}")

    except Exception as e:
        print(f"Error in AI call: {e}")
        import traceback
        traceback.print_exc()

def test_table_prompts():
    """Test table prompts generation"""
    print("\nTesting table prompts...")
    print("=" * 50)

    try:
        prompt = TablePrompts.get_table_extraction_prompt(
            "AHCC",
            "AHCC is derived from shiitake mushrooms. Contains alpha-glucans. Dose: 3g daily.",
            "https://example.com"
        )
        print(f"Prompt length: {len(prompt)}")
        print(f"Prompt preview: {prompt[:300]}...")

    except Exception as e:
        print(f"Error in prompt generation: {e}")
        import traceback
        traceback.print_exc()

def test_multi_ai():
    """Test multi AI client"""
    print("\nTesting multi AI client...")
    print("=" * 50)

    print(f"Available models: {multi_ai_client.available_models}")

    test_prompt = "What is AHCC? Respond in JSON format with just one field: {'test': 'response'}"

    for model in ['claude', 'openai', 'gemini']:
        if model in multi_ai_client.available_models:
            try:
                print(f"Testing {model}...")
                if model == 'claude':
                    response = multi_ai_client._call_claude(test_prompt)
                elif model == 'openai':
                    response = multi_ai_client._call_openai(test_prompt)
                elif model == 'gemini':
                    response = multi_ai_client._call_gemini(test_prompt)

                print(f"{model} response: {response[:100] if response else 'None'}...")

            except Exception as e:
                print(f"Error with {model}: {e}")

if __name__ == "__main__":
    test_multi_ai()
    test_table_prompts()
    test_ai_direct()