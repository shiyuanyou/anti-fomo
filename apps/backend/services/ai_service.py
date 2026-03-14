"""
AI Service - Unified interface for AI providers
Supports: OpenAI, Minimax, Zhipu AI (GLM)
"""
import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class AIProvider(Enum):
    OPENAI = "openai"
    MINIMAX = "minimax"
    ZHIPU = "zhipu"


@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None


class AIService:
    """Unified AI service interface"""

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("enabled", False)
        if not self.enabled:
            return

        provider = config.get("provider", "openai").lower()
        
        try:
            self.provider = AIProvider(provider)
        except ValueError:
            self.provider = AIProvider.OPENAI

        self.model = config.get("model", "gpt-4")
        self.api_key = config.get("api_key") or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = config.get("base_url") or os.getenv("AI_BASE_URL") or os.getenv("OPENAI_BASE_URL", "")
        
        self._client = None

    def _get_client(self):
        """Lazy load the appropriate client"""
        if self._client is not None:
            return self._client

        if self.provider == AIProvider.MINIMAX:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.minimax.chat/v1"
            )
        elif self.provider == AIProvider.ZHIPU:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        else:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else None
            )

        return self._client

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        """
        Send chat request to AI

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            AIResponse with content and metadata
        """
        if not self.enabled or not self.api_key:
            return AIResponse(
                content="AI service not configured",
                provider=self.provider.value,
                model=self.model
            )

        try:
            client = self._get_client()
            
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            response = client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return AIResponse(
                content=response.choices[0].message.content,
                provider=self.provider.value,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
            )

        except Exception as e:
            return AIResponse(
                content=f"Error: {str(e)}",
                provider=self.provider.value,
                model=self.model
            )

    def analyze_portfolio(
        self,
        portfolio_summary: str,
        volatility_data: str,
        market_status: Optional[str] = None,
    ) -> str:
        """Analyze portfolio and generate insights"""
        
        system_prompt = """你是一位专业的投资顾问和风险管理专家。你的任务是分析用户的投资组合波动情况，并提供专业、理性的投资建议。

请遵循以下原则：
1. 保持客观理性，用数据和逻辑说话
2. 强调长期投资的重要性
3. 提醒用户不要被短期波动影响情绪
4. 适当引用历史数据和统计学原理
5. 如果需要具体投资建议，请明确说明这是基于公开信息的观点，不构成投资建议"""

        user_message = f"""请分析以下投资组合波动情况：

【组合概况】
{portfolio_summary}

【波动数据】
{volatility_data}
{f'【市场状态】\n{market_status}' if market_status else ''}

请给出：
1. 当前波动的主要原因分析
2. 是否需要调整的判断
3. 具体的调仓建议（如需要）
4. 心理层面的建议"""

        response = self.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1500,
        )

        return response.content


def create_ai_service(config: Dict[str, Any]) -> AIService:
    """Factory function to create AI service"""
    return AIService(config)
