#!/usr/bin/env python3
"""
Virtual Tutor System - Test Suite Runner
Runs pre-flight checks for TTS, Video Generation, and LLM components
"""

import sys
import time
from test_tts_generation import run_tts_generation_tests
from test_video_generation import run_video_generation_tests
from test_llm_response import run_llm_response_tests


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 100)
    print(f" {title}")
    print("=" * 100)


def main():
    """Run all tests"""
    print_header("VIRTUAL TUTOR SYSTEM - COMPREHENSIVE TEST SUITE")
    print("\n这套测试用于检查系统各个组件的配置和依赖")
    print("This test suite verifies configuration and dependencies for all components")

    total_start_time = time.time()

    # Run TTS tests
    print_header("1. TTS 生成测试 (TTS Generation Tests)")
    print("\n检查 EdgeTTS 和 Tacotron 模型的配置")
    print("Checking EdgeTTS and Tacotron model configuration")
    time.sleep(1)
    run_tts_generation_tests()

    time.sleep(3)

    # Run video tests
    print_header("2. 视频生成测试 (Video Generation Tests)")
    print("\n检查视频生成组件的配置和依赖")
    print("Checking video generation component configuration and dependencies")
    time.sleep(1)
    run_video_generation_tests()

    time.sleep(3)

    # Run LLM tests
    print_header("3. LLM 回复测试 (LLM Response Tests)")
    print("\n检查 LLM 组件的配置和依赖")
    print("Checking LLM component configuration and dependencies")
    time.sleep(1)
    run_llm_response_tests()

    # Total time
    total_elapsed_time = time.time() - total_start_time

    print_header("测试套件完成 (TEST SUITE COMPLETED)")
    print(f"\n总执行时间: {total_elapsed_time:.2f} 秒")
    print(f"Total execution time: {total_elapsed_time:.2f} seconds")
    print(f"总执行时间: {total_elapsed_time / 60:.2f} 分钟")
    print(f"Total execution time: {total_elapsed_time / 60:.2f} minutes")

    print("\n" + "=" * 100)
    print("下一步 (NEXT STEPS)")
    print("=" * 100)
    print("""
1. 查看上面的测试输出 (Review test output above)
   - ✓ PASSED: 该组件已配置正确 (Component is properly configured)
   - ✗ FAILED: 需要进一步设置 (Requires further setup)
   - ⚠ WARNING: 某些功能可能不完整 (Some features may be incomplete)

2. 运行单个测试套件 (Run individual test suites):
   python test_tts_generation.py
   python test_video_generation.py
   python test_llm_response.py

3. 故障排除 (Troubleshooting):
   - 检查服务是否运行 (Check if services are running)
   - 查看服务日志获取详细错误信息 (Check service logs for detailed errors)
   - 验证网络连接和端口可用性 (Verify network and port availability)

4. 运行完整集成测试 (Run full integration tests):
   - 启动所有必需的服务 (Start all required services)
   - 创建自定义测试脚本 (Create custom test scripts)
   - 验证端到端功能 (Verify end-to-end functionality)
    """)

    print("=" * 100)
    print("测试套件信息 (TEST SUITE INFORMATION)")
    print("=" * 100)
    print("""
测试类型 (Test Type): 预检查测试 (Pre-flight checks)
- 验证配置文件存在 (Verify configuration files)
- 检查依赖模块 (Check dependency modules)
- 测试服务连接 (Test service connectivity)
- 检查文件结构 (Verify file structure)

注意 (Notes):
- 这些是轻量级的预检查测试，不运行完整的功能测试
- 需要配置正确的服务地址和端口
- 某些检查可能会失败，但系统仍可工作（例如，可选依赖）

建议 (Recommendations):
- 定期运行这套测试以验证系统配置
- 在部署新版本前运行测试
- 调试问题时作为第一步运行
    """)

    print("=" * 100)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ 测试被用户中断 (Test suite interrupted by user)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 发生错误 (Unexpected error): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
