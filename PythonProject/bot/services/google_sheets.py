        import os
        import json
        from datetime import datetime

        # Импорты Google — только если реально используется
        service = None
        if os.getenv('GOOGLE_SHEET_ID') and os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY'):
            try:
                from google.oauth2.service_account import Credentials
                from googleapiclient.discovery import build
                SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
                creds_json = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY'))
                credentials = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
                service = build('sheets', 'v4', credentials=credentials)
            except Exception as e:
                print(f"⚠️ Ошибка инициализации Google Sheets: {e}")

        def find_row_by_request_id(request_id: str):
            """Найти строку по ID заявки в столбце A"""
            if not service:
                return None
            try:
                sheet = service.spreadsheets()
                result = sheet.values().get(
                    spreadsheetId=os.getenv('GOOGLE_SHEET_ID'),
                    range=f"{os.getenv('GOOGLE_SHEET_NAME', 'Заявки')}!A:A"
                ).execute()
                values = result.get('values', [])
                for i, row in enumerate(values):
                    if row and row[0] == request_id:
                        return i + 1
                return None
            except Exception as e:
                print(f"Ошибка поиска строки: {e}")
                return None

        def update_sheet_row(request_ dict):
            if not service:
                return
            row_index = find_row_by_request_id(request_data['id'])
            if not row_index:
                append_new_request_to_sheet(request_data)
                return

            row = [
                request_data.get('id', ''),
                request_data.get('first_name', ''),
                request_data.get('last_name', ''),
                request_data.get('group', ''),
                request_data.get('purpose', ''),
                request_data.get('file_name', ''),
                request_data.get('status', ''),
                request_data.get('comment', ''),
                request_data.get('date', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]

            sheet = service.spreadsheets()
            range_name = f"{os.getenv('GOOGLE_SHEET_NAME', 'Заявки')}!A{row_index}:J{row_index}"
            try:
                sheet.values().update(
                    spreadsheetId=os.getenv('GOOGLE_SHEET_ID'),
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body={"values": [row]}
                ).execute()
                _update_row_color(row_index, request_data.get('status', ''))
            except Exception as e:
                print(f"Ошибка обновления строки: {e}")

        def append_new_request_to_sheet(request_ dict):
            if not service:
                return
            row = [
                request_data.get('id', ''),
                request_data.get('first_name', ''),
                request_data.get('last_name', ''),
                request_data.get('group', ''),
                request_data.get('purpose', ''),
                request_data.get('file_name', ''),
                request_data.get('status', 'В очереди'),
                request_data.get('comment', ''),
                request_data.get('date', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            try:
                sheet = service.spreadsheets()
                sheet.values().append(
                    spreadsheetId=os.getenv('GOOGLE_SHEET_ID'),
                    range=f"{os.getenv('GOOGLE_SHEET_NAME', 'Заявки')}!A:J",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [row]}
                ).execute()
                row_index = find_row_by_request_id(request_data['id'])
                if row_index:
                    _update_row_color(row_index, request_data.get('status', 'В очереди'))
            except Exception as e:
                print(f"Ошибка добавления заявки в таблицу: {e}")

        def _update_row_color(row_index: int, status: str):
            if not service:
                return
            color = {
                "В очереди": {"red": 1.0, "green": 1.0, "blue": 0.8},
                "В работе": {"red": 1.0, "green": 0.92, "blue": 0.0},
                "Готово": {"red": 0.85, "green": 1.0, "blue": 0.85},
                "Архив": {"red": 0.93, "green": 0.93, "blue": 0.93},
            }.get(status, {"red": 1.0, "green": 1.0, "blue": 1.0})

            requests = [{
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": row_index - 1,
                        "endRowIndex": row_index,
                        "startColumnIndex": 0,
                        "endColumnIndex": 10
                    },
                    "cell": {"userEnteredFormat": {"backgroundColor": color}},
                    "fields": "userEnteredFormat.backgroundColor"
                }
            }]
            try:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=os.getenv('GOOGLE_SHEET_ID'),
                    body={"requests": requests}
                ).execute()
            except Exception as e:
                print(f"Ошибка раскраски: {e}")