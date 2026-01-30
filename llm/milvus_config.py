 #!/usr/bin/env python3
"""
Milvus API configuration
"""

import os
from typing import Optional

class MilvusConfig:
    """Milvus API configuration class"""
    
    # Milvus API service configuration
    MILVUS_API_BASE_URL: str = os.getenv("MILVUS_API_BASE_URL", "http://localhost:9090")
    MILVUS_API_TIMEOUT: int = int(os.getenv("MILVUS_API_TIMEOUT", "30"))
    
    # default query parameters
    DEFAULT_PERSONAL_K: int = int(os.getenv("DEFAULT_PERSONAL_K", "5"))
    DEFAULT_PUBLIC_K: int = int(os.getenv("DEFAULT_PUBLIC_K", "5"))
    DEFAULT_FINAL_K: int = int(os.getenv("DEFAULT_FINAL_K", "10"))
    
    # API endpoint configuration
    QUERY_ENDPOINT: str = os.getenv("MILVUS_QUERY_ENDPOINT", "/retriever")
    HEALTH_ENDPOINT: str = os.getenv("MILVUS_HEALTH_ENDPOINT", "/retriever")
    
    @classmethod
    def get_query_url(cls) -> str:
        """get query endpoint URL"""
        return f"{cls.MILVUS_API_BASE_URL.rstrip('/')}{cls.QUERY_ENDPOINT}"
    
    @classmethod
    def get_health_url(cls) -> str:
        """get health check endpoint URL"""
        return f"{cls.MILVUS_API_BASE_URL.rstrip('/')}{cls.HEALTH_ENDPOINT}"
    
    @classmethod
    def validate(cls) -> bool:
        """validate configuration"""
        try:
            import requests
            response = requests.get(cls.get_health_url(), timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Milvus API configuration validation failed: {e}")
            return False

# create global configuration instance
config = MilvusConfig()