#!/usr/bin/env python3
"""
Debug documents in _extract_with_table_ai
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

def debug_extraction():
    extractor = ExperimentalTableExtractor()

    # Simulate documents as they come from NCBI
    test_docs = [
        {
            'title': 'AHCC immunomodulatory effects',
            'text': 'AHCC (Active Hexose Correlated Compound) is a standardized extract of cultured Lentinula edodes mycelia. The main bioactive components are alpha-glucans with molecular weights of 5,000 Da. Clinical studies suggest a dose of 3 grams daily for immune support.',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/12345',
            'abstract': 'Study on AHCC effects'
        }
    ]

    print("=== Testing _extract_with_table_ai step by step ===")

    # Manual step-by-step execution
    ingredient = "AHCC"
    documents = test_docs
    ai_model = "claude"

    print(f"Documents: {len(documents)}")
    for i, doc in enumerate(documents):
        print(f"  Doc {i+1}: title='{doc.get('title', 'None')}', text_len={len(doc.get('text', ''))}")

    # Step 1: Check documents
    if not documents:
        print("ERROR: No documents")
        return

    # Step 2: Process each document
    for i, doc in enumerate(documents[:2], 1):
        print(f"\n--- Processing Document {i} ---")

        url = doc.get('url', '')
        text = doc.get('text', '')
        title = doc.get('title', '')
        full_text = f"{title}\n\n{text}" if title else text

        print(f"URL: {url}")
        print(f"Title: {title}")
        print(f"Text length: {len(text)}")
        print(f"Full text length: {len(full_text)}")

        # Check minimum length
        if len(full_text) < 50:
            print(f"SKIP: Text too short ({len(full_text)} chars)")
            continue

        # Step 3: Generate prompt
        try:
            prompt = TablePrompts.get_table_extraction_prompt(ingredient, full_text, url)
            print(f"Prompt generated: {len(prompt)} chars")
        except Exception as e:
            print(f"ERROR in prompt generation: {e}")
            continue

        # Step 4: Call AI
        try:
            print("Calling AI...")
            response = extractor._call_ai_direct(prompt, ai_model)
            print(f"AI response length: {len(response) if response else 0}")

            if response:
                print(f"Response preview: {response[:150]}...")

                # Step 5: Check for JSON
                if '{' in response:
                    print("JSON detected in response")

                    # Step 6: Extract JSON
                    try:
                        data = extractor._extract_json_from_response(response)
                        print(f"Extracted data: {data}")

                        if data:
                            # Step 7: Validate
                            valid = extractor._validate_table_data(data)
                            print(f"Data validation: {valid}")

                            if valid:
                                print("SUCCESS: Valid data extracted!")
                                return data
                            else:
                                print("FAIL: Data validation failed")
                        else:
                            print("FAIL: No data extracted from JSON")
                    except Exception as e:
                        print(f"ERROR in JSON extraction: {e}")
                else:
                    print("FAIL: No JSON in response")
            else:
                print("FAIL: Empty AI response")

        except Exception as e:
            print(f"ERROR in AI call: {e}")
            import traceback
            traceback.print_exc()

    print("\nFALLBACK: Returning empty result")
    return extractor._create_empty_table_result(ingredient)

if __name__ == "__main__":
    result = debug_extraction()
    print(f"\nFinal result: {result}")