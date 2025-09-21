"""
AI配置管理模块
管理AI模型的配置、API密钥、模型切换等
"""
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import asyncio

from ai_integration import AIModelConfig, AIModelType, ai_manager
from config import AI_CONFIG, PROJECT_ROOT

logger = logging.getLogger(__name__)

class AIConfigManager:
    """AI配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or str(PROJECT_ROOT / "ai_config.json")
        self.config = self._load_config()
        self._setup_ai_models()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载AI配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载AI配置失败: {e}")
        
        # 返回默认配置
        return {
            "models": {
                "gpt4": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://api.openai.com/v1",
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "timeout": 30,
                    "retry_count": 3,
                    "priority": 1
                },
                "deepseek": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://api.deepseek.com/v1",
                    "model_name": "deepseek-chat",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "timeout": 30,
                    "retry_count": 3,
                    "priority": 2
                },
                "gemini": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": None,
                    "model_name": "gemini-pro",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "timeout": 30,
                    "retry_count": 3,
                    "priority": 3
                },
                "qwen": {
                    "enabled": False,
                    "api_key": "",
                    "base_url": "https://dashscope.aliyuncs.com/api/v1",
                    "model_name": "qwen-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "timeout": 30,
                    "retry_count": 3,
                    "priority": 4
                },
                "grok": {
                    "enabled": False,
                    "api_key": "",
                    "base_url": "https://api.x.ai/v1",
                    "model_name": "grok-beta",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "timeout": 30,
                    "retry_count": 3,
                    "priority": 5
                }
            },
            "features": {
                "market_sentiment_analysis": True,
                "trading_signal_generation": True,
                "strategy_optimization": True,
                "risk_warning": True,
                "news_analysis": True,
                "technical_analysis_enhancement": True
            },
            "fallback_chain": ["gpt4", "deepseek", "gemini"],
            "last_updated": datetime.now().isoformat()
        }
    
    def _setup_ai_models(self):
        """设置AI模型"""
        enabled_models = []
        
        for model_name, config in self.config["models"].items():
            if not config.get("enabled", False):
                continue
            
            if not config.get("api_key"):
                logger.warning(f"模型 {model_name} 未配置API密钥，跳过")
                continue
            
            try:
                # 创建模型配置
                model_type = self._get_model_type(model_name)
                ai_config = AIModelConfig(
                    model_type=model_type,
                    api_key=config["api_key"],
                    base_url=config.get("base_url"),
                    model_name=config.get("model_name"),
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 2000),
                    timeout=config.get("timeout", 30),
                    retry_count=config.get("retry_count", 3)
                )
                
                # 添加到AI管理器
                success = ai_manager.add_provider(model_name, ai_config)
                if success:
                    enabled_models.append(model_name)
                    logger.info(f"成功添加AI模型: {model_name}")
                else:
                    logger.error(f"添加AI模型失败: {model_name}")
            
            except Exception as e:
                logger.error(f"设置AI模型 {model_name} 失败: {e}")
        
        # 设置回退链
        fallback_chain = [m for m in self.config["fallback_chain"] if m in enabled_models]
        if fallback_chain:
            ai_manager.set_fallback_chain(fallback_chain)
            logger.info(f"设置AI回退链: {fallback_chain}")
        else:
            logger.warning("没有可用的AI模型")
    
    def _get_model_type(self, model_name: str) -> AIModelType:
        """获取模型类型"""
        model_type_map = {
            "gpt4": AIModelType.GPT_4,
            "gpt3.5": AIModelType.GPT_3_5,
            "deepseek": AIModelType.DEEPSEEK,
            "gemini": AIModelType.GEMINI_PRO,
            "qwen": AIModelType.QWEN,
            "grok": AIModelType.GROK,
        }
        return model_type_map.get(model_name, AIModelType.CUSTOM)
    
    def save_config(self):
        """保存配置到文件"""
        try:
            self.config["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("AI配置已保存")
        except Exception as e:
            logger.error(f"保存AI配置失败: {e}")
    
    def update_model_config(self, model_name: str, config_updates: Dict[str, Any]):
        """更新模型配置"""
        if model_name not in self.config["models"]:
            logger.error(f"模型 {model_name} 不存在")
            return False
        
        try:
            self.config["models"][model_name].update(config_updates)
            self.save_config()
            
            # 重新设置AI模型
            self._setup_ai_models()
            
            logger.info(f"更新模型配置: {model_name}")
            return True
        except Exception as e:
            logger.error(f"更新模型配置失败: {e}")
            return False
    
    def set_api_key(self, model_name: str, api_key: str):
        """设置API密钥"""
        return self.update_model_config(model_name, {"api_key": api_key})
    
    def enable_model(self, model_name: str):
        """启用模型"""
        return self.update_model_config(model_name, {"enabled": True})
    
    def disable_model(self, model_name: str):
        """禁用模型"""
        return self.update_model_config(model_name, {"enabled": False})
    
    def set_fallback_chain(self, chain: List[str]):
        """设置回退链"""
        self.config["fallback_chain"] = chain
        self.save_config()
        
        # 更新AI管理器的回退链
        enabled_models = [m for m, config in self.config["models"].items() 
                         if config.get("enabled", False) and config.get("api_key")]
        valid_chain = [m for m in chain if m in enabled_models]
        ai_manager.set_fallback_chain(valid_chain)
        
        logger.info(f"设置回退链: {valid_chain}")
    
    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """获取模型状态"""
        status = {}
        for model_name, config in self.config["models"].items():
            status[model_name] = {
                "enabled": config.get("enabled", False),
                "has_api_key": bool(config.get("api_key")),
                "priority": config.get("priority", 999),
                "model_name": config.get("model_name", ""),
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 2000)
            }
        return status
    
    async def test_all_models(self) -> Dict[str, bool]:
        """测试所有模型"""
        results = {}
        for model_name in self.config["models"].keys():
            if model_name in ai_manager.providers:
                try:
                    # 发送简单测试请求
                    response = await ai_manager.generate_response(
                        "Hello, please respond with 'OK'",
                        provider_name=model_name,
                        max_tokens=10
                    )
                    results[model_name] = True
                    logger.info(f"模型 {model_name} 测试成功")
                except Exception as e:
                    results[model_name] = False
                    logger.error(f"模型 {model_name} 测试失败: {e}")
            else:
                results[model_name] = False
        
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        # 这里可以添加使用统计逻辑
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "model_usage": {}
        }
    
    def optimize_config(self):
        """优化配置"""
        # 根据使用统计优化配置
        enabled_models = [m for m, config in self.config["models"].items() 
                         if config.get("enabled", False) and config.get("api_key")]
        
        if not enabled_models:
            logger.warning("没有启用的模型，无法优化配置")
            return
        
        # 按优先级排序
        sorted_models = sorted(enabled_models, 
                             key=lambda x: self.config["models"][x].get("priority", 999))
        
        # 更新回退链
        self.set_fallback_chain(sorted_models)
        
        logger.info("配置优化完成")
    
    def export_config(self, file_path: str):
        """导出配置"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已导出到: {file_path}")
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
    
    def import_config(self, file_path: str):
        """导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 验证配置格式
            if "models" not in imported_config:
                raise ValueError("无效的配置文件格式")
            
            self.config = imported_config
            self.save_config()
            self._setup_ai_models()
            
            logger.info(f"配置已从 {file_path} 导入")
        except Exception as e:
            logger.error(f"导入配置失败: {e}")

class AIUsageTracker:
    """AI使用跟踪器"""
    
    def __init__(self):
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "model_usage": {},
            "daily_usage": {},
            "hourly_usage": {}
        }
    
    def track_request(self, model_name: str, success: bool, tokens: int = 0, cost: float = 0.0):
        """跟踪请求"""
        self.usage_stats["total_requests"] += 1
        
        if success:
            self.usage_stats["successful_requests"] += 1
        else:
            self.usage_stats["failed_requests"] += 1
        
        self.usage_stats["total_tokens"] += tokens
        self.usage_stats["total_cost"] += cost
        
        # 按模型统计
        if model_name not in self.usage_stats["model_usage"]:
            self.usage_stats["model_usage"][model_name] = {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "tokens": 0,
                "cost": 0.0
            }
        
        self.usage_stats["model_usage"][model_name]["requests"] += 1
        if success:
            self.usage_stats["model_usage"][model_name]["successful"] += 1
        else:
            self.usage_stats["model_usage"][model_name]["failed"] += 1
        
        self.usage_stats["model_usage"][model_name]["tokens"] += tokens
        self.usage_stats["model_usage"][model_name]["cost"] += cost
        
        # 按日期统计
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.usage_stats["daily_usage"]:
            self.usage_stats["daily_usage"][today] = 0
        self.usage_stats["daily_usage"][today] += 1
        
        # 按小时统计
        hour = datetime.now().strftime("%Y-%m-%d %H:00")
        if hour not in self.usage_stats["hourly_usage"]:
            self.usage_stats["hourly_usage"][hour] = 0
        self.usage_stats["hourly_usage"][hour] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.usage_stats.copy()
        
        # 计算成功率
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
        
        # 计算平均成本
        if stats["successful_requests"] > 0:
            stats["average_cost_per_request"] = stats["total_cost"] / stats["successful_requests"]
        else:
            stats["average_cost_per_request"] = 0.0
        
        return stats

# 创建全局实例
ai_config_manager = AIConfigManager()
ai_usage_tracker = AIUsageTracker()

if __name__ == "__main__":
    # 示例使用
    async def main():
        # 测试配置管理器
        print("AI模型状态:")
        status = ai_config_manager.get_model_status()
        for model, info in status.items():
            print(f"  {model}: 启用={info['enabled']}, API密钥={info['has_api_key']}")
        
        # 测试所有模型
        print("\n测试AI模型:")
        test_results = await ai_config_manager.test_all_models()
        for model, success in test_results.items():
            print(f"  {model}: {'成功' if success else '失败'}")
    
    # asyncio.run(main())
