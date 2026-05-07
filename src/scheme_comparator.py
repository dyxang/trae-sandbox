class SchemeComparator:
    def __init__(self):
        pass

    def _score_gini(self, gini):
        if gini < 0.15:
            return 25
        elif gini < 0.20:
            return 20
        elif gini < 0.25:
            return 15
        else:
            return 5

    def _score_ratio(self, ratio):
        if 0.45 <= ratio <= 0.55:
            return 25
        elif 0.40 <= ratio < 0.45 or 0.55 < ratio <= 0.60:
            return 18
        else:
            return 5

    def _score_correlation(self, r):
        if 0.3 <= r <= 0.5:
            return 25
        elif 0.2 <= r < 0.3 or 0.5 < r <= 0.6:
            return 18
        else:
            return 5

    def _score_change(self, change_pct):
        abs_change = abs(change_pct)
        if abs_change < 2:
            return 25
        elif abs_change < 3:
            return 18
        else:
            return 5

    def compare_schemes(self, scheme_results):
        comparison_table = []
        scores = []

        for idx, result in enumerate(scheme_results):
            gini = result.get("imbalance_detection", {}).get("gini_coefficient", {}).get("value", 1.0)
            up_down_ratio = result.get("direction_detection", {}).get("up_down_ratio", {}).get("value", 0.5)
            pearson_r = result.get("correlation_detection", {}).get("pearson_r", {}).get("value", 0.0)
            total_change_pct = result.get("total_change_pct", 0.0)

            gini_score = self._score_gini(gini)
            ratio_score = self._score_ratio(up_down_ratio)
            corr_score = self._score_correlation(pearson_r)
            change_score = self._score_change(total_change_pct)
            total_score = round(gini_score + ratio_score + corr_score + change_score, 1)

            scheme_name = result.get("scheme_name", f"scheme_{idx}")

            comparison_table.append({
                "scheme": scheme_name,
                "gini": gini,
                "up_down_ratio": up_down_ratio,
                "pearson_r": pearson_r,
                "total_change_pct": total_change_pct,
                "score": total_score,
            })
            scores.append(total_score)

        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        ranking = [0] * len(scores)
        for rank, idx in enumerate(sorted_indices, start=1):
            ranking[idx] = rank

        best_idx = sorted_indices[0]
        best_score = scores[best_idx]
        best_entry = comparison_table[best_idx]

        reasons = []
        if self._score_gini(best_entry["gini"]) == 25:
            reasons.append("基尼系数优秀")
        if self._score_ratio(best_entry["up_down_ratio"]) == 25:
            reasons.append("涨跌比例均衡")
        if self._score_correlation(best_entry["pearson_r"]) == 25:
            reasons.append("相关性适中")
        if self._score_change(best_entry["total_change_pct"]) == 25:
            reasons.append("总价变化小")

        if not reasons:
            reasons.append("综合评分最高")

        return {
            "comparison_table": comparison_table,
            "ranking": ranking,
            "best_scheme": {"index": best_idx, "reason": "，".join(reasons)},
            "scores": scores,
        }

    def generate_comparison_report(self, scheme_results, comparison_result):
        lines = []
        lines.append("=" * 40)
        lines.append("多方案比选报告")
        lines.append("=" * 40)
        lines.append("")

        lines.append("【各方案关键指标对比】")
        lines.append(f"{'方案':<15} {'基尼系数':<10} {'涨跌比例':<10} {'Pearson r':<10} {'总价变化%':<10} {'评分':<8}")
        lines.append("-" * 63)
        for entry in comparison_result["comparison_table"]:
            lines.append(f"{entry['scheme']:<15} {entry['gini']:<10} {entry['up_down_ratio']:<10} {entry['pearson_r']:<10} {entry['total_change_pct']:<10} {entry['score']:<8}")
        lines.append("")

        lines.append("【综合评分排名】")
        ranking = comparison_result["ranking"]
        scores = comparison_result["scores"]
        table = comparison_result["comparison_table"]
        sorted_schemes = sorted(range(len(ranking)), key=lambda i: ranking[i])
        for rank, idx in enumerate(sorted_schemes, start=1):
            lines.append(f"  第{rank}名: {table[idx]['scheme']} (评分: {scores[idx]})")
        lines.append("")

        lines.append("【推荐方案】")
        best = comparison_result["best_scheme"]
        best_entry = table[best["index"]]
        lines.append(f"  推荐方案: {best_entry['scheme']}")
        lines.append(f"  综合评分: {best_entry['score']}")
        lines.append(f"  推荐理由: {best['reason']}")

        return "\n".join(lines)

    def save_comparison_report(self, report_text, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)
