# src/data/status_manager.py
import json
import os
from datetime import datetime
from src.utils.logger import logger


VALID_STATUSES = [
    "Candidatado",
    "Vaga Externa (Aplicar)",
    "Em Contato",
    "Entrevista Técnica",
    "Aprovado / Proposta",
    "Recusado"
]


class StatusManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StatusManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, file_path: str = None):
        if getattr(self, '_initialized', False):
            return

        if not file_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(base_dir, "data", "job_status.json")

        self.file_path = file_path
        self.statuses = {}
        self._load()
        self._initialized = True

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.statuses = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read status file {self.file_path}: {e}")
                self.statuses = {}
        else:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            self.statuses = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.statuses, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to persist job statuses to {self.file_path}: {e}")

    def get_status(self, job_id: str, default: str = "Candidatado") -> dict:
        """Returns the status entry for a job ID."""
        if not job_id:
            return {"status": default, "notes": "", "updated_at": ""}
        return self.statuses.get(str(job_id), {"status": default, "notes": "", "updated_at": ""})

    def set_status(self, job_id: str, status: str, notes: str = None) -> bool:
        """Updates the status and optional notes for a job ID."""
        if not job_id:
            return False

        str_id = str(job_id)
        current = self.statuses.get(str_id, {})
        new_notes = notes if notes is not None else current.get("notes", "")

        self.statuses[str_id] = {
            "status": status if status in VALID_STATUSES else (current.get("status") or "Candidatado"),
            "notes": new_notes,
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self._save()
        logger.info(f"Updated status for Job {job_id} -> '{status}'")
        return True

    def get_all_statuses(self) -> dict:
        return self.statuses


status_manager = StatusManager()
