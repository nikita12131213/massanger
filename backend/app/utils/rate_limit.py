import time

from redis.asyncio import Redis


async def is_rate_limited(redis: Redis, key: str, limit: int, window_seconds: int = 60) -> bool:
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window_seconds)
    return current > limit


async def mark_typing(redis: Redis, conversation_id: int, user_id: int, ttl: int = 6) -> None:
    await redis.set(f"typing:{conversation_id}:{user_id}", int(time.time()), ex=ttl)


async def clear_typing(redis: Redis, conversation_id: int, user_id: int) -> None:
    await redis.delete(f"typing:{conversation_id}:{user_id}")
