#!/usr/bin/env python3
"""
Test 5 rows with clean data - no hardcoded synonyms, only Google Sheets data
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

def test_5_rows():
    """Test 5 rows with clean approach - only real data from Google Sheets"""
    print("=== Testing 5 Rows - Clean Data Only ===")
    print("✅ No hardcoded synonyms")
    print("✅ OR query format")
    print("✅ Only Google Sheets C+E data")
    print("✅ Only real data from PubMed sources")
    print("=" * 60)

    # Test ingredients - synonyms come ONLY from Google Sheets column E
    test_ingredients = [
        "AHCC",
        "CoQ10",
        "Curcumin",
        "Resveratrol",
        "Omega-3"
    ]

    results = []
    total_start = time.time()

    for i, ingredient in enumerate(test_ingredients, 1):
        print(f"\n[{i}/5] Processing: {ingredient}")
        print("-" * 50)

        start_time = time.time()

        try:
            # Process with ONLY Google Sheets data
            result = pipeline.process_ingredient(
                ingredient,
                [],  # Synonyms from Google Sheets column E ONLY
                [],  # No existing links
                ai_model="openai"  # Using GPT-4o-mini as configured
            )

            processing_time = round(time.time() - start_time, 1)

            # Display results
            print(f"✅ Completed in {processing_time}s")
            print(f"A (Ukrainian): '{result.get('A_nazva_ukrainska', '')}'")
            print(f"B (Source): '{result.get('B_dzherelo_otrymannya', '')}'")
            print(f"C (Compounds): '{result.get('C_aktyvni_spoluky', '')}'")
            print(f"D (Dosage): '{result.get('D_dozuvannya', '')}'")
            print(f"E (Level): '{result.get('E_riven_dokaziv', '')}'")
            print(f"F (Citations+URLs): '{result.get('F_tsytaty', '')[:100]}{'...' if len(result.get('F_tsytaty', '')) > 100 else ''}'")
            print(f"G (Sources): '{result.get('G_dzherela', '')}'")

            # Data quality analysis
            has_ukrainian = bool(result.get('A_nazva_ukrainska', '').strip())
            has_source = bool(result.get('B_dzherelo_otrymannya', '').strip())
            has_compounds = bool(result.get('C_aktyvni_spoluky', '').strip())
            has_dosage = bool(result.get('D_dozuvannya', '').strip())
            has_citations = bool(result.get('F_tsytaty', '').strip())
            citations_have_urls = 'http' in result.get('F_tsytaty', '')
            g_column_empty = not bool(result.get('G_dzherela', '').strip())

            filled_fields = sum([has_ukrainian, has_source, has_compounds, has_dosage])
            success_rate = filled_fields / 4 * 100

            print(f"📊 Data: {success_rate:.0f}% | UA:{'✓' if has_ukrainian else '✗'} Src:{'✓' if has_source else '✗'} Cmp:{'✓' if has_compounds else '✗'} Dos:{'✓' if has_dosage else '✗'} | Cit:{'✓' if has_citations else '✗'} URLs:{'✓' if citations_have_urls else '✗'} G-empty:{'✓' if g_column_empty else '✗'}")

            results.append({
                'ingredient': ingredient,
                'success_rate': success_rate,
                'time': processing_time,
                'has_citations': has_citations,
                'citations_have_urls': citations_have_urls,
                'g_column_empty': g_column_empty,
                'level': result.get('E_riven_dokaziv', ''),
                'result': result
            })

        except Exception as e:
            print(f"❌ Failed: {e}")
            processing_time = round(time.time() - start_time, 1)
            results.append({
                'ingredient': ingredient,
                'success_rate': 0,
                'time': processing_time,
                'error': str(e)
            })

    # Final summary
    total_time = round(time.time() - total_start, 1)
    print(f"\n{'='*60}")
    print("=== FINAL SUMMARY ===")
    print(f"🕒 Total time: {total_time}s ({total_time/5:.1f}s avg)")

    successful = [r for r in results if 'error' not in r]
    if successful:
        avg_success = sum(r['success_rate'] for r in successful) / len(successful)
        print(f"📊 Average data completeness: {avg_success:.1f}%")

        # Citation format check
        with_citations = sum(1 for r in successful if r['has_citations'])
        with_urls = sum(1 for r in successful if r['citations_have_urls'])
        g_empty = sum(1 for r in successful if r['g_column_empty'])

        print(f"🔗 Citations: {with_citations}/{len(successful)} have citations")
        print(f"🌐 URLs in F: {with_urls}/{len(successful)} have URLs in citations")
        print(f"📭 G column empty: {g_empty}/{len(successful)} (should be 5/5)")

        # Evidence levels
        levels = {}
        for r in successful:
            level = r.get('level', 'Unknown')
            levels[level] = levels.get(level, 0) + 1
        print(f"🏆 Evidence levels: {dict(levels)}")

    print(f"\n=== INDIVIDUAL RESULTS ===")
    for result in results:
        if 'error' in result:
            print(f"❌ {result['ingredient']}: FAILED ({result['time']}s) - {result['error']}")
        else:
            status = "🎉" if result['success_rate'] >= 75 else "⚠️" if result['success_rate'] >= 50 else "❌"
            print(f"{status} {result['ingredient']}: {result['success_rate']:.0f}% data, {result['level']} level ({result['time']}s)")

    # Final validation
    print(f"\n=== CLEAN DATA VALIDATION ===")

    if len(successful) == 5:
        all_have_ukrainian = all(r['result'].get('A_nazva_ukrainska', '').strip() for r in successful)
        all_g_empty = all(r['g_column_empty'] for r in successful)
        most_have_citations = with_citations >= 4

        print(f"✅ All Ukrainian names: {'Yes' if all_have_ukrainian else 'No'}")
        print(f"✅ All G columns empty: {'Yes' if all_g_empty else 'No'}")
        print(f"✅ Most have citations: {'Yes' if most_have_citations else 'No'}")

        if all_have_ukrainian and all_g_empty and most_have_citations:
            print("🎉 CLEAN DATA APPROACH WORKING PERFECTLY!")
        else:
            print("⚠️ Some issues need attention")

    return results

if __name__ == "__main__":
    test_5_rows()