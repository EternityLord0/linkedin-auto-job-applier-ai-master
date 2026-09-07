# src/data/question_cache.py
import json
import os
import re
import unicodedata
from src.utils.logger import logger


class QuestionCache:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QuestionCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, cache_file_path: str = None):
        if getattr(self, '_initialized', False):
            return

        if not cache_file_path:
            # Locate relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_file_path = os.path.join(base_dir, "data", "answered_questions.json")

        self.cache_file = cache_file_path
        self.cache = {}
        self._load_cache()
        self._initialized = True

    @staticmethod
    def normalize_text(text: str) -> str:
        """Removes accents, lowercases, and strips punctuation for robust matching."""
        if not text:
            return ""
        # Normalize unicode accents
        nfkd = unicodedata.normalize('NFKD', text)
        ascii_text = ''.join([c for c in nfkd if not unicodedata.combining(c)])
        # Lowercase and keep only alphanumeric and spaces
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', ascii_text.lower())
        # Collapse whitespace
        return ' '.join(cleaned.split())

    def _load_cache(self):
        """Loads answered questions from the JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = {self.normalize_text(k): str(v).strip() for k, v in data.items() if k}
                logger.info(f"Loaded {len(self.cache)} cached question responses from {os.path.basename(self.cache_file)}")
            except Exception as e:
                logger.warning(f"Could not load question cache from {self.cache_file}: {e}")
                self.cache = {}
        else:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            self.cache = {}

    def get_answer(self, question: str, options: list[str] = None) -> str | None:
        """
        Retrieves a cached answer for the given question.
        Supports exact match and substring/keyword matching.
        If options are provided, maps the cached answer to the closest option.
        """
        if not question:
            return None

        norm_q = self.normalize_text(question)
        if not norm_q:
            return None

        # 1. Exact match
        if norm_q in self.cache:
            raw_answer = self.cache[norm_q]
            return self._match_to_options(raw_answer, options) if options else raw_answer

        # 2. Substring match: Check if cached key is contained in question
        # Sort by key length descending to prefer more specific matches (e.g. "anos de experiencia com python" over "anos de experiencia")
        for key in sorted(self.cache.keys(), key=len, reverse=True):
            if len(key) >= 4 and key in norm_q:
                raw_answer = self.cache[key]
                return self._match_to_options(raw_answer, options) if options else raw_answer

        # 3. Reverse substring match: Check if question is inside cached key
        for key in self.cache:
            if len(norm_q) >= 6 and norm_q in key:
                raw_answer = self.cache[key]
                return self._match_to_options(raw_answer, options) if options else raw_answer

        return None

    def _match_to_options(self, answer: str, options: list[str]) -> str | None:
        """Matches a raw answer string to one of the available choices in radio/select/dropdown."""
        if not options:
            return answer

        norm_ans = self.normalize_text(answer)

        # Exact match in options
        for opt in options:
            if self.normalize_text(opt) == norm_ans:
                return opt

        # Substring match
        for opt in options:
            norm_opt = self.normalize_text(opt)
            if norm_ans in norm_opt or norm_opt in norm_ans:
                return opt

        # Yes/No normalization
        if norm_ans in ['sim', 'yes', 'true']:
            for opt in options:
                if any(y in self.normalize_text(opt) for y in ['sim', 'yes']):
                    return opt
        elif norm_ans in ['nao', 'no', 'false']:
            for opt in options:
                if any(n in self.normalize_text(opt) for n in ['nao', 'no']):
                    return opt

        # Numeric match
        for opt in options:
            if answer in opt:
                return opt

        return options[0] if options else answer

    def save_answer(self, question: str, answer: str):
        """Saves or updates a question-answer pair in the cache and persists to disk."""
        if not question or not answer:
            return

        norm_q = self.normalize_text(question)
        if not norm_q or len(norm_q) < 3:
            return

        str_answer = str(answer).strip()
        if not str_answer:
            return

        # Avoid overwriting with vague answers
        if norm_q in self.cache and self.cache[norm_q] == str_answer:
            return

        self.cache[norm_q] = str_answer

        # Persist to disk
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved new answer in cache: '{norm_q}' -> '{str_answer}'")
        except Exception as e:
            logger.warning(f"Failed to persist question cache to {self.cache_file}: {e}")


# Singleton instance for simple import
question_cache = QuestionCache()
