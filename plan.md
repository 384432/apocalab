# apocalab.com — v1 实施计划

> 技术负责人 / 全栈工程师：灵
> 版本：**v1.3（2026-11-11 修订）**。阶段 0 数据层已通过抽检，阶段 1 骨架与 `/blast-radius/` 已上线，阶段 2 首页与查表已上线；第 8 节 5 个决策点已全部裁决，正文按裁决结果改过。
> 本文所有页码、图号、公式，均来自我本机对手册 PDF 的抽取核对（见 2.1），不是从二手网页抄的。

**v1.3 相对 v1.2 改了什么**（只列会改变行为的）：

1. **og:image 升级为硬约束**：必须是构建期生成的 **PNG 1200×630**。SVG 一律不接受——分享卡片在微信、Slack、X、iMessage 里对 SVG 的支持都不一致，一张"在浏览器里能看"的 SVG 等于一张在群里不显示的卡片。这条写进 §3.5 并加进 §5 的构建断言。
2. **标题不许承诺页面上没有的东西**：人口层在阶段 4 才上线，首页 title 在它上线前不出现 `population`。上线后按 §4.1 原文恢复。

**v1.2 相对 v1.1 改了什么**（只列会改变行为的）：

1. **页数口径回滚**：城市页固定 **20 个**（就是已列的那 20 城）。80 是**首月总页量**，不是城市页数量。
2. **80 页的构成写实**：核心页 8 + 城市页 20 + 武器/历史弹页 12 + 约 40 个同赛道有独立搜索量的灾害与查询页（清单待定）。
3. **工时回到 70–85 h**：不是「压缩」，是把本来就不该有的工时去掉。
4. **城市页定位**：不负责流量，负责覆盖与内链；验收标准不变，也不为它追加任何工时。

**v1.1 相对 v1.0 改了什么**（只列会改变行为的）：

1. **D2 落地**：爆高口径从「固定 1,000 ft」改成「读每条等压线在图上的峰值」，每条线带自己的爆高；地爆读 HOB = 0 的图底边；火球空爆 110·W^0.4 / 地爆 145·W^0.4，禁止混搭。
2. **D4 落地**：城市人口统一为「城市中心半径 10 km 内 WorldPop 人口」，不用行政市界；效应圈内人口另算，两个数不合并。
3. **D5 落地**：备用底图改为自托管 Natural Earth 110m 公有领域轮廓，不用任何第三方免费额度。
4. **顺序调整**：`/blast-radius/` 提到地图之前，阶段 1 直接交一页可上线的静态表。
5. **三条硬约束入正文**：全站禁 demo 类字样；免责每页恰一行、放页底；地图禁旋转与俯仰。
6. **页数口径**：城市页固定 20 个；首月 80 页由核心页 8 + 城市页 20 + 武器/历史弹页 12 + 约 40 个有独立搜索量的灾害/查询页组成，靠**页面类型**补齐，不靠加城市。
7. **修正 v1.0 的两处出处错误**：缩放律是式 (3.61.2) p.101（不是 §3.75 p.108）；§12.66 的烧伤句在 p.563。

---

## 0. 先说三句结论

1. **能做，但有一个必须先说清的硬冲突**：手册里 5 psi / 1 psi 只有 **1 kt 一条曲线**。要出 15/100/1000 kt，只有两条路——用手册自己写的立方根缩放律（§3.61、§3.75），或者只做 1 kt 一档。你要三档，就得接受缩放，并接受「缩放值」这个标签。这是全文唯一的实质性问题，第 2.2 节讲透。**D1 已裁决：接受缩放**，每个缩放值都带固定标签。
2. **数据录入是整个 v1 的真实瓶颈**：约 70–85 工时里，**14 小时花在读图上**（对数坐标纸上逐点读数）。代码是次要成本。这也决定了开发顺序：数据层先做，做不出合格数据就不做页面。
3. **四个半径里，只有火球半径能直接引用公式**（§2.127，手册原文给了 90/110/145·W^0.4），另外三个必须从图上读。所以「每格带章/图/页」这件事，页面上是能做到的，但页面上要给的是**图号+页码+读数方式**，不是「表 3.xx 第 5 行」。

---

## 1. 定位与合规基线（不改动你的定位，只落成可执行约束）

- 站点性质：公开数据的交互式查询与可视化。程序只做查表 + 绘圈。
- 唯一数值来源：《The Effects of Nuclear Weapons》，Glasstone & Dolan 编，第 3 版，1977，US DoD / ERDA 出版，公有领域。DOI `10.2172/6852629`，镜像 `fourmilab.ch/etexts/www/effects/`。
- 全站英文，目标美国。写作口径：陈述手册怎么说，不替手册下结论；不出现「would die」「will be destroyed」这类因果断言，使用「within this ring, the manual's damage criteria place…」的引述式表达。
- **免责位置硬约束（你定的）**：每页**恰一行**脚注，放页面最底部。不做首屏免责条、不做副标题、不做弹层。文案固定：
  `Numbers are transcribed from The Effects of Nuclear Weapons (1977), a public-domain U.S. government publication. Not a prediction for any specific event.`
- **全站禁用词（构建期断言，命中即构建失败）**：`education demo` / `prototype` / `demo` / `simulation model` / `our estimate`。注意 `demolish`、`demographic`、`demolition` 都含 `demo` 子串，断言必须用词边界匹配，不能简单 `includes`——这条我写进校验脚本里，不靠人记。

---

## 2. 数据层（最重要的一节）

### 2.1 手册里到底有什么（我实测过，不是推测）

