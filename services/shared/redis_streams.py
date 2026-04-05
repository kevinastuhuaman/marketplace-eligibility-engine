"""Base classes for Redis Streams producer/consumer."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class StreamPublisher:
    def __init__(self, redis: Redis, stream_name: str, max_len: int = 10000):
        self.redis = redis
        self.stream_name = stream_name
        self.max_len = max_len

    async def publish(self, event_type: str, data: dict) -> str:
        payload = {
            "event_type": event_type,
            "data": json.dumps(data, default=str),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        msg_id = await self.redis.xadd(
            self.stream_name, payload, maxlen=self.max_len, approximate=True
        )
        logger.info(f"Published {event_type} to {self.stream_name}: {msg_id}")
        return msg_id


class StreamConsumer:
    def __init__(self, redis: Redis, stream_name: str, group_name: str, consumer_name: str):
        self.redis = redis
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self._running = False

    async def setup(self):
        try:
            await self.redis.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
            logger.info(f"Created consumer group {self.group_name} on {self.stream_name}")
        except Exception:
            pass  # Group already exists

    async def consume(self, handler, batch_size: int = 10, block_ms: int = 5000):
        await self.setup()
        self._running = True
        while self._running:
            try:
                messages = await self.redis.xreadgroup(
                    self.group_name,
                    self.consumer_name,
                    {self.stream_name: ">"},
                    count=batch_size,
                    block=block_ms,
                )
                if messages:
                    for stream, msg_list in messages:
                        for msg_id, data in msg_list:
                            event_type = data.get(b"event_type", b"").decode()
                            event_data = json.loads(data.get(b"data", b"{}").decode())
                            try:
                                await handler(event_type, event_data)
                                await self.redis.xack(self.stream_name, self.group_name, msg_id)
                            except Exception as e:
                                logger.error(f"Error processing {event_type}: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        self._running = False
