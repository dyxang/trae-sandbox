from datetime import datetime


class ReportGenerator:
    def _judge(self, check_item, warn_ranges=None):
        value = check_item["value"]
        passed = check_item["passed"]
        standard = check_item["standard"]

        if warn_ranges and not passed:
            for key, (lo, hi) in warn_ranges.items():
                if key in check_item:
                    v = check_item[key]
                    if lo is not None and v < lo:
                        continue
                    if hi is not None and v > hi:
                        continue
                    return "⚠警告"
            return "✗失败"

        if passed:
            if warn_ranges:
                for key, (lo, hi) in warn_ranges.items():
                    if key in check_item:
                        v = check_item[key]
                        near_boundary = False
                        if lo is not None and v >= lo:
                            near_boundary = True
                        if hi is not None and v <= hi:
                            near_boundary = True
                        if near_boundary:
                            return "⚠警告"
            return "✓通过"
        else:
            return "✗失败"

    def _judge_item(self, check_item):
        passed = check_item["passed"]
        value = check_item["value"]
        standard = check_item["standard"]

        if passed:
            if isinstance(value, (int, float)):
                if standard == "G < 0.25" and 0.20 <= value < 0.25:
                    return "⚠警告"
                if standard == "< 5%" and 3 <= value < 5:
                    return "⚠警告"
                if standard == "0.4~0.6" and (0.4 <= value < 0.45 or 0.55 < value <= 0.6):
                    return "⚠警告"
                if standard == "p > 0.05" and 0.05 < value <= 0.10:
                    return "⚠警告"
                if standard == "0.3 ≤ ρ ≤ 0.6" and (0.3 <= value < 0.35 or 0.55 < value <= 0.6):
                    return "⚠警告"
            return "✓通过"
        else:
            return "✗失败"

    def generate_report(self, data, quality_result, config=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        input_file = config.get("input_file") if config else "N/A"
        seed = config.get("random_seed") if config else 42

        total = len(data)
        locked_count = sum(1 for d in data if d.get("is_locked"))
        adjustable_count = total - locked_count
        locked_pct = round(locked_count / total * 100, 2) if total > 0 else 0
        adjustable_pct = round(adjustable_count / total * 100, 2) if total > 0 else 0

        adjustable = [d for d in data if not d.get("is_locked")]
        large_items = [d for d in adjustable if d.get("tier") == "large"]
        medium_items = [d for d in adjustable if d.get("tier") == "medium"]
        small_items = [d for d in adjustable if d.get("tier") == "small"]

        large_count = len(large_items)
        medium_count = len(medium_items)
        small_count = len(small_items)

        adj_total = sum(d.get("adjusted_price", 0) or 0 for d in adjustable)
        large_pct = round(sum(d.get("price", 0) or 0 for d in large_items) / adj_total * 100, 2) if adj_total > 0 else 0
        medium_pct = round(sum(d.get("price", 0) or 0 for d in medium_items) / adj_total * 100, 2) if adj_total > 0 else 0
        small_pct = round(sum(d.get("price", 0) or 0 for d in small_items) / adj_total * 100, 2) if adj_total > 0 else 0

        original_total = sum(d.get("price", 0) or 0 for d in data)
        new_total = sum(d.get("adjusted_price", 0) or 0 for d in data)
        change_amount = new_total - original_total
        change_rate = round(change_amount / original_total * 100, 2) if original_total else 0

        up_count = sum(1 for d in adjustable if d.get("adjusted_price", 0) > d.get("price", 0))
        down_count = sum(1 for d in adjustable if d.get("adjusted_price", 0) < d.get("price", 0))
        up_pct = round(up_count / adjustable_count * 100, 2) if adjustable_count > 0 else 0
        down_pct = round(down_count / adjustable_count * 100, 2) if adjustable_count > 0 else 0

        binomial_p = quality_result["direction_detection"]["binomial_test_p"]["value"]
        binomial_judge = self._judge_item(quality_result["direction_detection"]["binomial_test_p"])

        up_items = [
            (d, (d["adjusted_price"] - d["price"]) / d["price"] * 100)
            for d in adjustable if d["adjusted_price"] > d["price"]
        ]
        down_items = [
            (d, (d["adjusted_price"] - d["price"]) / d["price"] * 100)
            for d in adjustable if d["adjusted_price"] < d["price"]
        ]

        if up_items:
            max_up_item = max(up_items, key=lambda x: x[1])
            max_up_pct = round(max_up_item[1], 2)
            max_up_code = max_up_item[0]["code"]
        else:
            max_up_pct = 0
            max_up_code = ""

        if down_items:
            max_down_item = min(down_items, key=lambda x: x[1])
            max_down_pct = round(abs(max_down_item[1]), 2)
            max_down_code = max_down_item[0]["code"]
        else:
            max_down_pct = 0
            max_down_code = ""

        large_up_floats = [
            (d["adjusted_price"] - d["price"]) / d["price"] * 100
            for d in large_items if d["adjusted_price"] > d["price"]
        ]
        large_down_floats = [
            (d["adjusted_price"] - d["price"]) / d["price"] * 100
            for d in large_items if d["adjusted_price"] < d["price"]
        ]
        small_up_floats = [
            (d["adjusted_price"] - d["price"]) / d["price"] * 100
            for d in small_items if d["adjusted_price"] > d["price"]
        ]
        small_down_floats = [
            (d["adjusted_price"] - d["price"]) / d["price"] * 100
            for d in small_items if d["adjusted_price"] < d["price"]
        ]

        large_max_up = round(max(large_up_floats), 2) if large_up_floats else 0
        large_max_down = round(abs(min(large_down_floats)), 2) if large_down_floats else 0
        small_max_up = round(max(small_up_floats), 2) if small_up_floats else 0
        small_max_down = round(abs(min(small_down_floats)), 2) if small_down_floats else 0

        fp_spearman = quality_result["tier_compliance"]["float_price_spearman"]["value"]
        fp_spearman_judge = self._judge_item(quality_result["tier_compliance"]["float_price_spearman"])

        pearson_r = quality_result["correlation_detection"]["pearson_r"]["value"]
        pearson_judge = self._judge_item(quality_result["correlation_detection"]["pearson_r"])
        spearman_rho = quality_result["correlation_detection"]["spearman_rho"]["value"]
        spearman_judge = self._judge_item(quality_result["correlation_detection"]["spearman_rho"])
        ks_p = quality_result["correlation_detection"]["ks_test_p"]["value"]
        ks_judge = self._judge_item(quality_result["correlation_detection"]["ks_test_p"])

        gini = quality_result["imbalance_detection"]["gini_coefficient"]["value"]
        gini_judge = self._judge_item(quality_result["imbalance_detection"]["gini_coefficient"])
        z_outlier = quality_result["imbalance_detection"]["z_score_outliers"]["value"]
        z_judge = self._judge_item(quality_result["imbalance_detection"]["z_score_outliers"])

        all_checks = []
        for category in quality_result.values():
            for check in category.values():
                all_checks.append(check)

        pass_count = sum(1 for c in all_checks if self._judge_item(c) == "✓通过")
        warn_count = sum(1 for c in all_checks if self._judge_item(c) == "⚠警告")
        fail_count = sum(1 for c in all_checks if self._judge_item(c) == "✗失败")

        if fail_count > 0:
            suggestion = "存在失败项，建议调整约束参数或更换随机种子"
        elif warn_count > 0:
            suggestion = "存在警告项，建议关注但可接受"
        else:
            suggestion = "全部检验通过，方案可用"

        lines = []
        lines.append("=" * 40)
        lines.append("调价方案质量检验报告")
        lines.append("=" * 40)
        lines.append("")
        lines.append("【基本信息】")
        lines.append(f"输入文件: {input_file}")
        lines.append(f"处理时间: {timestamp}")
        lines.append(f"随机种子: {seed}")
        lines.append("")
        lines.append("【数量统计】")
        lines.append(f"总项目数: {total}")
        lines.append(f"锁定项: {locked_count} ({locked_pct}%)")
        lines.append(f"可调项: {adjustable_count} ({adjustable_pct}%)")
        lines.append(f"  - 大项: {large_count} (合价占比 {large_pct}%)")
        lines.append(f"  - 中项: {medium_count} (合价占比 {medium_pct}%)")
        lines.append(f"  - 小项: {small_count} (合价占比 {small_pct}%)")
        lines.append("")
        lines.append("【总价变化】")
        lines.append(f"原总价: {original_total:,.2f} 元")
        lines.append(f"新总价: {new_total:,.2f} 元")
        lines.append(f"变化额: {change_amount:,.2f} 元")
        lines.append(f"变化率: {change_rate}%")
        lines.append("")
        lines.append("【涨跌分布】")
        lines.append(f"上涨项: {up_count} ({up_pct}%)")
        lines.append(f"下跌项: {down_count} ({down_pct}%)")
        lines.append(f"二项检验p值: {binomial_p} ({binomial_judge})")
        lines.append("")
        lines.append("【浮动范围】")
        lines.append(f"最大上涨: +{max_up_pct}% ({max_up_code})")
        lines.append(f"最大下跌: -{max_down_pct}% ({max_down_code})")
        lines.append(f"大项最大浮动: +{large_max_up}% / -{large_max_down}%")
        lines.append(f"小项最大浮动: +{small_max_up}% / -{small_max_down}%")
        lines.append(f"浮动-合价Spearman: {fp_spearman} ({fp_spearman_judge})")
        lines.append("")
        lines.append("【相关性检验】")
        lines.append(f"Pearson r: {pearson_r} ({pearson_judge})")
        lines.append(f"Spearman ρ: {spearman_rho} ({spearman_judge})")
        lines.append(f"K-S检验p值: {ks_p} ({ks_judge})")
        lines.append("")
        lines.append("【不平衡检测】")
        lines.append(f"基尼系数: {gini} ({gini_judge})")
        lines.append(f"Z-Score异常值: {z_outlier['count']}个 ({z_outlier['pct']}%, {z_judge})")
        lines.append("")
        lines.append("【结论】")
        lines.append(f"✓ 通过: {pass_count}项")
        lines.append(f"⚠ 警告: {warn_count}项")
        lines.append(f"✗ 失败: {fail_count}项")
        lines.append("")
        lines.append(f"建议: {suggestion}")

        return "\n".join(lines)

    def save_report(self, report_text, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)
