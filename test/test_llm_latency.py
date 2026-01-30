#!/usr/bin/env python3
"""LLM API Latency Test"""
import requests
import time
import json
import sys

def test_latency(url, label, question="What is machine learning?"):
    """Test latency of a single endpoint"""
    payload = {
        "user_id": 1,
        "session_id": 1,
        "input": question
    }
    
    print(f"\n{'='*60}")
    print(f" Testing: {label}")
    print(f"URL: {url}")
    print(f"Question: {question}")
    print(f"{'='*60}")
    
    start = time.time()
    first_chunk_time = None
    chunks = 0
    content = ""
    
    try:
        with requests.post(url, json=payload, stream=True, timeout=60) as response:
            response.raise_for_status()
            
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                
                try:
                    data = json.loads(line.replace("data: ", ""))
                    
                    if first_chunk_time is None and data.get("status") == "streaming":
                        first_chunk_time = time.time()
                        ttft = first_chunk_time - start
                        print(f" Time to First Token (TTFT): {ttft:.3f}s")
                    
                    if data.get("status") == "streaming":
                        content += data.get("chunk", "")
                        chunks += 1
                        if chunks % 20 == 0:
                            print(f"   Received {chunks} chunks...")
                    
                    if data.get("status") == "finished":
                        total = time.time() - start
                        print(f" Completed!")
                        print(f"   Total time: {total:.3f}s")
                        print(f"   Total chunks: {chunks}")
                        print(f"   Response length: {len(content)} characters")
                        
                        print(f"\n {'='*60}")
                        print(" Performance Metrics")
                        print(f"{'='*60}")
                        print(f"Time to First Token (TTFT): {ttft:.3f}s")
                        print(f"Total Time:                 {total:.3f}s")
                        print(f"Response Speed:             {len(content)/total:.1f} chars/sec")
                        
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
                        print("-"*60)
                        preview = content[:200] + "..." if len(content) > 200 else content
                        print(preview)
                        print("-"*60)
                        
                        return {
                            "ttft": ttft,
                            "total": total,
                            "chunks": chunks,
                            "content": content
                        }
                
                except json.JSONDecodeError:
                    continue
        
    except Exception as e:
        print(f" Error: {e}")
        return None


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "What is machine learning?"
    
    print("\n" + "="*60)
    print(" LLM API Performance Test")
    print("="*60)
    
    # Test optimized version on port 8611
    result = test_latency("http://localhost:8611/chat/stream", "LLM API (8611)", question)
    
    if not result:
        print("\n Failed to test LLM API")
        print(" Please ensure the LLM service is running:")
        print("   cd llm && python api_interface_optimized.py")
    
    print("\n" + "="*60)
    print(" Test Completed")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Test interrupted")

