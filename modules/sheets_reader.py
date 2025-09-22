"""
Google Sheets Reader - читання інгредієнтів з таблиці
"""
import os
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCredentials
import pickle

from config import Config

class SheetsReader:
    """Клас для читання інгредієнтів з Google Sheets"""

    def __init__(self):
        self.service = self._initialize_sheets_service()
        self.spreadsheet_id = Config.SHEET_ID_ING

    def _initialize_sheets_service(self):
        """Ініціалізація Google Sheets API з OAuth"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

            # Шляхи до файлів
            creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
            token_path = os.path.join(os.path.dirname(__file__), '..', 'token_reader.pickle')

            if not os.path.exists(creds_path):
                print(f"[ERROR] Credentials file not found: {creds_path}")
                return None

            creds = None

            # Завантажуємо існуючий токен
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)

            # Якщо немає валідних credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Оновлюємо токен
                    creds.refresh(Request())
                else:
                    # Новий OAuth flow
                    print("[INFO] Starting OAuth authorization for reading...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        creds_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Зберігаємо токен
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

            service = build('sheets', 'v4', credentials=creds)
            print(f"[OK] Google Sheets Reader API initialized")
            return service

        except Exception as e:
            print(f"[ERROR] Failed to initialize Sheets Reader API: {e}")
            return None

    def read_ingredients(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Читає інгредієнти з Google Sheets

        Args:
            limit: Максимальна кількість інгредієнтів (None = всі)

        Returns:
            Список словників з інгредієнтами та синонімами
        """
        try:
            if not self.service:
                print("[ERROR] Sheets service not initialized")
                return []

            # Читаємо стовпчики C (інгредієнти), D (kingdom), E (синоніми), G (посилання)
            range_name = "'Ingredients_Main'!C2:G"  # Читаємо всі рядки без ліміту

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            if not values:
                print("[WARNING] No ingredients found in the sheet")
                return []

            ingredients_data = []

            for i, row in enumerate(values, 2):  # Починаємо з рядка 2
                if len(row) >= 1 and row[0].strip():  # Перевіряємо що є інгредієнт в стовпчику C
                    ingredient = row[0].strip()

                    # Синоніми зі стовпчика E (індекс 2)
                    synonyms = []
                    if len(row) >= 3 and row[2].strip():
                        # Розділяємо синоніми по комі, крапці з комою або новому рядку
                        synonyms_text = row[2].strip()
                        for sep in [',', ';', '\n']:
                            if sep in synonyms_text:
                                synonyms = [s.strip() for s in synonyms_text.split(sep) if s.strip()]
                                break
                        else:
                            synonyms = [synonyms_text] if synonyms_text else []

                    # Опціонально: стовпчик D (kingdom hint)
                    kingdom_hint = None
                    if len(row) >= 2 and row[1].strip():
                        kingdom_hint = row[1].strip()

                    # Стовпчик G (посилання) - індекс 4
                    existing_links = []
                    if len(row) >= 5 and row[4].strip():
                        links_text = row[4].strip()
                        # Розділяємо посилання по комі, крапці з комою або новому рядку
                        for sep in [',', ';', '\n']:
                            if sep in links_text:
                                existing_links = [link.strip() for link in links_text.split(sep) if link.strip() and 'http' in link]
                                break
                        else:
                            if 'http' in links_text:
                                existing_links = [links_text]

                    ingredients_data.append({
                        "ingredient": ingredient,
                        "synonyms": synonyms,
                        "kingdom_hint": kingdom_hint,
                        "existing_links": existing_links,
                        "row_number": i
                    })

                    # Обмеження кількості
                    if limit and len(ingredients_data) >= limit:
                        break

            print(f"[OK] Read {len(ingredients_data)} ingredients from Google Sheets")

            # Показуємо перші кілька для перевірки
            print("[INFO] First 3 ingredients:")
            for i, ing in enumerate(ingredients_data[:3], 1):
                synonyms_str = ', '.join(ing['synonyms'][:2]) if ing['synonyms'] else 'None'
                print(f"  {i}. {ing['ingredient']} (synonyms: {synonyms_str})")

            return ingredients_data

        except Exception as e:
            print(f"[ERROR] Failed to read ingredients: {e}")
            return []

    def get_ingredient_by_row(self, row_number: int) -> Optional[Dict[str, Any]]:
        """
        Читає один інгредієнт з конкретного рядка

        Args:
            row_number: Номер рядка в Google Sheets

        Returns:
            Словник з даними інгредієнта або None
        """
        try:
            if not self.service:
                return None

            range_name = f"'Ingredients_Main'!C{row_number}:G{row_number}"

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            if not values or not values[0]:
                return None

            row = values[0]
            if not row[0].strip():
                return None

            ingredient = row[0].strip()

            # Синоніми
            synonyms = []
            if len(row) >= 3 and row[2].strip():
                synonyms_text = row[2].strip()
                for sep in [',', ';', '\n']:
                    if sep in synonyms_text:
                        synonyms = [s.strip() for s in synonyms_text.split(sep) if s.strip()]
                        break
                else:
                    synonyms = [synonyms_text] if synonyms_text else []

            # Kingdom hint
            kingdom_hint = None
            if len(row) >= 2 and row[1].strip():
                kingdom_hint = row[1].strip()

            # Existing links зі стовпчика G
            existing_links = []
            if len(row) >= 5 and row[4].strip():
                links_text = row[4].strip()
                for sep in [',', ';', '\n']:
                    if sep in links_text:
                        existing_links = [link.strip() for link in links_text.split(sep) if link.strip() and 'http' in link]
                        break
                else:
                    if 'http' in links_text:
                        existing_links = [links_text]

            return {
                "ingredient": ingredient,
                "synonyms": synonyms,
                "kingdom_hint": kingdom_hint,
                "existing_links": existing_links,
                "row_number": row_number
            }

        except Exception as e:
            print(f"[ERROR] Failed to read ingredient from row {row_number}: {e}")
            return None

    def read_ingredients_for_processing(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Alias для read_ingredients для сумісності з launcher
        """
        return self.read_ingredients(limit)

    def get_sheet_info(self) -> Dict[str, Any]:
        """Повертає інформацію про таблицю"""
        try:
            if not self.service:
                return {}

            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            return {
                "title": spreadsheet.get('properties', {}).get('title', 'Unknown'),
                "sheets": [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])],
                "url": f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
            }

        except Exception as e:
            print(f"[ERROR] Failed to get sheet info: {e}")
            return {}

# Global instance
sheets_reader = SheetsReader()