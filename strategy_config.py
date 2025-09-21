"""
策略配置管理模块
支持策略的添加、配置、启用/禁用等功能
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """策略类型"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    CUSTOM = "custom"

class StrategyStatus(Enum):
    """策略状态"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    TESTING = "testing"

@dataclass
class StrategyParameter:
    """策略参数"""
    name: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    description: str = ""
    parameter_type: str = "float"  # float, int, bool, string, choice

@dataclass
class StrategyConfig:
    """策略配置"""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    status: StrategyStatus
    parameters: Dict[str, StrategyParameter]
    created_at: datetime
    updated_at: datetime
    created_by: str = "system"
    version: str = "1.0.0"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class StrategyConfigManager:
    """策略配置管理器"""
    
    def __init__(self, config_file: str = "strategy_configs.json"):
        self.config_file = config_file
        self.strategies: Dict[str, StrategyConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """加载策略配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for strategy_id, config_data in data.items():
                        # 转换枚举类型
                        config_data['strategy_type'] = StrategyType(config_data['strategy_type'])
                        config_data['status'] = StrategyStatus(config_data['status'])
                        config_data['created_at'] = datetime.fromisoformat(config_data['created_at'])
                        config_data['updated_at'] = datetime.fromisoformat(config_data['updated_at'])
                        
                        # 转换参数
                        parameters = {}
                        for param_name, param_data in config_data['parameters'].items():
                            parameters[param_name] = StrategyParameter(**param_data)
                        config_data['parameters'] = parameters
                        
                        self.strategies[strategy_id] = StrategyConfig(**config_data)
                logger.info(f"加载了 {len(self.strategies)} 个策略配置")
            except Exception as e:
                logger.error(f"加载策略配置失败: {e}")
                self._create_default_configs()
        else:
            self._create_default_configs()
    
    def _create_default_configs(self):
        """创建默认策略配置"""
        default_strategies = [
            {
                "id": "momentum_basic",
                "name": "基础动量策略",
                "description": "基于价格动量的简单策略",
                "strategy_type": StrategyType.MOMENTUM,
                "status": StrategyStatus.ENABLED,
                "parameters": {
                    "lookback_period": StrategyParameter(
                        name="lookback_period",
                        value=20,
                        min_value=5,
                        max_value=50,
                        step=1,
                        description="回望周期",
                        parameter_type="int"
                    ),
                    "threshold": StrategyParameter(
                        name="threshold",
                        value=0.02,
                        min_value=0.01,
                        max_value=0.1,
                        step=0.01,
                        description="动量阈值",
                        parameter_type="float"
                    )
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "tags": ["momentum", "basic"]
            },
            {
                "id": "mean_reversion_basic",
                "name": "基础均值回归策略",
                "description": "基于价格均值回归的策略",
                "strategy_type": StrategyType.MEAN_REVERSION,
                "status": StrategyStatus.ENABLED,
                "parameters": {
                    "lookback_period": StrategyParameter(
                        name="lookback_period",
                        value=20,
                        min_value=5,
                        max_value=50,
                        step=1,
                        description="回望周期",
                        parameter_type="int"
                    ),
                    "deviation_threshold": StrategyParameter(
                        name="deviation_threshold",
                        value=2.0,
                        min_value=1.0,
                        max_value=3.0,
                        step=0.1,
                        description="标准差倍数",
                        parameter_type="float"
                    )
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "tags": ["mean_reversion", "basic"]
            },
            {
                "id": "breakout_basic",
                "name": "基础突破策略",
                "description": "基于价格突破的策略",
                "strategy_type": StrategyType.BREAKOUT,
                "status": StrategyStatus.ENABLED,
                "parameters": {
                    "lookback_period": StrategyParameter(
                        name="lookback_period",
                        value=20,
                        min_value=5,
                        max_value=50,
                        step=1,
                        description="回望周期",
                        parameter_type="int"
                    ),
                    "breakout_threshold": StrategyParameter(
                        name="breakout_threshold",
                        value=0.02,
                        min_value=0.01,
                        max_value=0.1,
                        step=0.01,
                        description="突破阈值",
                        parameter_type="float"
                    )
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "tags": ["breakout", "basic"]
            }
        ]
        
        for strategy_data in default_strategies:
            strategy = StrategyConfig(**strategy_data)
            self.strategies[strategy.id] = strategy
        
        self._save_configs()
        logger.info("创建了默认策略配置")
    
    def _save_configs(self):
        """保存策略配置"""
        try:
            data = {}
            for strategy_id, strategy in self.strategies.items():
                strategy_dict = asdict(strategy)
                # 转换枚举和日期为字符串
                strategy_dict['strategy_type'] = strategy.strategy_type.value
                strategy_dict['status'] = strategy.status.value
                strategy_dict['created_at'] = strategy.created_at.isoformat()
                strategy_dict['updated_at'] = strategy.updated_at.isoformat()
                
                # 转换参数
                parameters = {}
                for param_name, param in strategy.parameters.items():
                    parameters[param_name] = asdict(param)
                strategy_dict['parameters'] = parameters
                
                data[strategy_id] = strategy_dict
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("策略配置已保存")
        except Exception as e:
            logger.error(f"保存策略配置失败: {e}")
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyConfig]:
        """获取策略配置"""
        return self.strategies.get(strategy_id)
    
    def get_all_strategies(self) -> Dict[str, StrategyConfig]:
        """获取所有策略配置"""
        return self.strategies.copy()
    
    def get_enabled_strategies(self) -> Dict[str, StrategyConfig]:
        """获取启用的策略"""
        return {k: v for k, v in self.strategies.items() if v.status == StrategyStatus.ENABLED}
    
    def add_strategy(self, strategy: StrategyConfig) -> bool:
        """添加策略"""
        try:
            if strategy.id in self.strategies:
                logger.warning(f"策略 {strategy.id} 已存在")
                return False
            
            self.strategies[strategy.id] = strategy
            self._save_configs()
            logger.info(f"添加策略成功: {strategy.id}")
            return True
        except Exception as e:
            logger.error(f"添加策略失败: {e}")
            return False
    
    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> bool:
        """更新策略"""
        try:
            if strategy_id not in self.strategies:
                logger.warning(f"策略 {strategy_id} 不存在")
                return False
            
            strategy = self.strategies[strategy_id]
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
            
            strategy.updated_at = datetime.now()
            self._save_configs()
            logger.info(f"更新策略成功: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"更新策略失败: {e}")
            return False
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """删除策略"""
        try:
            if strategy_id not in self.strategies:
                logger.warning(f"策略 {strategy_id} 不存在")
                return False
            
            del self.strategies[strategy_id]
            self._save_configs()
            logger.info(f"删除策略成功: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"删除策略失败: {e}")
            return False
    
    def enable_strategy(self, strategy_id: str) -> bool:
        """启用策略"""
        return self.update_strategy(strategy_id, {"status": StrategyStatus.ENABLED})
    
    def disable_strategy(self, strategy_id: str) -> bool:
        """禁用策略"""
        return self.update_strategy(strategy_id, {"status": StrategyStatus.DISABLED})
    
    def update_strategy_parameters(self, strategy_id: str, parameters: Dict[str, Any]) -> bool:
        """更新策略参数"""
        try:
            if strategy_id not in self.strategies:
                logger.warning(f"策略 {strategy_id} 不存在")
                return False
            
            strategy = self.strategies[strategy_id]
            
            # 更新参数值
            for param_name, param_value in parameters.items():
                if param_name in strategy.parameters:
                    strategy.parameters[param_name].value = param_value
            
            strategy.updated_at = datetime.now()
            self._save_configs()
            logger.info(f"更新策略参数成功: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"更新策略参数失败: {e}")
            return False

# 全局策略配置管理器实例
strategy_config_manager = StrategyConfigManager()
