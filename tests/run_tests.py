"""
测试运行器
运行所有测试并生成报告
"""
import unittest
import sys
import os
from pathlib import Path
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("量化交易AI系统 - 测试套件")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2,
        descriptions=True,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # 生成测试报告
    generate_test_report(result, end_time - start_time)
    
    return result

def run_specific_tests(test_modules):
    """运行特定测试模块"""
    print("=" * 60)
    print("量化交易AI系统 - 特定测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试模块: {', '.join(test_modules)}")
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module in test_modules:
        try:
            # 动态导入测试模块
            module_path = f"tests.{module}"
            test_module = __import__(module_path, fromlist=[''])
            
            # 添加测试用例
            tests = loader.loadTestsFromModule(test_module)
            suite.addTests(tests)
            
        except ImportError as e:
            print(f"警告: 无法导入测试模块 {module}: {e}")
            continue
    
    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2,
        descriptions=True,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # 生成测试报告
    generate_test_report(result, end_time - start_time)
    
    return result

def generate_test_report(result, duration):
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("测试报告")
    print("=" * 60)
    
    # 基本统计
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed}")
    print(f"失败: {failures}")
    print(f"错误: {errors}")
    print(f"跳过: {skipped}")
    print(f"成功率: {(passed / total_tests * 100):.1f}%" if total_tests > 0 else "0.0%")
    print(f"运行时间: {duration:.2f}秒")
    
    # 详细结果
    if failures:
        print("\n失败的测试:")
        print("-" * 40)
        for test, traceback in result.failures:
            print(f"❌ {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors:
        print("\n错误的测试:")
        print("-" * 40)
        for test, traceback in result.errors:
            print(f"💥 {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # 生成JSON报告
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "duration": duration,
        "total_tests": total_tests,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0.0,
        "test_results": []
    }
    
    # 添加测试结果详情
    for test, traceback in result.failures:
        report_data["test_results"].append({
            "test": str(test),
            "status": "FAILED",
            "error": traceback
        })
    
    for test, traceback in result.errors:
        report_data["test_results"].append({
            "test": str(test),
            "status": "ERROR",
            "error": traceback
        })
    
    # 保存报告
    report_file = Path("tests/test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n测试报告已保存到: {report_file}")
    
    # 返回状态
    if failures == 0 and errors == 0:
        print("\n✅ 所有测试通过!")
        return True
    else:
        print(f"\n❌ 测试失败: {failures} 个失败, {errors} 个错误")
        return False

def run_performance_tests():
    """运行性能测试"""
    print("=" * 60)
    print("性能测试")
    print("=" * 60)
    
    import time
    import psutil
    import gc
    
    # 获取系统信息
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"初始内存使用: {initial_memory:.2f} MB")
    
    # 运行测试
    start_time = time.time()
    result = run_all_tests()
    end_time = time.time()
    
    # 获取最终内存使用
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_usage = final_memory - initial_memory
    
    print(f"\n性能指标:")
    print(f"总运行时间: {end_time - start_time:.2f}秒")
    print(f"内存使用: {memory_usage:.2f} MB")
    print(f"平均每个测试: {(end_time - start_time) / result.testsRun:.3f}秒" if result.testsRun > 0 else "0秒")
    
    return result

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='量化交易AI系统测试运行器')
    parser.add_argument('--module', '-m', nargs='+', help='运行特定测试模块')
    parser.add_argument('--performance', '-p', action='store_true', help='运行性能测试')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.performance:
        result = run_performance_tests()
    elif args.module:
        result = run_specific_tests(args.module)
    else:
        result = run_all_tests()
    
    # 根据结果设置退出码
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
