"""
Rate limiting middleware for API and collectors.
"""
import time
import asyncio
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as redis
import logging
import hashlib

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""
    def __init__(self, limit: int, window: int, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limit} requests per {window} seconds"
        )
        self.headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Window": str(window),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + retry_after)
        }


class RateLimiter:
    """Rate limiter implementation using different storage backends."""
    
    def __init__(self, storage_backend: str = "memory"):
        self.storage_backend = storage_backend
        self.redis_client = None
        self.memory_storage = defaultdict(lambda: defaultdict(deque))
        
    async def initialize(self, redis_url: Optional[str] = None):
        """Initialize the rate limiter with storage backend."""
        if self.storage_backend == "redis" and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                await self.redis_client.ping()
                logger.info("Rate limiter initialized with Redis backend")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")
                self.storage_backend = "memory"
                logger.info("Falling back to memory backend")
        else:
            logger.info("Rate limiter initialized with memory backend")
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier for the client (IP, user ID, etc.)
            limit: Number of requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = int(time.time())
        
        if self.storage_backend == "redis" and self.redis_client:
            return await self._redis_check(key, limit, window, current_time)
        else:
            return self._memory_check(key, limit, window, current_time)
    
    async def _redis_check(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        current_time: int
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using Redis."""
        pipe = self.redis_client.pipeline()
        
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, current_time - window)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(key, window)
        
        results = await pipe.execute()
        request_count = results[1]
        
        remaining = max(0, limit - request_count)
        reset_time = current_time + window
        
        return request_count < limit, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": max(0, reset_time - current_time)
        }
    
    def _memory_check(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        current_time: int
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using in-memory storage."""
        requests = self.memory_storage[key]
        
        # Remove expired requests
        while requests and requests[0] <= current_time - window:
            requests.popleft()
        
        # Check if under limit
        request_count = len(requests)
        remaining = max(0, limit - request_count)
        reset_time = current_time + window
        
        if request_count < limit:
            requests.append(current_time)
            return True, {
                "limit": limit,
                "remaining": remaining - 1,  # Subtract 1 for current request
                "reset": reset_time,
                "retry_after": max(0, reset_time - current_time)
            }
        else:
            # Find retry after time (when oldest request expires)
            oldest_request = requests[0] if requests else current_time
            retry_after = oldest_request + window - current_time
            
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": reset_time,
                "retry_after": retry_after
            }
    
    async def reset(self, key: str):
        """Reset rate limit for a specific key."""
        if self.storage_backend == "redis" and self.redis_client:
            await self.redis_client.delete(key)
        else:
            self.memory_storage[key].clear()