我把第 2、3、7、12 章 PDF 和整本扫描件下到本地，逐页核对图表标题与印刷页码。**两套偏移量不要混用**：整本 `6852629.pdf` 里第 3 章 = 印刷页 + 9；分章 `eonw_3.pdf` 里 = 印刷页 + 79；ch7 = +275，ch2 = +25。下文写的页码一律是**印刷页**。结论如下：

| 用途 | 出处 | 印刷页 | 状态 |
|---|---|---|---|
| 火球半径（热极小值） | `R = 90 W^0.4`（R 英尺，W 千吨），§2.127 | 70 | **已核** |
| 火球半径（breakaway，空中爆炸） | 式 (2.127.1) `R = 110 W^0.4` | 70 | **已核** |
| 火球半径（接触地面爆炸） | 式 (2.127.2) `R = 145 W^0.4` | 71 | **已核** |
| 火球最大半径 ≈ 2 × breakaway | §2.129 | 71 | **已核** |
| 局部落尘上限爆高 `H = 180 W^0.4` ft | 式 (2.128.1) | 71 | **已核** |
| 立方根缩放律 `D/D₁ = (W/W₁)^(1/3)` | 式 (3.61.1)，§3.61 | 101 | **已核** |
| 地面距离按同一立方根律缩放 `D/D₁ = (W/W₁)^(1/3)` | 式 (3.61.2)，§3.61；§3.62 重述 | 101 / 102 | **已核**（v1.0 误记成 §3.75 p.108，已修正） |
| 「取爆高为零」即地爆 | §3.64 | 106 | **已核**（原文 “taking the height of burst … to be zero”） |
| 对 Fig. 3.73a–c 的缩放重述 | §3.73 | 110 | **已核** |
| 1 kt 自由空气爆炸：超压 vs 距离 | Fig. 3.72 | 109 | 已核（v1 未使用） |
| 1 kt 空中爆炸（高压段） | Fig. 3.73a | 111 | 未使用（若出现 10 psi 以上的数，必须注明取自本图） |
| 同上（中压段） | Fig. 3.73b | 113 | 未使用（同上） |
| **同上（低压段，含 1 / 2 / 4 / 6 / 8 / 10 psi）** | **Fig. 3.73c** | **115** | **已核 + 阶段 0 已数字化**（最关键的一张；**没有 5 psi 这条线**） |
| 「最优爆高」概念：使某超压地面距离最大的爆高 | §3.73 | 106 | **已核** |
| 热辐射：给定 Q 的距离曲线（多当量族） | Fig. 7.42 | 291 | **已核** |
| 热分配系数 f（空中爆炸，按当量） | Table 7.88 | 313 | 已核表头 |
| 有效热分配（地面爆炸，接触爆炸 f=0.18） | Table 7.101 | 319 | **已核** |
| 大气透过率 T（12 英里能见度） | Fig. 7.98 | 316–317 | 已核 |
| 皮肤烧伤所需辐照（按肤色/烧伤度数） | Fig. 12.64 | 564 | 已核（图为曲线，读数） |
| 1 Mt 时 4.5–6 cal/cm² 对应二度烧伤为主，斜距 9–10 mi | §12.66 | **563** | **已核**（v1.0 写 562 有误：§12.63 从 562 起，这句话在 563） |
| 1 Mt 时 8 cal/cm² 约 7 mi | §7.43 | 290 | **已核**（第二条标定锚点） |

**关键发现（决定整个数据方案）**：手册没有「按当量列半径」的表。超压只有 1 kt 的曲线族（Fig. 3.72/3.73a-c/3.74a-c），其他当量靠 §3.61 的立方根缩放推出去。热辐射反而好一些，Fig. 7.42 本身就是多当量曲线族。

### 2.2 四个半径的取数路径（逐条，含冲突说明）

**① 火球半径 fireball**
- 来源：式 (2.127.1) / (2.127.2)，p.70–71。
- 做法：构建期按当量算好写进 JSON。**这是全站唯一「用公式而不是读图」的数**，但公式是手册原文给的、不涉及我们任何拟合。
- 显示口径：默认给 **breakaway 半径**（空中爆炸），因为它是「可见火球最大时的半径」，与云团示意视觉最不易混淆；面板里小字注明 `Eq. (2.127.1), p.70`。
- 替代方案（若你要求绝对零计算）：只能给 1 kt 的值，或去读 Fig. 2.121 上 20 kt 一条曲线然后靠缩放推到别的当量——反而更绕且误差更大。不建议。

**② 5 psi / ③ 1 psi 半径（已按 D2 落地：读峰值，不选固定爆高）**

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


### 2.3 数据文件设计

`src/data/effects.json`（构建期生成、入库、可 diff）：

```jsonc
{
  "manual": {
    "title": "The Effects of Nuclear Weapons",
    "edition": "3rd", "year": 1977,
    "publisher": ["US Department of Defense", "ERDA"],
    "doi": "10.2172/6852629",
    "mirror": "https://www.fourmilab.ch/etexts/www/effects/",
    "public_domain": true
  },
  "entries": [
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
  ]
}
```

