"""
Построение эмбеддингов анкет.

Модель грузится один раз в память и переиспользуется
для всех пользователей.
"""
import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from bot.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str):
        logger.info("Загружаю модель эмбеддингов: %s", model_name)
        self._model = SentenceTransformer(model_name)
        logger.info("Модель эмбеддингов загружена")

    def encode(self, text: str) -> list[float]:
        """
        Строит вектор для текста анкеты.
        """
        text = (text or "").strip()
        if not text:
            return [0.0] * settings.EMBEDDING_DIM

        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService(settings.EMBEDDING_MODEL_NAME)