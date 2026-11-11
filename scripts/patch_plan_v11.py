# -*- coding: utf-8 -*-
"""把 plan.md 从 v1.0 升到 v1.1：写入 D2/D4/D5 裁决、三条调整、已核事实。
每处替换都断言命中次数，避免静默漏改。"""
import pathlib
import re
import sys

P = pathlib.Path(__file__).resolve().parent.parent / "plan.md"
text = P.read_text(encoding="utf-8")
orig_len = len(text)
log = []


def rep(old, new, label):
    global text
    n = text.count(old)
    if n != 1:
        print(f"FAIL [{label}] 期望命中 1 次，实际 {n} 次")
        sys.exit(1)
    text = text.replace(old, new)
    log.append(f"OK   {label}")


def resub(pattern, new, label):
    global text
    hits = re.findall(pattern, text, flags=re.S)
    if len(hits) != 1:
        print(f"FAIL [{label}] 期望命中 1 次，实际 {len(hits)} 次")
        sys.exit(1)
    text = re.sub(pattern, lambda m: new, text, count=1, flags=re.S)
    log.append(f"OK   {label}")


# ---------------------------------------------------------------- 1. 抬头
rep(
    "> 技术负责人 / 全栈工程师：灵\n"
    "> 状态：**待你裁决（第 8 节 5 个决策点）**。批准后从「阶段 0 数据层」开工，不跳序。\n"
    "> 本文所有页码、图号、公式，均来自我本机对四家手册 PDF 的抽取核对（见 2.1），不是从二手网页抄的。",
    "> 技术负责人 / 全栈工程师：灵\n"
    "> 版本：**v1.1（2026-11-11 修订）**。阶段 0 数据层已交付并通过抽检；第 8 节 5 个决策点已全部裁决，正文按裁决结果改过。\n"
    "> 本文所有页码、图号、公式，均来自我本机对手册 PDF 的抽取核对（见 2.1），不是从二手网页抄的。\n"
    "\n"
    "**v1.1 相对 v1.0 改了什么**（只列会改变行为的）：\n"
    "\n"
    "1. **D2 落地**：爆高口径从「固定 1,000 ft」改成「读每条等压线在图上的峰值」，每条线带自己的爆高；地爆读 HOB = 0 的图底边；火球空爆 110·W^0.4 / 地爆 145·W^0.4，禁止混搭。\n"
    "2. **D4 落地**：城市人口统一为「城市中心半径 10 km 内 WorldPop 人口」，不用行政市界；效应圈内人口另算，两个数不合并。\n"
    "3. **D5 落地**：备用底图改为自托管 Natural Earth 110m 公有领域轮廓，不用任何第三方免费额度。\n"
    "4. **顺序调整**：`/blast-radius/` 提到地图之前，阶段 1 直接交一页可上线的静态表。\n"
    "5. **三条硬约束入正文**：全站禁 demo 类字样；免责每页恰一行、放页底；地图禁旋转与俯仰。\n"
    "6. **页数口径**：首月 80 页靠加城市堆，不靠加页面类型。\n"
    "7. **修正 v1.0 的两处出处错误**：缩放律是式 (3.61.2) p.101（不是 §3.75 p.108）；§12.66 的烧伤句在 p.563。",
    "抬头 + v1.1 变更记录",
)

# ---------------------------------------------------------------- 2. 结论 1
rep(
    "这是全文唯一的实质性问题，第 2.2 节讲透，第 8 节 D1 等你拍板。",
    "这是全文唯一的实质性问题，第 2.2 节讲透。**D1 已裁决：接受缩放**，每个缩放值都带固定标签。",
    "§0 结论 1",
)

# ---------------------------------------------------------------- 3. 偏移量说明
rep(
    "我把第 2、3、7、12 章 PDF 下到本地，用 pypdf 抽文本，逐页核对图表标题与印刷页码（PDF 页与印刷页的偏移已确定，ch3=+79，ch7=+275，ch2=+25）。结论如下：",
    "我把第 2、3、7、12 章 PDF 和整本扫描件下到本地，逐页核对图表标题与印刷页码。**两套偏移量不要混用**：整本 `6852629.pdf` 里第 3 章 = 印刷页 + 9；分章 `eonw_3.pdf` 里 = 印刷页 + 79；ch7 = +275，ch2 = +25。下文写的页码一律是**印刷页**。结论如下：",
    "§2.1 偏移量口径",
)

