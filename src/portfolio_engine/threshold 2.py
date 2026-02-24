"""
Threshold Manager and Alert System
阈值管理和警报系统
"""
from enum import Enum
from typing import Dict, List
from dataclasses import dataclass

from .volatility import PortfolioVolatilityResult


class AlertLevel(Enum):
    """警报级别"""
    NONE = "none"           # 无警报
    WARNING = "warning"     # 警告
    ALERT = "alert"         # 警报


@dataclass
class ThresholdConfig:
    """阈值配置"""
    portfolio_warning: float      # 组合警告阈值
    portfolio_alert: float        # 组合警报阈值
    individual_warning: float     # 个股警告阈值
    individual_alert: float       # 个股警报阈值
    consecutive_warning: int      # 连续天数警告
    consecutive_alert: int        # 连续天数警报
    
    @classmethod
    def from_config(cls, config: Dict) -> 'ThresholdConfig':
        """从配置文件加载"""
        thresholds = config['thresholds']
        return cls(
            portfolio_warning=thresholds['portfolio_volatility']['warning'],
            portfolio_alert=thresholds['portfolio_volatility']['alert'],
            individual_warning=thresholds['individual_volatility']['warning'],
            individual_alert=thresholds['individual_volatility']['alert'],
            consecutive_warning=thresholds['consecutive_days']['warning'],
            consecutive_alert=thresholds['consecutive_days']['alert']
        )


@dataclass
class AlertResult:
    """警报结果"""
    level: AlertLevel
    portfolio_level: AlertLevel
    individual_alerts: List[tuple]  # (symbol, name, level)
    message: str
    should_notify: bool
    
    def __str__(self) -> str:
        if self.level == AlertLevel.NONE:
            return "当前波动正常，无需关注"
        
        level_label = "[WARNING]" if self.level == AlertLevel.WARNING else "[ALERT]"
        return f"{level_label} {self.message}"


class ThresholdManager:
    """阈值管理器"""
    
    def __init__(self, config: ThresholdConfig):
        self.config = config
    
    def check_portfolio_level(self, volatility: float) -> AlertLevel:
        """
        检查组合波动级别
        
        Args:
            volatility: 组合波动率
            
        Returns:
            警报级别
        """
        if volatility >= self.config.portfolio_alert:
            return AlertLevel.ALERT
        elif volatility >= self.config.portfolio_warning:
            return AlertLevel.WARNING
        return AlertLevel.NONE
    
    def check_individual_level(self, volatility: float) -> AlertLevel:
        """
        检查个股波动级别
        
        Args:
            volatility: 个股波动率
            
        Returns:
            警报级别
        """
        abs_vol = abs(volatility)
        if abs_vol >= self.config.individual_alert:
            return AlertLevel.ALERT
        elif abs_vol >= self.config.individual_warning:
            return AlertLevel.WARNING
        return AlertLevel.NONE
    
    def evaluate(self, portfolio_result: PortfolioVolatilityResult) -> AlertResult:
        """
        评估组合波动并生成警报
        
        Args:
            portfolio_result: 组合波动率结果
            
        Returns:
            警报结果
        """
        # 检查组合级别
        portfolio_level = self.check_portfolio_level(portfolio_result.total_volatility)
        
        # 检查个股级别
        individual_alerts = []
        max_individual_level = AlertLevel.NONE
        
        for result in portfolio_result.individual_results:
            level = self.check_individual_level(result.change_pct)
            if level != AlertLevel.NONE:
                individual_alerts.append((result.symbol, result.name, level))
                if level == AlertLevel.ALERT:
                    max_individual_level = AlertLevel.ALERT
                elif level == AlertLevel.WARNING and max_individual_level == AlertLevel.NONE:
                    max_individual_level = AlertLevel.WARNING
        
        # 确定总体级别
        overall_level = max(portfolio_level, max_individual_level, key=lambda x: x.value)
        
        # 生成消息
        message = self._generate_message(
            portfolio_level,
            portfolio_result,
            individual_alerts
        )
        
        # 是否需要通知
        should_notify = overall_level != AlertLevel.NONE
        
        return AlertResult(
            level=overall_level,
            portfolio_level=portfolio_level,
            individual_alerts=individual_alerts,
            message=message,
            should_notify=should_notify
        )
    
    def _generate_message(
        self,
        portfolio_level: AlertLevel,
        portfolio_result: PortfolioVolatilityResult,
        individual_alerts: List[tuple]
    ) -> str:
        """生成警报消息"""
        messages = []
        
        # 组合级别消息
        if portfolio_level == AlertLevel.ALERT:
            messages.append(
                f"[ALERT] 组合总波动 {portfolio_result.total_volatility:.2f}% "
                f"超过警报阈值 {self.config.portfolio_alert}%"
            )
        elif portfolio_level == AlertLevel.WARNING:
            messages.append(
                f"[WARNING] 组合总波动 {portfolio_result.total_volatility:.2f}% "
                f"超过警告阈值 {self.config.portfolio_warning}%"
            )
        
        # 个股级别消息
        if individual_alerts:
            alert_items = [item for item in individual_alerts if item[2] == AlertLevel.ALERT]
            warning_items = [item for item in individual_alerts if item[2] == AlertLevel.WARNING]
            
            if alert_items:
                alert_names = ", ".join([f"{item[1]}({item[0]})" for item in alert_items])
                messages.append(f"[ALERT] 以下持仓波动异常: {alert_names}")
            
            if warning_items:
                warning_names = ", ".join([f"{item[1]}({item[0]})" for item in warning_items])
                messages.append(f"[WARNING] 以下持仓波动较大: {warning_names}")
        
        if not messages:
            return "当前组合波动在正常范围内"
        
        return "\n".join(messages)
