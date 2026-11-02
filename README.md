# Result Multi-View Skill (实验结果综合审核与多版本全景追溯)

[![skills.sh](https://img.shields.io/badge/skills.sh-indexed-blue?style=flat-square)](https://skills.sh)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Agent-Claude%20Code%20%7C%20Cursor%20%7C%20Codex-8A2BE2?style=flat-square)](https://skills.sh)

> **为 AI Agent（Claude Code, Cursor, Codex, OpenCode 等）打造的通用实验结果综合审核、多版本全景追溯与高质感可视化 Skill。**
> 支持追踪科研项目中多达数十次微实验的迭代演进，提供三版本深度差分对比表（3-Way Audit Table）、定量硬门禁矩阵、窗口化栅格切片画廊与双交付物自动化输出（300 DPI 出版图板 + 离线自包含 HTML 看板）。

---

## 🌟 核心特性 (Features)

1. **实验全生命周期账本追踪 (Experiment Ledger)**
   - 每次小实验（哪怕只调一个超参或后处理阈值）均自动分配唯一 `exp_id`，记录时间戳、责任 Agent、Git Commit、超参数快照、样本规模与定量指标。
   - 彻底解决实验版本多达几十次后，数据散落、指标遗忘 baseline、无法复原的问题。

2. **三版本深度差分对比表 (3-Way Audit Table)**
   - 汲取高端地表覆盖审核报告设计规范，采用 `.val-v0`（基准版）、`.val-v1`（中间消融版）、`.val-v2`（当前定稿版）三栏并列结构。
   - 自动生成增量百分比、趋势徽标（`tag-pass` / `tag-warn` / `tag-fail`）以及物理机理裁决描述。

3. **内存安全窗口读与切片放大镜 (Windowed Tile Extractor)**
   - 严格遵循大数据与遥感生产纪律：**严禁整图 `.read()`，峰值内存受控 ≤10–15 GB**。
   - 单次仅窗口提取目标中心区域，自动叠加中心红十字（Cross-hair）坐标线与固定地表覆盖色标，Base64 纯离线内嵌。

4. **定量硬门禁核验矩阵 (Hard Gates Matrix)**
   - 对上线准入的关键指标（如产物齐备性 G0、接缝连续性 G0b、精度底线 G1、目标地类 F1 G2、年际震荡率 G4、零突变守恒 G5）逐项比对，亮红绿灯卡片。

5. **双交付物统一输出 (Dual Output Deliverables)**
   - **交付物 ①：学术报告级 300 DPI 全景大图板 (PNG)**：符合期刊与学位论文规范，包含版本演进轨迹、地类 F1 柱状图、门禁遵从矩阵、帕累托分布和典型审计卡片。
   - **交付物 ②：交互式离线自包含 HTML 审核看板**：深色科技风设计，带顶部毛玻璃导航、KPI 网格、交互式版本下拉切换器、动态演进曲线与画廊切片灯箱放大镜，单个 HTML 双击即开，断网可用。

---

## 🚀 安装方式 (Installation via skills.sh)

本 Skill 已注册至 [skills.sh](https://skills.sh) 开放生态。在任何支持 Agent 技能的项目中运行：

```bash
# 全局安装 (对本机所有 Agent 生效)
npx skills add ruiduobao/result-multi-view-skill -g

# 或仅为当前项目安装
npx skills add ruiduobao/result-multi-view-skill
```

---

## 💻 快速上手 (Quick Start)

### 1. 记录一次微实验 (Record)
```bash
python driver.py record \
  --registry "results/experiments_registry.json" \
  --exp-id "exp06_temporal_refine" \
  --version "v2.1" \
  --name "时序一致性滤波与边界平滑" \
  --verdict "PASS" \
  --category "post_processing" \
  --oa 0.8872 \
  --kappa 0.8540 \
  --f1 0.8690 \
  --pf-f1 0.8860 \
  --nf-f1 0.9430 \
  --ot-f1 0.9590 \
  --jitter 0.0195 \
  --seam 1.095 \
  --rationale "修复 0.5 度子瓦拼接周期性全零带，采用双向对称邻域平滑"
```

### 2. 多版本指标深度对比 (Compare)
```bash
python driver.py compare \
  --registry "results/experiments_registry.json" \
  --v0 "exp01_rf_baseline" \
  --v1 "exp03_aef_distill_v1" \
  --v2 "exp06_temporal_refine"
```

输出示例：
```
================================================================================
  多版本实验对比审计报告 (3-Way Version Audit)
  V0 基准: exp01_rf_baseline (v0.1) | V1 历程: exp03_aef_distill_v1 (v1.5) | V2 终版: exp06_temporal_refine (v2.1)
================================================================================
指标名称                       | V0 基准        | V1 历程        | V2 终版        | 增量变化      
--------------------------------------------------------------------------------
总体精度 (Overall Accuracy)    | 81.20%       | 85.80%       | 88.72%       | +7.52%    
Kappa 系数 (Kappa)           | 0.7410       | 0.8040       | 0.8540       | +0.1130   
种植园 (PF) F1                | 0.7180       | 0.8120       | 0.8860       | +0.1680   
年际像元震荡率 (Jitter Rate)      | 8.200%/yr    | 3.500%/yr    | 1.950%/yr    | -6.250%   
接缝拼接突变比 (Seam Ratio)       | 1.450x       | 1.220x       | 1.095x       | -0.355x   
硬门禁综合达标率 (Gates Passed)    | 未建立门禁        | 3/4          | 7/7 (100%)   | 全门禁绿灯     
================================================================================
```

### 3. 一键渲染双交付物 (Render)
```bash
python driver.py render \
  --registry "results/experiments_registry.json" \
  --board "results/figs/fig_comprehensive_audit_board.png" \
  --output "results/audit_dashboard.html"
```

---

## 🐍 Python API 调用

```python
from lib.audit_tracer import ExperimentLedger
from lib.tile_extractor import WindowedTileExtractor
from lib.visual_builder import MultiViewVisualBuilder

# 1. 载入实验账本
ledger = ExperimentLedger.load("experiments_registry.json")

# 2. 注册新实验
ledger.register_experiment({
    "exp_id": "exp07_dual_stream_distill",
    "version": "v2.2",
    "name": "双流特征融合与时间步蒸馏",
    "verdict": "PASS",
    "metrics": {
        "overall_accuracy": 0.8890,
        "kappa": 0.8565,
        "macro_f1": 0.8710,
        "class_f1": {"PF": 0.8870, "NF": 0.9440, "OT": 0.9600},
        "transition_rate": 0.0210,
        "seam_ratio": 1.098
    }
})
ledger.save("experiments_registry.json")

# 3. 提取 30m 红十字放大切片
extractor = WindowedTileExtractor()
b64_crop = extractor.extract_zoom_b64(
    raster_path="SEA_G1_2020.tif",
    col_mid=3710, row_mid=3710, half_size=300
)

# 4. 生成 300 DPI 出版大图板
builder = MultiViewVisualBuilder(project_title="实验结果综合审核看板")
builder.build_composite_board(ledger.experiments, "audit_board.png")
```

---

## 📂 仓库结构 (Repository Structure)

```
result-multi-view-skill/
├── SKILL.md                          # 根目录 Skill 指南
├── driver.py                         # 统一 CLI 驱动入口
├── templates/
│   ├── experiment_schema.json        # 实验注册标准 JSON Schema
│   ├── report_template.html          # 深色科技风 HTML 模板
│   └── sample_registry.json          # 5个典型版本的完整账本样例
├── lib/
│   ├── audit_tracer.py               # 账本版本管理与指标差分
│   ├── tile_extractor.py             # 内存安全窗口读与切片提取
│   └── visual_builder.py             # 300 DPI 全景图板生成器
├── examples/
│   ├── run_demo.py                   # 端到端测试脚本
│   ├── demo_experiment_registry.json # 演练生成的 5 版本实验账本
│   ├── demo_composite_board.png      # 产出样例：300 DPI 大图板
│   └── demo_audit_dashboard.html     # 产出样例：自包含 HTML 看板
└── skills/
    └── result-multi-view-skill/      # 标准多 Skill 格式子目录
```

---

## 📄 开源许可证 (License)

本项目基于 [MIT 许可证](LICENSE) 开源发布。
欢迎通过 Issue 或 Pull Request 提交扩展！
