import pytest
import numpy as np
from src.data_processor import DataProcessor


def test_lock_0000_code():
    dp = DataProcessor()
    data = [
        {"code": "0000123456", "name": "普通项目", "price": 100},
        {"code": "010101001", "name": "普通项目", "price": 200},
    ]
    result = dp.identify_locked_items(data)
    assert result[0]["is_locked"] is True
    assert result[1]["is_locked"] is False


def test_lock_keywords():
    dp = DataProcessor()
    data = [
        {"code": "010101001", "name": "税金项目", "price": 100},
        {"code": "010101002", "name": "规费项目", "price": 100},
        {"code": "010101003", "name": "安全文明施工", "price": 100},
        {"code": "010101004", "name": "暂列金额项", "price": 100},
        {"code": "010101005", "name": "普通项目", "price": 100},
    ]
    result = dp.identify_locked_items(data)
    assert result[0]["is_locked"] is True
    assert result[1]["is_locked"] is True
    assert result[2]["is_locked"] is True
    assert result[3]["is_locked"] is True
    assert result[4]["is_locked"] is False


def test_lock_hierarchy_code():
    dp = DataProcessor()
    data = [
        {"code": "2BA", "name": "普通项目", "price": 100},
        {"code": "2BAA", "name": "普通项目", "price": 100},
        {"code": "123", "name": "普通项目", "price": 100},
        {"code": "010101001", "name": "普通项目", "price": 100},
    ]
    result = dp.identify_locked_items(data)
    assert result[0]["is_locked"] is True
    assert result[1]["is_locked"] is True
    assert result[2]["is_locked"] is False
    assert result[3]["is_locked"] is False


def test_lock_summary():
    dp = DataProcessor()
    data = [
        {"code": "010101001", "name": "合计项目", "price": 100},
        {"code": "010101002", "name": "汇总项目", "price": 100},
        {"code": "010101003", "name": "小计项目", "price": 100},
        {"code": "010101004", "name": "总计项目", "price": 100},
        {"code": "010101005", "name": "普通项目", "price": 100},
    ]
    result = dp.identify_locked_items(data)
    assert result[0]["is_locked"] is True
    assert result[1]["is_locked"] is True
    assert result[2]["is_locked"] is True
    assert result[3]["is_locked"] is True
    assert result[4]["is_locked"] is False


def test_lock_zero_price():
    dp = DataProcessor()
    data = [
        {"code": "010101001", "name": "普通项目", "price": 0},
        {"code": "010101002", "name": "普通项目", "price": None},
        {"code": "010101003", "name": "普通项目", "price": 100},
    ]
    result = dp.identify_locked_items(data)
    assert result[0]["is_locked"] is True
    assert result[1]["is_locked"] is True
    assert result[2]["is_locked"] is False


def test_no_adjustable_items():
    dp = DataProcessor()
    data = [
        {"code": "0000123456", "name": "税金合计", "price": 0},
    ]
    with pytest.raises(ValueError, match="ERR_NO_ADJUSTABLE_ITEMS"):
        dp.identify_locked_items(data)


def test_tier_grouping():
    dp = DataProcessor()
    data = [
        {"code": "010101001", "name": "项目A", "price": 200},
        {"code": "010101002", "name": "项目B", "price": 200},
        {"code": "010101003", "name": "项目C", "price": 200},
        {"code": "010101004", "name": "项目D", "price": 200},
        {"code": "010101005", "name": "项目E", "price": 200},
        {"code": "010101006", "name": "项目F", "price": 100},
        {"code": "010101007", "name": "项目G", "price": 100},
        {"code": "010101008", "name": "项目H", "price": 100},
        {"code": "010101009", "name": "项目I", "price": 100},
        {"code": "010101010", "name": "项目J", "price": 100},
        {"code": "010101011", "name": "项目K", "price": 1},
        {"code": "010101012", "name": "项目L", "price": 1},
        {"code": "010101013", "name": "项目M", "price": 1},
        {"code": "010101014", "name": "项目N", "price": 1},
        {"code": "010101015", "name": "项目O", "price": 1},
    ]
    dp.identify_locked_items(data)
    dp.tier_grouping(data)

    adjustable = [d for d in data if not d["is_locked"]]
    large_items = [d for d in adjustable if d["tier"] == "large"]
    small_items = [d for d in adjustable if d["tier"] == "small"]
    medium_items = [d for d in adjustable if d["tier"] == "medium"]

    assert len(large_items) > 0
    assert len(small_items) > 0
    assert all(d["price"] == 200 for d in large_items)
    assert all(d["price"] == 1 for d in small_items)
    assert all(d["price"] == 100 for d in medium_items)


