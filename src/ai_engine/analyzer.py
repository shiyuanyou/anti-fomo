"""
AI Analysis Module
AI 分析模块 - 使用 AI 分析波动情况并给出建议
"""
import os
from typing import Dict, Optional

from openai import OpenAI
from dotenv import load_dotenv

from portfolio_engine import PortfolioVolatilityResult
from portfolio_engine import AlertResult


class AIAnalyzer:
    """AI 分析器"""
    
    def __init__(self, config: Dict):
        """
        初始化 AI 分析器
        
        Args:
            config: AI 配置
        """
        self.enabled = config.get('enabled', False)
        if not self.enabled:
            return

        load_dotenv()
        
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4')
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY') or os.getenv('AI_API_KEY') or ''
        self.base_url = config.get('base_url') or os.getenv('OPENAI_BASE_URL') or ''
        self.prompt_template = config.get('prompt_template', '')

        if self.api_key:
            if self.base_url:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            else:
                self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("警告: 未配置 API Key，AI 分析功能将不可用")
    
    def analyze(
        self,
        portfolio_result: PortfolioVolatilityResult,
        alert_result: AlertResult
    ) -> Optional[str]:
        """
        使用 AI 分析波动情况
        
        Args:
            portfolio_result: 组合波动率结果
            alert_result: 警报结果
            
        Returns:
            AI 分析建议
        """
        if not self.enabled or not self.client:
            return None
        
        # 准备数据
        volatility_details = self._format_volatility_details(portfolio_result)
        recent_trend = self._analyze_trend(portfolio_result)
        allocation_summary = self._format_allocation_summary(portfolio_result)
        month_return_summary = self._format_month_return_summary(portfolio_result)
        rebalance_hint = self._format_rebalance_hint(portfolio_result)
        alert_level = alert_result.level.value
        
        # 构建提示词
        prompt = self.prompt_template.format(
            alert_level=alert_level,
            total_volatility=f"{portfolio_result.total_volatility:.2f}",
            volatility_details=volatility_details,
            recent_trend=recent_trend,
            allocation_summary=allocation_summary,
            month_return_summary=month_return_summary,
            rebalance_hint=rebalance_hint,
        )
        
        try:
            # 调用 AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业、理性的投资顾问，擅长分析市场波动并给出客观建议。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            if content:
                print("\nAI 分析建议:\n" + content + "\n")
            return content
        
        except Exception as e:
            print(f"AI 分析失败: {str(e)}")
            return None
    
    def _format_volatility_details(self, portfolio_result: PortfolioVolatilityResult) -> str:
        """格式化波动明细"""
        lines = []
        for result in portfolio_result.individual_results:
            lines.append(
                f"- {result.name}({result.symbol}): "
                f"涨跌 {result.change_pct:+.2f}%, "
                f"波动率 {result.volatility:.2f}%, "
                f"权重 {result.weight:.1%}"
            )
        return "\n".join(lines)

    def _format_allocation_summary(self, portfolio_result: PortfolioVolatilityResult) -> str:
        """格式化持仓权重"""
        lines = []
        for result in portfolio_result.individual_results:
            lines.append(f"- {result.name}({result.symbol}): 权重 {result.weight:.1%}")
        return "\n".join(lines)

    def _format_month_return_summary(self, portfolio_result: PortfolioVolatilityResult) -> str:
        """格式化近一月涨跌幅"""
        lines = []
        for result in portfolio_result.individual_results:
            lines.append(
                f"- {result.name}({result.symbol}): 近一月 {result.month_return_pct:+.2f}%"
            )
        return "\n".join(lines)

    def _format_rebalance_hint(self, portfolio_result: PortfolioVolatilityResult) -> str:
        """生成调仓提示"""
        results = sorted(
            portfolio_result.individual_results,
            key=lambda x: x.month_return_pct,
            reverse=True,
        )
        if len(results) < 2:
            return ""

        top = results[0]
        bottom = results[-1]
        return (
            f"近一月上涨较多: {top.name}({top.symbol}) {top.month_return_pct:+.2f}%; "
            f"相对落后: {bottom.name}({bottom.symbol}) {bottom.month_return_pct:+.2f}%"
        )
    
    def _analyze_trend(self, portfolio_result: PortfolioVolatilityResult) -> str:
        """分析趋势（简化版）"""
        up_count = sum(1 for r in portfolio_result.individual_results if r.change_pct > 0)
        down_count = sum(1 for r in portfolio_result.individual_results if r.change_pct < 0)
        total = len(portfolio_result.individual_results)
        
        if up_count > down_count:
            trend = f"整体偏强，{up_count}/{total} 持仓上涨"
        elif down_count > up_count:
            trend = f"整体偏弱，{down_count}/{total} 持仓下跌"
        else:
            trend = "涨跌平衡"
        
        return trend
