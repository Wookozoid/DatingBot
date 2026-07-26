"""
Кластеризация анкет по интересам поверх эмбеддингов.

Используем MiniBatchKMeans.
"""
import numpy as np
from sklearn.cluster import MiniBatchKMeans

from bot.config import settings


def fit_clusters(embeddings: list[list[float]]) -> tuple[list[int], int]:
    """
    Обучает кластеризацию на переданных эмбеддингах.
    """
    X = np.asarray(embeddings)
    n_clusters = max(2, min(settings.N_CLUSTERS, len(X) // 5)) # Если пользователей мало разбиваем на кластеры поменьше

    model = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = model.fit_predict(X)
    return labels.tolist(), n_clusters