"""
driver.py
Unified executable driver for result-multi-view-skill.
Enables agents to record, index, compare, visualize, and audit dozens of micro-experiments.
Outputs both:
  1) Standalone interactive HTML dashboard (inspired by report_v2_eco_synthesis.html)
  2) 300 DPI publication-grade composite visual board (PNG)
"""

import os
import sys
import json
import argparse
import datetime
from typing import Optional, Dict, Any, List

# Ensure UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure lib directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from lib.audit_tracer import ExperimentLedger
from lib.tile_extractor import WindowedTileExtractor
from lib.visual_builder import MultiViewVisualBuilder


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new experiment ledger."""
    ledger = ExperimentLedger(project_name=args.project, project_description=args.desc)
    ledger.save(args.registry)
    print(f"[OK] Initialized empty experiment ledger at: {args.registry}")


def cmd_record(args: argparse.Namespace) -> None:
    """Record or update an experiment run into the ledger."""
    ledger = ExperimentLedger.load(args.registry)

    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8") as f:
            exp_data = json.load(f)
    else:
        # Build from CLI arguments
        if not args.exp_id:
            raise ValueError("--exp-id is required when --json-file is not provided")
        exp_data = {
            "exp_id": args.exp_id,
            "version": args.version or "v1.0",
            "name": args.name or args.exp_id,
            "verdict": args.verdict or "PASS",
            "category": args.category or "ablation",
            "author": args.author or "Agent",
            "rationale": args.rationale or "",
            "metrics": {
                "overall_accuracy": args.oa or 0.85,
                "kappa": args.kappa or 0.80,
                "macro_f1": args.f1 or 0.82,
                "class_f1": {
                    "PF": args.pf_f1 or 0.80,
                    "NF": args.nf_f1 or 0.90,
                    "OT": args.ot_f1 or 0.92
                },
                "transition_rate": args.jitter or 0.025,
                "seam_ratio": args.seam or 1.10
            }
        }

    ledger.register_experiment(exp_data, set_active=args.active)
    ledger.save(args.registry)
    print(f"[OK] Successfully recorded experiment '{exp_data['exp_id']}' (v{exp_data.get('version')}) into: {args.registry}")


def cmd_compare(args: argparse.Namespace) -> None:
    """Compare 2 or 3 experiment versions side-by-side."""
    ledger = ExperimentLedger.load(args.registry)
    comp = ledger.compute_threeway_comparison(v0_id=args.v0, v1_id=args.v1, v2_id=args.v2)

    print("\n" + "="*80)
    print(f"  多版本实验对比审计报告 (3-Way Version Audit)")
    print(f"  V0 基准: {comp['v0']['id']} ({comp['v0']['version']}) | V1 历程: {comp['v1']['id']} ({comp['v1']['version']}) | V2 终版: {comp['v2']['id']} ({comp['v2']['version']})")
    print("="*80)
    fmt = "{:<26} | {:<12} | {:<12} | {:<12} | {:<10}"
    print(fmt.format("指标名称", "V0 基准", "V1 历程", "V2 终版", "增量变化"))
    print("-" * 80)
    for r in comp["rows"]:
        print(fmt.format(r["metric_name"][:24], r["v0_val"], r["v1_val"], r["v2_val"], r["v2_delta"]))
    print("="*80 + "\n")


def cmd_render(args: argparse.Namespace) -> None:
    """Render interactive HTML dashboard and optional 300 DPI composite board."""
    ledger = ExperimentLedger.load(args.registry)
    if not ledger.experiments:
        print(f"[WARN] No experiments found in ledger: {args.registry}. Please record experiments first.")
        return

    # 1. Generate 300 DPI Composite Visual Board (if requested)
    board_path = args.board
    if board_path:
        builder = MultiViewVisualBuilder(project_title=f"{ledger.project_name} 实验结果综合审核看板")
        builder.build_composite_board(
            experiments=ledger.experiments,
            output_png=board_path,
            active_exp_id=ledger.active_exp_id
        )
        print(f"[OK] Generated 300 DPI composite visual board: {board_path}")

    # 2. Render Interactive HTML Dashboard
    template_path = args.template or os.path.join(SCRIPT_DIR, "templates", "report_template.html")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        tmpl = f.read()

    kpi = ledger.get_summary_kpis()
    comp = ledger.compute_threeway_comparison()
    active_exp = ledger.get_experiment(ledger.active_exp_id) or ledger.experiments[-1]

    # Convert board image to base64 if present
    board_b64 = ""
    if board_path and os.path.exists(board_path):
        board_b64 = WindowedTileExtractor.file_to_b64(board_path)

    # Build dynamic HTML replacements
    html_out = tmpl
    html_out = html_out.replace("{{PROJECT_NAME}}", ledger.project_name)
    html_out = html_out.replace("{{PROJECT_DESCRIPTION}}", ledger.project_description or "泛热带30m长时间序列遥感数据生产与实验结果审核")
    html_out = html_out.replace("{{UPDATED_AT}}", ledger.updated_at)
    html_out = html_out.replace("{{TOTAL_EXPERIMENTS}}", str(kpi["total_experiments"]))
    html_out = html_out.replace("{{PASS_COUNT}}", str(kpi["pass_count"]))
    html_out = html_out.replace("{{ACTIVE_VERSION}}", str(kpi["active_version"]))
    html_out = html_out.replace("{{ACTIVE_OA}}", f"{kpi['active_oa']*100:.2f}%")
    html_out = html_out.replace("{{ACTIVE_KAPPA}}", f"{kpi['active_kappa']:.4f}")
    html_out = html_out.replace("{{ACTIVE_MACRO_F1}}", f"{kpi['active_macro_f1']:.4f}")
    html_out = html_out.replace("{{ACTIVE_VERDICT}}", str(kpi["active_verdict"]))
    html_out = html_out.replace("{{ACTIVE_RATIONALE}}", active_exp.get("rationale", ""))
    html_out = html_out.replace("{{BOARD_IMAGE_B64}}", board_b64)

    # Inject Comparison Table Rows
    table_rows_html = []
    for r in comp["rows"]:
        tag_cls = r.get("status", "tag-pass")
        row = f"""<tr>
  <td><b>{r['metric_name']}</b></td>
  <td>{r['rule_category']}</td>
  <td class="val-v0">{r['v0_val']}</td>
  <td class="val-v1">{r['v1_val']}</td>
  <td class="val-v2">{r['v2_val']}</td>
  <td><span class="{tag_cls}">{r['v2_delta']}</span> {r['verdict']}</td>
