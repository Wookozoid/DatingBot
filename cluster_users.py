"""
Пересчитывает кластеры интересов для всех пользователей
с эмбеддингом и записывает cluster_id в БД.
"""
import asyncio

from bot.config import settings
from bot.services.clustering import fit_clusters
from storage.database import async_session_factory, init_db
from storage.repository import get_all_embedded_users, get_embedding, set_user_cluster


async def cluster_users() -> None:
    await init_db()

    async with async_session_factory() as session:
        users = await get_all_embedded_users(session)

        if len(users) < settings.MIN_USERS_FOR_CLUSTERING:
            print(
                f"Недостаточно анкет с эмбеддингом: {len(users)} < {settings.MIN_USERS_FOR_CLUSTERING}."
            )
            return

        embeddings = [get_embedding(u) for u in users]
        labels, n_clusters = fit_clusters(embeddings)

        for user, label in zip(users, labels):
            await set_user_cluster(session, user.id, label)

    print(f"Готово: {len(users)} анкет распределены по {n_clusters} кластерам.")

    counts: dict[int, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    for cluster_id in sorted(counts):
        print(f"Кластер {cluster_id}: {counts[cluster_id]} анкет")


if __name__ == "__main__":
    asyncio.run(cluster_users())