from redis import Redis

from app.config import get_settings
from app.tasks.celery_app import celery_app

settings = get_settings()
redis_sync = Redis.from_url(settings.redis_url, decode_responses=True)


@celery_app.task
def cleanup_typing() -> int:
    keys = redis_sync.keys("typing:*")
    removed = 0
    for key in keys:
        ttl = redis_sync.ttl(key)
        if ttl <= 0:
            redis_sync.delete(key)
            removed += 1
    return removed