</tr>"""
        table_rows_html.append(row)
    html_out = html_out.replace("{{THREEWAY_ROWS_HTML}}", "\n".join(table_rows_html))

    # Inject Case Cards (Qualitative tile/sample crops)
    case_cards_html = []
    # Collect all cases across experiments (especially active and baseline)
    all_cases = []
    for exp in reversed(ledger.experiments):
        for c in exp.get("cases", []):
            if c not in all_cases:
                all_cases.append(c)

    for c in all_cases[:9]:  # Show up to 9 featured cases
        img_src = c.get("image_b64") or c.get("image_path") or ""
        stats_line = ""
        if "stats" in c and c["stats"]:
            stats_line = " · ".join([f"{k}: <b>{v}</b>" for k, v in c["stats"].items()])

        card = f"""<div class="case-card" data-tile="{c.get('tile_id', '')}">
  <div class="case-header">
    <h3>{c.get('title', '典型审计切片')}</h3>
    <span class="case-badge">{c.get('location', '重点研究区')}</span>
  </div>
  <div class="case-preview">
    <img src="{img_src}" alt="{c.get('title', '')}" loading="lazy">
  </div>
  <p>
    <b>问题根因</b>：{c.get('root_cause', '历史版本存在边界模糊与时序类别跳变。')}<br>
    <b>治理效果</b>：{c.get('effect', '经过定点优化后，假性闪烁显著抑制，地类一致率显著提高。')}
  </p>
  {f'<div class="case-stats">{stats_line}</div>' if stats_line else ''}
