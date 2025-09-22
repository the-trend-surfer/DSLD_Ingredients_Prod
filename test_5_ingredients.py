#!/usr/bin/env python3
"""
Test 5 ingredients with new combined citation format
"""
import sys
import os
import time

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

def test_5_ingredients():
    """Test 5 different ingredients with separate B/C/D cycles"""
    print("=== Testing 5 Ingredients with Combined Citations ===")
    print("Format: Citations + URLs combined in column F, column G empty")
    print("=" * 70)

    # Test ingredients - синоніми беруться з Google Sheets стовпчика E
    ingredients = [
        ("AHCC", []),  # Синоніми з Google Sheets
        ("CoQ10", []),  # Синоніми з Google Sheets
        ("Curcumin", []),  # Синоніми з Google Sheets
        ("Resveratrol", []),  # Синоніми з Google Sheets
        ("Omega-3", [])  # Синоніми з Google Sheets
    ]

    results = []
    total_start = time.time()

    for i, (ingredient, synonyms) in enumerate(ingredients, 1):
        print(f"\n[{i}/5] Processing: {ingredient}")
        print("-" * 50)

        start_time = time.time()

        try:
            result = pipeline.process_ingredient(
                ingredient,
                synonyms,
                [],
                ai_model="openai"  # Using GPT-5-mini as requested
            )

            processing_time = round(time.time() - start_time, 1)

            # Display results
            print(f"✅ Completed in {processing_time}s")
            print(f"A_nazva_ukrainska: '{result.get('A_nazva_ukrainska', '')}'")
            print(f"B_dzherelo_otrymannya: '{result.get('B_dzherelo_otrymannya', '')}'")
            print(f"C_aktyvni_spoluky: '{result.get('C_aktyvni_spoluky', '')}'")
            print(f"D_dozuvannya: '{result.get('D_dozuvannya', '')}'")
            print(f"E_riven_dokaziv: '{result.get('E_riven_dokaziv', '')}'")
            print(f"F_tsytaty: '{result.get('F_tsytaty', '')}'")
            print(f"G_dzherela: '{result.get('G_dzherela', '')}'")

            # Quality check
            has_ukrainian = bool(result.get('A_nazva_ukrainska', '').strip())
            has_source = bool(result.get('B_dzherelo_otrymannya', '').strip())
            has_compounds = bool(result.get('C_aktyvni_spoluky', '').strip())
            has_dosage = bool(result.get('D_dozuvannya', '').strip())
            has_citations = bool(result.get('F_tsytaty', '').strip())

            success_count = sum([has_ukrainian, has_source, has_compounds, has_dosage])
            success_rate = success_count / 4 * 100

            print(f"📊 Data completeness: {success_rate:.0f}% (UA:{'✓' if has_ukrainian else '✗'} Source:{'✓' if has_source else '✗'} Compounds:{'✓' if has_compounds else '✗'} Dose:{'✓' if has_dosage else '✗'} Citations:{'✓' if has_citations else '✗'})")

            results.append({
                'ingredient': ingredient,
                'success_rate': success_rate,
                'time': processing_time,
                'result': result
            })

        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({
                'ingredient': ingredient,
                'success_rate': 0,
                'time': round(time.time() - start_time, 1),
                'error': str(e)
            })

    # Summary
    total_time = round(time.time() - total_start, 1)
    print(f"\n{'='*70}")
    print("=== FINAL SUMMARY ===")
    print(f"Total processing time: {total_time}s")
    print(f"Average per ingredient: {total_time/5:.1f}s")

    successful = [r for r in results if 'error' not in r]
    if successful:
        avg_success = sum(r['success_rate'] for r in successful) / len(successful)
        print(f"Average success rate: {avg_success:.1f}%")

    print(f"\nResults breakdown:")
    for result in results:
        if 'error' in result:
            print(f"❌ {result['ingredient']}: FAILED ({result['time']}s)")
        else:
            print(f"{'🎉' if result['success_rate'] >= 75 else '⚠️' if result['success_rate'] >= 50 else '❌'} {result['ingredient']}: {result['success_rate']:.0f}% ({result['time']}s)")

    # Citation format check
    print(f"\n=== CITATION FORMAT CHECK ===")
    citations_with_urls = 0
    empty_g_columns = 0

    for result in results:
        if 'error' not in result:
            f_content = result['result'].get('F_tsytaty', '')
            g_content = result['result'].get('G_dzherela', '')

            if f_content and '(' in f_content and 'http' in f_content:
                citations_with_urls += 1

            if not g_content.strip():
                empty_g_columns += 1

    print(f"✅ Citations with URLs in F: {citations_with_urls}/{len(successful)}")
    print(f"✅ Empty G columns: {empty_g_columns}/{len(successful)}")

    if citations_with_urls == len(successful) and empty_g_columns == len(successful):
        print("🎉 NEW CITATION FORMAT WORKING PERFECTLY!")
    else:
        print("⚠️ Citation format needs attention")

    return results

if __name__ == "__main__":
    test_5_ingredients()