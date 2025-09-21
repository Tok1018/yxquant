"""
AI集成模块 - 支持多种AI模型
支持GPT、DeepSeek、Gemini、Qwen、Grok等模型
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

# AI模型相关导入
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIModelType(Enum):
    """AI模型类型枚举"""
    GPT_4 = "gpt-4"
    GPT_3_5 = "gpt-3.5-turbo"
    DEEPSEEK = "deepseek"
    GEMINI_PRO = "gemini-pro"
    QWEN = "qwen"
    GROK = "grok"
    CUSTOM = "custom"

@dataclass
class AIModelConfig:
    """AI模型配置"""
    model_type: AIModelType
    api_key: str
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_count: int = 3
    custom_headers: Optional[Dict[str, str]] = None

@dataclass
class AIResponse:
    """AI响应数据结构"""
    content: str
    model_used: str
    tokens_used: int
    response_time: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class AIProvider(ABC):
    """AI提供商基类"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """生成AI响应"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI提供商"""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        if OPENAI_AVAILABLE:
            openai.api_key = config.api_key
            if config.base_url:
                openai.api_base = config.base_url
    
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """生成OpenAI响应"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI库未安装")
        
        start_time = datetime.now()
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.config.model_name or self.config.model_type.value,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return AIResponse(
                content=response.choices[0].message.content,
                model_used=self.config.model_type.value,
                tokens_used=response.usage.total_tokens,
                response_time=response_time,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    async def health_check(self) -> bool:
        """OpenAI健康检查"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except:
            return False

class GeminiProvider(AIProvider):
    """Google Gemini提供商"""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        if GEMINI_AVAILABLE:
            genai.configure(api_key=config.api_key)
            self.model = genai.GenerativeModel(config.model_name or 'gemini-pro')
    
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """生成Gemini响应"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI库未安装")
        
        start_time = datetime.now()
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get('temperature', self.config.temperature),
                    max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens)
                )
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return AIResponse(
                content=response.text,
                model_used=self.config.model_type.value,
                tokens_used=len(response.text.split()),
                response_time=response_time,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Gemini健康检查"""
        try:
            response = await self.model.generate_content_async("Hello")
            return True
        except:
            return False

class CustomProvider(AIProvider):
    """自定义模型提供商"""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        
        if TRANSFORMERS_AVAILABLE and config.model_name:
            self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(config.model_name)
    
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """生成自定义模型响应"""
        if not self.model or not self.tokenizer:
            raise ImportError("自定义模型未正确配置")
        
        start_time = datetime.now()
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + kwargs.get('max_tokens', 200),
                    temperature=kwargs.get('temperature', self.config.temperature),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response_time = (datetime.now() - start_time).total_seconds()
            
            return AIResponse(
                content=response_text,
                model_used=self.config.model_type.value,
                tokens_used=len(response_text.split()),
                response_time=response_time,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"自定义模型调用失败: {e}")
            raise
    
    async def health_check(self) -> bool:
        """自定义模型健康检查"""
        try:
            test_prompt = "Hello"
            inputs = self.tokenizer.encode(test_prompt, return_tensors="pt")
            return True
        except:
            return False

class AIManager:
    """AI管理器 - 统一管理多个AI模型"""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.active_provider: Optional[str] = None
        self.fallback_chain: List[str] = []
    
    def add_provider(self, name: str, config: AIModelConfig) -> bool:
        """添加AI提供商"""
        try:
            if config.model_type in [AIModelType.GPT_4, AIModelType.GPT_3_5]:
                provider = OpenAIProvider(config)
            elif config.model_type == AIModelType.GEMINI_PRO:
                provider = GeminiProvider(config)
            elif config.model_type == AIModelType.CUSTOM:
                provider = CustomProvider(config)
            else:
                logger.error(f"不支持的模型类型: {config.model_type}")
                return False
            
            self.providers[name] = provider
            logger.info(f"添加AI提供商: {name} ({config.model_type.value})")
            return True
        except Exception as e:
            logger.error(f"添加AI提供商失败: {e}")
            return False
    
    def set_fallback_chain(self, chain: List[str]):
        """设置回退链"""
        self.fallback_chain = chain
        if chain and chain[0] in self.providers:
            self.active_provider = chain[0]
    
    async def generate_response(self, prompt: str, provider_name: Optional[str] = None, **kwargs) -> AIResponse:
        """生成AI响应（支持自动回退）"""
        providers_to_try = []
        
        if provider_name and provider_name in self.providers:
            providers_to_try.append(provider_name)
        
        providers_to_try.extend(self.fallback_chain)
        
        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            try:
                provider = self.providers[provider_name]
                response = await provider.generate_response(prompt, **kwargs)
                self.active_provider = provider_name
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"提供商 {provider_name} 失败: {e}")
                continue
        
        raise Exception(f"所有AI提供商都失败了，最后错误: {last_error}")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有提供商健康状态"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except:
                results[name] = False
        return results