# ---------------------------------------------------------------- 4. §2.1 关键几行
rep(
    "| 「其他当量的同一超压作用距离按 W^(1/3) 缩放」 | §3.75 | 108 | **已核** |\n"
    "| 1 kt 自由空气爆炸：超压 vs 距离 | Fig. 3.72 | 109 | **已核**（图题已抽到） |\n"
    "| 1 kt 空中爆炸：地面距离 vs 超压 vs 爆高（高压段） | Fig. 3.73a | 111 | 版式推定，录入时核 |\n"
    "| 同上（中压段） | Fig. 3.73b | 113 | 版式推定，录入时核 |\n"
    "| **同上（低压段，含 1–30 psi）** | **Fig. 3.73c** | **115** | **已核**（最关键的一张） |",
    "| 地面距离按同一立方根律缩放 `D/D₁ = (W/W₁)^(1/3)` | 式 (3.61.2)，§3.61；§3.62 重述 | 101 / 102 | **已核**（v1.0 误记成 §3.75 p.108，已修正） |\n"
    "| 「取爆高为零」即地爆 | §3.64 | 106 | **已核**（原文 “taking the height of burst … to be zero”） |\n"
    "| 对 Fig. 3.73a–c 的缩放重述 | §3.73 | 110 | **已核** |\n"
    "| 1 kt 自由空气爆炸：超压 vs 距离 | Fig. 3.72 | 109 | 已核（v1 未使用） |\n"
    "| 1 kt 空中爆炸（高压段） | Fig. 3.73a | 111 | 未使用（若出现 10 psi 以上的数，必须注明取自本图） |\n"
    "| 同上（中压段） | Fig. 3.73b | 113 | 未使用（同上） |\n"
    "| **同上（低压段，含 1 / 2 / 4 / 6 / 8 / 10 psi）** | **Fig. 3.73c** | **115** | **已核 + 阶段 0 已数字化**（最关键的一张；**没有 5 psi 这条线**） |",
    "§2.1 图表清单",
)

rep(
    "| 1 Mt 时 4.5–6 cal/cm² 对应二度烧伤为主 | §12 正文 | 562 | **已核**（可做交叉校验锚点） |",
    "| 1 Mt 时 4.5–6 cal/cm² 对应二度烧伤为主，斜距 9–10 mi | §12.66 | **563** | **已核**（v1.0 写 562 有误：§12.63 从 562 起，这句话在 563） |\n"
    "| 1 Mt 时 8 cal/cm² 约 7 mi | §7.43 | 290 | **已核**（第二条标定锚点） |",
    "§2.1 §12.66 页码",
)