def test_direction_assignment():
    dp = DataProcessor(seed=42)
    data = [
        {"code": "010101001", "name": "项目A", "price": 200},
        {"code": "010101002", "name": "项目B", "price": 200},
        {"code": "010101003", "name": "项目C", "price": 200},
        {"code": "010101004", "name": "项目D", "price": 200},
        {"code": "010101005", "name": "项目E", "price": 200},
        {"code": "010101006", "name": "项目F", "price": 100},
        {"code": "010101007", "name": "项目G", "price": 100},
        {"code": "010101008", "name": "项目H", "price": 100},
        {"code": "010101009", "name": "项目I", "price": 100},
        {"code": "010101010", "name": "项目J", "price": 100},
        {"code": "010101011", "name": "项目K", "price": 1},
        {"code": "010101012", "name": "项目L", "price": 1},
        {"code": "010101013", "name": "项目M", "price": 1},
        {"code": "010101014", "name": "项目N", "price": 1},
        {"code": "010101015", "name": "项目O", "price": 1},
    ]
    dp.identify_locked_items(data)
    dp.tier_grouping(data)

    adjustable = [d for d in data if not d["is_locked"]]
    for item in adjustable:
        assert item["direction"] in ("up", "down")

    from collections import defaultdict
    tier_groups = defaultdict(list)
    for item in adjustable:
        tier_groups[item["tier"]].append(item)

    for tier, items in tier_groups.items():
        if len(items) >= 2:
            directions = {d["direction"] for d in items}
            assert "up" in directions
            assert "down" in directions


def _make_tier_test_data():
    data = []
    for i in range(5):
        data.append({"code": f"0101010{i+1:03d}", "name": f"大项{i}", "price": 200})
    for i in range(5):
        data.append({"code": f"0101011{i+1:03d}", "name": f"中项{i}", "price": 100})
    for i in range(5):
        data.append({"code": f"0101012{i+1:03d}", "name": f"小项{i}", "price": 1})
    return data


def test_coefficient_range_large():
    dp = DataProcessor(seed=42)
    data = _make_tier_test_data()
    dp.identify_locked_items(data)
    dp.tier_grouping(data)
    dp.generate_coefficients(data)

    large_items = [d for d in data if not d["is_locked"] and d["tier"] == "large"]
    for item in large_items:
        assert 0.985 <= item["coefficient"] <= 1.015


def test_coefficient_range_medium():
    dp = DataProcessor(seed=42)
    data = _make_tier_test_data()
    dp.identify_locked_items(data)
    dp.tier_grouping(data)
    dp.generate_coefficients(data)

    medium_items = [d for d in data if not d["is_locked"] and d["tier"] == "medium"]
    for item in medium_items:
        assert 0.975 <= item["coefficient"] <= 1.025


def test_coefficient_range_small():
    dp = DataProcessor(seed=42)
    data = _make_tier_test_data()
    dp.identify_locked_items(data)
    dp.tier_grouping(data)
    dp.generate_coefficients(data)

    small_items = [d for d in data if not d["is_locked"] and d["tier"] == "small"]
    for item in small_items:
        assert 0.965 <= item["coefficient"] <= 1.035


def test_seed_reproducibility():
    dp1 = DataProcessor(seed=42)
    data1 = [
        {"code": f"0101010{i:03d}", "name": f"项目{i}", "price": 100 + i * 10}
        for i in range(20)
    ]
    dp1.identify_locked_items(data1)
    dp1.tier_grouping(data1)
    dp1.generate_coefficients(data1)

    dp2 = DataProcessor(seed=42)
    data2 = [
        {"code": f"0101010{i:03d}", "name": f"项目{i}", "price": 100 + i * 10}
        for i in range(20)
    ]
    dp2.identify_locked_items(data2)
    dp2.tier_grouping(data2)
    dp2.generate_coefficients(data2)

    for d1, d2 in zip(data1, data2):
        assert d1["coefficient"] == d2["coefficient"]


def test_locked_item_price_unchanged():
    dp = DataProcessor()
    data = [
        {"code": "0000123456", "name": "税金项目", "price": 100},
        {"code": "010101001", "name": "普通项目", "price": 200},
    ]
    dp.identify_locked_items(data)
    dp.tier_grouping(data)
    dp.generate_coefficients(data)

    locked = [d for d in data if d["is_locked"]]
    for item in locked:
        assert item["adjusted_price"] == item["price"]