约束（由 `scripts/verify_data.py` 在构建前强制）：
- `value_type != "formula"` 的条目，`citation.page` 与 `citation.figure` 必须非空，否则构建失败。
- `value_type == "scaled_curve_read"` 的条目必须同时有 `base.*` 与 `scaling.*`。
- 同一 `(effect, yield_kt, burst)` 只允许一条。
- 所有 `checked_by` 为空的条目，页面渲染时在数字旁输出一个 `*`，并链到 methodology 的「已核 / 待核」清单——**你的抽查状态直接进页面**，不是写在我脑子里。
- 数值单调性检查：同 effect 下半径随当量必须单调递增，不满足直接报错（能抓住 90% 的手抖读数错误）。
- `effect == "overpressure_5psi"` 的每条，`readout` 必须含 `interpolated between 4 and 6 psi contours, at`，否则构建失败（防止某一行漏标注）。
- `value_type == "curve_read"`（热辐射）的每条，`scaled` 必须缺失或为 false——直读的值不允许带缩放标记。
- `burst == "ground"` 且 `effect` 属于热辐射的条目，一律不允许存在（地爆不给热辐射，见 2.2 ④）。
- 页面渲染时，`read_error` 与 `checked_by` 一起进 `data-*` 属性，便于以后做「已核 / 待核」标记而不改结构。

其他数据文件：
- `src/data/cities.json`：20 城 slug / 名称 / 经纬度（GeoNames geonameid）/ 城市文案里要用的真实地名数组 / 人口数（各半径内）。
- `src/data/fallout-cases.json`：核试验历史案例（名称、日期、当量、试验场、公开结论、出处）。
- `src/data/copy/*.md`：页面文案与城市文案，与数据分离，方便你直接改词。

### 2.4 溯源与抽查机制（你要人工对原文，我把它做成可操作的）

1. 每条数据带 `citation{chapter, section, figure, page}`，页面显示形如 `Ch. 3 · Fig. 3.73c · p. 115`，hover 显示完整引用串。
2. 构建期额外产出 `dist/data-ledger.csv`（不入站、只给你）：`id, 值, 单位, 图号, 页码, 读数方式, 录入人, 抽查状态`。你拿这张表对着 PDF 抽查，改 `checked_by` 即可。
3. 每条数据附一个可选 `readout` 字段：记录我在图上读到的坐标（例如「爆高 2,000 ft 水平线 × 5 psi 曲线，横向 3,1xx ft」），便于你复现我的读数过程而不是只看结果。
4. `scripts/verify_data.py` + 手工抽查，两道关。你抽查不过的，我重读，不解释。

### 2.5 人口数据

- 源：**WorldPop Global2，1 km，R2025A v1，年份 2020，constrained（UN-adjusted）**，GeoTIFF，30 arc-second，WGS84，单位 people/pixel。许可 CC BY 4.0（可商用，需署名）。
  选 UN-adjusted 的理由：20 个城市跨 10 个国家，各国普查口径不一致，用联合国校正后的国家总量更可比。这条会写进 methodology，并可一键切换成非校正版（脚本参数）。
- 分辨率与口径：1 km 格网，统计的是**夜间居住人口分布**，非实时人流、非伤亡。页面固定用这句：`Resident population, 1 km grid, WorldPop 2020. Not footfall, not casualties.`
- 「范围内人口」算法：格网像元**中心点**落入圆内即计入，累加 people/pixel。不用面积加权（加权会在 1 km 格子上制造并不存在的精度）。这个选择写进 methodology，并注明它是「离散近似，边缘 ±一圈」。
- 预处理（`scripts/build_population.py`）：
  1. 下载 20 个城市所在的全球 1 km 分幅（WorldPop 按国家/分幅发布，脚本按 bbox 取）；
  2. 裁 250 km × 250 km 的方形窗口；
  3. 转成 `uint16` 小端二进制 + 一个 `meta.json`（bbox、像元数、缩放系数、单位）；
  4. 每城一个文件 `public/data/pop/<slug>.bin`，约 250–500 KB，gzip 后更小；
  5. 同时预算每个城市 × 4 个半径的人口和，写进 `cities.json`（保证城市页和首屏无需任何下载即可显示人口）。
- 任意点选点：若点落在某城 250 km 窗口内，**按需**拉该城 `.bin`（lazy，一次，缓存），在 Canvas/JS 里环求和，<10 ms。窗口外 → 人口行显示 `Population data covers the 20 preset metros in this edition` 并给「跳到最近的城市」按钮。**绝不外推、绝不显示 0 冒充**。
- 这个「窗口 + lazy」是可控成本下的最优解；全球 1 km 栅格要 30 MB+，与 2 秒首屏冲突。

### 2.6 地名与搜索

- GeoNames `cities15000.zip`（约 25,000 条，含人口、坐标、国家、时区），CC BY 4.0。构建期过滤成 `public/data/cities-search.json`（只留 name / asciiname / country / lat / lon / population，约 1.2 MB，gzip 后 ~350 KB，按首字母分 4 个分片按需加载）。
- 搜索全离线：前缀 + 模糊匹配，不请求任何地理编码 API。选中后落 URL 参数。
- 只收录 20 个城市页；搜索命中的其他城市走首页地图（可正常出圈，但无静态页）。这符合「凑不出三项就不生成页面」的原则。

### 2.7 落尘：写清楚做什么、不做什么

- **不做**：任何地点级沉降足迹、剂量率、风向下的污染区预测。理由写入 methodology：手册的沉降预测依赖实测气象、地形、降水，且 §2.128 只给「本地落尘上限爆高」这一个判据，推不出单点足迹。
- **做 ①**：选点后按 8 个方位显示扇形**示意**（Canvas，半透明填充，无距离刻度、无剂量标尺，角落固定 `Schematic only — not a prediction. No scale.`）。扇形的张角写成配置项，不假装是气象数据。
- **做 ②**：核试验历史案例时间轴（`/methodology/` 下的区块，或独立锚点）。首批 6 条：Trinity、Hiroshima、Nagasaki、Castle Bravo、Tsar Bomba、Semipalatinsk 首次试验。每条只有：日期、当量、地点、一句公开记载的事实、出处链接。不做伤亡渲染。
- **交叉引用**：§2.128 式 (2.128.1)（p.71）给出「本地落尘显著的下限爆高」，这个可以在 methodology 里作为唯一可引用的落尘数字出现。