# ---------------------------------------------------------------- 5. §2.2 ②③④ 整段重写
resub(
    r"\*\*② 5 psi 半径 / ③ 1 psi 半径\*\*.*?(?=\n### 2\.3 数据文件设计)",
    """**② 5 psi / ③ 1 psi 半径（已按 D2 落地：读峰值，不选固定爆高）**

- 来源：Fig. 3.73c（p.115，1 kt，低压段）。**爆高不是我们挑的**：每条等压线在地面距离方向都有一个最右端（峰值点），读那一端的横坐标与纵坐标，得到「该 psi 的最大地面距离 + 达到该距离的爆高」。
- 手册 p.114 的算例正是这个读法，我直接引用、没有自己拟合：
  > “From Fig. 3.73c, the maximum ground distance to which 4 psi extends for a 1 KT weapon is 2,600 feet. This occurs for a burst height of approximately 1,100 feet.”
  我用像素复读到 2,618 ft，对原文 **+0.7%**，整族曲线由此定标。
- 1 kt 四条峰值：1 psi 7,020 ft @ 1,575 ft｜2 psi 4,192 ft @ 1,100 ft｜4 psi 2,600 ft @ 1,100 ft｜6 psi 2,010 ft @ 950 ft。
- **5 psi 图上没有印线**（只印 1 / 2 / 4 / 6 / 8 / 10 psi），按 4 与 6 psi 的对数压力位置插值，t = 0.5503 → **2,275 ft @ 1,017 ft**。台账里每一行 5 psi 的 `readout` 必须出现 `interpolated between 4 and 6 psi contours, at X ft`，页面上也照印。
- 多当量：`d = d₁kt × W^(1/3)`，依据式 (3.61.2) p.101（§3.62 p.102、§3.73 p.110 重述）。**爆高同律缩放** `H = H₁kt × W^(1/3)`，否则就不叫「同一条等压线」了。
- 值类型 `scaled_curve_read`，带 `base`（1 kt 英尺数 + 像素坐标）与 `scaling`（law / formula / pages），可逐条复算。
- 页面标签固定：`scaled from the 1 kt curve (§3.61, p.101)`。
- **地爆（D2 第二态）**：爆高取 0（§3.64 p.106），读每条等压线与图底边的交点。1 kt：1 psi 3,830 ft、4 psi 1,655 ft、5 psi 1,361 ft、6 psi 1,121 ft。
- **1 Mt 的爆高边界（必须上页面）**：峰值爆高按 W^(1/3) 缩放到 1 Mt 是 5 psi 10,174 ft、1 psi 15,750 ft，而 §3.73 p.110 的匀质海平面大气假设只覆盖 **5,000 ft 以内**。这条外推了 2–3 倍，且未做 §3.64–3.66 的高度修正（省略的方向使数值偏小）。结果面板必须显示 HOB，methodology 必须写这一句，并注明「按 §3.61 缩放、应读作上限」。

**④ 热辐射半径（三档全直读，一格不走缩放）**

- 来源：Fig. 7.42（p.291）。它本身就是多当量曲线族，15 / 100 / 1 Mt 三列都在图上，直接读。
- 纵轴是斜距（mi），横轴是辐照 Q 的对数。曲线族的计算条件：爆高 `200·W^0.4 ft`、能见度 12 mi 的空爆（§7.42 p.290）。斜距按 §12.66 p.563 的说明读作到爆心地面投影的距离（两者在远距离近似相等）。
- 阈值：默认 **4.5 cal/cm²（二度烧伤下缘，未遮挡浅肤色）**，表格另给 **10 cal/cm²（三度）** 一列。§12.65 p.563：4.5–6 cal/cm² 时约 18% 暴露人群二度烧伤、其余一度。
- **曲线标号无法直读，这件事必须写在 methodology 里，不能假装是读出来的**：Fig. 7.42 是扫描件，没有文字层，等值线旁边的数字标号我用程序读不出来。标定依据是手册自己的两句独立陈述——§12.66 p.563（1 Mt 时 4.5–6 cal/cm² 落在 9–10 mi）+ §7.43 p.290（1 Mt 时 8 cal/cm² 约 7 mi）——由此确定自外向内为 4.5 / 6 / 8 / 10 / 15 / 25 cal/cm²。三条锚点复现偏差 +3.6% / −3.9% / +5.0%。
- **不做地爆热辐射（已裁决）**：Fig. 7.42 是空爆曲线，地爆热辐射在手册里另走一套（§7.41 p.290）。地爆选项只给超压和火球，**页面上要明写这一条**，不能让用户以为漏算了。

""",
    "§2.2 ②③④ 重写",
)

# ---------------------------------------------------------------- 6. §2.3 JSON 示例
resub(
    r'  "entries": \[.*?\n  \]',
    """  "entries": [
    {
      "id": "overpressure_5psi.air.1000",
      "effect": "overpressure_5psi",              // fireball | overpressure_5psi | overpressure_1psi | thermal_2nd | thermal_3rd
      "label": "5 psi overpressure radius",
      "yield_kt": 1000,
      "burst": "air",                              // air | ground
      "radius_m": 6935, "radius_km": 6.93, "radius_ft": 22753,
      "hob_ft": 10174, "hob_m": 3101,              // 空爆为该等压线峰值爆高；地爆为 0
      "value_type": "scaled_curve_read",           // formula | curve_read | scaled_curve_read
      "citation": { "chapter": 3, "section": "§3.73 / §3.61", "figure": "3.73c", "page": 115 },
      "readout": "interpolated between 4 and 6 psi contours, at 2275 ft (1 kt, peak of each isobar) …",
      "conversion": "2275 ft × 1000^(1/3) = 22753 ft; × 0.3048 = 6935 m = 6.93 km",
      "raw_reading_cn": "…（中文原始读数，含像素坐标）",
      "read_error": "±5%",
      "read_by": "programmatic chart digitization (ring)",
      "checked_by": null,
      "note": "5 psi is NOT one of the contours printed on Fig. 3.73c …",
      "hob_note": null,
      "scaled": true,
      "scaled_label": "scaled from the 1 kt curve (§3.61, p.101)",
      "scaling": { "law": "cube_root", "formula": "d = d_1kt · W^(1/3)", "pages": [101, 102, 110] },
      "base": { "yield_kt": 1, "radius_ft": 2275.3, "hob_ft": 1017.4, "figure": "3.73c", "page": 115,
                "interpolated": true, "between_psi": [4, 6], "interp_fraction": 0.5503,
                "px": { "4psi": [642.3, 914.9], "6psi": [522.5, 946.0] } }
    }
  ]""",
    "§2.3 条目字段",
)

