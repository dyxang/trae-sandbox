import argparse
import os
import json
import random as _random


def _run_single_scheme(input_path, output_path, seed, discount, tolerance, config=None):
    from src.excel_handler import ExcelHandler
    from src.data_processor import DataProcessor
    from src.report_generator import ReportGenerator

    handler = ExcelHandler(input_path)
    structure = handler.detect_structure()
    data = handler.read_data(structure)

    processor = DataProcessor(seed=seed)
    data = processor.identify_locked_items(data)
    data = processor.tier_grouping(data)
    data = processor.generate_coefficients(data)
    data = processor.control_up_down_ratio(data)
    data = processor.control_correlation(data)
    data = processor.calibrate_total_price(data, target_discount_pct=discount, tolerance=tolerance)

    handler.write_results(data, structure, output_path)

    quality = processor.advanced_quality_check(data)

    report_config = config if config else None
    if report_config is None:
        report_config = type("Config", (), {"get": lambda self, k: {"input_file": input_path, "random_seed": seed}.get(k)})()
    else:
        if report_config.get("input_file") is None:
            report_config._config["input_file"] = input_path
        if report_config.get("random_seed") is None:
            report_config._config["random_seed"] = seed

    generator = ReportGenerator()
    report_text = generator.generate_report(data, quality, config=report_config)

    report_path = output_path.replace(".xlsx", "_report.txt")
    generator.save_report(report_text, report_path)

    print(f"方案完成 (seed={seed}): {output_path}")
    print(f"检验报告: {report_path}")

    return quality


def _run_batch_mode(args, config):
    from src.batch_processor import BatchProcessor

    discount = args.discount
    tolerance = args.tolerance
    if config:
        if discount is None and config.get("target_discount_pct") is not None:
            discount = config.get("target_discount_pct")
        if config.get("tolerance") is not None:
            tolerance = config.get("tolerance")

    bp = BatchProcessor(config=config)
    summary = bp.process_directory(args.input_dir, args.output_dir, seed=args.seed, discount=discount, tolerance=tolerance)

    print(f"\n批量处理完成: 成功 {summary['success_files']}/{summary['total_files']}")
    if summary["failed_files"]:
        print("失败文件:")
        for f in summary["failed_files"]:
            print(f"  {f['file']}: {f['error']}")


def _run_risk_mode(args, config):
    from src.excel_handler import ExcelHandler
    from src.risk_detector import RiskDetector

    handler = ExcelHandler(args.input)
    structure = handler.detect_structure()
    data = handler.read_data(structure)

    detector = RiskDetector()
    risk_result = detector.detect_risks(data)
    report_text = detector.generate_risk_report(data, risk_result)
    detector.save_risk_report(report_text, args.output)

    print(f"风险排查报告已保存: {args.output}")


def _run_compare_mode(args, config):
    from src.excel_handler import ExcelHandler
    from src.data_processor import DataProcessor
    from src.scheme_comparator import SchemeComparator

    report_files = [f.strip() for f in args.reports.split(",")]
    scheme_results = []

    for report_file in report_files:
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                content = f.read()
            quality = _parse_report_to_quality(content)
            scheme_results.append(quality)
        except Exception:
            xlsx_path = report_file.replace("_report.txt", ".xlsx")
            try:
                handler = ExcelHandler(xlsx_path)
                structure = handler.detect_structure()
                data = handler.read_data(structure)
                processor = DataProcessor(seed=42)
                data = processor.identify_locked_items(data)
                quality = processor.advanced_quality_check(data)
                original_total = sum(item.get("price", 0) or 0 for item in data)
                adjusted_total = sum(item.get("adjusted_price", 0) or 0 for item in data)
                quality["total_change_pct"] = round((adjusted_total - original_total) / original_total * 100, 2) if original_total else 0
                quality["scheme_name"] = os.path.basename(xlsx_path).replace(".xlsx", "")
                scheme_results.append(quality)
            except Exception as e:
                print(f"WARNING: 无法读取方案 {report_file}: {e}")

    if not scheme_results:
        print("ERROR: 没有可比较的方案")
        return

    comparator = SchemeComparator()
    comparison_result = comparator.compare_schemes(scheme_results)
    report_text = comparator.generate_comparison_report(scheme_results, comparison_result)

    output_path = args.output if args.output else "comparison_report.txt"
    comparator.save_comparison_report(report_text, output_path)

    print(f"方案比选报告已保存: {output_path}")


