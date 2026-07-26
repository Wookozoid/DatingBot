"""
Гибридный ранкинг кандидатов.

Итоговый скор кандидата C для пользователя U:
    score(C) = w_sim     * cosine_similarity(U, C)
            + w_cluster  * cluster_bonus(U, C)
            + w_feedback * feedback_score(U, C)
            + w_age      * age_score(U, C)

- cosine_similarity - семантическая близость био.
- cluster_bonus - бонус, если U и C попали в один кластер интересов.
- feedback_score - похож ли C на тех, кого U лайкал раньше, и НЕ похож ли
  на тех, кого дизлайкал (короче история реакций).
- age_score - чем ближе возраст, тем лучше
"""
import math

import numpy as np

from bot.config import settings
from storage.models import User
from storage.repository import get_embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.asarray(a), np.asarray(b)
    denom = (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)) or 1e-9
    return float(np.dot(a_arr, b_arr) / denom)


def _cluster_bonus(user_cluster: int | None, candidate_cluster: int | None) -> float:
    if user_cluster is None or candidate_cluster is None:
        return 0.0
    return 1.0 if user_cluster == candidate_cluster else 0.0


def _feedback_score(
    candidate_embedding: list[float],
    liked_embeddings: list[list[float]],
    disliked_embeddings: list[list[float]],
) -> float:
    if not liked_embeddings and not disliked_embeddings:
        return 0.0

    liked_sim = (
        np.mean([_cosine_similarity(candidate_embedding, e) for e in liked_embeddings])
        if liked_embeddings
        else 0.0
    )
    disliked_sim = (
        np.mean([_cosine_similarity(candidate_embedding, e) for e in disliked_embeddings])
        if disliked_embeddings
        else 0.0
    )
    return float(liked_sim - disliked_sim)


def _age_score(user_age: int, candidate_age: int) -> float:
    """
    Экспоненциальное затухание по разнице в возрасте
    """
    diff = abs(user_age - candidate_age)
    return math.exp(-diff / settings.AGE_SCALE_YEARS)


def rank_candidates(
    user: User,
    candidates: list[User],
    liked_embeddings: list[list[float]],
    disliked_embeddings: list[list[float]],
    top_n: int | None = None,
) -> list[User]:
    """
    Сортирует кандидатов по убыванию гибридного скора
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
        cluster_bonus = _cluster_bonus(user.cluster_id, candidate.cluster_id)
        feedback = _feedback_score(candidate_embedding, liked_embeddings, disliked_embeddings)
        age_score = _age_score(user.age, candidate.age)

        score = (
            settings.RANKING_WEIGHT_SIMILARITY * similarity
            + settings.RANKING_WEIGHT_CLUSTER * cluster_bonus
            + settings.RANKING_WEIGHT_FEEDBACK * feedback
            + settings.RANKING_WEIGHT_AGE * age_score
        )
        scored.append((score, candidate))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    ranked = [candidate for _, candidate in scored]
    return ranked[:top_n] if top_n is not None else ranked
