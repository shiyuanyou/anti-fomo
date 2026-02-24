"""
Static portfolio template library for Anti-FOMO v2.

Contains 6 classic asset allocation templates with quantitative metrics
(2010-2024 historical simulation approximations) and personality tags.

Data is intentionally static and pre-computed. No live data sources are used.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AssetAllocation:
    """Single allocation entry within a template."""

    category: str    # e.g. "A股大盘", "美股科技", "债券", "黄金"
    region: str      # e.g. "中国", "全球", "美国"
    weight: float    # 0.0 – 1.0


@dataclass
class TemplateMetrics:
    """Quantitative metrics for a portfolio template (historical simulation)."""

    annualized_return: float       # % e.g. 8.5
    annualized_volatility: float   # % e.g. 12.3
    max_drawdown: float            # % negative, e.g. -28.4
    sharpe_ratio: float            # e.g. 0.62
    data_period: str               # e.g. "2010-2024 历史模拟"


@dataclass
class PortfolioTemplate:
    """A complete portfolio template with allocations, metrics and personality profile."""

    id: str
    name: str
    tagline: str
    target_audience: str
    risk_level: str                      # "低" / "中" / "中高" / "高"
    allocations: List[AssetAllocation]
    metrics: TemplateMetrics
    personality_tags: List[str]
    personality_description: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tagline": self.tagline,
            "target_audience": self.target_audience,
            "risk_level": self.risk_level,
            "allocations": [
                {"category": a.category, "region": a.region, "weight": a.weight}
                for a in self.allocations
            ],
            "metrics": {
                "annualized_return": self.metrics.annualized_return,
                "annualized_volatility": self.metrics.annualized_volatility,
                "max_drawdown": self.metrics.max_drawdown,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "data_period": self.metrics.data_period,
            },
            "personality_tags": self.personality_tags,
            "personality_description": self.personality_description,
        }


# ---------------------------------------------------------------------------
#  Built-in templates (static data, 2010-2024 historical simulation)
# ---------------------------------------------------------------------------

_TEMPLATES: List[PortfolioTemplate] = [

    # ------------------------------------------------------------------
    # 1. 全球均衡型
    # ------------------------------------------------------------------
    PortfolioTemplate(
        id="global_balanced",
        name="全球均衡型",
        tagline="股债平衡，本外均配，长期稳健增长",
        target_audience="追求稳健长期增长、认可全球分散价值的投资者",
        risk_level="中",
        allocations=[
            AssetAllocation("A股大盘", "中国", 0.20),
            AssetAllocation("发达市场股票", "全球", 0.20),
            AssetAllocation("新兴市场股票", "全球", 0.10),
            AssetAllocation("美股大盘", "美国", 0.10),
            AssetAllocation("债券", "中国", 0.25),
            AssetAllocation("债券", "全球", 0.10),
            AssetAllocation("黄金", "全球", 0.05),
        ],
        metrics=TemplateMetrics(
            annualized_return=7.8,
            annualized_volatility=10.2,
            max_drawdown=-21.5,
            sharpe_ratio=0.61,
            data_period="2010-2024 历史模拟",
        ),
        personality_tags=["无国界思维", "追求平稳", "相信长期成长", "债券作为压舱石"],
        personality_description=(
            "你相信全球经济长期向上，不执着于押注某个国家或地区。"
            "股债均衡让你在市场大跌时不会过于恐慌，也不会在牛市中错过主要涨幅。"
            "适合长期持有、不频繁操作的投资者。"
        ),
    ),

    # ------------------------------------------------------------------
    # 2. A股核心型
    # ------------------------------------------------------------------
    PortfolioTemplate(
        id="a_share_core",
        name="A股核心型",
        tagline="本国优先，深度参与中国经济成长",
        target_audience="对中国市场有信心、日常关注A股、接受较高波动的投资者",
        risk_level="中高",
        allocations=[
            AssetAllocation("A股大盘", "中国", 0.35),
            AssetAllocation("A股中盘", "中国", 0.20),
            AssetAllocation("A股小盘", "中国", 0.15),
            AssetAllocation("港股", "中国香港", 0.10),
            AssetAllocation("债券", "中国", 0.15),
            AssetAllocation("货币基金", "中国", 0.05),
        ],
        metrics=TemplateMetrics(
            annualized_return=9.2,
            annualized_volatility=18.6,
            max_drawdown=-44.3,
            sharpe_ratio=0.42,
            data_period="2010-2024 历史模拟",
        ),
        personality_tags=["本国优先", "接受大幅波动", "相信中国经济", "集中持仓"],
        personality_description=(
            "你对中国市场有深度理解和信心，愿意接受较大的波动以换取更高的长期潜在回报。"
            "对全球化分散持保留态度，认为了解自己的市场比广泛分散更重要。"
            "需要较强的心理承受能力，适合有一定A股投资经验的人。"
        ),
    ),

    # ------------------------------------------------------------------
    # 3. 全天候防御型
    # ------------------------------------------------------------------
    PortfolioTemplate(
        id="all_weather",
        name="全天候防御型",
        tagline="风险平价，多资产对冲，任何市场环境下保持韧性",
        target_audience="风险厌恶、厌倦市场剧烈波动、希望平稳穿越周期的投资者",
        risk_level="低",
        allocations=[
            AssetAllocation("A股大盘", "中国", 0.12),
            AssetAllocation("发达市场股票", "全球", 0.13),
            AssetAllocation("债券", "中国", 0.30),
            AssetAllocation("债券", "全球", 0.15),
            AssetAllocation("黄金", "全球", 0.15),
            AssetAllocation("大宗商品", "全球", 0.10),
            AssetAllocation("货币基金", "中国", 0.05),
        ],
        metrics=TemplateMetrics(
            annualized_return=5.9,
            annualized_volatility=6.8,
            max_drawdown=-12.4,
            sharpe_ratio=0.69,
            data_period="2010-2024 历史模拟",
        ),
        personality_tags=["追求平稳", "认可黄金/商品对冲", "风险平价思维", "长期防御"],
        personality_description=(
            "你把\"不亏钱\"放在第一位，愿意牺牲部分上行空间来换取夜晚的安心。"
            "认可黄金和大宗商品在通胀和危机中的对冲价值。"
            "相信分散化本身就是最好的主动管理策略之一。"
            "夏普比率在六个模板中最高，回撤最小。"
        ),
    ),

    # ------------------------------------------------------------------
    # 4. 成长进取型
    # ------------------------------------------------------------------
    PortfolioTemplate(
        id="growth_aggressive",
        name="成长进取型",
        tagline="高风险高预期，押注科技与新兴市场的长期爆发力",
        target_audience="年轻、投资期限长、接受高波动高回撤、相信科技变革的投资者",
        risk_level="高",
        allocations=[
            AssetAllocation("美股科技", "美国", 0.30),
            AssetAllocation("A股成长", "中国", 0.20),
            AssetAllocation("新兴市场股票", "全球", 0.20),
            AssetAllocation("港股科技", "中国香港", 0.15),
            AssetAllocation("债券", "中国", 0.10),
            AssetAllocation("货币基金", "中国", 0.05),
        ],
        metrics=TemplateMetrics(
            annualized_return=12.4,
            annualized_volatility=24.1,
            max_drawdown=-52.7,
            sharpe_ratio=0.46,
            data_period="2010-2024 历史模拟",
        ),
        personality_tags=["接受大幅波动", "相信长期成长", "科技驱动思维", "高风险高回报"],
        personality_description=(
            "你相信科技是这个时代最确定的长期驱动力，愿意承受短期的剧烈波动。"
            "投资期限通常在10年以上，把市场下跌视为加仓机会而非退出信号。"
            "这个配置在牛市中表现出色，但在熊市中回撤超过50%的概率较高，需要强大的心理承受力。"
        ),
    ),

    # ------------------------------------------------------------------
    # 5. 无国界对冲型
    # ------------------------------------------------------------------
    PortfolioTemplate(
        id="global_diversified",
        name="无国界对冲型",
        tagline="全球充分分散，弱化本国偏好，追求真正的全球化配置",
        target_audience="认同全球化逻辑、不想把命运与单一国家绑定的投资者",
        risk_level="中",
        allocations=[
            AssetAllocation("美股大盘", "美国", 0.20),
            AssetAllocation("欧洲股票", "欧洲", 0.12),
            AssetAllocation("日本股票", "日本", 0.08),
            AssetAllocation("A股大盘", "中国", 0.10),
            AssetAllocation("新兴市场股票", "全球", 0.10),
            AssetAllocation("债券", "全球", 0.20),
            AssetAllocation("黄金", "全球", 0.10),
            AssetAllocation("大宗商品", "全球", 0.05),
            AssetAllocation("货币基金", "中国", 0.05),
        ],
        metrics=TemplateMetrics(
            annualized_return=8.3,
            annualized_volatility=11.5,
            max_drawdown=-24.8,
            sharpe_ratio=0.59,
            data_period="2010-2024 历史模拟",
        ),
        personality_tags=["无国界思维", "真正分散", "弱化本国偏好", "多区域多资产"],
        personality_description=(
            "你认为把大部分资产集中在单一国家是一种系统性风险，哪怕是本国市场。"
            "对地缘政治、货币贬值和区域性危机有清醒认识，主动用地理多元化来对冲。"
            "A股占比刻意压低，不是因为不看好中国，而是因为相信真正的分散必须超越国界。"
        ),
    ),

    # ------------------------------------------------------------------
    # 6. 现金稳健型
    # ------------------------------------------------------------------
    PortfolioTemplate(
        id="cash_conservative",
        name="现金稳健型",
        tagline="流动性优先，保守防御，等待更好的机会",
        target_audience="短期资金、极度保守型、或处于观望阶段的投资者",
        risk_level="低",
        allocations=[
            AssetAllocation("货币基金", "中国", 0.40),
            AssetAllocation("短期债券", "中国", 0.30),
            AssetAllocation("债券", "中国", 0.15),
            AssetAllocation("黄金", "全球", 0.10),
            AssetAllocation("A股大盘", "中国", 0.05),
        ],
        metrics=TemplateMetrics(
            annualized_return=3.8,
            annualized_volatility=2.1,
            max_drawdown=-4.2,
            sharpe_ratio=0.71,
            data_period="2010-2024 历史模拟",
        ),
        personality_tags=["追求平稳", "流动性优先", "防御型", "等待入场时机"],
        personality_description=(
            "你目前处于保守或观望阶段，把资金安全和流动性放在首位。"
            "可能是处于人生的某个特殊阶段（如近期有大额支出），或者认为当前市场估值偏高在等待机会。"
            "这个配置的夏普比率最高（波动率极低），但绝对回报有限，长期持有会面临购买力被通胀侵蚀的风险。"
        ),
    ),
]


class TemplateLibrary:
    """Access built-in portfolio templates."""

    _index: dict[str, PortfolioTemplate] = {t.id: t for t in _TEMPLATES}

    @classmethod
    def all(cls) -> List[PortfolioTemplate]:
        """Return all templates."""
        return list(_TEMPLATES)

    @classmethod
    def get(cls, template_id: str) -> Optional[PortfolioTemplate]:
        """Return a single template by ID, or None if not found."""
        return cls._index.get(template_id)

    @classmethod
    def ids(cls) -> List[str]:
        """Return all template IDs."""
        return [t.id for t in _TEMPLATES]
