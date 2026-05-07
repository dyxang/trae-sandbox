import numpy as np


class RiskDetector:
    def __init__(self):
        pass

    def detect_risks(self, data):
        adjustable = [item for item in data if not item.get("is_locked", False)]
        if not adjustable:
            return {
                "gini": {"value": 0.0, "passed": True},
                "z_score_outliers": {"value": 0, "items": []},
                "iqr_outliers": {"value": 0, "items": []},
                "risk_items": [],
                "risk_distribution": {"low": 0, "medium": 0, "high": 0},
            }

        prices = np.array([item["price"] for item in adjustable])
        n = len(prices)
        mu = np.mean(prices)
        diff_matrix = np.abs(prices[:, None] - prices[None, :])
        gini = float(np.sum(diff_matrix) / (2 * n * n * mu)) if mu != 0 else 0.0

        price_mean = np.mean(prices)
        price_std = np.std(prices, ddof=0)
        z_scores = (prices - price_mean) / price_std if price_std != 0 else np.zeros(n)

        z_outlier_items = []
        for i, item in enumerate(adjustable):
            if abs(z_scores[i]) > 2:
                z_outlier_items.append({"code": item["code"], "name": item["name"], "price": item["price"], "z_score": round(float(z_scores[i]), 4)})

        q1 = np.percentile(prices, 25)
        q3 = np.percentile(prices, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        iqr_outlier_items = []
        for i, item in enumerate(adjustable):
            if prices[i] < lower_bound or prices[i] > upper_bound:
                iqr_outlier_items.append({"code": item["code"], "name": item["name"], "price": item["price"]})

        risk_items = []
        risk_dist = {"low": 0, "medium": 0, "high": 0}

        for i, item in enumerate(adjustable):
            z = float(z_scores[i])
            is_z_high = abs(z) > 2
            is_iqr_outlier = prices[i] < lower_bound or prices[i] > upper_bound

            if is_z_high and is_iqr_outlier:
                risk_level = "high"
            elif is_z_high or is_iqr_outlier:
                risk_level = "medium"
            else:
                risk_level = "low"

            risk_dist[risk_level] += 1
            risk_items.append({
                "code": item["code"],
                "name": item["name"],
                "price": item["price"],
                "z_score": round(z, 4),
                "risk_level": risk_level,
            })

        return {
            "gini": {"value": round(gini, 4), "passed": gini < 0.25},
            "z_score_outliers": {"value": len(z_outlier_items), "items": z_outlier_items},
            "iqr_outliers": {"value": len(iqr_outlier_items), "items": iqr_outlier_items},
            "risk_items": risk_items,
            "risk_distribution": risk_dist,
        }

    def generate_risk_report(self, data, risk_result):
        lines = []
        lines.append("=" * 40)
        lines.append("报价风险排查报告")
        lines.append("=" * 40)
        lines.append("")

        lines.append("【风险概述】")
        gini_val = risk_result["gini"]["value"]
        gini_passed = risk_result["gini"]["passed"]
        gini_status = "✓通过" if gini_passed else "✗失败"
        lines.append(f"基尼系数: {gini_val} ({gini_status}, 标准: G < 0.25)")

        z_count = risk_result["z_score_outliers"]["value"]
        lines.append(f"Z-Score异常值: {z_count}个 (|Z| > 2)")

        iqr_count = risk_result["iqr_outliers"]["value"]
        lines.append(f"IQR异常值: {iqr_count}个 (超出1.5倍IQR范围)")
        lines.append("")

        lines.append("【高风险项目列表】")
        high_risk_items = [item for item in risk_result["risk_items"] if item["risk_level"] == "high"]
        if high_risk_items:
            for item in high_risk_items:
                lines.append(f"  {item['code']} {item['name']} - 合价: {item['price']:,.2f}, Z-Score: {item['z_score']}, 风险: 高")
        else:
            lines.append("  无高风险项目")
        lines.append("")

        lines.append("【风险等级分布】")
        dist = risk_result["risk_distribution"]
        total_risk = dist["low"] + dist["medium"] + dist["high"]
        lines.append(f"  低风险: {dist['low']}项 ({round(dist['low']/total_risk*100, 1) if total_risk else 0}%)")
        lines.append(f"  中风险: {dist['medium']}项 ({round(dist['medium']/total_risk*100, 1) if total_risk else 0}%)")
        lines.append(f"  高风险: {dist['high']}项 ({round(dist['high']/total_risk*100, 1) if total_risk else 0}%)")
        lines.append("")

        lines.append("【建议调整方向】")
        if high_risk_items:
            lines.append("  - 重点关注高风险项目，考虑适当调整其报价使其接近均值区间")
        if dist["medium"] > dist["low"]:
            lines.append("  - 中风险项目较多，建议整体优化报价分布的均衡性")
        if not gini_passed:
            lines.append("  - 基尼系数偏高，报价分布不均衡，建议缩小高低价差距")
        if z_count > 0:
            lines.append("  - 存在Z-Score异常项，建议检查是否存在报价偏离过大的项目")
        if iqr_count > 0:
            lines.append("  - 存在IQR异常项，建议检查极端报价的合理性")
        if not high_risk_items and gini_passed and z_count == 0 and iqr_count == 0:
            lines.append("  - 报价风险较低，当前报价分布较为均衡")

        return "\n".join(lines)

    def save_risk_report(self, report_text, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)
