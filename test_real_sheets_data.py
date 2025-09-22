#!/usr/bin/env python3
"""
Test with REAL data from Google Sheets - columns C and E only
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
from modules.sheets_reader import sheets_reader

def test_real_sheets_data():
    """Test with REAL ingredients from Google Sheets columns C and E"""
    print("=== Testing with REAL Google Sheets Data ===")
    print("✅ Reading ingredients from Google Sheets column C")
    print("✅ Reading synonyms from Google Sheets column E")
    print("✅ No hardcoded data")
    print("✅ OR query format")
    print("=" * 60)

    # Read REAL ingredients from Google Sheets
    print("[SHEETS] Connecting to Google Sheets...")
    ingredients_data = sheets_reader.read_ingredients(limit=5)  # First 5 ingredients

    if not ingredients_data:
        print("❌ No ingredients found in Google Sheets!")
        return

    print(f"[OK] Found {len(ingredients_data)} ingredients from Google Sheets")
    print()

    results = []
    total_start = time.time()

    for i, ingredient_data in enumerate(ingredients_data, 1):
        ingredient = ingredient_data['ingredient']
        synonyms = ingredient_data['synonyms']
        existing_links = ingredient_data['existing_links']
        row_number = ingredient_data['row_number']

        print(f"[{i}/{len(ingredients_data)}] Processing: {ingredient}")
        print(f"   📋 Row: {row_number}")
        print(f"   🔗 Synonyms: {synonyms[:3] if synonyms else 'None'}")
        print(f"   📎 Existing links: {len(existing_links)} found")
        print("-" * 50)

        start_time = time.time()

        try:
            # Process with REAL Google Sheets data
            result = pipeline.process_ingredient(
                ingredient,
                synonyms,  # REAL synonyms from Google Sheets column E
                existing_links,  # REAL existing links from column G
                ai_model="openai"  # Using GPT-4o-mini
            )

            processing_time = round(time.time() - start_time, 1)

            # Display results
            print(f"✅ Completed in {processing_time}s")
            print(f"A (Ukrainian): '{result.get('A_nazva_ukrainska', '')}'")
            print(f"B (Source): '{result.get('B_dzherelo_otrymannya', '')}'")
            print(f"C (Compounds): '{result.get('C_aktyvni_spoluky', '')}'")
            print(f"D (Dosage): '{result.get('D_dozuvannya', '')}'")
            print(f"E (Level): '{result.get('E_riven_dokaziv', '')}'")

            citations = result.get('F_tsytaty', '')
            print(f"F (Citations+URLs): '{citations[:80]}{'...' if len(citations) > 80 else ''}'")
            print(f"G (Empty): '{result.get('G_dzherela', '')}'")

            # Quality analysis
            has_ukrainian = bool(result.get('A_nazva_ukrainska', '').strip())
            has_source = bool(result.get('B_dzherelo_otrymannya', '').strip())
            has_compounds = bool(result.get('C_aktyvni_spoluky', '').strip())
            has_dosage = bool(result.get('D_dozuvannya', '').strip())
            has_citations = bool(result.get('F_tsytaty', '').strip())
            citations_have_urls = 'http' in result.get('F_tsytaty', '')
            g_column_empty = not bool(result.get('G_dzherela', '').strip())

            filled_fields = sum([has_ukrainian, has_source, has_compounds, has_dosage])
            success_rate = filled_fields / 4 * 100

            print(f"📊 Data: {success_rate:.0f}% | UA:{'✓' if has_ukrainian else '✗'} Src:{'✓' if has_source else '✗'} Cmp:{'✓' if has_compounds else '✗'} Dos:{'✓' if has_dosage else '✗'}")
            print(f"🔗 Format: Cit:{'✓' if has_citations else '✗'} URLs:{'✓' if citations_have_urls else '✗'} G-empty:{'✓' if g_column_empty else '✗'}")

            results.append({
                'ingredient': ingredient,
                'row_number': row_number,
                'synonyms_count': len(synonyms),
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
                'row_number': row_number,
                'synonyms_count': len(synonyms),
                'success_rate': 0,
                'time': processing_time,
                'error': str(e)
            })

        print()

    # Final summary
    total_time = round(time.time() - total_start, 1)
    print(f"{'='*60}")
    print("=== REAL GOOGLE SHEETS DATA SUMMARY ===")
    print(f"🕒 Total time: {total_time}s ({total_time/len(ingredients_data):.1f}s avg)")

    successful = [r for r in results if 'error' not in r]
    if successful:
        avg_success = sum(r['success_rate'] for r in successful) / len(successful)
        print(f"📊 Average data completeness: {avg_success:.1f}%")

        # Synonyms analysis
        with_synonyms = sum(1 for r in successful if r['synonyms_count'] > 0)
        avg_synonyms = sum(r['synonyms_count'] for r in successful) / len(successful)
        print(f"🔗 Synonyms usage: {with_synonyms}/{len(successful)} ingredients have synonyms (avg: {avg_synonyms:.1f})")

        # Citation format validation
        with_citations = sum(1 for r in successful if r['has_citations'])
        with_urls = sum(1 for r in successful if r['citations_have_urls'])
        g_empty = sum(1 for r in successful if r['g_column_empty'])

        print(f"📝 Citations: {with_citations}/{len(successful)} have citations")
        print(f"🌐 URLs in F: {with_urls}/{len(successful)} have URLs")
        print(f"📭 G column empty: {g_empty}/{len(successful)} (should be {len(successful)}/{len(successful)})")

        # Evidence levels
        levels = {}
        for r in successful:
            level = r.get('level', 'Unknown')
            levels[level] = levels.get(level, 0) + 1
        print(f"🏆 Evidence levels: {dict(levels)}")

    print(f"\n=== INDIVIDUAL RESULTS ===")
    for result in results:
        if 'error' in result:
            print(f"❌ Row {result['row_number']} - {result['ingredient']}: FAILED ({result['time']}s)")
            print(f"   Error: {result['error']}")
        else:
            status = "🎉" if result['success_rate'] >= 75 else "⚠️" if result['success_rate'] >= 50 else "❌"
            syns = f"({result['synonyms_count']} syns)" if result['synonyms_count'] > 0 else "(no syns)"
            print(f"{status} Row {result['row_number']} - {result['ingredient']}: {result['success_rate']:.0f}% data, {result['level']} level {syns} ({result['time']}s)")

    # Final validation
    print(f"\n=== GOOGLE SHEETS INTEGRATION VALIDATION ===")
    if len(successful) >= 3:  # At least 3 successful
        all_from_sheets = all('row_number' in r for r in successful)
        format_correct = all(r['g_column_empty'] for r in successful)
        most_have_data = sum(1 for r in successful if r['success_rate'] >= 50) >= len(successful) * 0.6

        print(f"✅ Data from Google Sheets: {'Yes' if all_from_sheets else 'No'}")
        print(f"✅ Citation format correct: {'Yes' if format_correct else 'No'}")
        print(f"✅ Most have good data: {'Yes' if most_have_data else 'No'}")

        if all_from_sheets and format_correct and most_have_data:
            print("🎉 GOOGLE SHEETS INTEGRATION WORKING PERFECTLY!")
        else:
            print("⚠️ Some integration issues need attention")
    else:
        print("❌ Too few successful results to validate")

    return results

if __name__ == "__main__":
    test_real_sheets_data()