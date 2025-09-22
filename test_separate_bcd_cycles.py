#!/usr/bin/env python3
"""
Test the new separate B/C/D cycles approach according to CLAUDE.md
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

def test_separate_bcd_cycles():
    """Test new B/C/D separate cycles approach"""
    print("=== Testing Separate B/C/D Cycles Approach ===")
    print("According to CLAUDE.md specification:")
    print("- Column B: Gemini search → L1-L4 filter → AI extract source")
    print("- Column C: Gemini search → L1-L4 filter → AI extract compounds")
    print("- Column D: Gemini search → L1-L4 filter → AI extract dosage")
    print("=" * 60)

    # Test with AHCC - використовуємо тільки дані з Google Sheets
    result = pipeline.process_ingredient(
        "AHCC",
        [],  # Синоніми беруться з Google Sheets стовпчика E
        []
    )

    print("\n=== RESULTS ===")
    print(f"A_nazva_ukrainska: '{result.get('A_nazva_ukrainska', '')}'")
    print(f"B_dzherelo_otrymannya: '{result.get('B_dzherelo_otrymannya', '')}'")
    print(f"C_aktyvni_spoluky: '{result.get('C_aktyvni_spoluky', '')}'")
    print(f"D_dozuvannya: '{result.get('D_dozuvannya', '')}'")
    print(f"E_riven_dokaziv: '{result.get('E_riven_dokaziv', '')}'")
    print(f"F_tsytaty: '{result.get('F_tsytaty', '')}'")
    print(f"G_dzherela: '{result.get('G_dzherela', '')}'")

    # Check data quality
    print("\n=== ANALYSIS ===")
    has_source = bool(result.get('B_dzherelo_otrymannya', '').strip())
    has_compounds = bool(result.get('C_aktyvni_spoluky', '').strip())
    has_dosage = bool(result.get('D_dozuvannya', '').strip())
    has_ukrainian_name = bool(result.get('A_nazva_ukrainska', '').strip())

    print(f"✅ Ukrainian name: {'Yes' if has_ukrainian_name else 'No'}")
    print(f"✅ Source material: {'Yes' if has_source else 'No'}")
    print(f"✅ Active compounds: {'Yes' if has_compounds else 'No'}")
    print(f"✅ Dosage: {'Yes' if has_dosage else 'No'}")

    success_rate = sum([has_source, has_compounds, has_dosage, has_ukrainian_name]) / 4 * 100
    print(f"\n📊 Success rate: {success_rate:.1f}%")

    if success_rate >= 75:
        print("🎉 NEW APPROACH WORKING WELL!")
    elif success_rate >= 50:
        print("⚠️  Needs improvements")
    else:
        print("❌ Major issues found")

    return result

if __name__ == "__main__":
    test_separate_bcd_cycles()