rep(
    "- 数值单调性检查：同 effect 下半径随当量必须单调递增，不满足直接报错（能抓住 90% 的手抖读数错误）。",
    "- 数值单调性检查：同 effect 下半径随当量必须单调递增，不满足直接报错（能抓住 90% 的手抖读数错误）。\n"
    "- `effect == \"overpressure_5psi\"` 的每条，`readout` 必须含 `interpolated between 4 and 6 psi contours, at`，否则构建失败（防止某一行漏标注）。\n"
    "- `value_type == \"curve_read\"`（热辐射）的每条，`scaled` 必须缺失或为 false——直读的值不允许带缩放标记。\n"
    "- `burst == \"ground\"` 且 `effect` 属于热辐射的条目，一律不允许存在（地爆不给热辐射，见 2.2 ④）。\n"
    "- 页面渲染时，`read_error` 与 `checked_by` 一起进 `data-*` 属性，便于以后做「已核 / 待核」标记而不改结构。",
    "§2.3 校验规则扩充",
)

# ---------------------------------------------------------------- 7. 新增 §2.8
rep(
    "\n---\n\n## 3. 技术架构",
    """
### 2.8 阶段 0 结果（已交付、已抽检通过）

24 条数据（12 条空爆 + 12 条地爆），`src/data/effects.json` + `data-ledger.csv`；`verify_data.py` **354 项检查全过**。

**空爆（默认口径，半径 km）**

| 效应 | 15 kt | 100 kt | 1 Mt | 出处 | 读数方式 |
|---|---|---|---|---|---|
| 火球（breakaway） | 0.10 | 0.21 | 0.53 | 式 (2.127.1) p.70 | 手册公式 |
| 5 psi | 1.71 | 3.22 | 6.93 | Fig. 3.73c p.115 | 读峰值 + 立方根缩放（5 psi 为 4/6 插值） |
| 1 psi | 5.28 | 9.93 | 21.40 | Fig. 3.73c p.115 | 读峰值 + 立方根缩放 |
| 热辐射 二度 4.5 cal/cm² | 3.37 | 6.99 | 16.68 | Fig. 7.42 p.291 | **直读，不缩放** |
| 热辐射 三度 10 cal/cm² | 1.77 | 4.02 | 10.35 | Fig. 7.42 p.291 | **直读，不缩放** |

**地爆（contact surface burst，只给火球与超压）**

| 效应 | 15 kt | 100 kt | 1 Mt |
|---|---|---|---|
| 火球（式 2.127.2，p.71） | 0.13 | 0.28 | 0.70 |
| 5 psi | 1.02 | 1.93 | 4.15 |
| 1 psi | 2.88 | 5.42 | 11.67 |

**空爆爆高（ft，页面必须显示）**：5 psi 2,509 / 4,723 / 10,174；1 psi 3,884 / 7,311 / 15,750；热辐射 591 / 1,262 / 3,170（Fig. 7.42 的 `200·W^0.4` 计算爆高）。火球是公式值，不消耗爆高。

**四条交叉校验**：p.114 算例 4 psi 2,600 ft（+0.7%）｜§12.66 二度 9–10 mi（+3.6% / −3.9%）｜§7.43 的 8 cal 约 7 mi（+5.0%）。

---

## 3. 技术架构""",
    "新增 §2.8 阶段 0 结果",
)