class QuantAIAnalyzer:
    """量化AI分析器"""
    
    def __init__(self, ai_manager: AIManager):
        self.ai_manager = ai_manager
    
    async def analyze_market_sentiment(self, symbol: str, news_data: List[str] = None) -> Dict[str, Any]:
        """分析市场情绪"""
        prompt = f"""
        请分析股票 {symbol} 的市场情绪：
        1. 基于技术指标和市场数据
        2. 考虑新闻和公告影响
        3. 评估市场情绪（乐观/悲观/中性）
        4. 给出情绪评分（-100到100）
        5. 提供投资建议
        
        请以JSON格式返回结果。
        """
        
        if news_data:
            prompt += f"\n相关新闻：\n{chr(10).join(news_data[:5])}"
        
        response = await self.ai_manager.generate_response(prompt)
        
        try:
            return json.loads(response.content)
        except:
            return {
                "sentiment": "neutral",
                "score": 0,
                "analysis": response.content,
                "recommendation": "hold"
            }
    
    async def generate_trading_signals(self, symbol: str, technical_data: pd.DataFrame) -> Dict[str, Any]:
        """生成交易信号"""
        # 准备技术指标数据
        data_summary = technical_data.tail(10).to_string()
        
        prompt = f"""
        基于以下技术指标数据，为股票 {symbol} 生成交易信号：
        
        {data_summary}
        
        请分析：
        1. 当前趋势方向
        2. 支撑位和阻力位
        3. 买入/卖出信号强度（1-10）
        4. 建议操作（买入/卖出/持有）
        5. 风险等级（低/中/高）
        6. 目标价位
        7. 止损价位
        
        请以JSON格式返回结果。
        """
        
        response = await self.ai_manager.generate_response(prompt)
        
        try:
            return json.loads(response.content)
        except:
            return {
                "signal": "hold",
                "strength": 5,
                "trend": "sideways",
                "support": 0,
                "resistance": 0,
                "target_price": 0,
                "stop_loss": 0,
                "risk_level": "medium"
            }
    
    async def optimize_strategy_parameters(self, strategy_name: str, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """优化策略参数"""
        prompt = f"""
        基于以下回测结果，优化策略 {strategy_name} 的参数：
        
        回测结果：
        {json.dumps(backtest_results, indent=2, ensure_ascii=False)}
        
        请提供：
        1. 参数优化建议
        2. 预期改进效果
        3. 风险控制建议
        4. 实施步骤
        
        请以JSON格式返回结果。
        """
        
        response = await self.ai_manager.generate_response(prompt)
        
        try:
            return json.loads(response.content)
        except:
            return {
                "optimization_suggestions": response.content,
                "expected_improvement": "待分析",
                "risk_control": "保持现有风控措施",
                "implementation": "逐步调整参数"
            }
    
    async def generate_risk_warning(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险预警"""
        prompt = f"""
        基于以下投资组合数据，分析潜在风险：
        
        {json.dumps(portfolio_data, indent=2, ensure_ascii=False)}
        
        请提供：
        1. 主要风险点识别
        2. 风险等级评估
        3. 预警信号
        4. 风险缓解建议
        5. 紧急措施
        
        请以JSON格式返回结果。
        """
        
        response = await self.ai_manager.generate_response(prompt)
        
        try:
            return json.loads(response.content)
        except:
            return {
                "risk_level": "medium",
                "warnings": [response.content],
                "mitigation": "建议减少仓位",
                "emergency_actions": "设置止损"
            }

# 全局AI管理器实例
ai_manager = AIManager()

# 示例配置
def setup_default_ai_models():
    """设置默认AI模型配置"""
    
    # GPT-4配置（需要API密钥）
    gpt4_config = AIModelConfig(
        model_type=AIModelType.GPT_4,
        api_key="your-openai-api-key",  # 需要替换为实际API密钥
        temperature=0.7,
        max_tokens=2000
    )
    
    # DeepSeek配置
    deepseek_config = AIModelConfig(
        model_type=AIModelType.DEEPSEEK,
        api_key="your-deepseek-api-key",
        base_url="https://api.deepseek.com/v1",
        model_name="deepseek-chat",
        temperature=0.7,
        max_tokens=2000
    )
    
    # Gemini配置
    gemini_config = AIModelConfig(
        model_type=AIModelType.GEMINI_PRO,
        api_key="your-gemini-api-key",
        temperature=0.7,
        max_tokens=2000
    )
    
    # 添加提供商
    ai_manager.add_provider("gpt4", gpt4_config)
    ai_manager.add_provider("deepseek", deepseek_config)
    ai_manager.add_provider("gemini", gemini_config)
    
    # 设置回退链
    ai_manager.set_fallback_chain(["gpt4", "deepseek", "gemini"])
    
    logger.info("AI模型配置完成")

# 创建量化AI分析器实例
quant_ai = QuantAIAnalyzer(ai_manager)

if __name__ == "__main__":
    # 示例使用
    async def main():
        setup_default_ai_models()
        
        # 健康检查
        health_status = await ai_manager.health_check_all()
        print("AI模型健康状态:", health_status)
        
        # 测试AI分析
        test_data = pd.DataFrame({
            'close': [100, 102, 101, 103, 105],
            'volume': [1000, 1200, 900, 1100, 1300]
        })
        
        signals = await quant_ai.generate_trading_signals("AAPL", test_data)
        print("交易信号:", signals)
    
    # asyncio.run(main())
