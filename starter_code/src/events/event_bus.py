import asyncio
from typing import List


class EventBus:
    """
    Async pub/sub event bus using asyncio queues.
    """

    def __init__(self):
        # Each subscriber gets its own queue
        self._subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        """
        Subscribe to the event stream.
        Returns an asyncio.Queue.
        """
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    async def publish(self, event) -> None:
        for queue in self._subscribers:
            await queue.put(event)
