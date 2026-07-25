"""
Ранжирования кандидатов по семантической близости эмбеддингов.

Дальше появится отбор по кластеру интересов, история лайков/дизлайков
превратиться в гибридный скор.

При переезде на PostgreSQL + pgvector эту функцию можно будет заменить на
SQL-сортировку (`ORDER BY embedding <=> :user_embedding`), в таком 
случае ничего в проекте кроме этой функции не поменяется.
"""
import numpy as np

from storage.models import User
from storage.repository import get_embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.asarray(a), np.asarray(b)
    denom = (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)) or 1e-9
    return float(np.dot(a_arr, b_arr) / denom)


def rank_candidates(user: User, candidates: list[User], top_n: int | None = None) -> list[User]:
    """
    Сортирует кандидатов по убыванию похожести анкеты на анкету user
    Если top_n не задан, то возвращает всех отранжированных кандидатов
    """
    user_embedding = get_embedding(user)
    if user_embedding is None:
        return []

    scored: list[tuple[float, User]] = []
    for candidate in candidates:
        candidate_embedding = get_embedding(candidate)
        if candidate_embedding is None:
            continue
        similarity = _cosine_similarity(user_embedding, candidate_embedding)
        scored.append((similarity, candidate))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    ranked = [candidate for _, candidate in scored]
    return ranked[:top_n] if top_n is not None else ranked
