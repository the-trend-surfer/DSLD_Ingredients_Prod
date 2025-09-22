"""
Google Sheets Writer - запис результатів у таблицю
"""
import os
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCredentials
import pickle
from datetime import datetime

from config import Config

class SheetsWriter:
    """Клас для запису результатів у Google Sheets"""

    def __init__(self):
        self.service = self._initialize_sheets_service()
        self.spreadsheet_id = Config.SHEET_ID_ING
        self.results_sheet_name = "Results_Table"

    def _initialize_sheets_service(self):
        """Ініціалізація Google Sheets API з OAuth"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

            # Шляхи до файлів
            creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
            token_path = os.path.join(os.path.dirname(__file__), '..', 'token.pickle')

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
                    print("[INFO] Starting OAuth authorization...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        creds_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Зберігаємо токен
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

            service = build('sheets', 'v4', credentials=creds)
            print(f"[OK] Google Sheets API initialized with OAuth")
            return service

        except Exception as e:
            print(f"[ERROR] Failed to initialize Sheets API: {e}")
            return None

    def create_results_sheet(self) -> bool:
        """Створює новий аркуш для результатів якщо не існує"""
        try:
            if not self.service:
                return False

            # Перевіряємо чи існує аркуш
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

            if self.results_sheet_name not in sheet_names:
                # Створюємо новий аркуш
                requests = [{
                    'addSheet': {
                        'properties': {
                            'title': self.results_sheet_name,
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 7  # A-G стовпчики згідно CLAUDE.md
                            }
                        }
                    }
                }]

                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()

                print(f"[OK] Created new sheet: {self.results_sheet_name}")

                # Додаємо заголовки
                self._write_headers()

            return True

        except Exception as e:
            print(f"[ERROR] Failed to create results sheet: {e}")
            return False

    def _write_headers(self):
        """Записує заголовки стовпчиків згідно CLAUDE.md структури"""
        headers = [
            "A: Назва українською",           # A: Ukrainian (English)
            "B: Джерело отримання",          # B: Source material
            "C: Активні сполуки",            # C: Active compounds
            "D: Дозування",                  # D: Dosage
            "E: Рівень доказів",             # E: Evidence level
            "F: Цитати",                     # F: Citations
            "G: Джерела"                     # G: Sources URLs
        ]

        try:
            range_name = f"{self.results_sheet_name}!A1:G1"

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()

            print(f"[OK] Headers written to {self.results_sheet_name}")

        except Exception as e:
            print(f"[ERROR] Failed to write headers: {e}")

    def write_table_result(self, table_data: Dict[str, Any], row_number: Optional[int] = None) -> bool:
        """
        Записує результат таблиці в Google Sheets

        Args:
            table_data: Дані у форматі таблиці
            row_number: Номер рядка (якщо None - додає в кінець)

        Returns:
            True якщо успішно записано
        """
        try:
            if not self.service:
                print("[ERROR] Sheets service not initialized")
                return False

            # Підготовуємо дані для запису
            row_data = self._prepare_row_data(table_data)

            if row_number is None:
                # Знаходимо перший порожній рядок
                row_number = self._find_next_empty_row()

            # Записуємо дані
            range_name = f"{self.results_sheet_name}!A{row_number}:G{row_number}"

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [row_data]}
            ).execute()

            ingredient = table_data.get('ingredient', table_data.get('A_nazva_ukrainska', 'Unknown'))
            print(f"[OK] Written {ingredient} to row {row_number}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to write table result: {e}")
            return False

    def _prepare_row_data(self, table_data: Dict[str, Any]) -> List[str]:
        """Підготовує дані рядка для запису згідно CLAUDE.md структури A-G"""

        # A: Назва українською (Ukrainian (English))
        a_nazva = table_data.get('A_nazva_ukrainska', '')

        # B: Джерело отримання
        b_dzherelo = table_data.get('B_dzherelo_otrymannya', '')

        # C: Активні сполуки
        c_spoluky = table_data.get('C_aktyvni_spoluky', '')

        # D: Дозування
        d_dozuvannya = table_data.get('D_dozuvannya', '')

        # E: Рівень доказів (L1/L2/L3/L4)
        e_riven = table_data.get('E_riven_dokaziv', '')

        # F: Цитати (точні фрази з статей)
        f_tsytaty = table_data.get('F_tsytaty', '')

        # G: Джерела (URL наукових джерел)
        g_dzherela = table_data.get('G_dzherela', '')

        return [a_nazva, b_dzherelo, c_spoluky, d_dozuvannya, e_riven, f_tsytaty, g_dzherela]

    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Форматує цитати для стовпчика (deprecated - now handled by pipeline directly)"""
        # This method is now deprecated since pipeline handles citation formatting
        # But kept for backward compatibility
        if isinstance(citations, str):
            return citations
        if not citations or not any(c.get('quote') for c in citations):
            return ''

        formatted = []
        for i, citation in enumerate(citations[:3], 1):  # Максимум 3 цитати
            quote = citation.get('quote', '')
            url = citation.get('url', '')
            if quote and quote != 'немає релевантних даних':
                # Якщо URL відсутній або є placeholder, не показуємо його
                if url and url != 'немає даних' and url != '' and 'http' in url:
                    formatted.append(f"{i}. \"{quote}\" ({url})")
                else:
                    formatted.append(f"{i}. \"{quote}\" (немає посилання)")

        return '\n'.join(formatted) if formatted else ''

    def _find_next_empty_row(self) -> int:
        """Знаходить наступний порожній рядок"""
        try:
            # Читаємо всі дані з стовпчика A
            range_name = f"{self.results_sheet_name}!A:A"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            return len(values) + 1  # +1 бо рядки починаються з 1

        except Exception as e:
            print(f"[ERROR] Failed to find empty row: {e}")
            return 2  # Default to row 2 if error

    def write_batch_results(self, results: List[Dict[str, Any]]) -> int:
        """
        Записує пакет результатів

        Args:
            results: Список результатів таблиці

        Returns:
            Кількість успішно записаних результатів
        """
        written_count = 0

        for result in results:
            if self.write_table_result(result):
                written_count += 1

        print(f"[BATCH] Written {written_count}/{len(results)} results to {self.results_sheet_name}")
        return written_count

    def get_sheet_url(self) -> str:
        """Повертає URL аркуша з результатами"""
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit#gid=0"

# Global instance
sheets_writer = SheetsWriter()