### 2.8 阶段 0 结果（已交付、已抽检通过）

24 条数据（空爆 15 条 = 5 个效应 × 3 档，地爆 9 条 = 3 个效应 × 3 档），`src/data/effects.json` + `data-ledger.csv`；`verify_data.py` **354 项检查全过**。

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

## 3. 技术架构

### 3.1 栈与目录

Astro 5 + TypeScript，`output: 'static'`。岛屿只用一个（地图），默认零 JS 也能读全站。

```
src/
  pages/
    index.astro
    blast-radius/index.astro
    nuclear-bomb-map/index.astro
    nuclear-winter/index.astro
    methodology/index.astro
    about/index.astro
    privacy/index.astro
    [city]/index.astro          ← getStaticPaths 读 cities.json
  components/   ResultPanel / EffectTable / MapShell / Citation / SiteNav / Footnote
  islands/      MapExplorer.ts        ← 唯一 hydrate 的组件
  lib/          effects.ts / projection.ts / urlState.ts / population.ts / citation.ts
  data/         effects.json / cities.json / fallout-cases.json / copy/
scripts/        build_population.py / build_og.py / verify_data.py / build_ledger.py
public/data/    cities-search-*.json / pop/<slug>.bin
```

### 3.2 地图与半径绘制（关键决策）

**半径圈不由 MapLibre 的 layer 画，由我们自己的 Canvas 覆盖层画。**

理由：你的降级要求是「瓦片挂了圈还在」。如果圈是 MapLibre layer，map 初始化失败或 style 报错时圈会一起没。做法：

- `<div id="basemap">` 交给 MapLibre，只负责底图；`<canvas id="rings">` 绝对定位叠在上面，由 `projection.ts` 自己算墨卡托投影，监听 `map.on('move')` 重绘。
- 圈用真实测地圆（按大圆半径算，投影后是多边形，不是屏幕圆），所以「按真实比例」成立。
- 数字标注跟着圈走，字体用系统栈（不加载 web font）。
- `map` 初始化失败 / style 加载超时 4s / 连续瓦片错误 → `basemap` 换成降级层，`rings` 照常，右下角一行 `Basemap unavailable — radii are still to scale.`。**不会出现永久的 Loading map。**
- **降级层（D5 已裁决）**：自托管 Natural Earth 110m 陆地轮廓（公有领域，约 120 KB，随站打包 `public/geo/ne110m-land.json`），瓦片挂掉时画「轮廓 + 半径圈 + 一行说明」。**不用任何第三方的免费额度，不引入第二份会变的条款**——这条比省 4 小时重要。
- **手势约束（你定的）**：`dragRotate: false`、`touchPitch: false`、`pitchWithRotate: false`、`maxPitch: 0`。半径圈是我们自己按墨卡托算的多边形，用户一转一倾就和底图错位；2D 产品不需要这两个手势。键盘也不给旋转。

### 3.3 底图配置（换源只改一处）

`src/lib/basemap.ts` 单一配置文件：

```ts
export const BASEMAP = {
  primary: { style: 'https://tiles.openfreemap.org/styles/fiord', slug: 'fiord' },
  // 备用（D5：自托管 Natural Earth 110m 轮廓，公有领域，随站打包）
  fallback: { kind: 'natural-earth-110m', path: '/geo/ne110m-land.json', bytes: 120_000 },
  interactions: { dragRotate: false, touchPitch: false, pitchWithRotate: false, maxPitch: 0 },
  void: '#0B0E13',
  attribution: 'OpenFreeMap © OpenMapTiles · Data from OpenStreetMap',
  styleTimeoutMs: 4000,
};
```
- 主源核实结果（官网原文）：公共实例**完全免费、不限请求数、无需 API key、无 cookie**，FAQ 明确 `Is commercial usage allowed? Yes.`，无 SLA（官网明说）。署名由 MapLibre 自动挂上，但我们仍手写一份常驻 footer，防止客户端差异。
- 风格选 **Fiord**（深色、地形感强）；Dark 作为同一源内的第二候选（同源换风格不算备用源）。
- 禁止清单照你写的执行：不用 Esri World Imagery、Google、Mapbox、任何 API key 服务。备用源**不是**别家的免费额度，是自托管的 Natural Earth 110m 轮廓（D5）。

### 3.4 URL 状态

- `/ ?city=new-york&y=100` （预置点，短、可分享、可被搜到）
- `/ ?lat=40.7128&lon=-74.0060&y=100&n=40.7128,-74.0060` （任意点，`n` 存地名用于分享图与标题）
- `/nuclear-bomb-map/?lat=&lon=&y=` 同构。
- 所有状态变更 `replaceState`（不污染历史），复制链接按钮给绝对 URL。
- 首屏无参 → 渲染默认（New York · 100 kt · air），**服务端直出，不靠 JS 补**。

### 3.5 分享图（构建期 PNG，绝不用 SVG）

