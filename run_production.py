#!/usr/bin/env python3
"""
🚀 PRODUCTION RUNNER - DLSD Evidence Collector
Обробка всіх інгредієнтів з Google Sheets з використанням:
- Синонімів зі стовпчика E
- Existing links зі стовпчика G (пріоритет)
- NCBI fallback з реальними даними
- Збереження в Google Sheets
"""
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Налаштування кодування для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sheets_reader import sheets_reader
from processes.pipeline import pipeline
from modules.sheets_writer import sheets_writer

class ProductionRunner:
    """Production runner для обробки всіх інгредієнтів"""

    def __init__(self):
        self.start_time = datetime.now()
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.results_log = []

    def run_production(self, limit: int = None, start_from: int = 1, ai_model: str = None):
        """
        Запуск продакшин обробки

        Args:
            limit: Максимальна кількість інгредієнтів (None = всі)
            start_from: Почати з якого інгредієнта
            ai_model: Конкретна AI модель для тестування (claude/openai/gemini)
        """
        print("DLSD EVIDENCE COLLECTOR - PRODUCTION MODE")
        print("=" * 60)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if limit:
            print(f"Processing: {limit} ingredients (starting from #{start_from})")
        else:
            print(f"Processing: ALL 6,457 ingredients (starting from #{start_from})")

        if ai_model:
            print(f"AI Model: {ai_model.upper()} ONLY")
        else:
            print(f"AI Model: Multi-AI (claude -> openai -> gemini)")

        print("=" * 60)

        # 1. Читаємо інгредієнти з Google Sheets
        print("\nReading ingredients from Google Sheets...")
        ingredients_data = sheets_reader.read_ingredients(limit=limit)

        if not ingredients_data:
            print("ERROR: No ingredients found")
            return

        # Фільтруємо якщо start_from > 1
        if start_from > 1:
            ingredients_data = ingredients_data[start_from-1:]
            print(f"Starting from ingredient #{start_from}")

        print(f"Found {len(ingredients_data)} ingredients")

        # 2. Ініціалізуємо Google Sheets для результатів
        print("\nInitializing Google Sheets for results...")
        if not pipeline.initialize_sheets():
            print("ERROR: Failed to initialize Google Sheets")
            return

        print(f"Google Sheets ready: {sheets_writer.get_sheet_url()}")

        # 3. Обробляємо кожен інгредієнт
        print(f"\nProcessing ingredients...")
        print("-" * 60)

        for i, ing_data in enumerate(ingredients_data, start_from):
            ingredient = ing_data.get("ingredient", "")
            synonyms = ing_data.get("synonyms", [])
            existing_links = ing_data.get("existing_links", [])

            try:
                self._process_single_ingredient(i, ingredient, synonyms, existing_links, len(ingredients_data) + start_from - 1, ai_model)

                # Progress save кожні 10 інгредієнтів
                if self.processed_count % 10 == 0:
                    self._save_progress()

                # Невелика пауза між інгредієнтами
                time.sleep(1)

            except KeyboardInterrupt:
                print(f"\nINTERRUPTED by user")
                break
            except Exception as e:
                print(f"\nCRITICAL ERROR processing {ingredient}: {e}")
                self.error_count += 1

        # 4. Фінальний звіт
        self._print_final_report()
        self._save_final_results()

    def _process_single_ingredient(self, index: int, ingredient: str, synonyms: List[str], existing_links: List[str], total: int, ai_model: str = None):
        """Обробка одного інгредієнта"""

        print(f"\n[{index}/{total}] Processing: {ingredient}")

        if synonyms:
            print(f"   Synonyms: {', '.join(synonyms[:3])}{'...' if len(synonyms) > 3 else ''}")

        if existing_links:
            print(f"   Existing links: {len(existing_links)} links from column G")

        # Запускаємо pipeline
        start_time = time.time()

        try:
            # Передаємо ai_model до pipeline якщо вказано
            if ai_model:
                result = pipeline.process_ingredient(ingredient, synonyms, existing_links=existing_links, ai_model=ai_model)
            else:
                result = pipeline.process_ingredient(ingredient, synonyms, existing_links=existing_links)

            # Аналізуємо результат з новою A-G структурою
            # C: Активні сполуки тепер є строкою, не списком
            compounds_text = result.get('C_aktyvni_spoluky', '')
            compounds_count = len(compounds_text.split(',')) if compounds_text else 0

            # D: Дозування
            has_dose = bool(result.get('D_dozuvannya', ''))

            # F: Цитати тепер є строкою, не списком
            citations_text = result.get('F_tsytaty', '')
            citations_count = len(citations_text.split(';')) if citations_text else 0

            processing_time = round(time.time() - start_time, 1)

            if compounds_count > 0 or has_dose:
                status = "SUCCESS"
                self.success_count += 1
            else:
                status = "NO DATA"

            print(f"   {status}: {compounds_count} compounds, dose: {'Yes' if has_dose else 'No'}, {citations_count} citations ({processing_time}s)")

            # Логуємо результат
            self.results_log.append({
                "index": index,
                "ingredient": ingredient,
                "compounds": compounds_count,
                "has_dose": has_dose,
                "citations": citations_count,
                "processing_time": processing_time,
                "status": "success" if (compounds_count > 0 or has_dose) else "no_data",
                "synonyms_used": len(synonyms),
                "existing_links_used": len(existing_links)
            })

        except Exception as e:
            print(f"   ERROR: {str(e)[:100]}")
            self.error_count += 1

            self.results_log.append({
                "index": index,
                "ingredient": ingredient,
                "error": str(e),
                "status": "error"
            })

        self.processed_count += 1

    def _save_progress(self):
        """Зберігає проміжний прогрес"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress_file = f"output/production_progress_{timestamp}.json"

        os.makedirs("output", exist_ok=True)

        progress_data = {
            "timestamp": timestamp,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "runtime": str(datetime.now() - self.start_time),
            "results": self.results_log[-10:]  # Останні 10 результатів
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)

    def _print_final_report(self):
        """Виводить фінальний звіт"""
        end_time = datetime.now()
        total_time = end_time - self.start_time

        print(f"\nPRODUCTION COMPLETED")
        print("=" * 60)
        print(f"Total processed: {self.processed_count}")
        print(f"Success: {self.success_count} ({round(self.success_count/max(1,self.processed_count)*100, 1)}%)")
        print(f"No data: {self.processed_count - self.success_count - self.error_count}")
        print(f"Errors: {self.error_count} ({round(self.error_count/max(1,self.processed_count)*100, 1)}%)")
        print(f"Total time: {total_time}")
        print(f"Google Sheets: {sheets_writer.get_sheet_url()}")
        print("=" * 60)

        # Топ успішних інгредієнтів
        successful = [r for r in self.results_log if r.get("status") == "success"]
        if successful:
            print(f"\nTOP SUCCESSFUL INGREDIENTS:")
            for r in sorted(successful, key=lambda x: x.get("compounds", 0) + (1 if x.get("has_dose") else 0), reverse=True)[:5]:
                print(f"   {r['index']}. {r['ingredient']} - {r['compounds']} compounds, dose: {'Yes' if r['has_dose'] else 'No'}")

    def _save_final_results(self):
        """Зберігає фінальні результати"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_file = f"output/PRODUCTION_RESULTS_{timestamp}.json"

        os.makedirs("output", exist_ok=True)

        final_data = {
            "production_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_processed": self.processed_count,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "success_rate": round(self.success_count/max(1,self.processed_count)*100, 2)
            },
            "system_config": {
                "uses_synonyms": True,
                "uses_existing_links": True,
                "ncbi_fallback": True,
                "ai_models": ["claude", "openai", "gemini"],
                "saves_to_sheets": True
            },
            "detailed_results": self.results_log,
            "sheets_url": sheets_writer.get_sheet_url()
        }

        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved: {final_file}")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='DLSD Evidence Collector - Production Run')
    parser.add_argument('--limit', type=int, help='Maximum number of ingredients to process')
    parser.add_argument('--start-from', type=int, default=1, help='Start from ingredient number')
    parser.add_argument('--test', action='store_true', help='Run test with first 10 ingredients')
    parser.add_argument('--ai-model', choices=['claude', 'openai', 'gemini'], help='Use specific AI model only')

    args = parser.parse_args()

    if args.test:
        args.limit = 10
        print("TEST MODE: Processing first 10 ingredients")

    runner = ProductionRunner()
    runner.run_production(limit=args.limit, start_from=args.start_from, ai_model=args.ai_model)

if __name__ == "__main__":
    main()