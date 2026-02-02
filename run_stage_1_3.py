import asyncio

from starter_code.src.events.event_bus import EventBus
from starter_code.src.agents.coordinator import CoordinatorAgent
from starter_code.src.agents.security_agent import SecurityAgent
from starter_code.src.context.shared_context import SharedContext
from starter_code.src.agents.bug_agent import BugAgent


async def main():
    event_bus = EventBus()

    # Subscribe early
    queue = event_bus.subscribe()

    # Printer task
    async def printer():
        while True:
            event = await queue.get()
            print(event)

    printer_task = asyncio.create_task(printer())

    # Agents
    coordinator = CoordinatorAgent(event_bus)
    security_agent = SecurityAgent(event_bus)
    bug_agent = BugAgent(event_bus)

    # Register specialists
    coordinator.register_specialist("security", security_agent)
    coordinator.register_specialist("bug", bug_agent)


    code = """
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    """

    shared_context = SharedContext(code)

    # Single entry point
    await coordinator.analyze(
        code,
        context={"shared_context": shared_context},
    )

    # Flush events
    await asyncio.sleep(1)

    printer_task.cancel()

    try:
        await printer_task
    except asyncio.CancelledError:
        pass



if __name__ == "__main__":
    asyncio.run(main())