- `scripts/build_og.py`（Pillow）：深色底 + Natural Earth 110m 陆地图层（灰蓝）+ 该点四个半径圈（真实比例）+ 圆心标记 + 左上当量/城市、右下人口、底部固定出处行。
- 输出 1200×630 PNG，每城 1 张（100 kt 口径）+ 首页 + `/nuclear-bomb-map/` + `/blast-radius/` + `/nuclear-winter/`，共约 24 张，全部 `build` 前生成到 `public/og/`。
- `og:title` 与 `<title>` **由同一个 `page` 对象渲染**（不可能不一致，从结构上消灭上一版的 bug）。
- `og:image` 绝对 URL，`og:image:width/height` 显式写出，同时给 `twitter:card=summary_large_image`。
- 构建后加一条断言脚本，以下任一条命中即**构建失败**（不是警告）：
  1. 任一页面 `og:title !== title`；
  2. 任一 `og:image` 以 `.svg` 结尾，或返回的 `content-type` 不是 `image/png`；
  3. 任一 `og:image` 的像素尺寸不是 1200×630（用 Pillow 打开实际校验，不信文件名）；
  4. 任一 `og:image` 不是以 `https://apocalab.com/` 开头的绝对 URL。

**为什么 PNG 是硬约束，不是偏好**：SVG 的分发链路不受我们控制。微信、Slack、X、iMessage 的抓取器对 SVG 的支持互不一致，多数直接不渲染；而它们的缓存一旦存了空图，改回来要等缓存过期。一张 1200×630 的 PNG 是这些抓取器唯一共同支持的格式。所以**分享图在构建期光栅化**，浏览器能力不参与这件事——这与站点其余部分"能用 HTML/CSS 就不上图"的原则不冲突，因为分享卡片根本不经过我们的 CSS。

**同理，也不接受运行时渲染的分享图**（Canvas 截图、`satori` 之类按请求生成）：分享卡片是抓取器拉的，它不执行我们的脚本。图必须在 `astro build` 之前就存在于 `public/og/`。

### 3.6 性能预算（移动端优先）

| 项 | 目标 | 手段 |
|---|---|---|
| 首屏 HTML+TXT | < 60 KB gzip | Astro 静态、内联 critical CSS、无 web font |
| 首屏可见结果 | < 1.2 s | 结果面板是纯 HTML；数字来自内联 JSON |
| 地图可见 | < 2 s（4G） | MapLibre 在 `requestIdleCallback` 后动态 `import()`；不阻塞首屏 |
| 切换当量到出圈 | < 300 ms | 纯查表 + Canvas 重绘，无网络 |
| JS 总量 | 首屏 < 40 KB，地图就绪后 +260 KB | 代码分割；`cities-search` 分片按需 |
| 降级 | 4 s 超时必定落到可用状态 | style 超时 + tile error 计数 |

移动端交互：选点 = 单击（`tap`），当量 = 三个大按钮（不做滑杆，滑杆是阶段二的事）；结果面板为底部抽屉，拇指可达；地图默认 zoom 由半径自动 fit（留 15% 边距）。

---

## 4. 页面清单与逐页规格

> Title 与 H1 都含目标词，且不重复同一句话；description 每页手写。

### 4.1 `/` — 主词 `nuke simulator`
- Title（阶段 2 已上线）: `Nuke Simulator: Blast Radius for Any City, 15 kt to 1 Mt`
- Title（人口层上线后恢复）: `Nuke Simulator: Blast Radius and Population for Any City`
- H1（阶段 2 已上线）: `Pick a city, pick a yield — the rings are drawn to scale from the manual`
- Default state（SSR）: New York, 100 kt, air burst → 4 个半径 + 各半径内人口 + 出处。
- 结构：地图（左/上）+ 结果面板（右/下）+ 三句话解释这是什么 + 4 条内链块（blast-radius / nuclear-bomb-map / methodology / 6 个城市）+ FAQ（8 条，FAQPage JSON-LD）+ 一行脚注。
- JS off：地图区替换为静态结果块 + 「See the full table →」指向 `/blast-radius/`。
- 工作量：**8 h**

### 4.2 `/blast-radius/` — `nuclear bomb blast radius`（US 8,100/月）

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

### 4.3 `/nuclear-bomb-map/` — `nuclear bomb map`（US 2,400/月）
- Title: `Nuclear Bomb Map — Drop a Pin Anywhere and See the Rings`
- H1: `A nuclear bomb map with real scale, not a cartoon`
- 与首页共用岛屿组件，差异在默认视角（世界 zoom 2）与文案侧重「地图」而非「模拟器」。
- 导航一级项，首页与城市页都链过来。
- 工作量：**4 h**

### 4.4 `/[city]/` × 20
- Title 模板（**每页手写，不批量套**）：`Nuclear Blast Radius in New York — 15 kt, 100 kt and 1 Mt`
- H1（各不相同）：`Where the rings land in New York`
- 内容三件套：① 15/100/1000 kt × 4 效应表（同 4.2 规格）；② 各半径内人口；③ 120–160 词真地名文案（Manhattan / Brooklyn / Jersey City / Newark…，来自 GeoNames + OSM 地名，不编）。
- 结构数据：`BreadcrumbList`（Home › Cities › New York）。内链：回首页、回 `/blast-radius/`、上/下各一个城市、`/nuclear-bomb-map/`。
- 20 城：new-york, los-angeles, chicago, houston, san-francisco, washington-dc, miami, seattle, boston, atlanta, london, paris, tokyo, berlin, sydney, toronto, mexico-city, sao-paulo, new-delhi, johannesburg。
- 生成门槛写入脚本：某城若 4 效应 × 3 当量有任一缺值 / 人口缺失 / 文案 < 100 词 → 该城**不生成页面**（符合你的「凑不出三项不要生成」）。
- 工作量：**10 h**（模板 4 h + 20 篇文案 6 h）