# ---------------------------------------------------------------- 8. §3.2 降级层 + 手势
rep(
    "- `map` 初始化失败 / style 加载超时 4s / 连续瓦片错误 → `basemap` 淡出为 `#0B0E13`，`rings` 照常，右下角出现一行 `Basemap unavailable — radii are still to scale.`。**不会出现永久的 Loading map。**\n"
    "- 可选增强（等你批）：降级时改画 Natural Earth 110m 陆地轮廓（公有领域，~120 KB GeoJSON），比纯色更有信息量。默认按你的规格走纯色。",
    "- `map` 初始化失败 / style 加载超时 4s / 连续瓦片错误 → `basemap` 换成降级层，`rings` 照常，右下角一行 `Basemap unavailable — radii are still to scale.`。**不会出现永久的 Loading map。**\n"
    "- **降级层（D5 已裁决）**：自托管 Natural Earth 110m 陆地轮廓（公有领域，约 120 KB，随站打包 `public/geo/ne110m-land.json`），瓦片挂掉时画「轮廓 + 半径圈 + 一行说明」。**不用任何第三方的免费额度，不引入第二份会变的条款**——这条比省 4 小时重要。\n"
    "- **手势约束（你定的）**：`dragRotate: false`、`touchPitch: false`、`pitchWithRotate: false`、`maxPitch: 0`。半径圈是我们自己按墨卡托算的多边形，用户一转一倾就和底图错位；2D 产品不需要这两个手势。键盘也不给旋转。",
    "§3.2 降级层与手势",
)

rep(
    "  primary: { style: 'https://tiles.openfreemap.org/styles/fiord', slug: 'fiord' },\n"
    "  // 备用（v1 先留空，见 8-D5）\n"
    "  fallback: null,",
    "  primary: { style: 'https://tiles.openfreemap.org/styles/fiord', slug: 'fiord' },\n"
    "  // 备用（D5：自托管 Natural Earth 110m 轮廓，公有领域，随站打包）\n"
    "  fallback: { kind: 'natural-earth-110m', path: '/geo/ne110m-land.json', bytes: 120_000 },\n"
    "  interactions: { dragRotate: false, touchPitch: false, pitchWithRotate: false, maxPitch: 0 },",
    "§3.3 底图配置",
)

rep(
    "- 禁止清单照你写的执行：不用 Esri World Imagery、Google、Mapbox、任何 API key 服务。备用源我不推荐用别家免费额度（条款都可能变），见 D5。",
    "- 禁止清单照你写的执行：不用 Esri World Imagery、Google、Mapbox、任何 API key 服务。备用源**不是**别家的免费额度，是自托管的 Natural Earth 110m 轮廓（D5）。",
    "§3.3 禁止清单",
)

# ---------------------------------------------------------------- 9. §4.2 上线标准
resub(
    r"### 4\.2 `/blast-radius/`.*?(?=\n### 4\.3)",
    """### 4.2 `/blast-radius/` — `nuclear bomb blast radius`（US 8,100/月）

- Title: `Nuclear Bomb Blast Radius, 15 kt to 1 Mt — Table With Sources`
- H1: `Every nuclear bomb blast radius in this table points to a page in the 1977 manual`
- 首屏即表格。行 = 火球 / 5 psi / 1 psi / 热辐射（二度、三度各一行）；列 = 15 / 100 / 1000 kt（阶段二扩到 12 档）。
- **每个格子里必须有四行**（这是溯源的最小单位，不能再少）：
  1. 数值 + 单位（km，2 位小数）；
  2. 该格实际用的爆高 `at 2,509 ft HOB` / `contact burst` / `formula — no burst height input`；
  3. 出处 `Ch. 3 · Fig. 3.73c · p. 115`（公式类写 `Eq. (2.127.1) · p. 70`）；
  4. 口径标签：`scaled from the 1 kt curve (§3.61, p.101)` / `interpolated between 4 and 6 psi contours` / `read directly, not scaled`。
- 表下第一段是「1 Mt 的爆高超出 5,000 ft 匀质大气假设」的说明，和表格同屏，不折叠、不放进 tooltip。
- 地爆表单独一张，明确写「contact surface burst：超压与火球；热辐射不在此口径内给出」。
- 纯 HTML 表，`<table>` 语义化，JS off 完整可读——**这一页是本站的第一个 JS 依赖为零的页面**。
- 表下给读数方式块（峰值读法 / 立方根缩放原文 / 5 psi 插值 / Fig. 7.42 标定依据），并链 `/methodology/`。

**上线标准（四条硬门，任一不达标不上线）**

| # | 门 | 判定方式 |
|---|---|---|
| G-a | 关 JS 能读完整表 | 构建后 HTML 里 15 个主数 + 24 条出处全部是静态文本，页面无 `<script>` |
| G-b | 每格带印刷页码 | 构建后断言 `p. 115` / `p. 291` / `p. 70` / `p. 71` 出现次数与格子数一致 |
| G-c | 5 psi 每行带插值标注 | 断言 `interpolated between 4 and 6 psi contours` 出现 6 次（空爆 3 + 地爆 3） |
| G-d | 1 Mt 带爆高边界说明 | 断言页面含 `5,000 ft` 与 `10,174 ft`，且两者在同一段内 |

- 工作量：**4 h**（不含数据）
""",
    "§4.2 上线标准",
)

