import redis

# Initialize Redis client
# decode_responses=True ensures that responses are returned as strings (not bytes)
redis_client = redis.Redis(
    host='localhost',  # Redis server host
    port=6379,         # Redis server port
    decode_responses=True
)
