import time
from fastapi import Request, HTTPException

class SimpleRateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        """
        max_calls: How many requests allowed?
        time_window: In how many seconds? (e.g., 5 calls in 10 seconds)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        
        # This dictionary will hold the history.
        # Key: Client IP (str)
        # Value: List of timestamps (List[float])
        self.client_history = {}

    def __call__(self, request: Request):
        """
        This special magic method allows us to use the class instance 
        like a function in FastAPI dependencies.
        """
        client_ip = request.client.host
        current_time = time.time()
        
        # 1. Get the history for this IP, or initialize empty list
        if client_ip not in self.client_history:
            self.client_history[client_ip] = []
            
        history = self.client_history[client_ip]
        
        # 2. CLEANUP: Remove timestamps that are too old (outside the window)
        # We keep only timestamps where: (current_time - timestamp) < time_window
        valid_history = [t for t in history if (current_time - t) < self.time_window]
        
        # 3. CHECK: Do they have room for a new request?
        if len(valid_history) >= self.max_calls:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Max {self.max_calls} requests per {self.time_window} seconds."
            )
            
        # 4. RECORD: Add the current timestamp to the history
        valid_history.append(current_time)
        
        # Update the storage
        self.client_history[client_ip] = valid_history
        
        return True