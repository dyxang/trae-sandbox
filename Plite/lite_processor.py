import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_processor import DataProcessor


class _ParameterizedDataProcessor(DataProcessor):
    def __init__(self, seed=42, large_range=(0.005, 0.01), medium_range=(0.01, 0.02), small_range=(0.02, 0.03)):
        super().__init__(seed=seed)
        self.large_range = large_range
        self.medium_range = medium_range
        self.small_range = small_range

    def _regenerate_coefficient(self, item):
        tier = item["tier"]
        direction = item["direction"]
        if tier == "large":
            base = self.rng.uniform(self.large_range[0], self.large_range[1])
        elif tier == "medium":
            base = self.rng.uniform(self.medium_range[0], self.medium_range[1])
        else:
            base = self.rng.uniform(self.small_range[0], self.small_range[1])
        noise = self.rng.normal(0, 0.003)
        if direction == "up":
            coefficient = 1 + base + noise
        else:
            coefficient = 1 - base + noise
        item["coefficient"] = coefficient
        item["adjusted_price"] = round(item["price"] * coefficient, 2)


class LiteDataProcessor:
    def __init__(self, seed=42):
        self.seed = seed

    def gui_data_to_processor_format(self, gui_rows):
        result = []
        for i, row in enumerate(gui_rows):
            item = {
                "code": str(i + 1).zfill(4),
                "name": row.get("name", ""),
                "price": row.get("price", 0),
                "is_locked": row.get("is_locked", False),
            }
            if row.get("float_up") is not None:
                item["custom_float_up"] = row["float_up"]
            if row.get("float_down") is not None:
                item["custom_float_down"] = row["float_down"]
            result.append(item)
        return result

    def _generate_coefficients_custom(self, data, large_range, medium_range, small_range):
        adjustable = [d for d in data if not d["is_locked"]]
        rng = np.random.RandomState(self.seed)

        for item in adjustable:
            tier = item["tier"]
            direction = item["direction"]

            if tier == "large":
                base = rng.uniform(large_range[0], large_range[1])
            elif tier == "medium":
                base = rng.uniform(medium_range[0], medium_range[1])
            else:
                base = rng.uniform(small_range[0], small_range[1])

            noise = rng.normal(0, 0.003)

            custom_up = item.get("custom_float_up")
            custom_down = item.get("custom_float_down")

            tier_limits = {
                "large": (large_range[0], large_range[1]),
                "medium": (medium_range[0], medium_range[1]),
                "small": (small_range[0], small_range[1]),
            }
            tier_low, tier_high = tier_limits[tier]

            if direction == "up":
                max_up = tier_high
                if custom_up is not None:
                    max_up = min(max_up, custom_up / 100.0)
                effective_base = min(base, max_up)
                coefficient = 1 + effective_base + noise
                coefficient = min(coefficient, 1 + max_up)
            else:
                max_down = tier_high
                if custom_down is not None:
                    max_down = min(max_down, abs(custom_down) / 100.0)
                effective_base = min(base, max_down)
                coefficient = 1 - effective_base + noise
                coefficient = max(coefficient, 1 - max_down)

            item["coefficient"] = coefficient
            item["adjusted_price"] = round(item["price"] * coefficient, 2)

        return data

    def _calibrate_total_price_custom(self, data, total_price_min, total_price_max, large_range, medium_range, small_range, tolerance=0.01):
        original_total = sum(item["price"] or 0 for item in data)

        target_total = None
        if total_price_max is not None:
            target_total = total_price_max
        elif total_price_min is not None:
            target_total = total_price_min

        if target_total is None:
            return data

        float_limits = {
            "large": large_range[1],
            "medium": medium_range[1],
            "small": small_range[1],
        }
        tier_priority = {"small": 0, "medium": 1, "large": 2}

        converged = False
        for tol in [tolerance, 0.1]:
            for _ in range(100):
                current_total = sum(item.get("adjusted_price", 0) or 0 for item in data)
                delta = target_total - current_total

                if abs(delta) <= tol:
                    converged = True
                    break

                adjustable = [item for item in data if not item["is_locked"]]
                adjustable.sort(key=lambda x: tier_priority.get(x.get("tier"), 1))

                total_weight = 0.0
                item_info = []

                for item in adjustable:
                    tier = item["tier"]
                    coefficient = item["coefficient"]
                    float_limit = float_limits[tier]
                    price = item["price"]

                    if delta > 0:
                        max_adjust = (1 + float_limit) - coefficient
                    else:
                        max_adjust = coefficient - (1 - float_limit)

                    max_adjust = max(max_adjust, 0)
                    weight = max_adjust * price
                    total_weight += weight
                    item_info.append((item, max_adjust, price))

                if total_weight <= 0:
                    break

                for item, max_adjust, price in item_info:
                    if max_adjust > 0:
                        dc = max_adjust * delta / total_weight
                        item["coefficient"] += dc
                        fl = float_limits[item["tier"]]
                        item["coefficient"] = max(1 - fl, min(1 + fl, item["coefficient"]))
                        item["adjusted_price"] = round(item["price"] * item["coefficient"], 2)

            if converged:
                break

        if not converged:
            current_total = sum(item.get("adjusted_price", 0) or 0 for item in data)
            delta = target_total - current_total
            if abs(delta) > 0.1:
                print("WARNING: 总价校准无法收敛，建议调整约束参数")

        for item in data:
            if not item["is_locked"]:
                fl = float_limits[item["tier"]]
                item["coefficient"] = max(1 - fl, min(1 + fl, item["coefficient"]))
                item["adjusted_price"] = round(item["price"] * item["coefficient"], 2)

        if total_price_min is not None:
            current_total = sum(item.get("adjusted_price", 0) or 0 for item in data)
            if current_total < total_price_min:
                delta = total_price_min - current_total
                adjustable = [item for item in data if not item["is_locked"]]
                adjustable.sort(key=lambda x: tier_priority.get(x.get("tier"), 1))

                total_weight = 0.0
                item_info = []
                for item in adjustable:
                    tier = item["tier"]
                    coefficient = item["coefficient"]
                    float_limit = float_limits[tier]
                    price = item["price"]
                    max_adjust = (1 + float_limit) - coefficient
                    max_adjust = max(max_adjust, 0)
                    weight = max_adjust * price
                    total_weight += weight
                    item_info.append((item, max_adjust, price))

                if total_weight > 0:
                    for item, max_adjust, price in item_info:
                        if max_adjust > 0:
                            dc = max_adjust * delta / total_weight
                            item["coefficient"] += dc
                            fl = float_limits[item["tier"]]
                            item["coefficient"] = max(1 - fl, min(1 + fl, item["coefficient"]))
                            item["adjusted_price"] = round(item["price"] * item["coefficient"], 2)

        if total_price_max is not None:
            current_total = sum(item.get("adjusted_price", 0) or 0 for item in data)
            if current_total > total_price_max:
                delta = total_price_max - current_total
                adjustable = [item for item in data if not item["is_locked"]]
                adjustable.sort(key=lambda x: tier_priority.get(x.get("tier"), 1))

                total_weight = 0.0
                item_info = []
                for item in adjustable:
                    tier = item["tier"]
                    coefficient = item["coefficient"]
                    float_limit = float_limits[tier]
                    price = item["price"]
                    max_adjust = coefficient - (1 - float_limit)
                    max_adjust = max(max_adjust, 0)
                    weight = max_adjust * price
                    total_weight += weight
                    item_info.append((item, max_adjust, price))

                if total_weight > 0:
                    for item, max_adjust, price in item_info:
                        if max_adjust > 0:
                            dc = max_adjust * delta / total_weight
                            item["coefficient"] += dc
                            fl = float_limits[item["tier"]]
                            item["coefficient"] = max(1 - fl, min(1 + fl, item["coefficient"]))
                            item["adjusted_price"] = round(item["price"] * item["coefficient"], 2)

        return data

    def run_lite_adjustment(self, gui_rows,
                            large_range=(0.005, 0.01),
                            medium_range=(0.01, 0.02),
                            small_range=(0.02, 0.03),
                            total_price_min=None,
                            total_price_max=None,
                            up_down_min=0.4,
                            up_down_max=0.6,
                            seed=42):
        self.seed = seed

        data = self.gui_data_to_processor_format(gui_rows)

        processor = _ParameterizedDataProcessor(
            seed=seed,
            large_range=large_range,
            medium_range=medium_range,
            small_range=small_range,
        )

        data = processor.identify_locked_items(data)
        data = processor.tier_grouping(data)
        data = self._generate_coefficients_custom(data, large_range, medium_range, small_range)
        data = processor.control_up_down_ratio(data, min_ratio=up_down_min, max_ratio=up_down_max)
        data = processor.control_correlation(data)

        if total_price_min is not None or total_price_max is not None:
            data = self._calibrate_total_price_custom(
                data, total_price_min, total_price_max,
                large_range, medium_range, small_range,
            )

        quality = processor.advanced_quality_check(data)

        result_rows = []
        original_total = 0
        adjusted_total = 0
        locked_count = 0
        adjustable_count = 0
        up_count = 0
        down_count = 0

        for i, item in enumerate(data):
            gui_row = gui_rows[i] if i < len(gui_rows) else {}
            quantity = gui_row.get("quantity", 0)
            unit_price = gui_row.get("unit_price", 0)
            price = item.get("price", 0)
            adjusted_price = item.get("adjusted_price", price)
            is_locked = item.get("is_locked", False)
            tier = item.get("tier")

            if quantity and quantity > 0:
                adjusted_unit_price = round(adjusted_price / quantity, 2)
            else:
                adjusted_unit_price = adjusted_price

            if price and price > 0:
                float_pct = round((adjusted_price - price) / price * 100, 2)
            else:
                float_pct = 0.0

            original_total += price or 0
            adjusted_total += adjusted_price or 0

            if is_locked:
                locked_count += 1
            else:
                adjustable_count += 1
                if adjusted_price > price:
                    up_count += 1
                elif adjusted_price < price:
                    down_count += 1

            result_rows.append({
                "name": item.get("name", ""),
                "quantity": quantity,
                "unit_price": unit_price,
                "price": price,
                "adjusted_unit_price": adjusted_unit_price,
                "adjusted_price": adjusted_price,
                "float_pct": float_pct,
                "is_locked": is_locked,
                "tier": tier,
            })

        change_amount = round(adjusted_total - original_total, 2)
        change_pct = round(change_amount / original_total * 100, 2) if original_total > 0 else 0.0

        summary = {
            "original_total": round(original_total, 2),
            "adjusted_total": round(adjusted_total, 2),
            "change_amount": change_amount,
            "change_pct": change_pct,
            "locked_count": locked_count,
            "adjustable_count": adjustable_count,
            "up_count": up_count,
            "down_count": down_count,
        }

        return {
            "result_rows": result_rows,
            "quality": quality,
            "summary": summary,
        }