# ---------------------------------------------------------------- 10. §6 顺序
resub(
    r"## 6\. 开发顺序与工作量（总 70–85 h）.*?(?=\n---\n\n## 7\.)",
    """## 6. 开发顺序与工作量（总 ~104 h）

**顺序按你的调整改过：`/blast-radius/` 提前到地图之前。** 理由不再是「先有数据后有页面」，而是「这一页只要有真数字真表格就能接 `nuclear bomb blast radius` 这个月搜 8,100 的词，不需要地图」。

| 阶段 | 内容 | 工时 | 出口标准（不达标不进入下一阶段） |
|---|---|---|---|
| **0 数据层** ✅ | 曲线读数、`effects.json`、`verify_data.py`、`data-ledger.csv` | 14 h | **已通过 2026-11-11**：24 条数据、354 项自检全过、抽检 5 条对上原图 |
| **1 骨架 + `/blast-radius/`** | Astro 工程、`effects.ts`、Base 布局、`/blast-radius/`、`/methodology/` 首版 | 12 h | 4.2 的四条硬门全绿 |
| **2 首页 + 查表** | ResultPanel SSR、首页默认值（New York · 100 kt）、URL 状态 | 8 h | JS off 首页有完整结果；切当量 <300 ms |
| **3 地图 + 视觉** | MapLibre、Canvas 覆盖层、测地圆、Natural Earth 降级、移动端抽屉 | 16 h | 断网/挂瓦片时轮廓与圈仍在且不空白；4G 首屏 2 s 内 |
| **4 `/nuclear-bomb-map/`** | 世界视角 + 导航接入 | 4 h | 导航可点达；分享链接可还原 |
| **5 城市页 ×20** | 模板 + 生成门槛 + 20 篇文案 + og 图 | 10 h | 20 页全过门槛；每页 3 条内链 |
| **6 城市页扩到 80 页** | 20 → 60–70 城 | 16 h | 首月 80 页在线，每页都过生成门槛 |
| **7 内容与法务** | nuclear-winter 2500 词、methodology 定稿、about、privacy | 18 h | 引用可点、无自算数字 |
| **8 收口** | sitemap/robots/canonical 断言、Lighthouse、OG 全量核查 | 6 h | 第 5 节清单全绿 |
| — | **阶段二**（12 当量页，等你确认） | 8 h | 复用同套数据与模板 |

总量从 v1.0 的 70–85 h 上调到 **~104 h**，多出来的两块是：城市页扩到 80 页（+16 h）、骨架与 `/blast-radius/` 合并成一段（+2 h，因为这一页现在要按上线标准做，不是草稿）。

### 6.1 首月 80 页怎么堆（你定的第 3 条）

80 页靠**加城市**，不靠加页面类型。原因：新页面类型的边际成本里有「新数据口径 + 新文案结构 + 新 schema」三样，每加一种都要重走一遍方法论；城市页的边际成本只有「120–160 词地名文案 + 一次人口预算」，而且数据和模板完全复用。

- 阶段 5 先把 20 城跑通，确认模板与生成门槛（缺值 / 缺人口 / 文案 <100 词 → 该城不生成）。
- 阶段 6 按 20 城一批扩到 60–70 城，每批过一次门槛检查。
- **不一次铺满**：先看前 20 城的收录信号，再决定要不要继续往上堆。这跟你定的站群准则一致——信号顺序是收录 → 外链 → 页量 → 排名，页量排在收录后面，不该先堆。
""",
    "§6 开发顺序 + 6.1 页数节奏",
)

