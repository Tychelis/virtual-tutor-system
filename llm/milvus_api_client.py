 #!/usr/bin/env python3
"""
Milvus API client - call external Milvus API service via HTTP request
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MilvusAPIClient:
    """Milvus API client"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        initialize Milvus API client
        
        Args:
            base_url: Milvus API service base URL, if None, use settings in configuration file
        """
        try:
            from milvus_config import config
            self.base_url = (base_url or config.MILVUS_API_BASE_URL).rstrip('/')
            self.timeout = config.MILVUS_API_TIMEOUT
            self.query_endpoint = config.QUERY_ENDPOINT
            self.health_endpoint = config.HEALTH_ENDPOINT
        except ImportError:
            # if configuration file does not exist, use default values
            self.base_url = (base_url or "http://localhost:9090").rstrip('/')
            self.timeout = 30
            self.query_endpoint = "/retriever"
            self.health_endpoint = "/retriever"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def query(self, 
              question: str, 
              user_id: str, 
              personal_k: int = 5, 
              public_k: int = 5, 
              final_k: int = 5,
              threshold: float = 0.5
              ) -> Dict[str, Any]:
        """
        query Milvus database
        
        Args:
            question: query question
            user_id: user ID
            personal_k: number of results returned by personal knowledge base
            public_k: number of results returned by public knowledge base
            final_k: number of results returned by final knowledge base
            
        Returns:
            query result dictionary
        """
        try:
            # build request data
            request_data = {
                "question": question,
                "user_id": user_id,
                "personal_k": personal_k,
                "public_k": public_k,
                "final_k": final_k,
                "threshold": threshold
            }
            # request_data = {
            #     "question": question,
            #     "user_id": user_id,
            #     "threshold": threshold,
            #     "top_k": top_k
            # }
            
            logger.info(f"query Milvus API: {request_data}")
            
            # send POST request
            response = self.session.post(
                f"{self.base_url}{self.query_endpoint}",
                json=request_data,
                timeout=self.timeout
            )
            
            # check response status
            response.raise_for_status()
            
            # parse response
            result = response.json()
            logger.info(f"Milvus API returned {len(result.get('hits', []))} results")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Milvus API request failed: {e}")
            return {
                "error": f"API request failed: {str(e)}",
                "results": [],
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Milvus API response parsing failed: {e}")
            return {
                "error": f"response parsing failed: {str(e)}",
                "results": [],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Milvus API query error: {e}")
            return {
                "error": f"unknown error: {str(e)}",
                "results": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        check Milvus API service health status
        
        Returns:
            health status information
        """
        try:
            response = self.session.get(
                f"{self.base_url}{self.health_endpoint}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Milvus API health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# create global client instance
milvus_client = MilvusAPIClient()

def query_milvus_api(question: str, 
                    user_id: str, 
                    personal_k: int = 5, 
                    public_k: int = 5, 
                    final_k: int = 5,
                    threshold: float = 0.5) -> Dict[str, Any]:
    """
    convenience function: query Milvus API
    
    Args:
        question: query question
        user_id: user ID
        personal_k: number of results returned by personal knowledge base
        public_k: number of results returned by public knowledge base
        final_k: number of results returned by final knowledge base
        
    Returns:
        query result dictionary
    """
    return milvus_client.query(question, user_id, personal_k, public_k, final_k, threshold)

def check_milvus_api_health() -> Dict[str, Any]:
    """
    convenience function: check Milvus API health status
    
    Returns:
        health status information
    """
    return milvus_client.health_check()

# test function
def test_milvus_api():
    """test Milvus API functionality"""
    print("=== test Milvus API ===")
    
    # health check
    # print("1. health check...")
    # health = check_milvus_api_health()
    # print(f"health status: {health}")
    
    # test query
    print("\n2. test query...")
    # result = query_milvus_api(
    #     question="Course Staff",
    #     user_id="alice",
    #     personal_k=3,
    #     public_k=3,
    #     final_k=5
    # )
    result = query_milvus_api(
        question="course staff",
        user_id="test",
        personal_k=3,
        public_k=3,
        final_k=4,
        threshold=0.1
    )
    # print(f"result: {result['hits']}")
    print(f"query result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if "error" in result:
        print(f" query failed: {result['error']}")
    else:
        print(f" query successful, returned {len(result.get('hits', []))} results")

if __name__ == "__main__":
    test_milvus_api()