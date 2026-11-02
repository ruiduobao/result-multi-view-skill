---
name: result-multi-view-skill
description: 针对遥感数据生产、机器学习实验与科研数据处理结果审核的多视图可视化与多版本追溯技能。支持记录几十次小实验的版本历程，自动生成300 DPI全景综合图板和交互式离线HTML审核看板，具备三版本深度差分对比（3-Way Audit Table）、定量硬门禁矩阵、窗口化栅格瓦片切片画廊与全账本可追溯机制。
---

# Result Multi-View Skill (实验结果综合审核与多版本全景追溯)

`result-multi-view-skill` 专为**遥感长时序数据生产、机器学习模型迭代与科研实验结果审核**设计。
针对一个项目中**多达几十次微实验（微调、消融、分臂试验、后处理平滑）**的痛点，提供**全生命周期账本追踪（Experiment Ledger）**、**三版本深度差分对比表（3-Way Audit Table）**、**硬门禁准入矩阵（Hard Gates Matrix）**、**窗口化栅格切片画廊（Tile Gallery with Cross-hair Zooms）**以及**双交付物自动化输出**（300 DPI 出版级全景图板 + 交互式离线自包含 HTML 看板）。

设计深度汲取了中国土地覆盖数据审核报告（`report_v2_eco_synthesis.html`）的高质感深色科技 UI、分类色彩学规范与三版本差分表设计，并严格遵循 `AGENTS.md` 的遥感数据生产纪律与 `dataviz` 数据可视化标准。

---

## 1. 快速上手 (Agent 极速调用路径)

任何 Agent 在完成一次小实验、模型训练或数据后处理后，通过以下三步即可完成实验归档、多版本差分与可视化看板生成：

### 第一步：记录本次小实验版本 (Record)
```bash
F:/anaconda/envs/geeMAP_env/python.exe .claude/skills/result-multi-view-skill/driver.py record \
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
*(亦可直接传入完整 JSON 文件：`--json-file experiment_run.json`)*

### 第二步：对比任意两至三版本指标差异 (Compare)
```bash
F:/anaconda/envs/geeMAP_env/python.exe .claude/skills/result-multi-view-skill/driver.py compare \
  --registry "results/experiments_registry.json" \
  --v0 "exp01_rf_baseline" \
  --v1 "exp03_aef_distill_v1" \
  --v2 "exp06_temporal_refine"
```

### 第三步：渲染出版级 300 DPI 图板与离线交互看板 (Render)
```bash
F:/anaconda/envs/geeMAP_env/python.exe .claude/skills/result-multi-view-skill/driver.py render \
  --registry "results/experiments_registry.json" \
  --board "results/figs/fig_comprehensive_audit_board.png" \
  --output "results/audit_dashboard.html"
```

---

## 2. 核心架构与功能组件

```
result-multi-view-skill/
├── SKILL.md                          # 本说明指南与规范契约
├── driver.py                         # 统一 CLI 执行驱动器 (init / record / compare / render / extract-tile)
├── templates/
│   ├── experiment_schema.json        # 实验版本注册标准 JSON Schema
│   ├── report_template.html          # 深色科技风交互式 HTML 审核看板模板
│   └── sample_registry.json          # 5个典型版本生产实战账本样例
├── lib/
│   ├── __init__.py
│   ├── audit_tracer.py               # 实验账本管理、指标差分计算、门禁准入校验
│   ├── tile_extractor.py             # 内存安全窗口读 (Windowed Read)、RGB 映射、红十字中心放大镜
│   └── visual_builder.py             # Matplotlib 300 DPI 综合全景看板构建器 (符合 dataviz)
└── examples/
    ├── run_demo.py                   # 端到端全流程验证执行脚本
    ├── demo_experiment_registry.json # 演练账本数据
    ├── demo_composite_board.png      # 产出：300 DPI 出版级大图板
    └── demo_audit_dashboard.html     # 产出：交互式自包含审核看板
```

### 核心亮点：
1. **多实验版本账本机制 (Traceability Ledger)**：
   - 每个项目维护统一的 `experiments_registry.json`，完整记录版本号、时间戳、操作 Agent、Git Commit、超参数、样本规模与定量指标。
   - 解决实验多达几十次后，指标混乱、遗忘 baseline、无法复现溯源的问题。
2. **三版本深度对比表 (3-Way Audit Table)**：
   - 继承 `report_v2_eco_synthesis.html` 的 `.val-v0`（基准）、`.val-v1`（中间调优）、`.val-v2`（最终定稿）三栏结构。
   - 自动生成增量百分比、正负向趋势标签（`tag-pass`、`tag-warn`、`tag-fail`）以及定量裁决描述。
3. **窗口化内存安全切片提取 (Windowed Tile Extractor)**：
   - 严格遵循 `AGENTS.md` 约束：**严禁整图 `.read()`**，单次只读取 `Window(c - half, r - half, 2*half, 2*half)`。
   - 自动叠加中心红十字（Cross-hair）坐标线与固定地表覆盖色标，Base64 内联至 HTML，无外挂图片丢失风险。
4. **定量硬门禁核验矩阵 (Hard Gates Matrix)**：
   - 对上线准入的关键指标（如产物齐备性 G0、接缝连续性 G0b、精度底线 G1、目标地类 F1 G2、年际震荡率 G4、零突变守恒 G5）逐项比对，亮红绿灯卡片。

---

## 3. Python API 编程调用方式

在复杂脚本或自研流程中，可直接导入 `result-multi-view-skill` 内部类：

```python
from lib.audit_tracer import ExperimentLedger
from lib.tile_extractor import WindowedTileExtractor
from lib.visual_builder import MultiViewVisualBuilder