# ---------------------------------------------------------------- 11. 风险表三行
rep(
    "| R3 | 手册只有 1 kt 曲线 → 1000 kt 的缩放外推距离原文「megaton range」边界 | §3.61 | 1 Mt 恰在边界内，但这属于手册自己承认的范围上限 | 1000 kt 保留，methodology 明写「at the upper end of the manual's stated scaling range」；不做 >1 Mt |",
    "| R3 | **1 Mt 的爆高（5 psi 10,174 ft / 1 psi 15,750 ft）超出 §3.73 p.110 的 5,000 ft 匀质大气假设** | 3.73c 缩放 | 该档半径叠加了手册未量化的额外不确定度 | **保留 1 Mt**：结果面板显示 HOB；methodology 写「按 §3.61 缩放、应读作上限」；注明未做 §3.64–3.66 高度修正（省略方向使值偏小）；不做 >1 Mt |",
    "R3 爆高越界",
)

rep(
    "| R6 | Fig. 7.42 未必覆盖 15 kt | thermal 15 kt | 该格缺值 | 缺则用 §7.96 的 D∝W^0.5 缩放并标 `scaled`；再缺则该格不生成、整页不出 |",
    "| R6 | **Fig. 7.42 曲线标号不可直读**（扫描件无文字层） | thermal 全部 6 格 | 阈值与曲线对不上，整列错 | **已处置**：三档全部直读该图，标号由 §12.66 p.563 + §7.43 p.290 两句话反推，三条锚点偏差 +3.6% / −3.9% / +5.0%；methodology 明写标定依据与「无文字层」 |",
    "R6 热辐射标定",
)

rep(
    "| R10 | 备用底图源难找 | 3.3 | 主源挂了只剩纯色 | 见 D5：①纯色降级（合规足够）②自托管 z0–5 PMTiles（R2 免费额度，~30 MB，真独立） |",
    "| R10 | 备用底图源难找 | 3.3 | 主源挂了只剩纯色 | **已解决（D5）**：自托管 Natural Earth 110m 轮廓，公有领域、约 120 KB、随站打包，不依赖任何第三方条款 |",
    "R10 备用底图",
)

# ---------------------------------------------------------------- 12. §8 换成裁决记录
resub(
    r"## 8\. 需要你裁决的 5 件事（其余我按上面默认走）.*?(?=\n---\n\n## 9\.)",
    """## 8. 五个决策点：已裁决（2026-11-11）

| # | 议题 | 裁决 | 落地位置 |
|---|---|---|---|
| D1 | 缩放律（R1） | **接受**。三档全出；每条缩放值带 `scaled from the 1 kt curve (§3.61, p.101)`；`readout` 记 1 kt 基准读数与像素坐标；用 §12.66 做交叉校验 | 2.2 / 2.8 / `effects.json` |
| D2 | 爆高口径（R4） | **读峰值**，不选固定爆高、不拟合最优爆高公式；面板显示 HOB 与 burst type；第二态为地爆，读 HOB = 0 底边；火球空爆 110·W^0.4 / 地爆 145·W^0.4，禁止混搭 | 2.2 ②③ / 4.2 |
| D3 | 热辐射阈值（R5） | **二度（4.5 cal/cm²，未遮挡浅肤色）默认 + 三度（10 cal/cm²）另列**；页面写明肤色与遮蔽假设 | 2.2 ④ / 4.2 |
| D4 | 城市人口口径（R8） | **城市中心半径 10 km 内 WorldPop 人口**，不用行政边界；效应圈内人口另算，两个数不合并；页面明写半径、年份、版本 | 2.5 / 4.4 |
| D5 | 备用底图 | **自托管 Natural Earth 110m 公有领域轮廓**（约 120 KB，随站打包）；不用任何第三方免费额度；瓦片挂掉画轮廓 + 半径圈 + 一行说明 | 3.2 / 3.3 |

三条调整同样已落地：`/blast-radius/` 提前到地图之前（6）；关掉地图旋转与俯仰（3.2）；首月 80 页靠加城市（6.1）；全站禁 demo 类字样 + 免责恰一行（1）。

**仍待你后续定的两件**：阶段二 12 当量页做不做（+8 h）；`/nuclear-bomb-map/` 与首页要不要合并（当前分开，因为两个词各自有量，合并会牺牲其中一个的标题口径）。
""",
    "§8 裁决记录",
)

