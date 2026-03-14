"""
Portfolio Configuration Module
管理股票组合配置
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class AllocationType(Enum):
    """配置类型"""
    AMOUNT = "amount"  # 金额
    RATIO = "ratio"    # 比例


class HoldingType(Enum):
    """持仓类型"""
    INDEX = "index"    # 指数
    STOCK = "stock"    # 个股


@dataclass
class Holding:
    """持仓信息"""
    symbol: str                    # 代码
    name: str                      # 名称
    holding_type: HoldingType      # 类型
    allocation_type: AllocationType # 配置类型
    value: float                   # 金额或比例
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Holding':
        """从字典创建持仓对象"""
        return cls(
            symbol=data['symbol'],
            name=data['name'],
            holding_type=HoldingType(data['type']),
            allocation_type=AllocationType(data['allocation_type']),
            value=float(data['value'])
        )
    
    def get_weight(self, total_amount: float) -> float:
        """
        获取持仓权重
        
        Args:
            total_amount: 总金额
            
        Returns:
            持仓权重（0-1之间）
        """
        if self.allocation_type == AllocationType.RATIO:
            return self.value / 100.0
        else:
            return self.value / total_amount if total_amount > 0 else 0


class Portfolio:
    """投资组合"""
    
    def __init__(self, holdings: List[Holding]):
        self.holdings = holdings
        self._total_amount = None
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'Portfolio':
        """从配置创建组合"""
        holdings = [Holding.from_dict(h) for h in config['portfolio']['holdings']]
        return cls(holdings)
    
    def get_total_amount(self) -> float:
        """获取总金额"""
        if self._total_amount is None:
            # 计算所有金额类型的总和
            amount_sum = sum(
                h.value for h in self.holdings 
                if h.allocation_type == AllocationType.AMOUNT
            )
            
            # 计算所有比例类型的总和
            ratio_sum = sum(
                h.value for h in self.holdings 
                if h.allocation_type == AllocationType.RATIO
            )
            
            # 如果有比例配置但没有金额配置，则无法计算总金额
            if ratio_sum > 0 and amount_sum == 0:
                self._total_amount = 1.0
                return self._total_amount
            
            # 总金额 = 明确金额 / (1 - 总比例)
            if ratio_sum < 100:
                self._total_amount = amount_sum / (1 - ratio_sum / 100.0)
            else:
                self._total_amount = amount_sum
        
        return self._total_amount
    
    def get_holding_weights(self) -> Dict[str, float]:
        """获取所有持仓权重"""
        if not self.holdings:
            return {}

        ratio_sum = sum(
            h.value for h in self.holdings
            if h.allocation_type == AllocationType.RATIO
        )
        amount_sum = sum(
            h.value for h in self.holdings
            if h.allocation_type == AllocationType.AMOUNT
        )

        # 只有比例时，按比例归一化
        if ratio_sum > 0 and amount_sum == 0:
            return {
                h.symbol: (h.value / ratio_sum)
                for h in self.holdings
            }

        total = self.get_total_amount()
        return {
            h.symbol: h.get_weight(total)
            for h in self.holdings
        }
    
    def get_symbols(self) -> List[str]:
        """获取所有代码"""
        return [h.symbol for h in self.holdings]
    
    def get_holding(self, symbol: str) -> Holding:
        """根据代码获取持仓"""
        for h in self.holdings:
            if h.symbol == symbol:
                return h
        raise ValueError(f"未找到代码为 {symbol} 的持仓")
