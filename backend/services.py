import asyncio
from typing import List
from schemas import Event

class EventService:
    def __init__(self):
        # This simulates our database
        self.db: List[Event] = []

    async def add_event(self, event: Event) -> Event:
        """
        Simulate a database write.
        """
        # 1. Simulate Network Latency (The "Wait")
        # In a real app, this would be: await database.save(event)
        # We pause for 0.5 seconds, BUT we don't block the server!
        await asyncio.sleep(0.5) 
        
        # 2. Save data
        self.db.append(event)
        return event

    async def get_events(self) -> List[Event]:
        """
        Simulate a database read.
        """
        await asyncio.sleep(0.2) # Simulate read latency
        return self.db

# Create a single instance to be used by the app
backend_service = EventService()