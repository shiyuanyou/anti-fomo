"""
Interactive Asset Configurator
交互式资产配置工具
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
import yaml
from datetime import datetime


@dataclass
class AssetItem:
    """资产配置项"""
    name: str
    code: str
    ratio: float
    auto_calculate: bool
    start_price: Optional[float]


@dataclass
class AssetCategory:
    """资产分类"""
    name: str
    children: List["AssetCategory"] = field(default_factory=list)
    items: List[AssetItem] = field(default_factory=list)


def _default_categories() -> List[AssetCategory]:
    return [
        AssetCategory(
            name="股票",
            children=[
                AssetCategory(name="中国大陆"),
                AssetCategory(name="中国香港"),
                AssetCategory(
                    name="全球",
                    children=[
                        AssetCategory(name="美国"),
                        AssetCategory(name="东亚"),
                        AssetCategory(name="欧洲"),
                        AssetCategory(name="印度"),
                        AssetCategory(name="中东"),
                    ],
                ),
            ],
        ),
        AssetCategory(name="货币基金"),
        AssetCategory(
            name="大宗商品类",
            children=[
                AssetCategory(name="黄金"),
                AssetCategory(name="石油"),
                AssetCategory(name="商品综合"),
            ],
        ),
    ]


def _print_categories(categories: List[AssetCategory], prefix: str = "") -> List[AssetCategory]:
    flat: List[AssetCategory] = []
    index = 1
    for cat in categories:
        label = f"{prefix}{index}. {cat.name}"
        print(label)
        flat.append(cat)
        if cat.children:
            child_prefix = f"{prefix}{index}."
            child_flat = _print_categories(cat.children, prefix=child_prefix)
            flat.extend(child_flat)
        index += 1
    return flat


def _choose_category(categories: List[AssetCategory]) -> Optional[AssetCategory]:
    print("\n请选择一个分类（输入编号，回车取消）:")
    flat = _print_categories(categories)
    choice = input("分类编号: ").strip()
    if not choice:
        return None

    try:
        parts = [int(p) for p in choice.split(".") if p]
    except ValueError:
        print("无效编号，请重新选择。")
        return None

    current = categories
    selected: Optional[AssetCategory] = None
    for idx in parts:
        if idx < 1 or idx > len(current):
            print("编号超出范围，请重新选择。")
            return None
        selected = current[idx - 1]
        current = selected.children

    return selected


def _prompt_float(prompt: str, min_value: float = 0.0, max_value: float = 100.0) -> float:
    while True:
        value = input(prompt).strip()
        try:
            number = float(value)
        except ValueError:
            print("请输入数字。")
            continue
        if number < min_value or number > max_value:
            print(f"请输入 {min_value} 到 {max_value} 之间的数值。")
            continue
        return number


def _prompt_optional_float(prompt: str) -> Optional[float]:
    value = input(prompt).strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        print("无效数字，已忽略。")
        return None


def _prompt_yes_no(prompt: str, default: bool = True) -> bool:
    default_label = "Y/n" if default else "y/N"
    value = input(f"{prompt} ({default_label}): ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes"}


def _add_item(category: AssetCategory):
    print(f"\n新增子项 - {category.name}")
    name = input("名称: ").strip()
    if not name:
        print("名称不能为空。")
        return
    code = input("代码/标识（可为空）: ").strip()
    ratio = _prompt_float("配置比例(0-100): ")
    auto_calc = _prompt_yes_no("是否由系统计算", default=True)
    start_price = _prompt_optional_float("起始价格/成本（可空）: ")
    category.items.append(
        AssetItem(
            name=name,
            code=code,
            ratio=ratio,
            auto_calculate=auto_calc,
            start_price=start_price,
        )
    )
    print("已添加。")


def _remove_item(category: AssetCategory):
    if not category.items:
        print("当前分类没有子项。")
        return
    print("\n请选择要删除的子项:")
    for idx, item in enumerate(category.items, start=1):
        print(f"{idx}. {item.name} ({item.code}) - {item.ratio:.2f}%")
    value = input("编号: ").strip()
    try:
        index = int(value)
    except ValueError:
        print("无效编号。")
        return
    if index < 1 or index > len(category.items):
        print("编号超出范围。")
        return
    removed = category.items.pop(index - 1)
    print(f"已删除: {removed.name}")


def _list_items(category: AssetCategory):
    if not category.items:
        print("当前分类没有子项。")
        return
    print(f"\n{category.name} 子项:")
    for item in category.items:
        auto = "自动" if item.auto_calculate else "手动"
        start = f" 起始价 {item.start_price:.2f}" if item.start_price is not None else ""
        print(f"- {item.name} ({item.code}) 比例 {item.ratio:.2f}% | {auto}{start}")


def _collect_all_items(category: AssetCategory) -> List[AssetItem]:
    items = list(category.items)
    for child in category.children:
        items.extend(_collect_all_items(child))
    return items


def _serialize_category(category: AssetCategory) -> Dict:
    return {
        "name": category.name,
        "items": [
            {
                "name": item.name,
                "code": item.code,
                "ratio": item.ratio,
                "auto_calculate": item.auto_calculate,
                "start_price": item.start_price,
            }
            for item in category.items
        ],
        "children": [_serialize_category(child) for child in category.children],
    }


def _write_config(categories: List[AssetCategory], output_path: Path) -> None:
    all_items: List[AssetItem] = []
    for cat in categories:
        all_items.extend(_collect_all_items(cat))

    holdings = []
    total_ratio = sum(item.ratio for item in all_items)
    calculable_items = [item for item in all_items if item.auto_calculate and item.code]
    calculable_ratio = sum(item.ratio for item in calculable_items)
    calculable_weights = {
        item.code: (item.ratio / calculable_ratio)
        for item in calculable_items
        if calculable_ratio > 0
    }
    equity_start = {
        item.code: item.start_price
        for item in calculable_items
        if item.start_price is not None
    }

    for item in all_items:
        if not item.code:
            continue
        holdings.append(
            {
                "symbol": item.code,
                "name": item.name,
                "type": "index",
                "allocation_type": "ratio",
                "value": item.ratio,
            }
        )

    config = {
        "portfolio": {"holdings": holdings},
        "asset_allocation": {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "categories": [_serialize_category(cat) for cat in categories],
            "total_ratio": total_ratio,
            "calculable_ratio": calculable_ratio,
            "calculable_weights": calculable_weights,
            "equity_start": equity_start,
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

    print(f"\n✅ 已生成配置文件: {output_path}")


def run_asset_configurator():
    print("=" * 60)
    print("资产配置向导")
    print("=" * 60)
    
    categories = _default_categories()

    while True:
        print("\n请选择操作:")
        print("1. 选择分类并添加子项")
        print("2. 选择分类并删除子项")
        print("3. 查看分类子项")
        print("4. 生成初始配置")
        print("5. 退出")
        choice = input("输入编号: ").strip()

        if choice == "1":
            selected = _choose_category(categories)
            if selected:
                _add_item(selected)
        elif choice == "2":
            selected = _choose_category(categories)
            if selected:
                _remove_item(selected)
        elif choice == "3":
            selected = _choose_category(categories)
            if selected:
                _list_items(selected)
        elif choice == "4":
            output = Path("config.asset.yaml")
            _write_config(categories, output)
        elif choice == "5":
            print("已退出。")
            break
        else:
            print("无效选择，请重新输入。")