# ---------------------------------------------------------------- 13. 合规基线
rep(
    "- 一行脚注（每页最多一行，页底）固定文案候选：\n"
    "  `Numbers are transcribed from The Effects of Nuclear Weapons (1977), a public-domain U.S. government publication. Not a prediction for any specific event.`\n"
    "- 全站禁用词：education demo / prototype / demo / simulation model / our estimate。",
    "- **免责位置硬约束（你定的）**：每页**恰一行**脚注，放页面最底部。不做首屏免责条、不做副标题、不做弹层。文案固定：\n"
    "  `Numbers are transcribed from The Effects of Nuclear Weapons (1977), a public-domain U.S. government publication. Not a prediction for any specific event.`\n"
    "- **全站禁用词（构建期断言，命中即构建失败）**：`education demo` / `prototype` / `demo` / `simulation model` / `our estimate`。注意 `demolish`、`demographic`、`demolition` 都含 `demo` 子串，断言必须用词边界匹配，不能简单 `includes`——这条我写进校验脚本里，不靠人记。",
    "§1 免责与禁用词",
)

# ---------------------------------------------------------------- 14. §5 清单补两条
rep(
    "- [ ] 构建断言：无 `lorem`、无 `TODO`、无 `demo`、无 `undefined`",
    "- [ ] 构建断言：无 `lorem`、无 `TODO`、无 `undefined`；禁词按词边界匹配（`\\bdemo\\b` 等）\n"
    "- [ ] 构建断言：`/blast-radius/` 的四条硬门（4.2）逐条过",
    "§5 构建断言",
)

# ---------------------------------------------------------------- 15. §10 首批 12 行改成已完成
rep(
    "首批必须填满的 12 行：\n"
    "\n"
    "```\n"
    "blast.fireball.15kt / .100kt / .1000kt            → §2.127 式(2.127.1) p.70（公式）\n"
    "blast.5psi.15kt / .100kt / .1000kt                → Fig.3.73c p.115 读 1kt 基准 → §3.61 p.101 缩放\n"
    "blast.1psi.15kt / .100kt / .1000kt                → 同上\n"
    "thermal.2nd.15kt / .100kt / .1000kt               → Fig.7.42 p.291 读（缺档则 §7.96 缩放）\n"
    "```",
    "~~首批必须填满的 12 行~~ → **阶段 0 已完成，实际落了 24 行**（空爆 12 + 地爆 12），见 `data-ledger.csv`。实际取值路径与 v1.0 的差异：\n"
    "\n"
    "```\n"
    "fireball.air.15/100/1000        → 式(2.127.1) p.70（公式，非读图）\n"
    "fireball.ground.15/100/1000     → 式(2.127.2) p.71（公式，地爆口径）\n"
    "overpressure_5psi.air.*         → Fig.3.73c p.115 读每条等压线峰值 → 4/6 psi 插值 → §3.61 式(3.61.2) p.101 缩放\n"
    "overpressure_5psi.ground.*      → Fig.3.73c p.115 读 HOB=0 底边 → 缩放\n"
    "overpressure_1psi.air.*         → Fig.3.73c p.115 读峰值 → 缩放\n"
    "overpressure_1psi.ground.*      → Fig.3.73c p.115 读底边 → 缩放\n"
    "thermal_2nd.air.*               → Fig.7.42 p.291 三档直读（4.5 cal/cm²）\n"
    "thermal_3rd.air.*               → Fig.7.42 p.291 三档直读（10 cal/cm²）\n"
    "```",
    "§10 首批 12 行",
)

P.write_text(text, encoding="utf-8")
print("\n".join(log))
print(f"\n字数：{orig_len} → {len(text)}（{len(text) - orig_len:+d}）")