### 4.5 `/nuclear-winter/` — `nuclear winter`（US 9,900/月）
- Title: `Nuclear Winter: What the Published Research Actually Says`
- H1: `Nuclear winter, from the 1983 paper to the 2019 model runs`
- 2,500+ 词。结构：定义 → 机制（烟尘进入平流层）→ 关键研究时间线（TTAPS 1983 / Robock 2007 / Coupe 2019 / Toon 2019）→ 争议与不确定 → 与本站数据的关系（明确说：本站不算核冬天，只引述已发表结论）。
- 图表 2–3 个：只用**已发表数字**重绘（如烟尘量 vs 全球平均降温），标注「redrawn from X (year), Fig. Y」；不做任何新计算。
- 引用：脚注式，8–12 条，优先可公开访问的原文/摘要链接。
- 内链：`/methodology/`、`/blast-radius/`、首页。
- 工作量：**14 h**（含查证）

### 4.6 `/methodology/`
- 手册版本/DOI/镜像；四类数值的取数路径与图号页码；立方根缩放的原文引用与适用边界（手册说「megaton range」以内）；读图误差（对数坐标 ±3–8%，写区间不写单值保证）；WorldPop 版本/年份/分辨率/像元中心法；GeoNames 版本；**「本站没有算什么」清单**（10 条：不做伤亡估计、不做实时人流、不做落尘足迹、不做 3D、不做自由当量滑杆外推、不做地下/水下/高空爆炸、不做多弹头、不做地形遮蔽、不做建筑结构响应、不做辐射剂量）。
- 含 `data-ledger` 的可读版本（抽查状态表）。
- 工作量：**5 h**

### 4.7 `/about/` `/privacy/`
- about：谁做的、为什么做、数据从哪来、怎么纠错（给一个邮箱，用现有 Agent Mail 或普通邮箱）。
- privacy：无账号、无 cookie、无追踪（GA4/Clarity 先不加，v1 保持 zero-tracking，这也省掉一类合规问题）、CDN 日志说明、外链。
- 工作量：**2 h**

---

## 5. SEO 落地清单（逐条可勾）

- [ ] 全站静态；JS off 下每页数字/文案/内链都在 HTML（用 `astro build` 后 grep 校验，写进 CI）
- [ ] 首页 SSR 默认值（New York · 100 kt）
- [ ] 一页一词；Title ≠ H1 且都含目标词
- [ ] description 逐页手写
- [ ] og:image **必须是构建期生成的 PNG，尺寸实测 1200×630**（Pillow 打开量，不看文件名）；**SVG 一律不允许**；`og:title` 与 `title` 同源；绝对 URL；`og:image:width/height` 显式写出
- [ ] title / description / H1 不得出现页面上还没有的功能词（当前：`population` 在人口层上线前禁用）
- [ ] JSON-LD：首页 + 各 FAQ 区 `FAQPage`；城市页 `BreadcrumbList`；`/blast-radius/` 加 `Dataset`（可选）
- [ ] canonical 全部指向 `https://apocalab.com/...`（构建时断言不含 `vercel.app` / `pages.dev`）
- [ ] `sitemap.xml`（`@astrojs/sitemap`，自动含 20 城）
- [ ] `robots.txt` 指 sitemap
- [ ] 内链 ≥3 条/页；城市页必链首页 + `/blast-radius/`
- [ ] 构建断言：无 `lorem`、无 `TODO`、无 `undefined`；禁词按词边界匹配（`\bdemo\b` 等）
- [ ] 构建断言：`/blast-radius/` 的四条硬门（4.2）逐条过
- [ ] Lighthouse 移动端：Perf ≥ 90，SEO = 100，A11y ≥ 90

---

## 6. 开发顺序与工作量（总 70–85 h）

**顺序按你的调整改过：`/blast-radius/` 提前到地图之前。** 理由不再是「先有数据后有页面」，而是「这一页只要有真数字真表格就能接 `nuclear bomb blast radius` 这个月搜 8,100 的词，不需要地图」。

| 阶段 | 内容 | 工时 | 出口标准（不达标不进入下一阶段） |
|---|---|---|---|
| **0 数据层** ✅ | 曲线读数、`effects.json`、`verify_data.py`、`data-ledger.csv` | 14 h | **已通过 2026-11-11**：24 条数据、354 项自检全过、抽检 5 条对上原图 |
| **1 骨架 + `/blast-radius/`** | Astro 工程、`effects.ts`、Base 布局、`/blast-radius/`、`/methodology/` 首版 | 12 h | 4.2 的四条硬门全绿 |
| **2 首页 + 查表** | ResultPanel SSR、首页默认值（New York · 100 kt）、URL 状态 | 8 h | JS off 首页有完整结果；切当量 <300 ms |
| **3 地图 + 视觉** | MapLibre、Canvas 覆盖层、测地圆、Natural Earth 降级、移动端抽屉 | 16 h | 断网/挂瓦片时轮廓与圈仍在且不空白；4G 首屏 2 s 内 |
| **4 `/nuclear-bomb-map/`** | 世界视角 + 导航接入 | 4 h | 导航可点达；分享链接可还原 |
| **5 城市页 ×20** | 模板 + 生成门槛 + 20 篇文案 + og 图 | 10 h | 20 页全过门槛；每页 3 条内链 |
| **6 内容与法务 + 余量页** | nuclear-winter 2500 词、methodology 定稿、about、privacy、武器页 12、约 40 个灾害/查询页 | 18 h | 引用可点、无自算数字；每页有独立搜索意图 |
| **7 收口** | sitemap/robots/canonical 断言、Lighthouse、OG 全量核查 | 6 h | 第 5 节清单全绿 |
| — | **阶段二**（12 当量页，等你确认） | 8 h | 复用同套数据与模板 |

