#!/usr/bin/env python3
"""
Concurrent Performance Test Script

Test Flask application's concurrent performance under different deployment modes
"""

import requests
import concurrent.futures
import time
from datetime import datetime
import statistics
import sys

def test_endpoint(url, timeout=30):
    """Test a single request"""
    start_time = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        duration = time.time() - start_time
        return {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'duration': duration,
            'error': None
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'success': False,
            'status_code': None,
            'duration': duration,
            'error': str(e)
        }

def run_concurrent_test(url, num_requests=100, max_workers=10):
    """Run concurrent test"""
    print(f"\n{'='*60}")
    print(f" Concurrent Test")
    print(f"{'='*60}")
    print(f"Test URL: {url}")
    print(f"Total Requests: {num_requests}")
    print(f"Concurrency: {max_workers}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nExecuting...")
    
    start_time = time.time()
    
    # 并发执行请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(test_endpoint, url) for _ in range(num_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    total_time = time.time() - start_time
    
    # 统计结果
    success_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]
    durations = [r['duration'] for r in success_results]
    
    # Print results
    print(f"\n{'='*60}")
    print(f" Test Results")
    print(f"{'='*60}")
    print(f" Successful Requests: {len(success_results)}/{num_requests} ({len(success_results)/num_requests*100:.1f}%)")
    print(f" Failed Requests: {len(failed_results)}")
    
    if durations:
        print(f"\n  Response Time Statistics:")
        print(f"   Average: {statistics.mean(durations):.3f}s")
        print(f"   Min: {min(durations):.3f}s")
        print(f"   Max: {max(durations):.3f}s")
        print(f"   Median: {statistics.median(durations):.3f}s")
        if len(durations) > 1:
            print(f"   Std Dev: {statistics.stdev(durations):.3f}s")
    
    print(f"\n Performance Metrics:")
    print(f"   Total Time: {total_time:.3f}s")
    print(f"   QPS (Queries Per Second): {num_requests/total_time:.1f}")
    print(f"   Throughput: {len(success_results)/total_time:.1f} req/s")
    
    if failed_results:
        print(f"\n  Failure Reasons:")
        error_counts = {}
        for r in failed_results:
            error = r['error'] or f"HTTP {r['status_code']}"
            error_counts[error] = error_counts.get(error, 0) + 1
        for error, count in error_counts.items():
            print(f"   - {error}: {count} times")
    
    print(f"{'='*60}\n")
    
    return {
        'total_requests': num_requests,
        'success_count': len(success_results),
        'failed_count': len(failed_results),
        'total_time': total_time,
        'qps': num_requests/total_time,
        'avg_duration': statistics.mean(durations) if durations else 0
    }

def compare_deployments():
    """Compare performance of different deployment modes"""
    print("=" * 60)
    print(" Backend Concurrent Performance Test")
    print("=" * 60)
    print("\nThis script tests concurrent performance under different deployment modes")
    print("\nPlease ensure Backend service is running before testing!")
    print("  - Development mode: python run.py")
    print("  - Production mode: ./start_production.sh")
    
    base_url = input("\nEnter Backend URL (default: http://localhost:8203): ").strip()
    if not base_url:
        base_url = "http://localhost:8203"
    
    # Check service availability
    print(f"\nChecking service availability...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f" Service is healthy (HTTP {response.status_code})")
    except Exception as e:
        print(f" Service unavailable: {e}")
        print(f"\nPlease start Backend service first!")
        sys.exit(1)
    
    # Choose test scenario
    print("\n" + "=" * 60)
    print("Choose Test Scenario:")
    print("  1. Light test (50 requests, 5 concurrency)")
    print("  2. Medium test (100 requests, 10 concurrency) [Recommended]")
    print("  3. Heavy test (200 requests, 20 concurrency)")
    print("  4. Extreme test (500 requests, 50 concurrency)")
    print("  5. Custom")
    print("=" * 60)
    
    choice = input("\nPlease choose (default: 2): ").strip() or "2"
    
    test_configs = {
        "1": (50, 5),
        "2": (100, 10),
        "3": (200, 20),
        "4": (500, 50),
    }
    
    if choice in test_configs:
        num_requests, max_workers = test_configs[choice]
    elif choice == "5":
        num_requests = int(input("Total requests: "))
        max_workers = int(input("Concurrency: "))
    else:
        print("Invalid choice, using default configuration")
        num_requests, max_workers = 100, 10
    
    # Run test
    result = run_concurrent_test(
        f"{base_url}/api/health",
        num_requests=num_requests,
        max_workers=max_workers
    )
    
    # Performance evaluation
    print(" Performance Evaluation:")
    qps = result['qps']
    if qps < 10:
        rating = " Poor (might be using Flask development server)"
        suggestion = "Recommend using Gunicorn for production deployment"
    elif qps < 30:
        rating = " Fair (might be using sync workers)"
        suggestion = "Recommend using gevent workers to improve concurrency"
    elif qps < 80:
        rating = " Good (meets basic production requirements)"
        suggestion = "Consider increasing worker count for further optimization"
    else:
        rating = " Excellent (high-performance configuration)"
        suggestion = "Outstanding performance!"
    
    print(f"   Rating: {rating}")
    print(f"   Suggestion: {suggestion}")
    print()

def quick_test():
    """Quick test (10 requests, 2 concurrency)"""
    print(" Quick Test Mode\n")
    
    base_url = "http://localhost:8203"
    
    # Check service
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f" Backend service is healthy\n")
    except Exception as e:
        print(f" Backend service unavailable: {e}")
        print(f"Please start Backend service first!")
        sys.exit(1)
    
    # Run quick test
    result = run_concurrent_test(
        f"{base_url}/api/health",
        num_requests=10,
        max_workers=2
    )

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_test()
    else:
        compare_deployments()





