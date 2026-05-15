import re
import random
import numpy as np
from scipy.stats import spearmanr, binomtest, kstest


class LiteCore:
    def __init__(self, seed=42, large_range=(0.005, 0.01), medium_range=(0.01, 0.02), small_range=(0.02, 0.03)):
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        random.seed(seed)
        self.large_range = large_range
        self.medium_range = medium_range
        self.small_range = small_range

    def identify_locked_items(self, data):
        lock_keywords = ["税金", "规费", "安全文明", "暂列金额"]
        summary_keywords = ["合计", "汇总", "小计", "总计"]

        for item in data:
            code = item.get("code", "")
            name = item.get("name", "")
            price = item.get("price")

            is_locked = False

            if code.startswith("0000"):
                is_locked = True

            if not is_locked and any(kw in name for kw in lock_keywords):
                is_locked = True

            if not is_locked:
                if len(code) < 8 and re.match(r'^[A-Za-z0-9]+$', code) and not code.isdigit():
                    is_locked = True

            if not is_locked and any(kw in name for kw in summary_keywords):
                is_locked = True

            if not is_locked and (price is None or price == 0):
                is_locked = True

            item["is_locked"] = is_locked
            if is_locked:
                item["adjusted_price"] = price

        adjustable = [d for d in data if not d["is_locked"]]
        if len(adjustable) == 0:
            raise ValueError("ERR_NO_ADJUSTABLE_ITEMS: 所有项目均为锁定项")

        return data

    def tier_grouping(self, data):
        adjustable = [d for d in data if not d["is_locked"]]
        prices = [d["price"] for d in adjustable]
        mean_price = np.mean(prices)
        std_price = np.std(prices)

        for item in adjustable:
            price = item["price"]
            if price > mean_price + std_price:
                item["tier"] = "large"
            elif price < mean_price - std_price:
                item["tier"] = "small"
            else:
                item["tier"] = "medium"

        tier_groups = {"large": [], "medium": [], "small": []}
        for item in adjustable:
            tier_groups[item["tier"]].append(item)

        for tier, items in tier_groups.items():
            directions = ["up", "down"] * ((len(items) + 1) // 2)
            random.shuffle(directions)
            for i, item in enumerate(items):
                item["direction"] = directions[i]

        for item in data:
            if item["is_locked"]:
                item.setdefault("tier", None)
                item.setdefault("direction", None)

        return data

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

    def control_up_down_ratio(self, data, min_ratio=0.4, max_ratio=0.6):
        adjustable = [item for item in data if not item["is_locked"]]
        n_up = sum(1 for item in adjustable if item["direction"] == "up")
        n_down = sum(1 for item in adjustable if item["direction"] == "down")

        if n_up + n_down == 0:
            return data

        up_ratio = n_up / (n_up + n_down)

        if min_ratio <= up_ratio <= max_ratio:
            return data

        tier_priority = {"small": 0, "medium": 1, "large": 2}

        for _ in range(10):
            if min_ratio <= up_ratio <= max_ratio:
                break

            if up_ratio > max_ratio:
                candidates = [item for item in adjustable if item["direction"] == "up"]
                candidates.sort(key=lambda x: tier_priority.get(x.get("tier"), 1))
                if candidates:
                    item = candidates[0]
                    item["direction"] = "down"
                    self._regenerate_coefficient(item)
            elif up_ratio < min_ratio:
                candidates = [item for item in adjustable if item["direction"] == "down"]
                candidates.sort(key=lambda x: tier_priority.get(x.get("tier"), 1))
                if candidates:
                    item = candidates[0]
                    item["direction"] = "up"
                    self._regenerate_coefficient(item)

            n_up = sum(1 for item in adjustable if item["direction"] == "up")
            n_down = sum(1 for item in adjustable if item["direction"] == "down")
            up_ratio = n_up / (n_up + n_down)

        if not (min_ratio <= up_ratio <= max_ratio):
            print("WARNING: 涨跌比例严重失衡，建议更换随机种子")

        return data

    def control_correlation(self, data, target_min=0.3, target_max=0.5):
        adjustable = [item for item in data if not item["is_locked"]]

        if len(adjustable) < 2:
            return data

        original_prices = np.array([item["price"] for item in adjustable])
        adjusted_prices = np.array([item["adjusted_price"] for item in adjustable])

        r = np.corrcoef(original_prices, adjusted_prices)[0, 1]

        if target_min <= r <= target_max:
            return data

        for _ in range(5):
            if target_min <= r <= target_max:
                break

            if r > target_max:
                noise_std = 0.005
            else:
                noise_std = 0.001

            for item in adjustable:
                tier = item["tier"]
                direction = item["direction"]

                if tier == "large":
                    base = self.rng.uniform(self.large_range[0], self.large_range[1])
                elif tier == "medium":
                    base = self.rng.uniform(self.medium_range[0], self.medium_range[1])
                else:
                    base = self.rng.uniform(self.small_range[0], self.small_range[1])

                noise = self.rng.normal(0, noise_std)

                if direction == "up":
                    coefficient = 1 + base + noise
                else:
                    coefficient = 1 - base + noise

                item["coefficient"] = coefficient
                item["adjusted_price"] = round(item["price"] * coefficient, 2)

            adjusted_prices = np.array([item["adjusted_price"] for item in adjustable])
            r = np.corrcoef(original_prices, adjusted_prices)[0, 1]

        return data

    def advanced_quality_check(self, data):
        adjustable = [item for item in data if not item["is_locked"]]

        adjusted_prices = np.array([item["adjusted_price"] for item in adjustable])
        original_prices = np.array([item["price"] for item in adjustable])
        float_pcts = np.array([
            (item["adjusted_price"] - item["price"]) / item["price"] * 100
            for item in adjustable
        ])

        n = len(adjusted_prices)
        mu = np.mean(adjusted_prices)
        diff_matrix = np.abs(adjusted_prices[:, None] - adjusted_prices[None, :])
        gini = np.sum(diff_matrix) / (2 * n * n * mu) if mu != 0 else 0.0

        float_mean = np.mean(float_pcts)
        float_std = np.std(float_pcts, ddof=0)
        z_scores = (float_pcts - float_mean) / float_std if float_std != 0 else np.zeros(n)
        z_outlier_count = int(np.sum(np.abs(z_scores) > 2))
        z_outlier_pct = round(z_outlier_count / n * 100, 2) if n > 0 else 0.0

        q1 = np.percentile(float_pcts, 25)
        q3 = np.percentile(float_pcts, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        iqr_outlier_count = int(np.sum((float_pcts < lower_bound) | (float_pcts > upper_bound)))

        n_up = sum(1 for item in adjustable if item["adjusted_price"] > item["price"])
        n_down = sum(1 for item in adjustable if item["adjusted_price"] < item["price"])
        up_down_ratio = n_up / (n_up + n_down) if (n_up + n_down) > 0 else 0.5

        binom_result = binomtest(n_up, n_up + n_down, 0.5) if (n_up + n_down) > 0 else None
        binomial_test_p = float(binom_result.pvalue) if binom_result is not None else 1.0

        if n >= 2:
            pearson_r = float(np.corrcoef(original_prices, adjusted_prices)[0, 1])
            if np.isnan(pearson_r):
                pearson_r = 0.0
        else:
            pearson_r = 0.0

        if n >= 2:
            spearman_rho_val, _ = spearmanr(original_prices, adjusted_prices)
            if np.isnan(spearman_rho_val):
                spearman_rho_val = 0.0
            spearman_rho_val = float(spearman_rho_val)
        else:
            spearman_rho_val = 0.0

        if n >= 2:
            ks_result = kstest(float_pcts, 'norm', args=(float_mean, float_std)) if float_std > 0 else kstest(float_pcts, 'norm', args=(float_mean, 1.0))
            ks_test_p = float(ks_result.pvalue)
        else:
            ks_test_p = 1.0

        large_items = [item for item in adjustable if item.get("tier") == "large"]
        small_items = [item for item in adjustable if item.get("tier") == "small"]

        large_floats = [
            (item["adjusted_price"] - item["price"]) / item["price"] * 100
            for item in large_items
        ] if large_items else [0]
        small_floats = [
            (item["adjusted_price"] - item["price"]) / item["price"] * 100
            for item in small_items
        ] if small_items else [0]

        large_max_float = round(max(large_floats), 2)
        small_min_float = round(min(small_floats), 2)

        if n >= 2:
            fp_spearman, _ = spearmanr(float_pcts, original_prices)
            if np.isnan(fp_spearman):
                fp_spearman = 0.0
            fp_spearman = float(fp_spearman)
        else:
            fp_spearman = 0.0

        return {
            "imbalance_detection": {
                "gini_coefficient": {
                    "value": round(float(gini), 4),
                    "passed": float(gini) < 0.25,
                    "standard": "G < 0.25",
                },
                "z_score_outliers": {
                    "value": {"count": z_outlier_count, "pct": z_outlier_pct},
                    "passed": z_outlier_pct < 5,
                    "standard": "< 5%",
                },
                "iqr_outliers": {
                    "value": iqr_outlier_count,
                    "passed": True,
                    "standard": "参考值",
                },
            },
            "direction_detection": {
                "up_down_ratio": {
                    "value": round(float(up_down_ratio), 4),
                    "passed": 0.4 <= up_down_ratio <= 0.6,
                    "standard": "0.4~0.6",
                },
                "binomial_test_p": {
                    "value": round(float(binomial_test_p), 4),
                    "passed": binomial_test_p > 0.05,
                    "standard": "p > 0.05",
                },
            },
            "correlation_detection": {
                "pearson_r": {
                    "value": round(float(pearson_r), 4),
                    "passed": True,
                    "standard": "参考值",
                },
                "spearman_rho": {
                    "value": round(float(spearman_rho_val), 4),
                    "passed": 0.3 <= abs(spearman_rho_val) <= 0.6,
                    "standard": "0.3 ≤ ρ ≤ 0.6",
                },
                "ks_test_p": {
                    "value": round(float(ks_test_p), 4),
                    "passed": ks_test_p > 0.05,
                    "standard": "p > 0.05",
                },
            },
            "tier_compliance": {
                "large_max_float": {
                    "value": large_max_float,
                    "passed": True,
                    "standard": "参考值",
                },
                "small_min_float": {
                    "value": small_min_float,
                    "passed": True,
                    "standard": "参考值",
                },
                "float_price_spearman": {
                    "value": round(float(fp_spearman), 4),
                    "passed": True,
                    "standard": "参考值",
                },
            },
        }
