from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    Limits requests per IP address per endpoint.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Only rate limit specific endpoints
        if request.url.path.startswith("/api/v1/inquiries"):
            client_ip = request.client.host if request.client else "unknown"
            
            # Clean old requests
            now = datetime.utcnow()
            self.requests[client_ip] = [
                req_time
                for req_time in self.requests[client_ip]
                if now - req_time < timedelta(minutes=1)
            ]
            
            # Check rate limit
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                )
            
            # Record request
            self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response

