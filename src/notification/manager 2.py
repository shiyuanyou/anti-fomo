"""
Notification System
通知系统 - 支持控制台、邮件、文件等多种通知方式
"""
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from portfolio_engine import PortfolioVolatilityResult
from portfolio_engine import AlertResult


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config: Dict):
        """
        初始化通知管理器
        
        Args:
            config: 通知配置
        """
        self.enabled = config.get('enabled', True)
        self.methods = config.get('methods', [])
    
    def send(
        self,
        portfolio_result: PortfolioVolatilityResult,
        alert_result: AlertResult,
        ai_analysis: Optional[str] = None
    ):
        """
        发送通知
        
        Args:
            portfolio_result: 组合波动结果
            alert_result: 警报结果
            ai_analysis: AI 分析结果
        """
        if not self.enabled or not alert_result.should_notify:
            return
        
        # 构建通知内容
        content = self._build_content(portfolio_result, alert_result, ai_analysis)
        
        # 发送到各个渠道
        for method in self.methods:
            method_type = method.get('type')
            
            if method_type == 'console':
                self._send_console(content)
            elif method_type == 'file':
                self._send_file(content, method)
            elif method_type == 'email':
                self._send_email(content, method)
    
    def _build_content(
        self,
        portfolio_result: PortfolioVolatilityResult,
        alert_result: AlertResult,
        ai_analysis: Optional[str]
    ) -> str:
        """构建通知内容"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lines = [
            "=" * 60,
            f"Anti-FOMO 波动监控报告",
            f"时间: {timestamp}",
            "=" * 60,
            "",
            str(alert_result),
            "",
        ]

        if alert_result.should_notify:
            lines.extend([
                "组合波动详情:",
                "-" * 60,
                str(portfolio_result),
                ""
            ])
        else:
            lines.extend([
                "组合波动：正常范围，无需关注明细",
                ""
            ])
        
        if ai_analysis:
            lines.extend([
                "",
                "AI 专业分析:",
                "-" * 60,
                ai_analysis,
                ""
            ])
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _send_console(self, content: str):
        """控制台输出"""
        print(content)
    
    def _send_file(self, content: str, method: Dict):
        """写入文件"""
        log_path = method.get('log_path', './logs/alerts.log')
        
        # 确保目录存在
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 追加写入
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(content + "\n\n")
        
        print(f"通知已保存到: {log_path}")
    
    def _send_email(self, content: str, method: Dict):
        """发送邮件（简化版，需要配置 SMTP）"""
        smtp_host = method.get('smtp_host')
        if not smtp_host:
            print("邮件通知未配置 SMTP，跳过")
            return
        
        # TODO: 实现邮件发送逻辑
        print("邮件通知功能待实现")
