import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class LocalDatabase:
    def __init__(self, db_file='data/requests.json', archive_file='data/archive.json'):
        self.db_file = db_file
        self.archive_file = archive_file
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        if not os.path.exists(self.db_file):
            self._save_data([])
        if not os.path.exists(self.archive_file):
            self._save_archive([])
    
    def _load_data(self) -> List[Dict]:
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, data: List[Dict]):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_archive(self) -> List[Dict]:
        try:
            with open(self.archive_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_archive(self, data: List[Dict]):
        with open(self.archive_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_request(self, request_data: Dict):
        data = self._load_data()
        request = {
            'id': request_data.get('id', ''),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'first_name': request_data.get('first_name', ''),
            'last_name': request_data.get('last_name', ''),
            'group': request_data.get('group', ''),
            'purpose': request_data.get('purpose', ''),
            'status': 'В очереди',
            'file_name': request_data.get('file_name', ''),
            'file_path': request_data.get('file_path', ''),
            'telegram_id': request_data.get('telegram_id', ''),
            'username': request_data.get('username', ''),
            'comment': '',
            'completed_date': None
        }
        data.append(request)
        self._save_data(data)
    
    def update_status(self, request_id: str, new_status: str) -> bool:
        data = self._load_data()
        for request in data:
            if request.get('id') == request_id:
                request['status'] = new_status
                self._save_data(data)
                return True
        return False
    
    def get_all_requests(self) -> List[Dict]:
        return self._load_data()
    
    def get_pending_requests(self) -> List[Dict]:
        data = self._load_data()
        return [r for r in data if r.get('status') == 'В очереди']
    
    def get_in_progress_requests(self) -> List[Dict]:
        data = self._load_data()
        return [r for r in data if r.get('status') == 'В работе']
    
    def get_completed_requests(self) -> List[Dict]:
        data = self._load_data()
        return [r for r in data if r.get('status') == 'Готово']
    
    def get_pending_count(self) -> int:
        return len(self.get_pending_requests())
    
    def get_request_by_id(self, request_id: str) -> Optional[Dict]:
        data = self._load_data()
        for request in data:
            if request.get('id') == request_id:
                return request
        return None
    
    def delete_request(self, request_id: str) -> bool:
        data = self._load_data()
        original_len = len(data)
        data = [r for r in data if r.get('id') != request_id]
        if len(data) < original_len:
            self._save_data(data)
            return True
        return False
    
    def add_comment(self, request_id: str, comment: str) -> bool:
        """Добавить комментарий к заявке"""
        data = self._load_data()
        for request in data:
            if request.get('id') == request_id:
                request['comment'] = comment
                self._save_data(data)
                return True
        return False
    
    def archive_request(self, request_id: str) -> bool:
        """Переместить заявку в архив"""
        data = self._load_data()
        archive = self._load_archive()
        
        for i, request in enumerate(data):
            if request.get('id') == request_id:
                # Добавляем дату архивации
                request['archived_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                archive.append(request)
                data.pop(i)
                
                self._save_data(data)
                self._save_archive(archive)
                return True
        return False
    
    def get_archive(self) -> List[Dict]:
        """Получить все архивные заявки"""
        return self._load_archive()
    
    def clean_old_archive(self, days: int = 14) -> int:
        """Очистить архив старше указанного количества дней"""
        archive = self._load_archive()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cleaned_count = 0
        new_archive = []
        
        for request in archive:
            archived_date_str = request.get('archived_date')
            if archived_date_str:
                archived_date = datetime.strptime(archived_date_str, '%Y-%m-%d %H:%M:%S')
                if archived_date >= cutoff_date:
                    new_archive.append(request)
                else:
                    cleaned_count += 1
            else:
                new_archive.append(request)
        
        self._save_archive(new_archive)
        return cleaned_count
    
    def manual_cleanup(self) -> Dict[str, int]:
        """Ручная очистка старых заявок из основной БД"""
        data = self._load_data()
        archive = self._load_archive()
        
        # Переносим все "Готово" в архив
        completed = [r for r in data if r.get('status') == 'Готово']
        remaining = [r for r in data if r.get('status') != 'Готово']
        
        for request in completed:
            if 'archived_date' not in request:
                request['archived_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            archive.append(request)
        
        self._save_data(remaining)
        self._save_archive(archive)
        
        # Очищаем старый архив
        archived_cleaned = self.clean_old_archive(14)
        
        return {
            'moved_to_archive': len(completed),
            'cleaned_from_archive': archived_cleaned
        }
