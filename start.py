"""
量化交易AI系统启动脚本
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database import db_manager
from ai_config_manager import ai_config_manager
from ai_integration import ai_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖包"""
    logger.info("检查依赖包...")
    
    # 核心依赖包
    core_packages = [
        'pandas', 'numpy', 'matplotlib', 'plotly',
        'yfinance', 'akshare', 'tushare', 'sklearn',
        'fastapi', 'uvicorn', 'pydantic'
    ]
    
    missing_core = []
    for package in core_packages:
        try:
            __import__(package)
        except ImportError:
            missing_core.append(package)
    
    if missing_core:
        logger.error(f"缺少核心依赖包: {missing_core}")
        logger.error("请运行: pip install -r requirements.txt")
        return False
    
    # 可选依赖包
    optional_packages = ['talib', 'openai', 'google.generativeai']
    missing_optional = []
    for package in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_optional:
        logger.warning(f"缺少可选依赖包: {missing_optional}")
        logger.warning("这些包不是必需的，但某些功能可能不可用")
    
    logger.info("核心依赖包检查通过")
    return True

def initialize_database():
    """初始化数据库"""
    logger.info("初始化数据库...")
    try:
        # 数据库会在DatabaseManager初始化时自动创建
        logger.info("数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

async def initialize_ai_models():
    """初始化AI模型"""
    logger.info("初始化AI模型...")
    try:
        # 设置AI模型
        ai_config_manager._setup_ai_models()
        
        # 检查可用模型
        health_status = await ai_manager.health_check_all()
        available_models = [model for model, status in health_status.items() if status]
        
        if available_models:
            logger.info(f"可用AI模型: {available_models}")
            logger.info(f"当前活跃模型: {ai_manager.active_provider}")
        else:
            logger.warning("没有可用的AI模型")
            logger.warning("请在 ai_config.json 中配置API密钥")
        
        return True
    except Exception as e:
        logger.error(f"AI模型初始化失败: {e}")
        return False

def show_system_info():
    """显示系统信息"""
    logger.info("=" * 60)
    logger.info("量化交易AI系统")
    logger.info("=" * 60)
    logger.info("功能特性:")
    logger.info("  ✓ 多AI模型支持 (GPT、DeepSeek、Gemini、Qwen、Grok)")
    logger.info("  ✓ 智能策略分析")
    logger.info("  ✓ 风险管理")
    logger.info("  ✓ 回测系统")
    logger.info("  ✓ Web API接口")
    logger.info("  ✓ 实时数据获取")
    logger.info("=" * 60)

def show_usage_examples():
    """显示使用示例"""
    logger.info("使用示例:")
    logger.info("1. 启动Web API服务:")
    logger.info("   python ai_api.py")
    logger.info("")
    logger.info("2. 运行演示脚本:")
    logger.info("   python ai_demo.py")
    logger.info("")
    logger.info("3. 配置AI模型:")
    logger.info("   编辑 ai_config.json 文件，添加API密钥")
    logger.info("")
    logger.info("4. 查看API文档:")
    logger.info("   访问 http://localhost:8000/docs")
    logger.info("=" * 60)

async def main():
    """主函数"""
    try:
        # 显示系统信息
        show_system_info()
        
        # 检查依赖
        if not check_dependencies():
            return
        
        # 初始化数据库
        if not initialize_database():
            return
        
        # 初始化AI模型
        await initialize_ai_models()
        
        # 显示使用示例
        show_usage_examples()
        
        logger.info("系统启动完成！")
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
