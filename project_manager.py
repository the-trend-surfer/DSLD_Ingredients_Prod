#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 DLSD PROJECT MANAGER
Комплексна система управління проєктом з:
- Resume capability (продовження з місця зупинки)
- Range processing (діапазони рядків)
- Real-time dashboard
- Error handling та retry
- Interactive CLI control
"""
import sys
import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse

# Налаштування кодування для Windows
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except AttributeError:
        # Вже налаштовано або не потрібно
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sheets_reader import sheets_reader
from processes.pipeline import pipeline
from modules.sheets_writer import sheets_writer

@dataclass
class ProjectState:
    """Стан проєкту для збереження та відновлення"""
    project_id: str
    start_time: str
    total_ingredients: int
    current_index: int
    start_row: int
    end_row: int
    processed_count: int
    success_count: int
    error_count: int
    skipped_count: int
    ai_model: str
    failed_ingredients: List[Dict[str, Any]]
    successful_ingredients: List[Dict[str, Any]]
    last_update: str
    estimated_time_remaining: Optional[float] = None
    average_time_per_ingredient: Optional[float] = None

class ProjectManager:
    """Головний менеджер проєкту з dashboard та контролем помилок"""

    def __init__(self):
        self.state_file = "project_state.json"
        self.state: Optional[ProjectState] = None
        self.dashboard_running = False
        self.dashboard_thread = None

    def create_new_project(self, start_row: int, end_row: int, ai_model: str = "openai") -> str:
        """Створення нового проєкту"""
        project_id = f"DLSD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Читаємо загальну кількість інгредієнтів
        print("📋 Reading ingredients from Google Sheets...")
        try:
            ingredients = sheets_reader.read_ingredients_for_processing()
            total_ingredients = len(ingredients)
        except Exception as e:
            print(f"❌ Failed to read ingredients: {e}")
            return None

        # Валідація діапазону
        if end_row > total_ingredients:
            end_row = total_ingredients
            print(f"⚠️  Adjusted end_row to {end_row} (max available)")

        if start_row > end_row:
            print(f"❌ Invalid range: start_row ({start_row}) > end_row ({end_row})")
            return None

        # Створюємо стан проєкту
        self.state = ProjectState(
            project_id=project_id,
            start_time=datetime.now().isoformat(),
            total_ingredients=total_ingredients,
            current_index=start_row - 1,  # 0-based index
            start_row=start_row,
            end_row=end_row,
            processed_count=0,
            success_count=0,
            error_count=0,
            skipped_count=0,
            ai_model=ai_model,
            failed_ingredients=[],
            successful_ingredients=[],
            last_update=datetime.now().isoformat()
        )

        self.save_state()

        print(f"✅ Created new project: {project_id}")
        print(f"📊 Range: rows {start_row}-{end_row} ({end_row - start_row + 1} ingredients)")
        print(f"🤖 AI Model: {ai_model}")

        return project_id

    def load_existing_project(self) -> bool:
        """Завантаження існуючого проєкту"""
        if not os.path.exists(self.state_file):
            return False

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                self.state = ProjectState(**state_data)

            print(f"✅ Loaded existing project: {self.state.project_id}")
            print(f"📊 Progress: {self.state.processed_count}/{self.state.end_row - self.state.start_row + 1}")
            print(f"✅ Success: {self.state.success_count}")
            print(f"❌ Errors: {self.state.error_count}")
            print(f"⏸️  Last update: {self.state.last_update}")

            return True

        except Exception as e:
            print(f"❌ Failed to load project state: {e}")
            return False

    def save_state(self):
        """Збереження стану проєкту"""
        if not self.state:
            return

        self.state.last_update = datetime.now().isoformat()

        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.state), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Failed to save state: {e}")

    def calculate_stats(self) -> Dict[str, Any]:
        """Розрахунок статистики проєкту"""
        if not self.state:
            return {}

        start_time = datetime.fromisoformat(self.state.start_time)
        current_time = datetime.now()
        elapsed_time = current_time - start_time

        # Середній час на інгредієнт
        if self.state.processed_count > 0:
            avg_time = elapsed_time.total_seconds() / self.state.processed_count
            self.state.average_time_per_ingredient = avg_time

            # Оцінка часу, що залишився
            remaining_items = (self.state.end_row - self.state.start_row + 1) - self.state.processed_count
            if remaining_items > 0:
                estimated_remaining = remaining_items * avg_time
                self.state.estimated_time_remaining = estimated_remaining
            else:
                self.state.estimated_time_remaining = 0
        else:
            self.state.average_time_per_ingredient = None
            self.state.estimated_time_remaining = None

        return {
            "elapsed_time": elapsed_time,
            "avg_time_per_ingredient": self.state.average_time_per_ingredient,
            "estimated_remaining": self.state.estimated_time_remaining,
            "success_rate": (self.state.success_count / max(1, self.state.processed_count)) * 100,
            "error_rate": (self.state.error_count / max(1, self.state.processed_count)) * 100,
            "progress_percentage": (self.state.processed_count / max(1, self.state.end_row - self.state.start_row + 1)) * 100
        }

    def start_dashboard(self, mode="console"):
        """Запуск real-time dashboard в окремому потоці"""
        if mode == "web":
            # Запуск веб-dashboard
            try:
                from simple_web_dashboard import SimpleDashboardServer
                self.web_dashboard = SimpleDashboardServer()
                dashboard_url = self.web_dashboard.start_server()
                print(f"🌐 Web dashboard started: {dashboard_url}")
                return dashboard_url
            except Exception as e:
                print(f"⚠️  Web dashboard error: {e}, falling back to console")
                mode = "console"

        if mode == "console":
            # Консольний dashboard
            self.dashboard_running = True
            self.dashboard_thread = threading.Thread(target=self._dashboard_loop, daemon=True)
            self.dashboard_thread.start()

    def stop_dashboard(self):
        """Зупинка dashboard"""
        # Зупинка консольного dashboard
        self.dashboard_running = False
        if self.dashboard_thread:
            self.dashboard_thread.join(timeout=1)

        # Зупинка веб-dashboard
        if hasattr(self, 'web_dashboard'):
            self.web_dashboard.stop_server()

    def _dashboard_loop(self):
        """Основний цикл dashboard"""
        while self.dashboard_running:
            try:
                self._display_dashboard()
                time.sleep(5)  # Оновлення кожні 5 секунд
            except Exception as e:
                print(f"Dashboard error: {e}")
                time.sleep(10)

    def _display_dashboard(self):
        """Відображення dashboard"""
        if not self.state:
            return

        stats = self.calculate_stats()

        # Очищення екрану (Windows/Unix compatible)
        os.system('cls' if os.name == 'nt' else 'clear')

        print("🎯 DLSD PROJECT MANAGER - REAL-TIME DASHBOARD")
        print("=" * 70)
        print(f"📊 Project: {self.state.project_id}")
        print(f"🤖 AI Model: {self.state.ai_model}")
        print(f"📅 Started: {datetime.fromisoformat(self.state.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)

        # Progress bar
        progress = stats.get("progress_percentage", 0)
        bar_length = 40
        filled_length = int(bar_length * progress // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"📈 Progress: [{bar}] {progress:.1f}%")

        print("-" * 70)
        print(f"📋 Range: rows {self.state.start_row}-{self.state.end_row}")
        print(f"🔢 Total items: {self.state.end_row - self.state.start_row + 1}")
        print(f"✅ Processed: {self.state.processed_count}")
        print(f"🎯 Successful: {self.state.success_count} ({stats.get('success_rate', 0):.1f}%)")
        print(f"❌ Errors: {self.state.error_count} ({stats.get('error_rate', 0):.1f}%)")
        print(f"⏭️  Skipped: {self.state.skipped_count}")

        print("-" * 70)

        # Timing info
        elapsed = stats.get("elapsed_time")
        if elapsed:
            print(f"⏱️  Elapsed: {str(elapsed).split('.')[0]}")

        if stats.get("avg_time_per_ingredient"):
            avg_time = timedelta(seconds=stats["avg_time_per_ingredient"])
            print(f"⚡ Avg time/item: {str(avg_time).split('.')[0]}")

        if stats.get("estimated_remaining"):
            remaining = timedelta(seconds=stats["estimated_remaining"])
            eta = datetime.now() + remaining
            print(f"⏰ Estimated remaining: {str(remaining).split('.')[0]}")
            print(f"🎯 ETA: {eta.strftime('%Y-%m-%d %H:%M:%S')}")

        print("-" * 70)

        # Recent activity
        if self.state.successful_ingredients:
            recent_success = self.state.successful_ingredients[-3:]
            print("🟢 Recent successes:")
            for item in recent_success:
                print(f"   ✅ {item.get('ingredient', 'Unknown')}")

        if self.state.failed_ingredients:
            recent_failures = self.state.failed_ingredients[-3:]
            print("🔴 Recent failures:")
            for item in recent_failures:
                print(f"   ❌ {item.get('ingredient', 'Unknown')}: {item.get('error', 'Unknown error')}")

        print("-" * 70)
        print("💡 Press Ctrl+C to stop processing")
        print(f"📝 State auto-saved at: {self.state.last_update}")

    def process_ingredients(self, resume: bool = False) -> Dict[str, Any]:
        """Основна функція обробки інгредієнтів"""
        if not self.state:
            print("❌ No project state found. Create a new project first.")
            return None

        print(f"🚀 Starting ingredient processing...")
        print(f"📊 Will process rows {self.state.start_row}-{self.state.end_row}")

        # Запуск dashboard (веб за замовчуванням)
        self.start_dashboard(mode="web")

        try:
            # Читаємо інгредієнти
            ingredients = sheets_reader.read_ingredients_for_processing()

            # Ініціалізуємо Google Sheets для результатів
            if not pipeline.initialize_sheets():
                print("⚠️  Google Sheets not available - results will only be returned in memory")
            else:
                print(f"✅ Results will be written to: {sheets_writer.get_sheet_url()}")

            # Обробка інгредієнтів у заданому діапазоні
            for i in range(self.state.current_index, min(self.state.end_row, len(ingredients))):
                ingredient_data = ingredients[i]
                ingredient_name = ingredient_data.get("ingredient", f"Row {i+1}")

                print(f"\n[{i+1}/{self.state.end_row}] Processing: {ingredient_name}")

                try:
                    # Обробка через pipeline
                    result = pipeline.process_ingredient(
                        ingredient_data.get("ingredient", ""),
                        ingredient_data.get("synonyms", []),
                        ingredient_data.get("kingdom_hint"),
                        ingredient_data.get("existing_links", []),
                        self.state.ai_model
                    )

                    # Аналізуємо результат
                    if self._is_successful_result(result):
                        self.state.success_count += 1
                        self.state.successful_ingredients.append({
                            "ingredient": ingredient_name,
                            "row": i + 1,
                            "compounds": len(result.get("aktyvni_spoluky", [])),
                            "has_dose": result.get("dobova_norma", "") != "немає даних",
                            "citations": len(result.get("dzherela_tsytaty", []))
                        })
                        print(f"✅ SUCCESS: {ingredient_name}")
                    else:
                        self.state.error_count += 1
                        error_msg = self._extract_error_message(result)
                        self.state.failed_ingredients.append({
                            "ingredient": ingredient_name,
                            "row": i + 1,
                            "error": error_msg,
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"❌ FAILED: {ingredient_name} - {error_msg}")

                except Exception as e:
                    self.state.error_count += 1
                    error_msg = str(e)
                    self.state.failed_ingredients.append({
                        "ingredient": ingredient_name,
                        "row": i + 1,
                        "error": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"💥 EXCEPTION: {ingredient_name} - {error_msg}")

                # Оновлюємо стан
                self.state.processed_count += 1
                self.state.current_index = i + 1
                self.save_state()

        except KeyboardInterrupt:
            print(f"\n⏸️  Processing interrupted by user")
            print(f"📊 Processed: {self.state.processed_count} ingredients")
            print(f"✅ Successful: {self.state.success_count}")
            print(f"❌ Failed: {self.state.error_count}")

        finally:
            self.stop_dashboard()

        # Підсумок
        final_stats = self.calculate_stats()
        self._display_final_summary(final_stats)

        return {
            "project_id": self.state.project_id,
            "processed": self.state.processed_count,
            "successful": self.state.success_count,
            "failed": self.state.error_count,
            "stats": final_stats
        }

    def _is_successful_result(self, result: Dict[str, Any]) -> bool:
        """Перевірка чи результат успішний"""
        if not result:
            return False

        # Перевіряємо наявність ключових даних
        has_compounds = len(result.get("aktyvni_spoluky", [])) > 0
        has_dose_info = result.get("dobova_norma", "") != "немає даних"
        has_citations = len(result.get("dzherela_tsytaty", [])) > 0

        # Успішним вважаємо якщо є хоча б compounds або dose
        return has_compounds or has_dose_info

    def _extract_error_message(self, result: Dict[str, Any]) -> str:
        """Витягування повідомлення про помилку"""
        if not result:
            return "No result returned"

        # Шукаємо в різних місцях
        error_sources = [
            result.get("error"),
            result.get("log", {}).get("notes"),
            result.get("pipeline_metadata", {}).get("error"),
            "Processing completed but no useful data found"
        ]

        for error in error_sources:
            if error:
                return str(error)

        return "Unknown error"

    def _display_final_summary(self, stats: Dict[str, Any]):
        """Відображення фінального підсумку"""
        print("\n" + "=" * 70)
        print("🏁 PROCESSING COMPLETED")
        print("=" * 70)
        print(f"📊 Project: {self.state.project_id}")
        print(f"📅 Started: {datetime.fromisoformat(self.state.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏁 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        elapsed = stats.get("elapsed_time")
        if elapsed:
            print(f"⏱️  Total time: {str(elapsed).split('.')[0]}")

        print("-" * 70)
        print(f"📋 Range processed: rows {self.state.start_row}-{self.state.end_row}")
        print(f"✅ Successful: {self.state.success_count} ({stats.get('success_rate', 0):.1f}%)")
        print(f"❌ Failed: {self.state.error_count} ({stats.get('error_rate', 0):.1f}%)")
        print(f"📊 Total processed: {self.state.processed_count}")

        if stats.get("avg_time_per_ingredient"):
            avg_time = timedelta(seconds=stats["avg_time_per_ingredient"])
            print(f"⚡ Average time per ingredient: {str(avg_time).split('.')[0]}")

        print("-" * 70)

        # Збереження результатів
        results_file = f"output/PROJECT_RESULTS_{self.state.project_id}.json"
        try:
            os.makedirs("output", exist_ok=True)
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "project_summary": asdict(self.state),
                    "final_stats": stats,
                    "completion_time": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")

        if sheets_writer.get_sheet_url():
            print(f"📊 Google Sheets: {sheets_writer.get_sheet_url()}")

        print("=" * 70)

def interactive_cli():
    """Інтерактивний CLI для управління проєктом"""
    manager = ProjectManager()

    print("🎯 DLSD PROJECT MANAGER")
    print("=" * 50)

    # Перевіряємо чи є існуючий проєкт
    has_existing = manager.load_existing_project()

    if has_existing:
        print("\n📋 EXISTING PROJECT FOUND")
        print("-" * 30)
        choice = input("Choose action:\n"
                      "1. Resume existing project\n"
                      "2. View project status\n"
                      "3. Start new project\n"
                      "4. Exit\n"
                      "Enter choice (1-4): ").strip()

        if choice == "1":
            print(f"🔄 Resuming project {manager.state.project_id}...")
            return manager.process_ingredients(resume=True)
        elif choice == "2":
            manager.start_dashboard()
            input("\nPress Enter to stop dashboard...")
            manager.stop_dashboard()
            return
        elif choice == "3":
            pass  # Continue to new project creation
        elif choice == "4":
            return
        else:
            print("❌ Invalid choice")
            return

    # Створення нового проєкту
    print("\n🆕 CREATE NEW PROJECT")
    print("-" * 30)

    try:
        start_row = int(input("Enter start row (default 1): ") or "1")
        end_row = int(input("Enter end row (default 100): ") or "100")

        print("\nAvailable AI models:")
        print("1. openai (recommended)")
        print("2. claude")
        print("3. gemini")
        model_choice = input("Choose AI model (1-3, default 1): ").strip() or "1"

        model_map = {"1": "openai", "2": "claude", "3": "gemini"}
        ai_model = model_map.get(model_choice, "openai")

        project_id = manager.create_new_project(start_row, end_row, ai_model)
        if project_id:
            print(f"\n🚀 Starting processing...")
            return manager.process_ingredients()
        else:
            print("❌ Failed to create project")

    except ValueError:
        print("❌ Invalid input. Please enter valid numbers.")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

def main():
    """Головна функція з підтримкою CLI аргументів"""
    parser = argparse.ArgumentParser(description="DLSD Project Manager")
    parser.add_argument("--start", type=int, help="Start row (1-based)")
    parser.add_argument("--end", type=int, help="End row (1-based)")
    parser.add_argument("--model", choices=["openai", "claude", "gemini"],
                       default="openai", help="AI model to use")
    parser.add_argument("--resume", action="store_true", help="Resume existing project")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--dashboard", choices=["console", "web"], default="web", help="Dashboard type")
    parser.add_argument("--dashboard-only", action="store_true", help="Show dashboard only")

    args = parser.parse_args()

    manager = ProjectManager()

    if args.dashboard_only:
        # Тільки dashboard
        if manager.load_existing_project():
            manager.start_dashboard(mode=args.dashboard)
            try:
                input("Press Enter to stop dashboard...")
            except KeyboardInterrupt:
                pass
            manager.stop_dashboard()
        else:
            print("❌ No existing project found")
        return

    if args.interactive or (not args.start and not args.end and not args.resume):
        # Інтерактивний режим
        return interactive_cli()

    if args.resume:
        # Відновлення існуючого проєкту
        if manager.load_existing_project():
            return manager.process_ingredients(resume=True)
        else:
            print("❌ No existing project found to resume")
            return

    if args.start and args.end:
        # Прямий запуск з параметрами
        project_id = manager.create_new_project(args.start, args.end, args.model)
        if project_id:
            return manager.process_ingredients()
        else:
            print("❌ Failed to create project")

    else:
        print("❌ Please specify --start and --end, or use --interactive mode")
        parser.print_help()

if __name__ == "__main__":
    main()