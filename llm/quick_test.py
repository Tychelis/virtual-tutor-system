#!/usr/bin/env python3
"""快速性能测试"""
import requests
import time
import json

def test_latency(url, label):
    """测试单个端点的延迟"""
    payload = {
        "user_id": 1,
        "session_id": 1,
        "input": "What is machine learning?"
    }
    
    print(f"\n{'='*60}")
    print(f" Testing: {label}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    start = time.time()
    first_chunk_time = None
    chunks = 0
    
    try:
        with requests.post(url, json=payload, stream=True, timeout=30) as response:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data = json.loads(line.replace("data: ", ""))
                    
                    if first_chunk_time is None and data.get("status") == "streaming":
                        first_chunk_time = time.time()
                        ttft = first_chunk_time - start
                        print(f" Time to First Token: {ttft:.3f}s")
                    
                    if data.get("status") == "streaming":
                        chunks += 1
                    
                    if data.get("status") == "finished":
                        total = time.time() - start
                        print(f" Total time: {total:.3f}s")
                        print(f"   Chunks: {chunks}")
                        return {
                            "ttft": first_chunk_time - start if first_chunk_time else 0,
                            "total": total,
                            "chunks": chunks
                        }
        
    except Exception as e:
        print(f" Error: {e}")
        return None

# 测试两个版本
print("\n" + "="*60)
print(" Performance Comparison Test")
print("="*60)

original_result = test_latency("http://localhost:8610/chat/stream", "ORIGINAL (8610)")
optimized_result = test_latency("http://localhost:8611/chat/stream", "OPTIMIZED (8611)")

# 对比结果
if original_result and optimized_result:
    print("\n" + "="*60)
    print(" Comparison Results")
    print("="*60)
    
    ttft_improvement = ((original_result["ttft"] - optimized_result["ttft"]) / original_result["ttft"]) * 100
    total_improvement = ((original_result["total"] - optimized_result["total"]) / original_result["total"]) * 100
    
    print(f"\n Time to First Token (TTFT):")
    print(f"   Original:  {original_result['ttft']:.3f}s")
    print(f"   Optimized: {optimized_result['ttft']:.3f}s")
    print(f"   Improvement: {ttft_improvement:+.1f}%")
    
    print(f"\n  Total Time:")
    print(f"   Original:  {original_result['total']:.3f}s")
    print(f"   Optimized: {optimized_result['total']:.3f}s")
    print(f"   Improvement: {total_improvement:+.1f}%")
    
    print("\n" + "="*60)
    
    if ttft_improvement > 30:
        print(" EXCELLENT! 首字延迟提升超过30%")
    elif ttft_improvement > 0:
        print(" GOOD! 首字延迟有所改善")
    else:
        print("  需要进一步优化")