</div>"""
        case_cards_html.append(card)

    html_out = html_out.replace("{{CASE_CARDS_HTML}}", "\n".join(case_cards_html) if case_cards_html else "<p style='color:#94a3b8;'>暂无定性案例图像，可使用 extract-tile 工具录入。</p>")

    # Inject JSON payload for Chart.js and interactive version selector
    html_out = html_out.replace("{{EXPERIMENTS_JSON}}", json.dumps(ledger.experiments, ensure_ascii=False))

    output_html = args.output
    os.makedirs(os.path.dirname(os.path.abspath(output_html)), exist_ok=True)
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"[OK] Generated interactive multi-view audit dashboard: {output_html}")


def cmd_extract_tile(args: argparse.Namespace) -> None:
    """Extract a windowed patch from a GeoTIFF raster."""
    extractor = WindowedTileExtractor()
    b64 = extractor.extract_zoom_b64(
        raster_path=args.raster,
        band=args.band,
        col_mid=args.col,
        row_mid=args.row,
        half_size=args.half_size,
        draw_crosshair=not args.no_crosshair
    )
    if args.output:
        import base64
        data = b64.split(",")[1]
        with open(args.output, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"[OK] Saved windowed tile PNG: {args.output}")
    else:
        print(f"[OK] Extracted base64 string length: {len(b64)} chars")


def main():
    parser = argparse.ArgumentParser(description="result-multi-view-skill CLI driver")
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to execute")

    # init
    p_init = subparsers.add_parser("init", help="Initialize empty experiment registry")
    p_init.add_argument("--registry", required=True, help="Path to experiment_registry.json")
    p_init.add_argument("--project", default="Research Project", help="Project name")
    p_init.add_argument("--desc", default="", help="Project description")

    # record
    p_rec = subparsers.add_parser("record", help="Record or update an experiment run")
    p_rec.add_argument("--registry", required=True, help="Path to experiment_registry.json")
    p_rec.add_argument("--json-file", help="Path to experiment JSON file")
    p_rec.add_argument("--exp-id", help="Experiment ID slug (e.g. exp01_baseline)")
    p_rec.add_argument("--version", help="Version label (e.g. v1.0)")
    p_rec.add_argument("--name", help="Descriptive name")
    p_rec.add_argument("--verdict", choices=["PASS", "CHECK", "FAIL"], default="PASS")
    p_rec.add_argument("--category", default="ablation")
    p_rec.add_argument("--author", default="Agent")
    p_rec.add_argument("--rationale", default="")
    p_rec.add_argument("--oa", type=float, help="Overall accuracy (0..1)")
    p_rec.add_argument("--kappa", type=float, help="Kappa coefficient")
    p_rec.add_argument("--f1", type=float, help="Macro F1 (0..1)")
    p_rec.add_argument("--pf-f1", type=float, help="Plantation F1 (0..1)")
    p_rec.add_argument("--nf-f1", type=float, help="Natural Forest F1 (0..1)")
    p_rec.add_argument("--ot-f1", type=float, help="Other land cover F1 (0..1)")
    p_rec.add_argument("--jitter", type=float, help="Annual jitter/transition rate (0..1)")
    p_rec.add_argument("--seam", type=float, help="Seam ratio (<=1.20)")
    p_rec.add_argument("--active", action="store_true", default=True, help="Set as active/latest experiment")

    # compare
    p_cmp = subparsers.add_parser("compare", help="Compare 2 or 3 versions")
    p_cmp.add_argument("--registry", required=True, help="Path to experiment_registry.json")
    p_cmp.add_argument("--v0", help="Baseline experiment ID")
    p_cmp.add_argument("--v1", help="Intermediate experiment ID")
    p_cmp.add_argument("--v2", help="Final experiment ID")

    # render
    p_rnd = subparsers.add_parser("render", help="Render interactive HTML dashboard & 300 DPI board")
    p_rnd.add_argument("--registry", required=True, help="Path to experiment_registry.json")
    p_rnd.add_argument("--output", required=True, help="Output HTML file path")
    p_rnd.add_argument("--board", help="Optional output 300 DPI composite board PNG path")
    p_rnd.add_argument("--template", help="Custom HTML template path")

    # extract-tile
    p_ext = subparsers.add_parser("extract-tile", help="Extract windowed patch from GeoTIFF")
    p_ext.add_argument("--raster", required=True, help="Input GeoTIFF raster path")
    p_ext.add_argument("--col", type=int, default=300, help="Center column index")
    p_ext.add_argument("--row", type=int, default=300, help="Center row index")
    p_ext.add_argument("--half-size", type=int, default=300, help="Half window size")
    p_ext.add_argument("--band", type=int, default=1, help="Raster band index")
    p_ext.add_argument("--no-crosshair", action="store_true", help="Disable crosshair overlay")
    p_ext.add_argument("--output", help="Optional output PNG file path")

    args = parser.parse_args()
    if args.subcommand == "init":
        cmd_init(args)
    elif args.subcommand == "record":
        cmd_record(args)
    elif args.subcommand == "compare":
        cmd_compare(args)
    elif args.subcommand == "render":
        cmd_render(args)
    elif args.subcommand == "extract-tile":
        cmd_extract_tile(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
