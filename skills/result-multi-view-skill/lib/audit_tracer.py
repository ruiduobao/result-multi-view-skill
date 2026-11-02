"""
audit_tracer.py
Core ledger and experiment version traceability engine for result-multi-view-skill.
Enables tracking, indexing, comparing, and auditing dozens of micro-experiments.
"""

import os
import json
import datetime
from typing import Dict, List, Optional, Any


class ExperimentLedger:
    """Manages the lifecycle, versioning, and comparative metrics of experimental runs."""

    def __init__(self, project_name: str = "Research Project", project_description: str = ""):
        self.project_name = project_name
        self.project_description = project_description
        self.baseline_exp_id: Optional[str] = None
        self.active_exp_id: Optional[str] = None
        self.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.experiments: List[Dict[str, Any]] = []

    @classmethod
    def load(cls, file_path: str) -> "ExperimentLedger":
        """Load experiment registry from a JSON file."""
        if not os.path.exists(file_path):
            ledger = cls()
            return ledger

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ledger = cls(
            project_name=data.get("project_name", "Research Project"),
            project_description=data.get("project_description", "")
        )
        ledger.baseline_exp_id = data.get("baseline_exp_id")
        ledger.active_exp_id = data.get("active_exp_id")
        ledger.updated_at = data.get("updated_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ledger.experiments = data.get("experiments", [])
        return ledger

    def save(self, file_path: str) -> None:
        """Save registry to a JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        data = {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "baseline_exp_id": self.baseline_exp_id,
            "active_exp_id": self.active_exp_id,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "experiments": self.experiments
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_experiment(self, exp_data: Dict[str, Any], set_active: bool = True) -> Dict[str, Any]:
        """Register or update an experiment record."""
        required = ["exp_id", "version", "name", "metrics"]
        for k in required:
            if k not in exp_data:
                raise ValueError(f"Missing required experiment key: '{k}'")

        # Set sensible defaults
        exp_data.setdefault("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        exp_data.setdefault("verdict", "PASS")
        exp_data.setdefault("category", "ablation")
        exp_data.setdefault("author", "Agent")
        exp_data.setdefault("commit_hash", "")
        exp_data.setdefault("rationale", "")
        exp_data.setdefault("treatment", "")
        exp_data.setdefault("config", {})
        exp_data.setdefault("dataset", {})
        exp_data.setdefault("gates", [])
        exp_data.setdefault("cases", [])
        exp_data.setdefault("artifacts", {})

        # Upsert
        found = False
        for i, existing in enumerate(self.experiments):
            if existing["exp_id"] == exp_data["exp_id"]:
                self.experiments[i] = exp_data
                found = True
                break

        if not found:
            self.experiments.append(exp_data)

        if not self.baseline_exp_id and len(self.experiments) == 1:
            self.baseline_exp_id = exp_data["exp_id"]

        if set_active or not self.active_exp_id:
            self.active_exp_id = exp_data["exp_id"]

        return exp_data

    def get_experiment(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an experiment record by ID."""
        for exp in self.experiments:
            if exp["exp_id"] == exp_id:
                return exp
        return None

    def list_experiments(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all experiments, optionally filtered by category."""
        if category:
            return [e for e in self.experiments if e.get("category") == category]
        return list(self.experiments)

    def compute_threeway_comparison(
        self,
        v0_id: Optional[str] = None,
        v1_id: Optional[str] = None,
        v2_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compute side-by-side comparison among 3 versions (e.g., Baseline V0, Prior V1, Final V2),
        matching the report_v2_eco_synthesis.html .threeway-table pattern.
        """
        if not self.experiments:
            return {"error": "No experiments in registry"}

        # Auto-resolve version IDs if not provided
        if not v0_id:
            v0_id = self.baseline_exp_id or self.experiments[0]["exp_id"]
        if not v2_id:
            v2_id = self.active_exp_id or self.experiments[-1]["exp_id"]
        if not v1_id:
            # Pick a middle version if available
            if len(self.experiments) >= 3:
                mid_idx = len(self.experiments) // 2
                v1_id = self.experiments[mid_idx]["exp_id"]
            else:
                v1_id = v0_id

        e0 = self.get_experiment(v0_id) or self.experiments[0]
        e1 = self.get_experiment(v1_id) or e0
        e2 = self.get_experiment(v2_id) or self.experiments[-1]

        m0 = e0.get("metrics", {})
        m1 = e1.get("metrics", {})
        m2 = e2.get("metrics", {})

        # Table rows comparison
        comparison_rows = []

        # 1. Overall Accuracy
        oa0 = m0.get("overall_accuracy", 0.0)
        oa1 = m1.get("overall_accuracy", 0.0)
        oa2 = m2.get("overall_accuracy", 0.0)
        d_oa = oa2 - oa0
        comparison_rows.append({
            "metric_name": "总体精度 (Overall Accuracy)",
            "rule_category": "全球/区域精度",
            "v0_val": f"{oa0*100:.2f}%",
            "v1_val": f"{oa1*100:.2f}%",
            "v2_val": f"{oa2*100:.2f}%",
            "v2_delta": f"{'+' if d_oa>=0 else ''}{d_oa*100:.2f}%",
            "status": "tag-pass" if d_oa >= 0 else "tag-fail",
            "verdict": f"较基准提高 {abs(d_oa)*100:.2f} 个百分点" if d_oa >= 0 else "出现回退"
        })

        # 2. Kappa Coefficient
        k0 = m0.get("kappa", 0.0)
        k1 = m1.get("kappa", 0.0)
        k2 = m2.get("kappa", 0.0)
        d_k = k2 - k0
        comparison_rows.append({
            "metric_name": "Kappa 系数 (Kappa)",
            "rule_category": "统计一致性",
            "v0_val": f"{k0:.4f}",
            "v1_val": f"{k1:.4f}",
            "v2_val": f"{k2:.4f}",
            "v2_delta": f"{'+' if d_k>=0 else ''}{d_k:.4f}",
            "status": "tag-pass" if d_k >= 0 else "tag-fail",
            "verdict": f"一致性指标稳步提升至 {k2:.3f}"
        })

        # 3. Class F1s (e.g. 种植园 PF, 自然林 NF, 非林 OT)
        cf0 = m0.get("class_f1", {})
        cf1 = m1.get("class_f1", {})
        cf2 = m2.get("class_f1", {})

        all_classes = sorted(list(set(list(cf0.keys()) + list(cf1.keys()) + list(cf2.keys()))))
        class_labels = {"PF": "种植园 (PF) F1", "NF": "自然林 (NF) F1", "OT": "非林 (OT) F1"}
        for c in all_classes:
            f0 = cf0.get(c, 0.0)
            f1 = cf1.get(c, 0.0)
            f2 = cf2.get(c, 0.0)
            df = f2 - f0
            c_name = class_labels.get(c, f"地物类目 {c} F1")
            comparison_rows.append({
                "metric_name": c_name,
                "rule_category": "目标地类特异度",
                "v0_val": f"{f0:.4f}",
                "v1_val": f"{f1:.4f}",
                "v2_val": f"{f2:.4f}",
                "v2_delta": f"{'+' if df>=0 else ''}{df:.4f}",
                "status": "tag-pass" if df >= 0 else "tag-fail",
                "verdict": "达到并超出指标门槛" if f2 >= 0.85 else "保持平稳监控"
            })

        # 4. Annual Transition / Jitter Rate
        tr0 = m0.get("transition_rate", 0.0)
        tr1 = m1.get("transition_rate", 0.0)
        tr2 = m2.get("transition_rate", 0.0)
        d_tr = tr2 - tr0
        comparison_rows.append({
            "metric_name": "年际像元震荡率 (Jitter Rate)",
            "rule_category": "时序物理一致性",
            "v0_val": f"{tr0*100:.3f}%/yr",
            "v1_val": f"{tr1*100:.3f}%/yr",
            "v2_val": f"{tr2*100:.3f}%/yr",
            "v2_delta": f"{'+' if d_tr>=0 else ''}{d_tr*100:.3f}%",
            "status": "tag-pass" if tr2 <= 0.05 else "tag-warn",
            "verdict": "假性闪烁抑制在 5%/yr 安全限以内" if tr2 <= 0.05 else "需注意边缘扰动"
        })

        # 5. Seam Discontinuity Ratio
        sr0 = m0.get("seam_ratio", 1.0)
        sr1 = m1.get("seam_ratio", 1.0)
        sr2 = m2.get("seam_ratio", 1.0)
        comparison_rows.append({
            "metric_name": "接缝拼接突变比 (Seam Ratio)",
            "rule_category": "空间无缝拼接",
            "v0_val": f"{sr0:.3f}x",
            "v1_val": f"{sr1:.3f}x",
            "v2_val": f"{sr2:.3f}x",
            "v2_delta": f"{sr2 - sr0:+.3f}x",
            "status": "tag-pass" if sr2 <= 1.20 else "tag-fail",
            "verdict": "无条带突变伪影，完全达标" if sr2 <= 1.20 else "超标，需排查边缘重叠"
        })

        # 6. Hard Gates Summary
        gates2 = e2.get("gates", [])
        passed_gates = sum(1 for g in gates2 if g.get("passed", False))
        total_gates = len(gates2)
        comparison_rows.append({
            "metric_name": "硬门禁综合达标率 (Gates Passed)",
            "rule_category": "上线准入验收门",
            "v0_val": "未建立门禁",
            "v1_val": f"{sum(1 for g in e1.get('gates', []) if g.get('passed', False))}/{len(e1.get('gates', []))}" if e1.get('gates') else "部分门禁",
            "v2_val": f"{passed_gates}/{total_gates} (100%)" if passed_gates == total_gates else f"{passed_gates}/{total_gates}",
            "v2_delta": "全门禁绿灯" if passed_gates == total_gates and total_gates > 0 else f"{total_gates - passed_gates}项待复核",
            "status": "tag-pass" if passed_gates == total_gates and total_gates > 0 else "tag-warn",
            "verdict": "所有定量物理门禁 100% 达成" if passed_gates == total_gates and total_gates > 0 else "存在未通过门禁项"
        })

        return {
            "v0": {"id": e0["exp_id"], "version": e0["version"], "name": e0["name"], "timestamp": e0["timestamp"]},
            "v1": {"id": e1["exp_id"], "version": e1["version"], "name": e1["name"], "timestamp": e1["timestamp"]},
            "v2": {"id": e2["exp_id"], "version": e2["version"], "name": e2["name"], "timestamp": e2["timestamp"]},
            "rows": comparison_rows
        }

    def get_summary_kpis(self) -> Dict[str, Any]:
        """Aggregate project-level summary KPIs."""
        total_experiments = len(self.experiments)
        pass_count = sum(1 for e in self.experiments if e.get("verdict") == "PASS")
        check_count = sum(1 for e in self.experiments if e.get("verdict") == "CHECK")
        fail_count = sum(1 for e in self.experiments if e.get("verdict") == "FAIL")

        best_oa = 0.0
        best_exp = None
        for e in self.experiments:
            oa = e.get("metrics", {}).get("overall_accuracy", 0.0)
            if oa > best_oa:
                best_oa = oa
                best_exp = e

        active_exp = self.get_experiment(self.active_exp_id) if self.active_exp_id else (self.experiments[-1] if self.experiments else None)
        active_oa = active_exp.get("metrics", {}).get("overall_accuracy", 0.0) if active_exp else 0.0
        active_kappa = active_exp.get("metrics", {}).get("kappa", 0.0) if active_exp else 0.0
        active_f1 = active_exp.get("metrics", {}).get("macro_f1", 0.0) if active_exp else 0.0

        return {
            "total_experiments": total_experiments,
            "pass_count": pass_count,
            "check_count": check_count,
            "fail_count": fail_count,
            "best_oa": best_oa,
            "best_exp_id": best_exp.get("exp_id") if best_exp else "",
            "active_version": active_exp.get("version", "v0") if active_exp else "N/A",
            "active_oa": active_oa,
            "active_kappa": active_kappa,
            "active_macro_f1": active_f1,
            "active_verdict": active_exp.get("verdict", "N/A") if active_exp else "N/A",
            "latest_update": self.updated_at
        }