class RateLimitConfig:
    """Rate limit configuration for different endpoints and user types."""
    
    # API endpoints
    API_ENDPOINTS = {
        # Authentication endpoints (more restrictive)
        "POST:/auth/login": {"limit": 5, "window": 300},  # 5 per 5 minutes
        "POST:/auth/refresh": {"limit": 10, "window": 300},  # 10 per 5 minutes
        
        # Data endpoints
        "GET:/api/entities": {"limit": 100, "window": 60},  # 100 per minute
        "POST:/api/entities": {"limit": 50, "window": 60},   # 50 per minute
        "PUT:/api/entities": {"limit": 50, "window": 60},    # 50 per minute
        "DELETE:/api/entities": {"limit": 20, "window": 60}, # 20 per minute
        
        # Scoring endpoints
        "POST:/api/scoring/score": {"limit": 30, "window": 60},  # 30 per minute
        "POST:/api/scoring/batch": {"limit": 10, "window": 60},  # 10 per minute
        
        # Agent endpoints
        "POST:/api/agents/run": {"limit": 20, "window": 60},      # 20 per minute
        "POST:/api/agents/pipeline": {"limit": 5, "window": 300},  # 5 per 5 minutes
        
        # Configuration endpoints
        "GET:/api/config": {"limit": 200, "window": 60},    # 200 per minute
        "PUT:/api/config": {"limit": 10, "window": 60},    # 10 per minute
    }
    
    # User-based limits
    USER_LIMITS = {
        "anonymous": {"limit": 50, "window": 60},      # 50 per minute
        "user": {"limit": 200, "window": 60},          # 200 per minute
        "premium": {"limit": 500, "window": 60},       # 500 per minute
        "admin": {"limit": 1000, "window": 60},        # 1000 per minute
    }
    
    # Collector limits
    COLLECTOR_LIMITS = {
        "subdomain": {"limit": 1000, "window": 3600},   # 1000 per hour
        "email": {"limit": 500, "window": 3600},        # 500 per hour
        "vulnerability": {"limit": 200, "window": 3600}, # 200 per hour
        "cloud": {"limit": 300, "window": 3600},        # 300 per hour
    }
    
    # Global limits
    GLOBAL_LIMITS = {
        "requests_per_second": 1000,
        "concurrent_connections": 500,
        "burst_allowance": 10,
    }


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""
    
    def __init__(
        self, 
        app, 
        config: RateLimitConfig = None,
        redis_url: Optional[str] = None,
        key_generator: Optional[callable] = None
    ):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.limiter = RateLimiter()
        self.key_generator = key_generator or self._default_key_generator
        self.global_counters = defaultdict(int)
        self.global_last_reset = time.time()
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        # Initialize limiter if needed
        if not self.limiter.redis_client and self.limiter.storage_backend == "redis":
            await self.limiter.initialize()
        
        # Generate rate limit key
        key = await self.key_generator(request)
        
        # Get rate limit rules
        limit_rules = await self._get_limit_rules(request)
        
        # Check each rule
        for rule_key, rule in limit_rules.items():
            allowed, info = await self.limiter.is_allowed(
                f"{key}:{rule_key}", 
                rule["limit"], 
                rule["window"]
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {key}: {rule}")
                raise RateLimitExceeded(
                    rule["limit"], 
                    rule["window"], 
                    info["retry_after"]
                )
        
        # Check global limits
        await self._check_global_limits(request)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        await self._add_rate_limit_headers(response, limit_rules, key)
        
        return response
    
    async def _default_key_generator(self, request: Request) -> str:
        """Generate default rate limit key based on IP and user."""
        # Get client IP
        client_ip = request.client.host
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Get user info if available
        user_id = getattr(request.state, "user_id", None)
        user_role = getattr(request.state, "user_role", "anonymous")
        
        # Create composite key
        key_parts = [client_ip]
        if user_id:
            key_parts.append(f"user:{user_id}")
        else:
            key_parts.append(f"role:{user_role}")
        
        return hashlib.md5(":".join(key_parts).encode()).hexdigest()
    
    async def _get_limit_rules(self, request: Request) -> Dict[str, Dict[str, int]]:
        """Get applicable rate limit rules for the request."""
        rules = {}
        
        # Endpoint-specific rules
        method_path = f"{request.method.upper()}:{request.url.path}"
        for pattern, config in self.config.API_ENDPOINTS.items():
            if self._match_pattern(pattern, method_path):
                rules[f"endpoint:{pattern}"] = config
        
        # User-based rules
        user_role = getattr(request.state, "user_role", "anonymous")
        if user_role in self.config.USER_LIMITS:
            rules[f"user:{user_role}"] = self.config.USER_LIMITS[user_role]
        
        # Tenant-based rules (if applicable)
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            rules[f"tenant:{tenant_id}"] = {"limit": 1000, "window": 60}
        
        return rules
    
    def _match_pattern(self, pattern: str, path: str) -> bool:
        """Check if path matches the rate limit pattern."""
        # Simple exact match for now
        # Could be enhanced with regex for more complex patterns
        return pattern == path
    
    async def _check_global_limits(self, request: Request):
        """Check global rate limits."""
        current_time = time.time()
        
        # Reset counters every second
        if current_time - self.global_last_reset >= 1:
            self.global_counters.clear()
            self.global_last_reset = current_time
        
        # Increment request counter
        self.global_counters["requests"] += 1
        
        # Check requests per second
        if self.global_counters["requests"] > self.config.GLOBAL_LIMITS["requests_per_second"]:
            raise RateLimitExceeded(
                self.config.GLOBAL_LIMITS["requests_per_second"],
                1,
                1
            )
    
    async def _add_rate_limit_headers(
        self, 
        response: Response, 
        rules: Dict[str, Dict[str, int]], 
        key: str
    ):
        """Add rate limit headers to response."""
        # Get the most restrictive limit
        most_restrictive = None
        min_remaining = float('inf')
        
        for rule_key, rule in rules.items():
            _, info = await self.limiter.is_allowed(
                f"{key}:{rule_key}", 
                rule["limit"], 
                rule["window"]
            )
            
            if info["remaining"] < min_remaining:
                min_remaining = info["remaining"]
                most_restrictive = info
        
        if most_restrictive:
            response.headers["X-RateLimit-Limit"] = str(most_restrictive["limit"])
            response.headers["X-RateLimit-Remaining"] = str(most_restrictive["remaining"])
            response.headers["X-RateLimit-Reset"] = str(most_restrictive["reset"])
            response.headers["X-RateLimit-Window"] = str(most_restrictive.get("window", 60))


class CollectorRateLimiter:
    """Specialized rate limiter for data collectors."""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.limiter = RateLimiter()
        self.collector_stats = defaultdict(lambda: defaultdict(int))
    
    async def initialize(self, redis_url: Optional[str] = None):
        """Initialize the collector rate limiter."""
        await self.limiter.initialize(redis_url)
    
    async def check_collector_limit(
        self, 
        collector_type: str, 
        tenant_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, int]]:
        """Check if collector can run based on rate limits."""
        key_parts = ["collector", collector_type]
        if tenant_id:
            key_parts.append(f"tenant:{tenant_id}")
        
        key = ":".join(key_parts)
        
        if collector_type in self.config.COLLECTOR_LIMITS:
            config = self.config.COLLECTOR_LIMITS[collector_type]
            return await self.limiter.is_allowed(key, config["limit"], config["window"])
        else:
            # Default limit for unknown collectors
            return await self.limiter.is_allowed(key, 100, 3600)
    
    async def record_collector_run(
        self, 
        collector_type: str, 
        tenant_id: Optional[int] = None,
        items_processed: int = 0
    ):
        """Record collector execution statistics."""
        key_parts = ["stats", collector_type]
        if tenant_id:
            key_parts.append(f"tenant:{tenant_id}")
        
        key = ":".join(key_parts)
        
        self.collector_stats[key]["runs"] += 1
        self.collector_stats[key]["items"] += items_processed
        self.collector_stats[key]["last_run"] = datetime.utcnow().isoformat()
    
    def get_collector_stats(
        self, 
        collector_type: str, 
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get collector execution statistics."""
        key_parts = ["stats", collector_type]
        if tenant_id:
            key_parts.append(f"tenant:{tenant_id}")
        
        key = ":".join(key_parts)
        return dict(self.collector_stats[key])


# Global rate limiter instance
rate_limiter = RateLimitingMiddleware(
    app=None,  # Will be set when middleware is added to FastAPI app
    config=RateLimitConfig()
)

collector_rate_limiter = CollectorRateLimiter()


async def init_rate_limiting(redis_url: Optional[str] = None):
    """Initialize rate limiting system."""
    await rate_limiter.limiter.initialize(redis_url)
    await collector_rate_limiter.initialize(redis_url)
    logger.info("Rate limiting system initialized")