def _parse_report_to_quality(content):
    quality = {
        "imbalance_detection": {},
        "direction_detection": {},
        "correlation_detection": {},
        "tier_compliance": {},
    }

    lines = content.split("\n")
    scheme_name = "unknown"

    for line in lines:
        if "基尼系数:" in line:
            parts = line.split("基尼系数:")[1].strip().split()
            try:
                gini_val = float(parts[0])
            except (ValueError, IndexError):
                gini_val = 1.0
            quality["imbalance_detection"]["gini_coefficient"] = {"value": gini_val}
        elif "涨跌比例" in line and "value" not in str(quality.get("direction_detection", {}).get("up_down_ratio")):
            pass
        elif "Pearson r:" in line:
            parts = line.split("Pearson r:")[1].strip().split()
            try:
                r_val = float(parts[0])
            except (ValueError, IndexError):
                r_val = 0.0
            quality["correlation_detection"]["pearson_r"] = {"value": r_val}
        elif "变化率:" in line:
            parts = line.split("变化率:")[1].strip().replace("%", "").split()
            try:
                change_val = float(parts[0])
            except (ValueError, IndexError):
                change_val = 0.0
            quality["total_change_pct"] = change_val

    for line in lines:
        if "上涨项:" in line:
            parts = line.split("上涨项:")[1].strip().split()
            try:
                up_count = int(parts[0])
            except (ValueError, IndexError):
                up_count = 0
        elif "下跌项:" in line:
            parts = line.split("下跌项:")[1].strip().split()
            try:
                down_count = int(parts[0])
            except (ValueError, IndexError):
                down_count = 0

    try:
        up_down_ratio = up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5
    except NameError:
        up_down_ratio = 0.5
    quality["direction_detection"]["up_down_ratio"] = {"value": round(up_down_ratio, 4)}
    quality["scheme_name"] = scheme_name

    return quality


def main():
    parser = argparse.ArgumentParser(description="工程造价智能调价引擎")
    parser.add_argument("--mode", choices=["adjust", "batch", "risk", "compare"], default="adjust", help="运行模式")
    parser.add_argument("--input", default=None, help="输入Excel文件路径")
    parser.add_argument("--output", default=None, help="输出Excel文件路径")
    parser.add_argument("--input-dir", default=None, help="批量处理输入目录")
    parser.add_argument("--output-dir", default=None, help="批量处理输出目录")
    parser.add_argument("--reports", default=None, help="比选报告文件列表，逗号分隔")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--seeds", type=str, default=None, help="多个随机种子，逗号分隔")
    parser.add_argument("--num-schemes", type=int, default=None, help="方案数量（自动生成随机种子）")
    parser.add_argument("--discount", type=float, default=None, help="目标下浮比例，如1.5")
    parser.add_argument("--tolerance", type=float, default=0.01, help="误差容忍度")
    parser.add_argument("--config", type=str, default=None, help="YAML配置文件路径")
    args = parser.parse_args()

    from src.config import Config

    config = None
    if args.config:
        config = Config(args.config)
        errors = config.validate()
        if errors:
            for e in errors:
                print(f"配置错误: {e}")
            return

    if args.mode == "adjust":
        if not args.input or not args.output:
            parser.error("adjust模式需要 --input 和 --output 参数")
        _run_adjust_mode(args, config)
    elif args.mode == "batch":
        if not args.input_dir or not args.output_dir:
            parser.error("batch模式需要 --input-dir 和 --output-dir 参数")
        _run_batch_mode(args, config)
    elif args.mode == "risk":
        if not args.input or not args.output:
            parser.error("risk模式需要 --input 和 --output 参数")
        _run_risk_mode(args, config)
    elif args.mode == "compare":
        if not args.reports:
            parser.error("compare模式需要 --reports 参数")
        _run_compare_mode(args, config)


def _run_adjust_mode(args, config):
    discount = args.discount
    tolerance = args.tolerance

    if config:
        if discount is None and config.get("target_discount_pct") is not None:
            discount = config.get("target_discount_pct")
        if config.get("tolerance") is not None:
            tolerance = config.get("tolerance")

    seed = args.seed
    if config and config.get("random_seed") is not None:
        seed = config.get("random_seed")

    seed_list = []

    if args.seeds:
        seed_list = [int(s.strip()) for s in args.seeds.split(",")]
    elif args.num_schemes:
        rng = _random.Random(seed)
        seed_list = [rng.randint(1, 999999) for _ in range(args.num_schemes)]
    else:
        seed_list = [seed]

    if len(seed_list) == 1:
        _run_single_scheme(args.input, args.output, seed_list[0], discount, tolerance, config)
    else:
        output_base, output_ext = os.path.splitext(args.output)
        for seed in seed_list:
            scheme_output = f"{output_base}_seed{seed}{output_ext}"
            _run_single_scheme(args.input, scheme_output, seed, discount, tolerance, config)


if __name__ == "__main__":
    main()
