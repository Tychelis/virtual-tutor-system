#!/usr/bin/env python3
"""
完整的延迟对比测试工具
测试改前（原版）和改后（优化版）的性能差异

使用方法:
    python compare_latency.py
    
    # 自定义测试问题
    python compare_latency.py "What is deep learning?"
    
    # 多次测试取平均
    python compare_latency.py --rounds 3
    
    # 自动管理原版服务（启动测试后自动关闭）
    python compare_latency.py --auto-manage
"""

import requests
import time
import json
import sys
import subprocess
import os
import signal
from typing import Dict, Optional

class LatencyTester:
    """延迟测试器"""
    
    def __init__(self, auto_manage=False):
        self.original_url = "http://localhost:8610/chat/stream"  # 原版
        self.optimized_url = "http://localhost:8611/chat/stream"  # 优化版
        self.auto_manage = auto_manage
        self.original_process = None
        self.original_was_running = False
    
    def test_endpoint(self, url: str, question: str, label: str) -> Optional[Dict]:
        """测试单个端点"""
        print(f"\n{'='*70}")
        print(f" 测试: {label}")
        print(f"{'='*70}")
        print(f"问题: {question}")
        print(f"端点: {url}")
        print()
        
        payload = {
            "user_id": 1,
            "session_id": 1,
            "input": question
        }
        
        start_time = time.time()
        first_chunk_time = None
        chunks_received = 0
        total_content = ""
        
        try:
            with requests.post(url, json=payload, stream=True, timeout=60) as response:
                response.raise_for_status()
                
                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    
                    try:
                        data_str = line.replace("data: ", "")
                        chunk_data = json.loads(data_str)
                        
                        # 记录首字时间
                        if first_chunk_time is None and chunk_data.get("status") == "streaming":
                            first_chunk_time = time.time()
                            ttft = first_chunk_time - start_time
                            print(f" 首字延迟 (TTFT): {ttft:.3f}s")
                        
                        # 累积内容
                        if chunk_data.get("status") == "streaming":
                            content = chunk_data.get("chunk", "")
                            total_content += content
                            chunks_received += 1
                            
                            # 显示进度
                            if chunks_received % 20 == 0:
                                print(f"   已接收 {chunks_received} 个chunks...")
                        
                        # 完成
                        if chunk_data.get("status") == "finished":
                            total_time = time.time() - start_time
                            print(f" 完成!")
                            print(f"   总时间: {total_time:.3f}s")
                            print(f"   总chunks: {chunks_received}")
                            print(f"   响应长度: {len(total_content)} 字符")
                            
                            return {
                                "success": True,
                                "ttft": first_chunk_time - start_time if first_chunk_time else 0,
                                "total_time": total_time,
                                "chunks": chunks_received,
                                "response_length": len(total_content),
                                "response_preview": total_content[:200] + "..." if len(total_content) > 200 else total_content
                            }
                    
                    except json.JSONDecodeError:
                        continue
                
                # 如果没有收到finished信号
                if chunks_received > 0:
                    total_time = time.time() - start_time
                    return {
                        "success": False,
                        "ttft": first_chunk_time - start_time if first_chunk_time else 0,
                        "total_time": total_time,
                        "chunks": chunks_received,
                        "error": "No finished signal received"
                    }
        
        except requests.exceptions.Timeout:
            print(f" 超时错误")
            return {"success": False, "error": "Timeout"}
        
        except requests.exceptions.ConnectionError:
            print(f" 连接错误: 服务可能未启动")
            return {"success": False, "error": "Connection failed"}
        
        except Exception as e:
            print(f" 错误: {e}")
            return {"success": False, "error": str(e)}
    
    def check_service(self, port):
        """检查服务是否运行"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def start_original_service(self):
        """启动原版服务"""
        print("\n" + "="*70)
        print(" 自动服务管理")
        print("="*70)
        
        # 检查原版是否已经在运行
        if self.check_service(8610):
            print(" 原版服务 (8610) 已在运行")
            self.original_was_running = True
            return True
        
        print("  原版服务 (8610) 未运行")
        print(" 正在启动原版服务...")
        
        try:
            # 获取项目目录
            project_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 设置环境变量
            env = os.environ.copy()
            env['TAVILY_API_KEY'] = env.get('TAVILY_API_KEY', 'dummy-key-for-import')
            
            # 启动原版服务
            log_file = open('/tmp/llm_original_temp.log', 'w')
            self.original_process = subprocess.Popen(
                ['python', 'api_interface.py'],
                cwd=project_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                preexec_fn=os.setsid  # 创建新的进程组
            )
            
            # 等待服务启动
            print(" 等待服务启动...", end='', flush=True)
            max_wait = 30  # 最多等30秒
            for i in range(max_wait):
                time.sleep(1)
                if self.check_service(8610):
                    print(" ")
                    print(f" 原版服务已启动 (PID: {self.original_process.pid})")
                    return True
                print(".", end='', flush=True)
            
            print(" ")
            print(" 原版服务启动超时")
            return False
            
        except Exception as e:
            print(f" 启动原版服务失败: {e}")
            return False
    
    def stop_original_service(self):
        """停止原版服务"""
        if not self.auto_manage:
            return
        
        if self.original_was_running:
            print("\n 原版服务原本就在运行，保持运行状态")
            return
        
        if self.original_process:
            print("\n" + "="*70)
            print(" 清理临时服务")
            print("="*70)
            print(" 正在停止原版服务...")
            
            try:
                # 杀死整个进程组
                os.killpg(os.getpgid(self.original_process.pid), signal.SIGTERM)
                self.original_process.wait(timeout=5)
                print(" 原版服务已停止")
            except subprocess.TimeoutExpired:
                print("  强制停止...")
                os.killpg(os.getpgid(self.original_process.pid), signal.SIGKILL)
                print(" 原版服务已强制停止")
            except Exception as e:
                print(f"  停止服务时出错: {e}")
    
    def run_comparison(self, question: str, rounds: int = 1):
        """运行完整的对比测试"""
        print("\n" + "="*70)
        print(" 延迟对比测试")
        print("="*70)
        print(f"测试轮数: {rounds}")
        print(f"测试问题: {question}")
        print(f"自动管理: {'是' if self.auto_manage else '否'}")
        print("="*70)
        
        # 如果启用自动管理，先启动原版服务
        if self.auto_manage:
            if not self.start_original_service():
                print("\n 无法启动原版服务，测试终止")
                return
            print()  # 空行
        
        original_results = []
        optimized_results = []
        
        for round_num in range(1, rounds + 1):
            if rounds > 1:
                print(f"\n{'='*70}")
                print(f"第 {round_num}/{rounds} 轮测试")
                print("="*70)
            
            # 测试原版
            original_result = self.test_endpoint(
                self.original_url,
                question,
                f"原版 (改前) - 端口8610"
            )
            if original_result and original_result.get("success"):
                original_results.append(original_result)
            
            # 等待一下，避免缓存影响
            if rounds > 1:
                print("\n 等待3秒...")
                time.sleep(3)
            
            # 测试优化版
            optimized_result = self.test_endpoint(
                self.optimized_url,
                question,
                f"优化版 (改后) - 端口8611"
            )
            if optimized_result and optimized_result.get("success"):
                optimized_results.append(optimized_result)
            
            # 轮次间等待
            if round_num < rounds:
                print("\n 等待5秒后进行下一轮...")
                time.sleep(5)
        
        # 显示对比结果
        self.show_comparison(original_results, optimized_results, question)
        
        # 如果启用自动管理，测试后停止原版服务
        if self.auto_manage:
            self.stop_original_service()
    
    def show_comparison(self, original_results, optimized_results, question):
        """显示对比结果"""
        if not original_results or not optimized_results:
            print("\n 测试数据不完整，无法对比")
            return
        
        # 计算平均值
        def avg(results, key):
            values = [r[key] for r in results if key in r]
            return sum(values) / len(values) if values else 0
        
        original_ttft = avg(original_results, "ttft")
        optimized_ttft = avg(optimized_results, "ttft")
        original_total = avg(original_results, "total_time")
        optimized_total = avg(optimized_results, "total_time")
        
        ttft_improvement = ((original_ttft - optimized_ttft) / original_ttft) * 100 if original_ttft > 0 else 0
        total_improvement = ((original_total - optimized_total) / original_total) * 100 if original_total > 0 else 0
        
        print("\n" + "="*70)
        print(" 对比结果总结")
        print("="*70)
        
        print(f"\n测试问题: {question}")
        print(f"测试轮数: {len(original_results)}")
        
        print(f"\n{'指标':<20} {'原版(改前)':<15} {'优化版(改后)':<15} {'提升':<15}")
        print("-"*70)
        
        # 首字延迟 (TTFT) - 最重要的指标
        print(f"{' 首字延迟 (TTFT)':<20} {original_ttft:<15.3f}s {optimized_ttft:<15.3f}s ", end="")
        if ttft_improvement > 0:
            print(f" +{ttft_improvement:.1f}%")
        else:
            print(f" {ttft_improvement:.1f}%")
        
        # 总时间
        print(f"{'  总时间':<20} {original_total:<15.3f}s {optimized_total:<15.3f}s ", end="")
        if total_improvement > 0:
            print(f" +{total_improvement:.1f}%")
        else:
            print(f" {total_improvement:.1f}%")
        
        # Chunks
        original_chunks = avg(original_results, "chunks")
        optimized_chunks = avg(optimized_results, "chunks")
        print(f"{' Chunks数量':<20} {original_chunks:<15.0f} {optimized_chunks:<15.0f} -")
        
        # 响应长度
        original_len = avg(original_results, "response_length")
        optimized_len = avg(optimized_results, "response_length")
        print(f"{' 响应长度':<20} {original_len:<15.0f} {optimized_len:<15.0f} -")
        
        print("\n" + "="*70)
        print(" 总结")
        print("="*70)
        
        if ttft_improvement > 30:
            print(f" 优秀! 首字延迟提升了 {ttft_improvement:.1f}%")
            print(f"     用户等待时间从 {original_ttft:.2f}s 降至 {optimized_ttft:.2f}s")
        elif ttft_improvement > 10:
            print(f" 良好! 首字延迟提升了 {ttft_improvement:.1f}%")
        elif ttft_improvement > 0:
            print(f" 有改善，首字延迟提升了 {ttft_improvement:.1f}%")
        else:
            print(f"  首字延迟未改善，可能需要进一步优化")
        
        print("\n 说明:")
        print("   - 首字延迟 (TTFT) 是用户感知的关键指标")
        print("   - 优化目标是让用户更快看到响应开始")
        print("   - 总时间变长可能是因为生成了更详细的回答")
        
        # 显示响应预览
        if optimized_results and "response_preview" in optimized_results[0]:
            print("\n 优化版响应预览:")
            print("-"*70)
            print(optimized_results[0]["response_preview"])
            print("-"*70)
        
        print()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='延迟对比测试工具')
    parser.add_argument('question', nargs='?', 
                       default='What is machine learning?',
                       help='测试问题 (默认: What is machine learning?)')
    parser.add_argument('--rounds', '-r', type=int, default=1,
                       help='测试轮数 (默认: 1)')
    parser.add_argument('--check', action='store_true',
                       help='检查服务状态')
    parser.add_argument('--auto-manage', action='store_true',
                       help='自动启动原版服务并在测试后关闭')
    
    args = parser.parse_args()
    
    # 默认启用自动管理（如果没有明确指定check）
    auto_manage = args.auto_manage or (not args.check)
    
    tester = LatencyTester(auto_manage=auto_manage)
    
    # 检查服务状态
    if args.check:
        print("\n 检查服务状态...")
        print("-"*70)
        
        try:
            r1 = requests.get("http://localhost:8610/health", timeout=2)
            print(f" 原版服务 (8610): 运行中")
        except:
            print(f" 原版服务 (8610): 未运行")
        
        try:
            r2 = requests.get("http://localhost:8611/health", timeout=2)
            print(f" 优化版服务 (8611): 运行中")
        except:
            print(f" 优化版服务 (8611): 未运行")
        
        print("-"*70)
        return
    
    # 运行对比测试
    tester.run_comparison(args.question, args.rounds)


if __name__ == "__main__":
    tester = None
    try:
        # 创建tester实例以便在异常处理中使用
        import argparse
        parser = argparse.ArgumentParser(description='延迟对比测试工具')
        parser.add_argument('--auto-manage', action='store_true', help='自动管理原版服务')
        parser.add_argument('--check', action='store_true', help='检查服务状态')
        args, _ = parser.parse_known_args()
        
        auto_manage = args.auto_manage or (not args.check)
        tester = LatencyTester(auto_manage=auto_manage)
        
        main()
    except KeyboardInterrupt:
        print("\n\n  测试中断")
        if tester and tester.auto_manage:
            tester.stop_original_service()
        sys.exit(1)
    except Exception as e:
        print(f"\n 错误: {e}")
        import traceback
        traceback.print_exc()
        if tester and tester.auto_manage:
            tester.stop_original_service()
        sys.exit(1)

