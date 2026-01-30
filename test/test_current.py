#!/usr/bin/env python3
"""
Test Currently Running LLM Service
No comparison needed, just test actual performance

Usage:
    python test_current.py
    python test_current.py "What is deep learning?"
"""

import requests
import time
import json
import sys

def test_llm_service(question="What is machine learning?"):
    """Test LLM service performance"""
    
    # First detect which service is running
    print("\n Detecting running LLM services...")
    
    services = {
        "Optimized (8611)": "http://localhost:8611/chat/stream",
        "Original (8610)": "http://localhost:8610/chat/stream"
    }
    
    active_service = None
    active_url = None
    
    for name, url in services.items():
        try:
            health_url = url.replace("/chat/stream", "/health")
            r = requests.get(health_url, timeout=2)
            if r.status_code == 200:
                active_service = name
                active_url = url
                print(f" Found running service: {name}")
                break
        except:
            continue
    
    if not active_service:
        print("\n No running LLM service found")
        print("\nPlease start a service first:")
        print("  python api_interface_optimized.py &  # Optimized version")
        print("  or")
        print("  python api_interface.py &           # Original version")
        return
    
    # Test performance
    print("\n" + "="*70)
    print(f" Testing: {active_service}")
    print("="*70)
    print(f"Question: {question}")
    print()
    
    payload = {
        "user_id": 1,
        "session_id": 1,
        "input": question
    }
    
    start_time = time.time()
    first_chunk_time = None
    chunks = 0
    content = ""
    
    try:
        with requests.post(active_url, json=payload, stream=True, timeout=60) as response:
            response.raise_for_status()
            
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                
                try:
                    data = json.loads(line.replace("data: ", ""))
                    
                    if first_chunk_time is None and data.get("status") == "streaming":
                        first_chunk_time = time.time()
                        ttft = first_chunk_time - start_time
                        print(f" Time to First Token (TTFT): {ttft:.3f}s")
                    
                    if data.get("status") == "streaming":
                        content += data.get("chunk", "")
                        chunks += 1
                        if chunks % 20 == 0:
                            print(f"   Received {chunks} chunks...")
                    
                    if data.get("status") == "finished":
                        total_time = time.time() - start_time
                        print(f" Completed!")
                        print(f"   Total time: {total_time:.3f}s")
                        print(f"   Total chunks: {chunks}")
                        print(f"   Response length: {len(content)} characters")
                        
                        print("\n" + "="*70)
                        print(" Performance Metrics")
                        print("="*70)
                        print(f"Time to First Token (TTFT): {ttft:.3f}s")
                        print(f"Total Time:                 {total_time:.3f}s")
                        print(f"Response Speed:             {len(content)/total_time:.1f} chars/sec")
                        
                        # Evaluation
                        print("\n Performance Evaluation:")
                        if ttft < 1.0:
                            print(f"   Excellent! TTFT {ttft:.2f}s < 1 second")
                        elif ttft < 2.0:
                            print(f"   Good! TTFT {ttft:.2f}s < 2 seconds")
                        elif ttft < 3.0:
                            print(f"   Acceptable, TTFT {ttft:.2f}s < 3 seconds")
                        else:
                            print(f"   Slow, TTFT {ttft:.2f}s > 3 seconds")
                        
                        # Response preview
                        print("\n Response Preview:")
                        print("-"*70)
                        preview = content[:300] + "..." if len(content) > 300 else content
                        print(preview)
                        print("-"*70)
                        
                        return
                
                except json.JSONDecodeError:
                    continue
    
    except Exception as e:
        print(f"\n Error: {e}")

def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "What is machine learning?"
    
    print("\n" + "="*70)
    print(" LLM Service Performance Test")
    print("="*70)
    
    test_llm_service(question)
    
    print("\n Tips:")
    print("  - For comparison test, start both versions then run: python compare_latency.py")
    print("  - Check service status: python compare_latency.py --check")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Test interrupted")



