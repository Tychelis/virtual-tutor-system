#!/usr/bin/env python3
"""
异步优化性能测试脚本

用于测试Backend到Avatar转发的并发性能
"""
import asyncio
import httpx
import time
from typing import List, Tuple

# 配置
BASE_URL = "http://localhost:8203"
TEST_TOKEN = None  # 需要先登录获取token

async def test_single_request(client: httpx.AsyncClient, endpoint: str) -> Tuple[float, int]:
    """测试单个请求的响应时间"""
    headers = {}
    if TEST_TOKEN:
        headers["Authorization"] = f"Bearer {TEST_TOKEN}"
    
    start = time.time()
    try:
        response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
        elapsed = time.time() - start
        return elapsed, response.status_code
    except Exception as e:
        elapsed = time.time() - start
        print(f" 错误: {e}")
        return elapsed, -1


async def test_concurrent_requests(num_requests: int, endpoint: str) -> dict:
    """测试并发请求性能"""
    print(f"\n 测试 {num_requests} 个并发请求到 {endpoint}")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        start_time = time.time()
        
        # 创建并发任务
        tasks = [
            test_single_request(client, endpoint)
            for _ in range(num_requests)
        ]
        
        # 并发执行
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
    
    # 分析结果
    times = [r[0] for r in results]
    statuses = [r[1] for r in results]
    
    success_count = sum(1 for s in statuses if s == 200)
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    # 计算吞吐量
    throughput = num_requests / total_time
    
    result = {
        "num_requests": num_requests,
        "total_time": total_time,
        "avg_response_time": avg_time,
        "min_response_time": min_time,
        "max_response_time": max_time,
        "success_count": success_count,
        "success_rate": success_count / num_requests * 100,
        "throughput": throughput
    }
    
    return result


def print_results(result: dict):
    """打印测试结果"""
    print(f"\n 测试结果:")
    print(f"  总请求数: {result['num_requests']}")
    print(f"  总耗时: {result['total_time']:.2f}秒")
    print(f"  成功率: {result['success_rate']:.1f}% ({result['success_count']}/{result['num_requests']})")
    print(f"  平均响应时间: {result['avg_response_time']:.3f}秒")
    print(f"  最快响应: {result['min_response_time']:.3f}秒")
    print(f"  最慢响应: {result['max_response_time']:.3f}秒")
    print(f"  吞吐量: {result['throughput']:.2f} req/s")
    
    # 性能评估
    if result['avg_response_time'] < 1.0:
        print(f"   性能优秀")
    elif result['avg_response_time'] < 3.0:
        print(f"   性能良好")
    elif result['avg_response_time'] < 5.0:
        print(f"    性能一般")
    else:
        print(f"   性能较差")


async def run_performance_tests():
    """运行完整的性能测试套件"""
    print("=" * 60)
    print(" Backend到Avatar转发性能测试")
    print("=" * 60)
    
    # 测试端点（不需要认证的）
    test_cases = [
        (1, "/api/avatar/list", "单用户基准测试"),
        (2, "/api/avatar/list", "2用户并发"),
        (5, "/api/avatar/list", "5用户并发"),
        (10, "/api/avatar/list", "10用户并发"),
        (20, "/api/avatar/list", "20用户并发"),
    ]
    
    results = []
    
    for num_requests, endpoint, description in test_cases:
        print(f"\n{'=' * 60}")
        print(f" {description}")
        result = await test_concurrent_requests(num_requests, endpoint)
        print_results(result)
        results.append((description, result))
        
        # 等待一下，避免过载
        await asyncio.sleep(1)
    
    # 生成对比报告
    print("\n" + "=" * 60)
    print(" 性能对比总结")
    print("=" * 60)
    print(f"\n{'场景':<15} {'并发数':<8} {'总耗时(s)':<12} {'平均响应(s)':<15} {'吞吐量(req/s)':<15}")
    print("-" * 70)
    
    for description, result in results:
        print(f"{description:<15} {result['num_requests']:<8} "
              f"{result['total_time']:<12.2f} "
              f"{result['avg_response_time']:<15.3f} "
              f"{result['throughput']:<15.2f}")
    
    # 计算优化效果（对比单用户和多用户）
    if len(results) >= 2:
        baseline = results[0][1]  # 单用户基准
        concurrent = results[-1][1]  # 最大并发
        
        # 理论串行时间 = 单个请求时间 * 并发数
        theoretical_serial_time = baseline['avg_response_time'] * concurrent['num_requests']
        actual_time = concurrent['total_time']
        speedup = theoretical_serial_time / actual_time
        
        print(f"\n 优化效果分析:")
        print(f"  理论串行时间: {theoretical_serial_time:.2f}秒")
        print(f"  实际并发时间: {actual_time:.2f}秒")
        print(f"  加速比: {speedup:.2f}x")
        
        if speedup > 5:
            print(f"   异步优化效果显著！")
        elif speedup > 2:
            print(f"   异步优化有明显效果")
        else:
            print(f"    异步优化效果不明显，可能存在其他瓶颈")


async def quick_test():
    """快速测试：验证端点是否可用"""
    print(" 快速检查端点可用性...")
    
    endpoints = [
        "/api/avatar/list",
        "/api/tts/models",
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                status = "" if response.status_code == 200 else ""
                print(f"{status} {endpoint}: {response.status_code}")
            except Exception as e:
                print(f" {endpoint}: {str(e)}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Backend到Avatar转发 - 异步优化性能测试               ║
╚══════════════════════════════════════════════════════════════╝

使用说明:
1. 确保Backend服务运行在 localhost:8203
2. 确保Avatar服务运行在 localhost:8606
3. 运行此脚本进行性能测试

注意: 某些端点需要JWT认证，测试前请先登录获取token
""")
    
    # 运行测试
    try:
        # 首先快速检查
        asyncio.run(quick_test())
        
        # 询问是否继续完整测试
        print("\n  快速检查完成")
        response = input("是否继续完整性能测试？(y/n): ")
        
        if response.lower() == 'y':
            asyncio.run(run_performance_tests())
        else:
            print("测试已取消")
            
    except KeyboardInterrupt:
        print("\n\n  测试被用户中断")
    except Exception as e:
        print(f"\n 测试失败: {e}")
        import traceback
        traceback.print_exc()