总量回到 **70–85 h**，与 v1.0 一致。城市页固定 20 个，不为它追加任何工时。

### 6.1 首月 80 页怎么堆（你定的第 3 条）

**先分清两个数**：80 是**首月总页量**，城市页是其中的 **20 页**，不多不少。

| 组成 | 页数 | 说明 |
|---|---|---|
| 核心页 | 8 | `/`、`/blast-radius/`、`/nuclear-bomb-map/`、`/fallout-map/`、`/nuclear-winter/`、`/methodology/`、`/about/`、`/privacy/` |
| 城市页 | 20 | 已列的那 20 城，一城一页 |
| 武器/历史弹页 | 12 | 先做现有 12 个；扩不扩按后续数据定，不在本期承诺 |
| 灾害与查询页（余量） | ~40 | 同一赛道里**有独立搜索量**的页面类型，清单待定 |
| **合计** | **80** | |

**页量来源**：靠有独立搜索量的页面类型补齐，不靠加城市。

**城市页的定位**：不负责流量，负责覆盖与内链。它们把「半径数字」落到地理实体上，给核心页提供锚文本入口，同时让站点在地名类长尾里有落点。

**验收标准（不变）**：每页必须同时具备三项——① 三档当量（15 / 100 / 1000 kt）的半径数值；② 城市中心 10 km 内的背景人口（WorldPop，写明年份与版本）；③ 本地地名文案（120–160 词，含真实地名）。缺任一项 → 该城不生成页面。

**不为城市页追加任何额外工时**：20 页的模板 + 生成门槛 + 文案已含在阶段 5 的 10 h 里。这 20 页只在收录信号确认后按需微调，不设扩张阶段。

一个仍然成立的判断：**不一次铺满 80 页**。信号顺序是收录 → 外链 → 页量 → 排名，页量排在收录后面。核心 8 页 + 20 城市页先上线，看收录，再补余量页。

---

## 7. 风险清单（逐条，具体到哪一条 + 替代做法）

| # | 风险 | 具体位置 | 后果 | 替代 / 处置 |
|---|---|---|---|---|
| R1 | **多当量必须靠缩放律** | 5 psi / 1 psi | 与「不做任何推导」字面冲突 | 用手册 §3.61/§3.75 原文；静态化到 JSON；methodology 公开；页面小字标注。**需要你裁决** |
| R2 | 对数坐标读数误差 | Fig. 3.73c 上 1 psi 那一段 | 1 psi 半径可能 ±5–8% | 读数记到 3 位有效、页面四舍五入到 10 m；批量给区间；你抽查 5 条校准 |
| R3 | **1 Mt 的爆高（5 psi 10,174 ft / 1 psi 15,750 ft）超出 §3.73 p.110 的 5,000 ft 匀质大气假设** | 3.73c 缩放 | 该档半径叠加了手册未量化的额外不确定度 | **保留 1 Mt**：结果面板显示 HOB；methodology 写「按 §3.61 缩放、应读作上限」；注明未做 §3.64–3.66 高度修正（省略方向使值偏小）；不做 >1 Mt |
| R4 | 爆高口径你未指定 | 全站 | 同一点位不同爆高差 20–40% | 建议默认「对 5 psi 最优的空中爆炸」（§3.73 概念），面板显示实际爆高，第二态给 surface burst |
| R5 | 热辐射阈值未定义 | thermal radius | 换阈值半径差一倍 | 建议二度烧伤（浅肤色）为默认 + 三度另列；值从 Fig. 12.64 读，用 §12 p.562 的 4.5–6 cal/cm² 做校验锚点 |
| R6 | **Fig. 7.42 曲线标号不可直读**（扫描件无文字层） | thermal 全部 6 格 | 阈值与曲线对不上，整列错 | **已处置**：三档全部直读该图，标号由 §12.66 p.563 + §7.43 p.290 两句话反推，三条锚点偏差 +3.6% / −3.9% / +5.0%；methodology 明写标定依据与「无文字层」 |
| R7 | 1 km 人口栅格任意点覆盖 | 首页选点 | 全球 1 km 栅格 30 MB+ | 20 城 250 km 窗口 + lazy 加载；窗口外明示未覆盖，不外推 |
| R8 | 城市「范围内人口」定义歧义 | 城市页 | 数字说不清 | 建议统一为「半径内人口」，与效应圈同源；不引入行政市界人口（两套数会互相打脸） |
| R9 | 20 城跨 10 国，WorldPop 各国方法不一 | 城市页 | 横向不可比 | 统一 R2025A constrained UN-adjusted + 同一年 2020；methodology 明写 |
| R10 | 备用底图源难找 | 3.3 | 主源挂了只剩纯色 | **已解决（D5）**：自托管 Natural Earth 110m 轮廓，公有领域、约 120 KB、随站打包，不依赖任何第三方条款 |
| R11 | OpenFreeMap 无 SLA | 3.3 | 突发不可用 | 降级方案已覆盖；上线后每周一次探测脚本记录可用性 |
| R12 | `/nuclear-winter/` 图表版权 | 4.5 | 直接截论文图有风险 | 只用「已发表的数字」重绘，标注 redrawn from + 原始出处，不复制原图版式 |
| R13 | 内容敏感度（广告/支付审核） | 全站 | 后续订阅可能被支付方拒 | v1 保持零追踪、零广告、纯事实引述；文案避开「target your city」这类祈使句，用「at this location」 |
| R14 | 构建产物文件数 | 部署 | CF Pages 有文件数上限 | 20 城 × 少量资源 + 24 张 og，总量 < 500 文件，安全 |
| R15 | og 图需离线底图 | 3.5 | 无瓦片服务器可用 | Natural Earth 110m（公有领域）在构建期光栅化进 PNG，不需要任何地图 API；**输出必须是 PNG 1200×630，SVG 不接受**（SVG 在微信/Slack/X 的抓取器里不渲染） |
| R16 | `[city]` 路由与未来 slug 冲突 | 路由 | 新增 `/about/` 之类若与城市同名 | 静态路由优先于 `[city]`，且建 `reserved.json` 白名单在构建期断言 |