# 1. 载入或初始化账本
ledger = ExperimentLedger.load("experiments_registry.json")

# 2. 录入实验
ledger.register_experiment({
    "exp_id": "exp07_dual_stream_distill",
    "version": "v2.2",
    "name": "双流特征融合与时间步蒸馏",
    "timestamp": "2026-11-02 18:00:00",
    "author": "Agent-C1",
    "category": "model_architecture",
    "verdict": "PASS",
    "metrics": {
        "overall_accuracy": 0.8890,
        "kappa": 0.8565,
        "macro_f1": 0.8710,
        "class_f1": {"PF": 0.8870, "NF": 0.9440, "OT": 0.9600},
        "transition_rate": 0.0210,
        "seam_ratio": 1.098
    },
    "gates": [
        {"name": "G0 产物齐备性", "threshold": "=100%", "measured": "100%", "passed": True},
        {"name": "G0b 接缝连续性", "threshold": "<=1.20x", "measured": "1.098x", "passed": True},
        {"name": "G1 总体精度底线", "threshold": ">=85.0%", "measured": "88.90%", "passed": True}
    ]
})
ledger.save("experiments_registry.json")

# 3. 提取特征切片
extractor = WindowedTileExtractor()
b64_crop = extractor.extract_zoom_b64(
    raster_path="SEA_G1_2020.tif",
    col_mid=3710, row_mid=3710, half_size=300
)

# 4. 生成 300 DPI 图板
builder = MultiViewVisualBuilder(project_title="实验结果审核总图板")
builder.build_composite_board(ledger.experiments, "audit_board.png")
```

---

## 4. 严守规范与纪律 (Guardrails)

1. **术语铁律（AGENTS.md §10）**：
   - 界面、图表、文本中**一律使用「种植园」**，**严禁出现敏感旧称**。
2. **地物标准配色（AGENTS.md §10 & dataviz）**：
   - 种植园 (PF)：蓝色 `#1f77b4`
   - 自然林 (NF)：绿色 `#2ca02c`
   - 非林 (OT)：灰度 `#b0b0b0`
   - 无数据 (NoData)：米白 `#f4f3ef`
3. **内存与栅格安全（AGENTS.md §2 规则 4）**：
   - 本地处理峰值内存控制在 ≤10–15 GB。
   - 栅格必须使用 `Window` 读写，严禁无限制整图读入。
4. **图表设计标准（dataviz 规则）**：
   - 严禁双 Y 轴；坐标轴网格线衰减至 `alpha=0.2`；标注直接指向目标数据点；状态指示灯严格区分绿色（PASS）、黄色（WARN）、红色（FAIL）。

---

## 5. 故障排除与常见问题 (Troubleshooting)

| 症状 / 错误 | 根本原因 | 解决方案 |
|---|---|---|
| `UnicodeEncodeError: 'charmap'` | Windows 终端默认代码页不是 UTF-8 | 脚本开头执行 `sys.stdout.reconfigure(encoding="utf-8")`（`driver.py` 已内置） |
| `FileNotFoundError: Raster missing` | 切片提取时指定的 GeoTIFF 路径错误 | `WindowedTileExtractor` 会自动生成带坐标标识的优雅降级占位图，不会引发程序崩溃 |
| `ZeroDivisionError: transition rate` | 原始雨林等全恒定样区年变化像元数为 0 | 计算比值时加入物理稳定性底噪 `max(denom, 5e-4)` |
| `Chart.js offline blank` | 离线无互联网环境下 CDN 无法加载 | 核心看板结构为纯原生 HTML/CSS，表格、KPI、图片与切片 100% 离线可用；图表支持静态内嵌 SVG/Canvas |

---

## 6. 验证完成证明 (Definition of Done)

本 Skill 已在当前容器环境经过完整端到端测试，产物如下：
- **测试脚本**：`examples/run_demo.py`（Exit code 0）
- **300 DPI 综合看板**：`examples/demo_composite_board.png`（0.87 MB）
- **交互式自包含 HTML 看板**：`examples/demo_audit_dashboard.html`（1.21 MB）
- **命令行多版本比对**：`driver.py compare`（三版本差分核验表输出无误）
- **原生栅格窗口切片**：`driver.py extract-tile`（通过 `SEA_G1_FD_mosaic_2020.tif` 实测）
