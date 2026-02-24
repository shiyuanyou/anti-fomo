"""
TemplateAdvisor: AI-assisted personality matching and migration advice for v2.

Two public methods:
    match_personality(web_assets)          -> str  (which template fits the user best)
    suggest_migration(web_assets, template) -> str  (how to move toward a template)

Uses the OpenAI-compatible SDK. API key is read from environment variables:
    OPENAI_API_KEY  or  AI_API_KEY
Optional:
    OPENAI_BASE_URL  (for compatible providers)
    AI_MODEL        (default: gpt-4o-mini)

If no API key is configured, both methods return a graceful fallback message.
"""

from __future__ import annotations

import os
from typing import List, Optional

from dotenv import load_dotenv

# template_engine is a sibling package; import with relative path when loaded
# from src/ sys.path context.
from template_engine.templates import PortfolioTemplate, TemplateLibrary


_DEFAULT_MODEL = "gpt-4o-mini"


def _build_client():
    """Build an OpenAI client from environment variables. Returns None if no key."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY") or ""
    if not api_key:
        return None, None
    base_url = os.getenv("OPENAI_BASE_URL") or ""
    model = os.getenv("AI_MODEL") or _DEFAULT_MODEL
    from openai import OpenAI
    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)
    return client, model


def _describe_web_assets(web_assets: List[dict]) -> str:
    """Format web_assets into a concise description for the prompt."""
    total = sum(a.get("amount", 0) for a in web_assets)
    lines = []
    for a in web_assets:
        pct = a["amount"] / total * 100 if total > 0 else 0
        lines.append(
            f"- {a.get('name', '未知')} ({a.get('type', '')} / {a.get('region', '')} / "
            f"{a.get('style', '')}): {pct:.1f}%"
        )
    return "\n".join(lines)


def _describe_template(template: PortfolioTemplate) -> str:
    """Format a template into a concise description for the prompt."""
    alloc_lines = [
        f"  - {a.category} ({a.region}): {a.weight*100:.0f}%"
        for a in template.allocations
    ]
    return (
        f"模板: {template.name}\n"
        f"定位: {template.tagline}\n"
        f"风险等级: {template.risk_level}\n"
        f"配置:\n" + "\n".join(alloc_lines) + "\n"
        f"性格标签: {', '.join(template.personality_tags)}"
    )


class TemplateAdvisor:
    """AI advisor for portfolio template personality matching and migration advice."""

    def __init__(self):
        self._client, self._model = _build_client()
        if self._client is None:
            print("TemplateAdvisor: no API key configured, AI features will return fallback text")

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def match_personality(self, web_assets: List[dict]) -> str:
        """
        Analyse user holdings and recommend which template(s) best match
        their implicit investment personality.

        Args:
            web_assets: list of web_asset dicts (name, amount, type, region, style).

        Returns:
            A natural-language personality analysis and template recommendation.
        """
        if self._client is None:
            return self._fallback_personality(web_assets)

        asset_desc = _describe_web_assets(web_assets)
        templates_desc = "\n\n".join(
            _describe_template(t) for t in TemplateLibrary.all()
        )

        prompt = (
            "你是一位资产配置顾问，专注于帮助投资者认知自身的投资性格，而非给出买卖建议。\n\n"
            "以下是用户当前的资产配置：\n"
            f"{asset_desc}\n\n"
            "以下是我们提供的六个标准配置模板：\n\n"
            f"{templates_desc}\n\n"
            "请完成以下任务：\n"
            "1. 分析用户当前配置所反映的投资性格（100字以内，直接切入要点）\n"
            "2. 推荐最匹配的 1-2 个模板，说明理由\n"
            "3. 指出用户当前配置与主流模板最明显的偏离点（如过度集中、缺少某类资产等）\n\n"
            "风格要求：专业、简洁，不用标题，不用 Markdown，直接输出段落文字。"
            "不给出任何买卖指令或具体操作建议。"
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"AI 分析暂时不可用（{e}）。{self._fallback_personality(web_assets)}"

    def suggest_migration(
        self,
        web_assets: List[dict],
        template: PortfolioTemplate,
    ) -> str:
        """
        Generate migration advice: how the user might move their current
        holdings toward the target template.

        Args:
            web_assets: list of web_asset dicts.
            template: the target PortfolioTemplate.

        Returns:
            Natural-language migration suggestions (directional only, no trade orders).
        """
        if self._client is None:
            return self._fallback_migration(template)

        asset_desc = _describe_web_assets(web_assets)
        template_desc = _describe_template(template)

        prompt = (
            "你是一位资产配置顾问，帮助用户理解如何调整配置方向，但不给出任何具体买卖指令。\n\n"
            "用户当前配置：\n"
            f"{asset_desc}\n\n"
            "目标配置模板：\n"
            f"{template_desc}\n\n"
            "请提供迁移建议，包含：\n"
            "1. 主要调整方向（超配了哪些、低配了哪些，各 2-3 句话）\n"
            "2. 迁移过程中需要注意的认知或心理准备（1-2 句话）\n"
            "3. 迁移是否符合用户的隐含性格（1 句判断）\n\n"
            "风格要求：专业、简洁，不超过 300 字，不用 Markdown，直接输出段落。"
            "严禁出现\"买入\"、\"卖出\"、\"减仓\"、\"加仓\"等具体操作词语；"
            "使用\"增加配置比例\"、\"降低配置比例\"等方向性表述。"
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"AI 分析暂时不可用（{e}）。{self._fallback_migration(template)}"

    # ------------------------------------------------------------------
    #  Fallback (no API key)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_personality(web_assets: List[dict]) -> str:
        total = sum(a.get("amount", 0) for a in web_assets)
        cn_amt = sum(
            a["amount"] for a in web_assets
            if a.get("region", "") in ("中国大陆", "中国香港")
        )
        cn_ratio = cn_amt / total if total > 0 else 0
        if cn_ratio > 0.7:
            bias = "明显偏向中国市场，具有较强的本国市场偏好"
        elif cn_ratio > 0.4:
            bias = "中外资产相对均衡，有一定的全球分散意识"
        else:
            bias = "海外配置比重较高，具备较强的全球化配置意识"

        return (
            f"根据当前配置分析，你的资产{bias}。"
            "如需获取个性化的 AI 深度分析和模板推荐，请配置 OPENAI_API_KEY 或 AI_API_KEY 环境变量。"
        )

    @staticmethod
    def _fallback_migration(template: PortfolioTemplate) -> str:
        return (
            f"向「{template.name}」迁移的方向性建议：逐步调整各资产类别的配置比例，"
            f"使之趋近模板的目标权重分布。{template.tagline}。"
            "如需获取个性化的 AI 迁移建议，请配置 OPENAI_API_KEY 或 AI_API_KEY 环境变量。"
        )