---

## 8. 五个决策点：已裁决（2026-11-11）

| # | 议题 | 裁决 | 落地位置 |
|---|---|---|---|
| D1 | 缩放律（R1） | **接受**。三档全出；每条缩放值带 `scaled from the 1 kt curve (§3.61, p.101)`；`readout` 记 1 kt 基准读数与像素坐标；用 §12.66 做交叉校验 | 2.2 / 2.8 / `effects.json` |
| D2 | 爆高口径（R4） | **读峰值**，不选固定爆高、不拟合最优爆高公式；面板显示 HOB 与 burst type；第二态为地爆，读 HOB = 0 底边；火球空爆 110·W^0.4 / 地爆 145·W^0.4，禁止混搭 | 2.2 ②③ / 4.2 |
| D3 | 热辐射阈值（R5） | **二度（4.5 cal/cm²，未遮挡浅肤色）默认 + 三度（10 cal/cm²）另列**；页面写明肤色与遮蔽假设 | 2.2 ④ / 4.2 |
| D4 | 城市人口口径（R8） | **城市中心半径 10 km 内 WorldPop 人口**，不用行政边界；效应圈内人口另算，两个数不合并；页面明写半径、年份、版本 | 2.5 / 4.4 |
| D5 | 备用底图 | **自托管 Natural Earth 110m 公有领域轮廓**（约 120 KB，随站打包）；不用任何第三方免费额度；瓦片挂掉画轮廓 + 半径圈 + 一行说明 | 3.2 / 3.3 |

三条调整同样已落地：`/blast-radius/` 提前到地图之前（6）；关掉地图旋转与俯仰（3.2）；城市页固定 20 个、首月 80 页靠页面类型补齐（6.1）；全站禁 demo 类字样 + 免责恰一行（1）。

**仍待你后续定的三件**：约 40 个灾害/查询页的具体清单（你下次给）；阶段二 12 当量页做不做（+8 h）；`/nuclear-bomb-map/` 与首页要不要合并（当前分开，因为两个词各自有量，合并会牺牲其中一个的标题口径）。

---

## 9. 口径自查（**不是入库数据，只为验证链路走通**）

仅用已核实的式 (2.127.1) `R = 110·W^0.4 ft` 跑一遍，确认单位与量级没问题：

| 当量 | breakaway 火球半径（≈ ft → m） |
|---|---|
| 15 kt | ≈ 325 ft ≈ 99 m |
| 100 kt | ≈ 694 ft ≈ 212 m |
| 1 Mt | ≈ 1,743 ft ≈ 531 m |

与公开常识量级一致，说明链路可用。**5 psi / 1 psi / 热辐射三行现在是空的，阶段 0 读图后填，你抽查过才进页面。**

---

## 10. 附：数据录入模板（阶段 0 用的工作表表头）

`id | effect | yield_kt | burst | radius_ft | radius_m | hob_ft | value_type | figure | page | 读数过程 | 录入 | 抽查 | 备注`

~~首批必须填满的 12 行~~ → **阶段 0 已完成，实际落了 24 行**（空爆 12 + 地爆 12），见 `data-ledger.csv`。实际取值路径与 v1.0 的差异：

```
fireball.air.15/100/1000        → 式(2.127.1) p.70（公式，非读图）
fireball.ground.15/100/1000     → 式(2.127.2) p.71（公式，地爆口径）
overpressure_5psi.air.*         → Fig.3.73c p.115 读每条等压线峰值 → 4/6 psi 插值 → §3.61 式(3.61.2) p.101 缩放
overpressure_5psi.ground.*      → Fig.3.73c p.115 读 HOB=0 底边 → 缩放
overpressure_1psi.air.*         → Fig.3.73c p.115 读峰值 → 缩放
overpressure_1psi.ground.*      → Fig.3.73c p.115 读底边 → 缩放
thermal_2nd.air.*               → Fig.7.42 p.291 三档直读（4.5 cal/cm²）
thermal_3rd.air.*               → Fig.7.42 p.291 三档直读（10 cal/cm²）
```

---

## 11. 我这边的收尾说明

- 本地 `.tmp_handbook/` 是我抽 PDF 的临时目录（4 个 PDF + 抽取脚本 + 文本）。阶段 0 还要用它做读数核对，所以先留着，**首次提交前会写进 `.gitignore` 并清掉**，不进仓库。
- 工作区现有的 4 张 PNG（蘑菇云、地形图、横幅）我看过了，v1 只可能用作 `/nuclear-winter/` 的插图或 og 图底纹；如果要用，我会先给你看合成效果，不直接上。
- 我不同意把「免责」做成页面元素之外的任何东西，但你这条要求我照做：全站每页恰一行，页底。
