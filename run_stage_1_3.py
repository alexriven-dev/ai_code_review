import asyncio

from starter_code.src.events.event_bus import EventBus
from starter_code.src.agents.coordinator import CoordinatorAgent
from starter_code.src.agents.security_agent import SecurityAgent
from starter_code.src.context.shared_context import SharedContext


async def main():
    event_bus = EventBus()

    # Print all events to console
    async def printer():
        queue = event_bus.subscribe()
        while True:
            event = await queue.get()
            print(event.to_json())

    asyncio.create_task(printer())

    coordinator = CoordinatorAgent(event_bus)
    security_agent = SecurityAgent(event_bus)

    coordinator.register_specialist("security", security_agent)

    code = """
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    """

    shared_context = SharedContext(code)

    # Stage 1
    plan = await coordinator.analyze(
        code,
        context={"shared_context": shared_context},
    )

    # Stage 3 (manual invocation for now)
    await security_agent.analyze(
        code,
        context={"shared_context": shared_context},
    )


if __name__ == "__main__":
    asyncio.run(main())
