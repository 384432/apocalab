# apocalab.com — v1 实施计划

> 技术负责人 / 全栈工程师：灵
> 版本：**v1.6（2026-11-13 修订）**。阶段 0 数据层已通过抽检，阶段 1 骨架与 `/blast-radius/`、阶段 2 首页与查表、阶段 3 `/nuclear-bomb-map/` 均已交付；交付形态自 v1.4 起锁定为 **Cloudflare Pages 静态站**（§3.7）。第 8 节 5 个决策点已全部裁决，正文按裁决结果改过。v1.6 改动：收录开关改成 `SITE_LIVE` 布尔值（§3.7）、title 撤回 `20 Cities`（§4.9）、首月页数从 80 改成 **53**（§4.10）、城市页规格与人口口径落地（§4.11）。
> 本文所有页码、图号、公式，均来自我本机对手册 PDF 的抽取核对（见 2.1），不是从二手网页抄的。

**v1.6 相对 v1.5 改了什么**（只列会改变行为的）：

1. **收录开关加了一层 `SITE_LIVE`（§3.7）**。v1.5 的规则是「main 可收录、其它分支 noindex」，但域名还没指向 Pages，而每页 canonical 都指向 `apocalab.com`。生产可收录、canonical 拿不到，等于把 `*.pages.dev` 那套地址送进索引。当时置 `SITE_LIVE = false`，生产与预览都 noindex；上线当天只改这一个布尔值。**该值已于 2026-11-16 06:05 CST 翻为 `true`（§3.7「⑤⑥ 记录」），本条只作变更历史。**
2. **`/nuclear-bomb-map/` 的 title 去掉 `, 20 Cities`（§4.3、§4.9）**。用 20 个城市词（合计月搜不到 100）去抵押一次构建失败不划算；城市页照做，进度不挂在 title 上。新 title：`Nuclear Bomb Map: Rings on Real Ground at True Scale`。
3. **首月页数 80 → 53（§4.10）**。按美国月搜逐词查过 49 个词，能诚实交付又真有人搜的只有 13 个查询页。53 = 核心 8 + 城市 20 + 武器/历史 12 + 查询 13。**「约 40 个灾害查询页」这个数字作废**，实时数据地图类（飓风/山火/闪电/龙卷/洪水/地震）明令不做。
4. **城市页规格落地（§4.11）**：URL 放在 `/nuclear-bomb-map/{slug}/`，title 模板 `Nuclear Bomb Effects on {City}: 15 kt to 1 Mt`，三项数据里一项直取 `effects.json`、两项现算，人口口径句写死在页面上。

**v1.4 相对 v1.3 改了什么**（只列会改变行为的）：

1. **交付形态写回 Cloudflare Pages（§3.7）**。v1.0–v1.3 的计划里**根本没有部署一节**——这是漏项，不是取舍。结果阶段 2 我用平台自带托管交了一版预览，偏离了最初就定死的 Cloudflare Pages。现在补齐：`dist/` 静态产出、`output: 'static'`、不装 adapter、预览期 `_headers` 加 `noindex`、正式域名上线时删掉该行。
2. **§3.1 目录树改成真实结构**，不再写不存在的文件名。
3. **修正 §3.2 / §3.6 的三处实测偏差**：投影文件叫 `mercator.ts`；降级不是「4 s 超时悬崖」（降级层首帧就在，瓦片只是升级，窗口 7 s）；MapLibre 分块是 +285 KB gzip 而不是 +260 KB。
4. **三页 title / H1 重写并把分工写死（§4.1–4.3）**：`/` 主词 `nuke simulator`、`/blast-radius/` 主词 `nuclear bomb blast radius`、`/methodology/` 主词 `how nuclear blast radius is calculated`。首页 title 里不再出现 `blast radius`——两页打同一个词是自己在跟自己抢。四条 title 之间任意两页的最长共同词串不得超过 3 个词，`check_site.py` 断言。

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

- 源：**WorldPop Global2 R2025A，100 m，2020，constrained（UN-adjusted）**，通过 `POST https://api.worldpop.org/v3/catchment` 取数，许可 CC BY 4.0（可商用，需署名）。选 UN-adjusted 的理由：20 个城市跨 10 个国家，各国普查口径不一致，用联合国校正后的国家总量更可比。
- **分辨率 100 m，不是原计划的 1 km —— 这是改进，不是妥协。** 原计划是下载各国 1 km 分幅、自己裁窗、自己按像元中心求和，那条路会把「重采样选择」和「边缘取整」写进数字里；实际用的是 WorldPop 自己的服务，在**原生 100 m** 栅格上做面积分，任何人拿同一个圆、同一年份能复算出同一个数。代价是不再有本地栅格可离线播放（原计划的 250 km 窗口 + lazy 那套因此作废），换来的是每个数字都可复核。`city-pop.json` 的 `source.note` 与城市页正文都写着 100 m。
- 分辨率与口径：统计的是**夜间居住人口分布**，非实时人流、非伤亡。
- **查询半径统一 25 km（`catchRadiusKm`）**：1 Mt 的 1 psi 环是 21.40 km，10 km 的圆装不下它；若用 10 km 抓，页面上的「环内人口」其实是被 10 km 截断的那块，而标题写着 1 psi。所以每城一次 catchment 就取到 25 km，页面上所有半径（火球 / 5 psi / 1 psi / 二度 / 三度）和 10 km 城市圆都是这**同一次请求里的 cumulative**，绝不环减环、绝不拿城市人口减环内人口当存活数。
- 断言（两处，缺一不可）：`scripts/build_city_pop.py` 在抓数前拒绝 `CATCH_RADIUS_KM < 最大环`；`src/lib/city-pop.ts` 在模块加载时用 `effects.json` 算出 `MAX_RING_KM`，任何城市记录 `catchRadiusKm < MAX_RING_KM` 直接抛错 —— 也就是构建失败，而不是印一个被截断的数字。
- 「范围内人口」算法由 WorldPop 服务完成（圆内像元积分），我们只在 `per_km2_check()` 里校验每环带密度不超过 400,000 人/km²，防止单位错（m / km）在 200 响应里蒙混过关。
- **地标**：每个城市页必须有 2–3 个只属于该城的真实地名（公园 / 水域 / 地标），来自 GeoNames 国家级 dump（`US/GB/FR/JP.zip`，CC BY 4.0，缓存在 `.tmp_handbook/geonames/`），由 `scripts/fetch_city_places.py` 选点写进 `src/data/city-places.json`。选点规则：距城市点 0.4–10 km，只取 P/H/S/L/T 五类，名字必须是纯字母（排除编号、网格、行政区），三类尽量各一个；页面正文说明它落在哪个环里。**纯模板页不接受。**

### 2.6 地名与搜索

- GeoNames `cities15000.zip`（**34,214 条**，含人口、坐标、国家、时区），CC BY 4.0。构建期切成 **27 个分片（26 个字母桶 + `other`），首屏不加载任何分片**，用户开始输入才取对应一个桶；全量 gzip **886,209 字节**、最大桶 **103,144 字节**。字段、分片粒度、失败降级的全部数值与硬约束**见 §15**，本节不另立一套数。
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

**签核状态**：空爆 15 条 2026-11-11 签；地爆 9 条 2026-11-14 签。地爆这批不是「沿用同一批基准所以算过了」——是把 Fig. 3.73c（p.115）的 HOB = 0 底边按 600 dpi 重渲染后独立重读：三个 1 kt 基准 4 psi 1,655 ft、6 psi 1,121 ft、1 psi 3,830 ft，与曲线和底边的数字化交点（1,665 / 1,122 / 3,832 ft）相差 ≤0.6%，都在 ±5% 读数误差内，由这两条基准缩放出来的六个半径也因此一并复核。**数值一处没改**，签的是原来那九个。24 条全部有 `checked_by`，产物里的 `*` 目前是 0 处；`*` 的渲染逻辑保留，以后新加的行只要不签就会自己带星。

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
  components/   ResultPanel.astro（首页面板）/ RadiusCell.astro（表格单元格）/ BombMap.astro
  lib/          effects.ts / panel.ts / island.ts / cities.ts / mercator.ts / site.ts
  scripts/      bomb-map.ts           ← 全站唯一在浏览器里跑的地图脚本（动态 import MapLibre）
  data/         effects.json / cities.json
scripts/        build_effects.py / build_cities.py / verify_data.py / check_site.py / check_urls.py
public/         ne_110m_land.geojson / favicon.svg / _headers / robots.txt
```

### 3.2 地图与半径绘制（关键决策）

**半径圈不由 MapLibre 的 layer 画，由我们自己的 Canvas 覆盖层画。**

理由：你的降级要求是「瓦片挂了圈还在」。如果圈是 MapLibre layer，map 初始化失败或 style 报错时圈会一起没。做法：

- `<div id="basemap">` 交给 MapLibre，只负责底图；`<canvas id="rings">` 绝对定位叠在上面，由 `lib/mercator.ts` 自己算墨卡托投影，监听 `map.on('move')` 重绘。
- 圈用真实测地圆（按大圆半径算，投影后是多边形，不是屏幕圆），所以「按真实比例」成立。
- 数字标注跟着圈走，字体用系统栈（不加载 web font）。
- **降级层首帧就在，不是超时才出现**：HTML 一渲染完就先画轮廓 + 圈，瓦片只是在它之上淡入。所以「打不开」这件事不存在——只有「有没有真实底图」的区别。触发降级的条件只有两条：MapLibre 初始化抛错（含无 WebGL），或 7 s 内没跑完 `load`；style 就位之后的单张瓦片 / 字形 404 不算失败（MapLibre 会为单个资源报 error，圈不受影响）。降级时地图左下角出现一行 `Basemap unavailable — radii are still to scale.`
- **降级层（D5 已裁决）**：自托管 Natural Earth 110m 陆地轮廓（公有领域，138 KB 原始 / 约 40 KB gzip，随站打包 `public/ne_110m_land.geojson`），瓦片挂掉时画「轮廓 + 半径圈 + 一行说明」。**不用任何第三方的免费额度，不引入第二份会变的条款**——这条比省 4 小时重要。
- **手势约束（你定的）**：`dragRotate: false`、`touchPitch: false`、`pitchWithRotate: false`、`maxPitch: 0`。半径圈是我们自己按墨卡托算的多边形，用户一转一倾就和底图错位；2D 视图不需要这两个手势。**这条只约束 2D 视图——3D 视图的相机自由度由 §14.3 a 定义。** 补这句的理由：两节不划范围时读起来互相矛盾，后人无法判断 3D 该不该开相机。键盘也不给旋转。

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
| 地图可见 | < 2 s（4G） | 首帧就是自绘轮廓 + 圈；MapLibre 动态 `import()` 后台升级，不阻塞首帧 |
| 切换当量到出圈 | < 300 ms | 纯查表 + Canvas 重绘，无网络 |
| JS 总量 | 首屏 < 40 KB，地图就绪后 +285 KB（gzip） | 代码分割；MapLibre 只在 `/nuclear-bomb-map/` 上按需加载 |
| 降级 | 可用状态在首帧即成立，不依赖任何网络请求 | 轮廓 + 圈先画；瓦片升级窗口 7 s |

移动端交互：选点 = 单击（`tap`），当量 = 三个大按钮（不做滑杆，滑杆是阶段二的事）；结果面板为底部抽屉，拇指可达；地图默认 zoom 由半径自动 fit（留 15% 边距）。

---

### 3.7 部署（Cloudflare Pages，静态，零适配器）

**这是硬约束，不是可选项。** 站点只以 Cloudflare Pages 的形式交付，理由不是偏好：整站的成立条件是「关掉 JS 也能读、没有服务端状态、CDN 直接吐 HTML」，一旦接了 adapter，Pages 就会去跑 Functions，这三个前提同时失效。

- **构建**：`npm run build`（即 `astro build`）→ `dist/`。`astro.config.mjs` 保持 `output: 'static'`，不装 `@astrojs/cloudflare` 或任何 adapter。`check_site.py` 断言配置里没有 `adapter:`、没有 `@astrojs/*`、`dist/` 里没有 `functions/`。
- **Pages 项目设置**：构建命令 `npm run build`，输出目录 `dist`，Node 20+。仓库根的 `wrangler.toml` 用 `pages_build_output_dir = "./dist"` 兜底，手工 `wrangler pages deploy` 也不会把仓库根当成产物。
- **收录开关 = 一个布尔值 + 一个分支，不是写死一行**：`dist/_headers` 由 `scripts/gen_headers.mjs` 在 `astro:build:done` 时生成。它**从 `src/lib/site.ts` 读取 `SITE_LIVE`**，不在生成器里复制一份值；读不到或读到多份声明就构建失败，不许猜。

| `SITE_LIVE` | 构建分支 | 产物模式 | `_headers` |
|---|---|---|---|
| `false` | `main` | **staged** | `/*` 带 `X-Robots-Tag: noindex` |
| `false` | 其它 / 本地无变量 | staged | 同上 |
| `true` | `main` | production | 整份文件不写任何 `X-Robots-Tag` |
| `true` | 其它 / 本地无变量 | preview | `/*` 带 `X-Robots-Tag: noindex` |

  **当前 `SITE_LIVE = true`（2026-11-16 06:05 CST 翻的，见下面「⑤⑥ 记录」）。** 在此之前它是 `false`，原因写在时间线里：域名还没指向 Pages，而每页 canonical 都指向 `apocalab.com`；Google 拿不到 canonical 目标时会直接收录 `*.pages.dev` 那套地址，域名上线那天就变成两份同内容——所以那段时间生产和预览都 noindex，sitemap 照常生成、但**不提交**给 GSC。
  **上线当天只改 `src/lib/site.ts` 里的 `false` → `true`，重新构建**，没有第二个手工步骤（实际执行时就是一个 commit 只改这一行）。`check_site.py` §16 用同一个文件里的值决定期望：产物模式与它不符即失败，所以「改了值忘了改闸门」这条路不存在。
  三个方向都有硬断言：staged / preview 必须带这个头；production 整份 `_headers` 与全部 HTML 都不许出现 `noindex` 字样；任何模式下 HTML 都不许出现 `<meta name="robots">`（收录开关只留一条路）。生成器还会把 `# mode:` / `# site-live:` 写进产物，闸门校验这两行自证。
- **删掉 `public/_headers` 的理由**：静态副本会在部署时覆盖生成物，谁盖谁取决于平台复制顺序 —— 这种「有时生效」的配置比没有更危险。闸门断言 `public/_headers` 不存在，删它就是构建失败。
- **`_headers` 还负责 `.geojson` 的 MIME**：Pages 对未知扩展名默认 `application/octet-stream`，降级轮廓那条路径要它明确是 `application/json`。
- **交付物只有两种**：Cloudflare Pages 的 `*.pages.dev` 地址与正式域名 `apocalab.com`。`SITE_LIVE=false` 那段时期（2026-11-16 06:05 CST 之前）生产与预览都带 noindex；翻开关之后 `apocalab.pages.dev` 与主域同源同构建，同样不再带 noindex，靠 canonical 收拢（见「⑤⑥ 记录」末条）。平台自带的托管预览链接不再作为交付物，也不写进任何文档。
- **兜底部署路径（平台构建队列堵塞时）**：Git 直连构建会整段时间卡在 `queued`（`clone_repo` 根本没有开始），此时线上停留旧版本。兜底是本地按目标分支口径构建后直传同一份产物：

  ```
  CF_PAGES_BRANCH=main npm run build
  npx wrangler@4 pages deploy dist --project-name apocalab --branch main    # 生产
  npx wrangler@4 pages deploy dist --project-name apocalab --branch preview # 预览别名
  ```

  两条硬要求：① `--project-name apocalab` 必须显式给，且部署返回里的 alias 必须是 `apocalab.pages.dev` / `preview.apocalab.pages.dev` —— 上级目录 `E:\CODEX\wrangler.jsonc` 属于另一个项目（`lumaroot-site`），wrangler 会把它当「用户配置」抓走，不核对就会把产物传到别处；② 直传前本地四个闸门必须已经全绿，直传是分发动作，不是验收动作。
  直传不会篡改 Git 记录，平台恢复后下一次 `git push` 的构建会照常把同一个 commit 再发布一次，内容一致、无需回滚。
- **上线顺序（硬顺序，不是建议）**：七步 —— **④b 是 2026-11-16 插进来的一步**（`www` → 裸域 301），排在 ④ 与 ⑤ 之间 —— 缺一步都不往下走。①②④⑥ 的动作与验收全在线上，本地全绿不代表能切。**顺序的要义是：绑域名在前、翻开关在后**——`SITE_LIVE` 唯一控制的输出就是全站 `X-Robots-Tag: noindex`（2026-11-14 逐项核过：`robots.txt`、`sitemap.xml`、页面 HTML、canonical/`og:url`、页面脚本都不受它影响；见 `scripts/gen_headers.mjs` 与 `astro.config.mjs`，全仓库只有这两处读它），noindex 期间绑域名没有任何 SEO 损失（noindex 就是不让收录），反而能让正式域名先过一遍闸门；把「正式域名实测」排在翻开关之后，真出问题时站已经可以被收录了。

  | # | 动作 | 为什么不能省 |
  |---|---|---|
  | ① | `node scripts/verify_map.mjs https://apocalab.pages.dev`（先起 headless Chrome 在 9333 端口），三态全过：瓦片可达 / 瓦片屏蔽 / 关 JS | 考的是 CDN 上 `.geojson` 的 MIME、`_headers` 的实际生效、真实网络下的降级路径，本地 `astro build` 验不出来 |
  | ② | `python scripts/check_urls.py --online https://apocalab.pages.dev`：随机不存在的路径必须 **404**、404 响应必须是本站 404 页（五条回收链接在 `<main>` 里）、五条链接逐个真发请求确认 200、不存在的 `.png` 必须 **404**（Content-Type 只 WARN，见下面那条已知偏差） | 软 404 是**托管平台的 not-found 行为**，本地静态服务器（`SimpleHTTPRequestHandler`）永远正确 404，复现不出来 |
  | ③ | 绑定 `apocalab.com` + 改 DNS。**当前状态（2026-11-16）：已通过** —— 正式域名 `200`，`/sitemap.xml` `200`（`application/xml`，10 条 loc 全部 `https://apocalab.com/` 开头），Pages 自定义域已 `Active`。此前的 530/`1016`（无记录）与 522（记录在、Pages 侧未加）保留在下面的时间线里作排查依据 | **noindex 期间绑域名没有任何 SEO 损失**（noindex 就是不让收录），反而能让正式域名先过一遍闸门；反过来把这一步排到翻开关之后，真出问题时站已经可以被收录了。**当时**整站仍在 noindex（`SITE_LIVE=false` 那段时期），域名指过来只是让内容在一个「不许被收录」的地址上先跑通 |
  | ④ | `python scripts/check_urls.py --online https://apocalab.com` —— host 从 `apocalab.pages.dev` 换成正式域名再跑一遍。**不通过不许往下走**。**当前状态（2026-11-16）：已通过** —— 首测 **84 PASS / 0 FAIL / 1 WARN**（那条 WARN 是既定的 `.png` 类型偏差），见下方「实测记录 · 接通后首测」。**「已通过」的口径钉死为三件事：域名 200 + `X-Robots-Tag: noindex` 仍在 + sitemap 10 条 loc 均以 `https://apocalab.com/` 开头。** 注意这三条是 **④ 当时的判据**（那时 `SITE_LIVE=false`，带 noindex 才对）；翻开关后这条判据反过来，见 ⑥ 与「⑤⑥ 记录」。三项之外一律不作数：不等于可收录，不等于可提交 GSC | **不换 host，闸门测的就还是 `pages.dev`，正式域名等于一次都没测过**；DNS、证书、`_headers` 在正式域名上的生效，都是新的东西。这一步之前，正式域名从未被任何闸门碰过 |
  | ④b | **`www` → 裸域 301。** DNS 加一条 `CNAME` `www` → `apocalab.pages.dev`（**代理必须开，橙色云**）、**不加进 Pages 的 Custom domains**、**不加通配符**；再把那条 Redirect Rule 的匹配条件从「通配符 URL」改成自定义筛选表达式 `http.host eq "www.apocalab.com"`，动作 Dynamic、目标 `concat("https://apocalab.com", http.request.uri.path)`、状态码 `301`、保留查询字符串。**当前状态（2026-11-16）：已通过**，六条实测见下面「④b 记录」 | 灰云会让 `www` 直接回源到 `apocalab.pages.dev`，而 Pages 对 `www` 不做 301，等于两份 200 内容；把它绑进 Custom domains 同理——**这一步的目的就是让 `www` 永远不以 200 出现**。匹配条件必须只看 host：原模板把请求 URL 写成 `https://www.apocalab.com/*`，**含协议头**，只匹配 443，`:80` 会漏成 522 |
  | ⑤ | 把 `src/lib/site.ts` 的 `SITE_LIVE` 改成 `true`，构建、推送、等部署完成——去掉全站 `noindex`。**前置闸门：必须先等「任意城市搜索」上线并自测通过**（见下面那条），否则不许翻。**当前状态（2026-11-16 06:05 CST / 22:05 UTC）：已执行**，只改了这一个布尔值，见下方「⑤⑥ 记录」 | 这是**唯一一个放开收录的动作**，排在域名已经验收之后，所以放开的那一刻，被放开的地址是新的、已验过的那个 |
  | ⑥ | 抓首页响应头与 HTML（`https://apocalab.com/`，顺带 `https://apocalab.pages.dev/`）：**noindex 必须已经消失**，**canonical 必须仍指向 `https://apocalab.com/`**。**当前状态（2026-11-16 06:07 CST / 22:07 UTC）：已通过**，12 条响应头逐个抓过、`check_live.py` 40/0、`check_www.py` 六条全过 | 这一步验的是**两件来源不同的事**，缺一不可：noindex 响应头来自 `SITE_LIVE`，canonical 来自 `SITE_ORIGIN`。前者不消失 = 没真正放开收录；后者若被顺手改到 `pages.dev` = 把正式域名上的页面自己否掉 |

  **①没过不切，②没过也不切，④不通过不翻开关；跑了没过，先修，不许「先上线再看」。**
  **口径（③ 与 ⑥ 的关系）**：canonical 从头到尾都由 `SITE_ORIGIN` 固定为 `https://apocalab.com/`，**翻转前就已经指向它**，不随 `SITE_LIVE` 变。所以「翻开关」改变的是收录许可，不是 canonical 指向；⑥ 才会同时验这两件事。
  **③–⑥ 必须在同一天连续做完，不许隔夜。** 两个方向的后果不对称，危险的那个是「只翻开关、没绑域名」：production 立刻可被收录，而 canonical 指向的 `apocalab.com` 还没有内容——爬虫拿到的是 `pages.dev` 一份、canonical 打不开，域名上线那天同一内容就落在两个 hostname 上，正是 `SITE_LIVE` 存在的理由。反过来「只绑域名、没翻开关」不会进索引（两边都还 noindex），但会让正式域名空转，并且「已经绑了」这个状态很容易被当成已经上线，所以同样不许隔夜。
  **③ 的绑域名与 DNS、④ 的正式域名闸门、④b 的 `www` 301 均已于 2026-11-16 执行完毕并通过；⑤ 的翻开关与 ⑥ 的验收已于 2026-11-16 06:05–06:07 CST 连续做完并通过。七步至此全部走完。** 此后不许再新增任何 DNS 记录或 Redirect Rule，除非上面那张表里有一条红过。

  **前置闸门（2026-11-16 新增，排在七步之外、拦在 ⑤ 之前）：`SITE_LIVE` 的翻转必须等「任意城市搜索」上线并自测通过之后，才允许执行。** 理由一句：现在翻转，谷歌与首批访客看到的是 20 个城市、3 档当量的固定面板，与 `nuke simulator` 这个词的期待不一致，收录窗口一旦用掉就换不回来。
  - 这条**只拦 ⑤**：③ 的域名绑定、④ 的线上自验、以及 ⑥ 之后的验收动作都不受影响，照常推进。
  - 「任意城市搜索」要做到什么程度、和其余交互差距怎么排序，见 §14；本闸门只认一件事：**输入一个不在那 20 个里的城市，页面能给出那座城市的环**。
  - 触发条件是**自测通过**，不是「代码合并」：合并了但输入任意的城市仍然只回纽约，等于没做到。关 JS 只有单一状态这件事属 §14 的另一条差距，不由本闸门裁决。

  **顺序连带约束（2026-11-16）：⑤ 被上面那条闸门拦住期间，排在 ⑤ 之后的动作一律顺延，不许单独执行、更不许记成「已通过」。** 具体到「把 host 换成 `apocalab.com` 再跑一遍 `check_urls.py --online`」这个动作：它在早期排法里是翻转之后（⑥），在当前排法里是翻转之前（④，已通过）——**无论按哪种排法，只要 ⑤ 还没翻，就不允许出现新的「正式域名已验收」记录**。理由一句：否则会出现「开关没翻、域名侧却记成已验收」的记录，后来人看不出真相。

  **域名接通时间线（三个阶段，前两段是排查依据，不要删）**：
  - **① `530` / `error code: 1016`（2026-11-16 03:00）**：Cloudflare DNS 里 `apocalab.com` **0/200 条记录**，apex 与 www 都没有任何记录。**不是记录冲突，是根本没有记录指向 Pages** —— 这一步决定了排查方向：不需要删任何东西，直接新建。
  - **② `522`（2026-11-15 19:20 UTC）**：记录已经在了，但 **Pages 侧还没加这个自定义域**，所以 CF 连不回源站。这一段证明「只有 DNS 记录不算接通」，对应下面 b 步那半个动作。
  - **③ `200`（2026-11-16，本轮实测）**：DNS 记录 + Pages 自定义域 **两侧都到位**。首页 200、标题 `Nuke Simulator: What a Nuclear Bomb Would Do to Any City`、34,785 字节；`/sitemap.xml` 200、`application/xml`、10 条 loc 全部 `https://apocalab.com/` 开头。
  - 时间线的意义：`1016` → `522` → `200` 三段分别对应「没记录」「有记录但 Pages 没认」「两侧都认」，以后同样的码回来，直接看落在哪一段就知道缺哪一半。

  **实测记录 · 接通后首测（2026-11-16 03:2x，host = `https://apocalab.com`）**：
  - `python scripts/check_urls.py --online https://apocalab.com` → **PASS 84 / FAIL 0 / WARN 1**，exit 0。五节全过：sitemap 10 条 loc、站点级文件、降级资源、本地 404、线上 not-found 行为。唯一那条 WARN 是既定的 `.png` 类型偏差（`/zzz-<token>.png` → 404 + `text/html`），按下面的「已知偏差」结案，不是本轮新增问题。
  - **`X-Robots-Tag: noindex` —— 当时在。** 首页、`/sitemap.xml`、`/methodology/` 三个响应头逐个抓过，都带 `noindex`；首页 HTML 里没有 `<meta name="robots">`，canonical 是 `https://apocalab.com/`。**这是 03:2x 的快照，现已作废**：2026-11-16 06:05 CST 翻开关后该头已从全部页面消失。
  - 判定：**正常中间态 —— 可访问、不可收录，可进入 ④b 步**（`www` → 裸域 301），再往后才是 ⑤ 的翻 `SITE_LIVE`。这不是缺陷，正是 ③ 完成、④b 与 ⑤ 都还没做时应有的样子。
  - 环境备注：本机解析层被代理 TAP 拦掉（对 `114.114.114.114` / `223.5.5.5` / 网关的 UDP:53 全是空应答），`apocalab.com` 在本机 `getaddrinfo` 直接失败。**`check_urls.py` 一个字节没改**，跑的时候外面套了一层运行时解析垫片（DoH 拿 A 记录后再连），请求仍是带真实 SNI 与 Host 的正常 TLS 请求。以后在这台机上跑正式域名会先看到「域名未接通（DNS）」的 exit 2，那是本机解析问题，不是站点问题 —— 先按这个办法取 IP，再跑闸门。

  **③ 的排查清单（1016 / 522 时的手工步骤，已执行完毕，保留备查）**：
  - **a. DNS → Records → Add record**。当时 `apocalab.com` 是 **0/200 条记录**，apex 与 www 都没有任何记录，所以这是一次**从零添加**，填确定值：
    - 类型 **`CNAME`**
    - 名称 **`@`**（即 `apocalab.com`）
    - 目标 **`apocalab.pages.dev`**
    - 代理状态 **已代理**（橙色云）
    - **记录为空，直接添加，无需先删**：没有记录就无从冲突，「先删后建」是给残留记录准备的说明，套在这里会误导后来排查的人。
    - **apex 用 CNAME 是允许的**：Cloudflare 对根域做 CNAME 扁平化（CNAME flattening），不是非法配置。**不要改用 A 记录指向 Pages 的 IP** —— Pages 的地址是共享任播、会变，钉死 IP 是自找故障。
  - **b. 记录加好后，去 Pages → 项目 `apocalab` → Custom domains → 添加 `apocalab.com`，等它变 `Active`。** DNS 上有记录、Pages 认这个域名，**两边任缺一个都不算接通**：只有 DNS 记录、Pages 没认，回的是 **522**（本轮实测过这一段）；这也是 ③ 那两个半小时里页面打不开的真正原因。
  - **c. 等 1~5 分钟**（首次签证书可能要更久），再验三条：首页 200 / sitemap 200 / 响应头 `X-Robots-Tag: noindex` 在（当时 `SITE_LIVE=false`，它在是正确状态；这是 ③ 阶段的判据，翻开关后它必须反过来）。

  **`www` 的处置已经落地（原来「不属本轮范围、等指令」那段作废）**：`www.apocalab.com` 现在有一条唯一的 `CNAME` → `apocalab.pages.dev`（**已代理**），外加**一条** Redirect Rule 做 301；Pages 的 Custom domains 里**始终没有** `www`。三条红线继续有效：不许把 `www` 加进 Custom domains、不许加通配符、不许用灰云。细节见下面这段。

  **④b 记录（2026-11-16 05:20–06:02 CST / 21:20–22:02 UTC：加记录 → 改规则 → 验收完成）——`www` → 裸域 301 已通过。**

  - **DNS**：`CNAME` / 名称 `www` / 目标 `apocalab.pages.dev` / **已代理**。橙云可由地址族判定，不必看面板：`www` 的 A 是 `104.21.69.191` / `172.67.212.52`、AAAA 是 `2606:4700:3033::6815:45bf` / `2606:4700:3031::ac43:d434`，**与 apex 完全相同**；灰云会直接答 `apocalab.pages.dev` 的 `172.66.44.140` / `172.66.47.116`。CNAME 目标被扁平化，从外部查不到，**目标值只能在面板确认**。
  - **红线逐条核过**：① `www` 从未 200 出一整页（每次都是 301 或 5xx）→ 没进 Custom domains；② `x` / `abc` / `wwww` / `mail.apocalab.com` 四个探测名全 **NXDOMAIN** → 没有通配符；③ 橙云成立；④ 全程只有这一条记录、一条规则。
  - **规则（改的是那一条，不是新加）**：模板「从 WWW 重定向到根」→ 匹配方式由「通配符 URL」改为**自定义筛选表达式** `http.host eq "www.apocalab.com"`；动作 **Dynamic**，目标 `concat("https://apocalab.com", http.request.uri.path)`；状态码 **301**；**保留查询字符串**勾选。
  - **改匹配条件的技术原因（写死，别再猜）：原请求 URL 字段填的是 `https://www.apocalab.com/*`，含协议头 `https://`，所以这条通配符只匹配 443。** `http://` 请求一条规则都不命中 → 被转发给源站 → Pages 不认识 `www` 这个 host → **522**（连测 3 次稳定复现、无 `Location`）。改成只看 host 的表达式后，80 与 443 都命中，且都是单跳。**不要用「开 zone 级 Always Use HTTPS」绕过**：那是全 zone 的行为，还会把单跳变成两跳。
  - **六条实测（不跟随重定向，看原始码；2026-11-16 05:58 CST）**：

    | 请求 | 码 | Location |
    |---|---|---|
    | `https://www.apocalab.com/` | 301 | `https://apocalab.com/` |
    | `https://www.apocalab.com/nuclear-bomb-map/` | 301 | `https://apocalab.com/nuclear-bomb-map/` |
    | `https://www.apocalab.com/nuclear-bomb-map/?city=denver&yield=100` | 301 | `https://apocalab.com/nuclear-bomb-map/?city=denver&yield=100` |
    | `http://www.apocalab.com/` | 301 | `https://apocalab.com/` |
    | `http://www.apocalab.com/nuclear-bomb-map/` | 301 | `https://apocalab.com/nuclear-bomb-map/` |
    | `http://www.apocalab.com/nuclear-bomb-map/?city=denver&yield=100` | 301 | `https://apocalab.com/nuclear-bomb-map/?city=denver&yield=100` |

    路径与查询串逐字保留，六条全是**单跳**：`Location` 的 host 直接就是裸域，没有先跳一次 `https://www.…`。
  - **无循环检查**：`https://www.apocalab.com/` → 一跳 `301 https://apocalab.com/` → **200，45,194 字节，标题 `Nuke Simulator: What a Nuclear Bomb Would Do to Any City`**，最终 URL 里不再出现 `www`。
  - **apex 未受影响**：`http://apocalab.com/` 仍是 **301 → `https://apocalab.com/`**（响应体 534 字节，来源是 Pages 自定义域自己的 http→https，与 `www` 那条规则无关）；`https://apocalab.com/` 当时是 **200 + `X-Robots-Tag: noindex`**（05:58 的快照，`SITE_LIVE` 尚未翻；该头已随 ⑤ 去掉）。
  - **301 响应上没有 `X-Robots-Tag`**：`_headers` 只作用于 Pages 吐出的内容，边缘生成的 301 不经过它。这不是缺陷——301 本身不是可索引的页面。
  - TLS：`www` 走的是 Universal SSL 的 Let's Encrypt 证书（CN `apocalab.com`，SAN 含 `*.apocalab.com`），到期 2027-02-06，不需要单独签。
  - **可重跑**：`python scripts/check_www.py` —— 六条 + 无循环 + `http://apocalab.com/` 对照，结果写 `www-gate.json`，任一失败 exit 1。以后改规则、换域名、翻开关都先跑它。

  **⑤⑥ 记录 —— 翻开关与上线验收已通过（2026-11-16）。**

  - **⑤ 翻开关的时刻**：`src/lib/site.ts` 的 `SITE_LIVE` 由 `false` 改为 `true`，**只改这一行**，commit `a3f4993`（`go live: SITE_LIVE = true`）。
    - **推送 / 部署开始：2026-11-16 06:05:58 CST（2026-11-15 22:05:58 UTC）**，以 `git push origin main` 完成、远端 `refs/heads/main` 已指 `a3f4993` 为准。
    - **部署完成：2026-11-16 06:06:40 CST（2026-11-15 22:06:40 UTC）**。口径是「第一次观测到 `/` 不再带 `X-Robots-Tag` 的那次轮询」；前一次轮询 06:06:31 CST 仍带 `noindex`，所以真实切换点落在 **06:06:31–06:06:40 CST** 之间。**整个部署约 42 秒。**
  - **本地构建口径**：本机没有 `CF_PAGES_BRANCH` 时，`true` 会落进 preview 分支（仍带 noindex）。所以本地验生产产物必须显式给分支：`CF_PAGES_BRANCH=main node node_modules/astro/astro.js build`，构建日志自证 `_headers: production (CF_PAGES_BRANCH=main) [SITE_LIVE=true]`。线上由平台注入 `main`，不需要这一步。
  - **⑥-1 · 12 条响应头（2026-11-16 06:07 CST / 22:07 UTC，host `https://apocalab.com`）—— 全部 200，全部没有 `X-Robots-Tag`**：

    | URL | 码 | `X-Robots-Tag` |
    |---|---|---|
    | `/` | 200 | 无 |
    | `/blast-radius/` | 200 | 无 |
    | `/nuclear-bomb-map/` | 200 | 无 |
    | `/methodology/` | 200 | 无 |
    | `/nuclear-winter/` | 200 | 无 |
    | `/nuclear-bomb-map/new-york/` | 200 | 无 |
    | `/nuclear-bomb-map/los-angeles/` | 200 | 无 |
    | `/nuclear-bomb-map/london/` | 200 | 无 |
    | `/nuclear-bomb-map/paris/` | 200 | 无 |
    | `/nuclear-bomb-map/tokyo/` | 200 | 无 |
    | `/sitemap.xml` | 200 | 无 |
    | `/robots.txt` | 200 | 无 |

  - **⑥-2 · dist 扫描：`noindex` 出现 0 次。** 扫的是 `dist/` 下全部 `.html` 与 `_headers`，共 **12 个文件**（11 页 + `_headers`），命中 **0**。`dist/_headers` 自证头为 `# mode: production` / `# site-live: true` / `# branch: main`，正文里除 `.geojson` 的 `Content-Type` 外没有任何规则。
  - **⑥-3 · `robots.txt` 原文（线上抓取）**：三行，没有 `Disallow`（更没有任何 `Disallow: /`），sitemap 指裸域：

    ```
    User-agent: *
    Allow: /
    Sitemap: https://apocalab.com/sitemap.xml
    ```

  - **⑥-4 · canonical 与 sitemap**：10 个页面（排除 `404.html`）的 canonical **逐个**为 `https://apocalab.com/…` 对应路径；`404.html` 无 canonical（既定设计）。sitemap **10 条 loc**，**全部**以 `https://apocalab.com/` 开头。
  - **⑥-5 · `www` 未被这次部署影响**：翻开关后重跑 `python scripts/check_www.py` → **PASS**。六条（443 三条 + 80 三条）仍是单跳 **301** → `https://apocalab.com/` 同路径，查询串完整；无循环检查一跳落 200；`http://apocalab.com/` 仍是 **301 → `https://apocalab.com/`**。
  - **⑥ 的两个可重跑闸门**：`python scripts/check_live.py`（上面 1–4 项，40 项断言，写 `live-gate.json`，任一失败 exit 1）与 `python scripts/check_www.py`（第 5 项）。
  - **`apocalab.pages.dev` 会跟着一起失去 noindex —— 已知、可接受、不要为它单独加头。** 它与主域**是同一份构建**，`SITE_LIVE` 是构建期常量，没有「按 host 分流」这回事，所以翻牌后 `https://apocalab.pages.dev/` 同样是 200 + 无 `X-Robots-Tag`（实测 06:08 CST：200、无该头、canonical 指 `https://apocalab.com/`、44,827 字节）。收拢手段只有 canonical：它与主域每页 canonical 完全一致，重复内容会被归并到裸域。**明确不做的事**：不给 `.pages.dev` 单独加 `noindex` —— CF Pages 的 `_headers` 只支持按**路径**匹配、不支持按 host 匹配，为它写一条 `/*` 规则会把主域一起屏蔽掉，等于用一次误伤换一个本来就不需要的头。预览分支不受影响：`https://preview.apocalab.pages.dev/` 实测仍是 **200 + `X-Robots-Tag: noindex`**（preview 分支的构建，符合 `SITE_LIVE` 表第 4 行）。
  - **此后 noindex 在本文档里只作历史时间线出现**（`SITE_LIVE=false` 时期的记录、`_headers` 四种组合表、404 的`_headers` 生效说明），**不得再把「全站带 noindex」写成当前状态**。当前状态：production 与 `pages.dev` 都不带，preview 分支带。

  **实测记录（2026-11-16 03:00，接通前）——域名未接通（DNS），不是 SEO 缺陷。** 保留作排查依据：Pages 项目当时就是健康的，只是域名没真正指向它：
  - **根因（你截图核过）：这个域在 Cloudflare DNS 里 `0/200` 条记录，apex 与 www 一条都没有。** 所以是「**没有任何记录指向 Pages**」，不是旧记录打架——这一条决定了排查方向：不需要删任何东西，直接新建。
  - 你发起的请求：`https://apocalab.com/` → **530, error code: 1016**，17 字节纯文本；`/sitemap.xml` → 同样 530 1016；`https://www.apocalab.com/` → 同样 530 1016；而 `https://apocalab.pages.dev/` → **200，34,785 字节，标题正确，canonical 指 `https://apocalab.com/`**。
  - 我这边跑闸门：`python scripts/check_urls.py --online https://apocalab.com` → **前置判定中止，exit 2**，本机连 DNS 都解析不出来（`getaddrinfo failed`）。同一台机上 `--online https://apocalab.pages.dev` 仍是 **84 PASS / 0 FAIL / 1 WARN**，本地 68 PASS 不变 —— 两边对照证明问题在域名解析这一层。
  - 旁证（AliDNS DoH，只读查询）：`apocalab.com` 的 NS 已经是 `ligia.ns.cloudflare.com` / `bruce.ns.cloudflare.com`；apex 查 A **无应答**（NOERROR、answer 空）；`www.apocalab.com` 查 A 返回 **NXDOMAIN**。两条查询与「记录数为 0」完全吻合——zone 在 CF 手里，只是没有任何记录，按上面 a–c 做。
  - 结论写在前面，别被后面的红字带跑：**这是域名未接通的证据，不是 SEO 缺陷，也不是产物问题。**

  **闸门的前置判定（2026-11-16 加进 `check_urls.py` §5）**：`--online` 先请求一次根地址，遇到三种情况之一就打印**一行**「域名未接通（DNS）→ 中止，后续断言不执行」并 **exit 2**，不再跑后面的断言：① 连不上（DNS 解析失败 / 连接被断）；② 状态码 ≥ 500；③ 响应体前 4KB 含 `error code: 1016`。理由：否则每次跑都得到一串与 DNS 无关的假 FAIL，真正的红灯会淹在里面。**exit 2 与 exit 1 是两个意思**：1 = 断言失败（站有问题），2 = 这一轮没测成（域名没接通）。负向测试过：本地造一个 530 + `error code: 1016` 的假 host，闸门正好打一行、exit 2、零条 FAIL。

  **硬约束：域名返回 5xx / 1016 期间，任何人不得翻 `SITE_LIVE`，也不得把 sitemap 提交到 GSC。** 理由一句：翻开关只是去掉 `noindex`，而这时候站根本打不开，翻了等于把「可被收录」这件事提前预支。
- **404 由产物承担，不由项目设置承担（v1.8）**：`src/pages/404.astro` → `dist/404.html`，CF Pages 对未匹配路径优先用它。这是先手，先证明产物够用，改项目设置（Not Found Handling → `404-page`）是它不生效时才动的第二手，动的时候要贴改前改后。三条约束写死在页面上：**不加 canonical**（这个地址不是页面的地址）、**不加 `<meta name="robots">`**（404 状态本身就是信号，两种信号不叠）、**不进 sitemap**（sitemap 列页面，不列错误态）。页里只放五条回收链接，用的就是 §4.8 那五个锚文本，不另开一套链接规则。
  **实测（2026-11-14，加 404.html 先后只差这一次部署，项目设置一个都没动）**：
  - `/zzz-no-such-page-9f3a/` → **404** + 本站 404 页（改之前是 200 + 首页完整 HTML）；
  - `/zzz.png` → **404**，Content-Type `text/html`。状态码达标，类型不达标——按下面的「已知偏差」结案，不修。
  - `_headers` 对 404 响应同样生效（当时 404 响应上仍带着 `X-Robots-Tag: noindex`；翻开关后 404 也不再带），所以「拿 header 改 404 的类型」这条路技术上通，只是不该走。
  - 所以「改项目设置」这一步**不需要执行**，留着给以后真的出现 200 时用。

  **已知偏差 · 判断为可接受：不存在的 `.png` 返回 404，但 Content-Type 是 `text/html`。**
  - 现状：平台对所有未匹配路径都发同一张 `404.html`，带扩展名也不例外，所以 `/zzz.png` 拿到的是 404 + 一张 HTML 错误页。
  - 判断：**可接受，到此为止。** 爬虫读的那个信号是状态码，它已经是 404；剩下的只是「错误页该标什么类型」。`_headers` 确实对 404 响应生效，技术上能给 `/*.png` 写 `Content-Type: image/png`，但那是**把 HTML 字节标成 PNG**——一个自相矛盾的响应，比「404 + 一张 HTML 错误页」更假。nginx 与 Apache 对自家错误页同样标 `text/html`。
  - 处置：**不修。** 不改 `_headers` 去加 `Content-Type`，不挂成待办，闸门维持 **WARN**（不是 FAIL），也不为了消掉这个 WARN 去改实现或加例外逻辑。
  - 真正的红线是另一件事：图片路径返回 **200** + HTML。闸门对 200 是 FAIL，所以那条永远拦得住；WARN 只描述「错误页的类型」，不影响判定。
  闸门：`check_urls.py` §4 验本地产物（`dist/404.html` 在、五条链接在 `<main>` 里、无 canonical、无 meta robots），§5 只在 `--online` 时验线上真实状态码、Content-Type、以及那五条链接**逐个真发请求确认 200**。§4 做过反向测试（砍一条链接 + 塞一个 canonical → 正好两条 FAIL）；§5 的断言在修好之前的线上响应上真失败过一次，不是摆设。


---

## 4. 页面清单与逐页规格

> Title 与 H1 都含目标词，且不重复同一句话；description 每页手写。

### 4.1 `/` — 主词 `nuke simulator`
- Title: `Nuke Simulator: What a Nuclear Bomb Would Do to Any City`（**不出现 `blast radius`**——那是 `/blast-radius/` 的词）
- H1: `Nuke Simulator — see what a nuclear bomb would do to any city`
- 人口层上线后：title 不变（主词已锁定 `nuke simulator`），只在 description 里加 10 km 人口；标题不跟着功能改，避免每次改版都丢一次相关性。
- Default state（SSR）: New York, 100 kt, air burst → 4 个半径 + 各半径内人口 + 出处。
- 结构：地图（左/上）+ 结果面板（右/下）+ 三句话解释这是什么 + 4 条内链块（blast-radius / nuclear-bomb-map / methodology / 6 个城市）+ FAQ（8 条，FAQPage JSON-LD）+ 一行脚注。
- JS off：地图区替换为静态结果块 + 「See the full table →」指向 `/blast-radius/`。
- 工作量：**8 h**

### 4.2 `/blast-radius/` — `nuclear bomb blast radius`（US 8,100/月）

- Title: `Nuclear Bomb Blast Radius Table: 15 kt, 100 kt, 1 Mt`
- H1: `Nuclear Bomb Blast Radius, with the printed page behind every number`
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
- Title: `Nuclear Bomb Map: Rings on Real Ground at True Scale`（v1.6 去掉 `, 20 Cities`）
- H1: `Nuclear Bomb Map — the rings on the ground, not on a chart`
- 与首页共用 `lib/island.ts` + `panelRows()`，所以同一个组合在两页不可能显示不同的数；但**首页保留 SVG 真比例圆环，不用地图替换**——SVG 关 JS 也看得见，地图看不见，两者不是替代关系。
- 默认视角 = 按该城最大半径自动 fit（16:9 画幅里外圈占短边 40%），不是固定世界 zoom：世界视图看不出任何一圈的相对大小。
- 导航一级项，首页与城市页都链过来。
- **正文不能只有一张图**：一张地图的页面，谷歌判断不了它讲什么。规格固定为：≥ 700 词英文正文、4–6 个 H2、每节 ≥ 100 词（只有下限；超 250 词只 WARN），且**每节必须含具体数字并带印刷页码**（`p. 115` / `p. 101` / `p. 110` 这种）。小节按此顺序：5 psi 是什么口径 / 1 psi 是什么口径 / 火球与热辐射环不是一回事 / 为什么圈不随当量线性增长（立方根律 §3.61 p.101）/ 20 城与人口口径 / 这些数字读不出来的时候（爆高越界 p.110）。`check_site.py` §18 逐节判定。
- **title 里不再出现城市数量**（v1.6）。原来的 `20 Cities` 是拿一个 5 天后到期、而 20 个城市词加起来月搜不到 100 的数字去抵押构建失败，不划算。城市页照做，进度记在 §11。
- 工作量：**4 h**（正文另计 **2 h**）

### 4.4 城市页 × 20 — 规格见 §4.11
- **URL 自 v1.6 起是 `/nuclear-bomb-map/{slug}/`，不是根路径 `/[slug]/`**。§4.11 说明理由（根路径的 `/london/` 抢不过任何站，挂在地图下才有主题归属）。
- Title 模板：`Nuclear Bomb Effects on {City}: 15 kt to 1 Mt`（v1.6 改；原模板 `Nuclear Blast Radius in New York — …` 与 `/blast-radius/` 抢同一批词）。
- 内容三件套：① 15/100/1000 kt × 5 效应距离表（直取 `effects.json`，不重算）；② 10 km 人口与各环内人口（现算，两个数分开，不合并）；③ 一段该城独有的说明（只用该页数字能支撑的话，地名不编）。
- 结构数据：`Dataset`（`BreadcrumbList` 等 20 页齐了再加）。内链：回首页、回 `/blast-radius/`、回 `/nuclear-bomb-map/`、`/methodology/`。
- 20 城：new-york, los-angeles, chicago, houston, san-francisco, washington-dc, miami, seattle, boston, atlanta, london, paris, tokyo, berlin, sydney, toronto, mexico-city, sao-paulo, new-delhi, johannesburg。
- 生成门槛写入脚本：某城若 5 效应 × 3 当量有任一缺值 / 人口缺失 → 该城**不生成页面**（符合你的「凑不出三项不要生成」）。
- 工作量：**10 h**（模板 4 h + 20 篇文案 6 h）

### 4.5 `/nuclear-winter/` — `nuclear winter`（US 9,900/月）
- Title: `Nuclear Winter: What the Published Research Actually Says`
- H1: `Nuclear winter, from the 1983 paper to the 2019 model runs`
- **这是 literature summary，不是本站的计算。** 页面顶部（作者上方，正文第一段之前）必须有一句固定的声明，原文：

  > `These are published model studies, not figures from the 1977 manual. Nothing on this page is our own calculation.`

- **引用清单固定四篇，缺一不可**（四篇都在正文里各占一个引文位置，不是只挂在页脚）：

  | 简称 | 作者 | 出处 | 在页面上的角色 |
  |---|---|---|---|
  | TTAPS 1983 | Turco, Toon, Ackerman, Pollack & Sagan | *Science* **222**, 1283–1292 (1983), doi:10.1126/science.222.4630.1283 | 原始论文：首次给出「核冬天」这个名字与量级 |
  | Robock 2007 | Robock, Oman & Stenchikov | *J. Geophys. Res.* **112**, D13107 (2007), doi:10.1029/2006JD008235 | 现代气候模型复核（50 Tg 与 150 Tg 两档） |
  | Toon 2019 | Toon, Bardeen, Robock, Xia, Kristensen, McKinzie, ... | *Sci. Adv.* **5**, eaay5478 (2019), doi:10.1126/sciadv.aay5478 | 区域核冲突（印巴）情景 |
  | Coupe 2019 | Coupe, Bardeen, Robock & Toon | *J. Geophys. Res. Atmos.* **124** (2019), doi:10.1029/2019JD030509 | 同一情景在 WACCM4 里的复算，与 ModelE 对比 |

  **一处更正（2026-11-14）**：你给的「Robock, Oman & Stenchikov 2007, ACP」实际发在 **JGR Atmospheres**（ACP 2007 年那篇是 Toon 等七人关于区域冲突的论文）。引用按实际出处写，不按记忆写。
- **每条数字后面直接跟 `(作者 年份)`**，不写页码 —— 它不是手册，页码没有意义。例：`... cooling the global surface by 2° to 5°C (Toon 2019).`
- 只有一条规则比格式更重要：**手册数据和气候模型数字绝不进同一张表**。手册能提供的只有第 9 章（残骸辐射与落尘）那部分，单独一节、单独标题、逐条标印刷页 `p. xxx`，并在节内明写它讲的是单次爆炸的局部落尘，不是全球气候。
- 图表：只用**已发表数字**重绘（烟尘量 → 全球平均降温），标注 `redrawn from Toon (2019)`；不做任何新计算、不做插值。
- 内链：`/methodology/`、`/blast-radius/`、`/nuclear-bomb-map/`，锚文本按 §4.8。**反向也要有**（v1.7）：首页、`/blast-radius/`、`/nuclear-bomb-map/`、`/methodology/` 与每个城市页的正文都必须各带一条 `nuclear winter` 指向本页 —— 它上线时全站零入链，只有 sitemap 一条发现路径。闸门 §17 逐页判定，§24 另有通用硬规则：sitemap 里任何 URL 的站内入链 < 2 就构建失败。
- **长度与节数按 §4.10 的查询页硬要求执行**（正文 ≥ 700 词、4–6 个 H2、每节 ≥ 100 词），不是本节的 2,500 词：两个数字冲突时以闸门能判的那一个为准，扩写等 GSC 有曝光之后再做。
- 工作量：**14 h**（含查证）

### 4.6 `/methodology/`
- 手册版本/DOI/镜像；四类数值的取数路径与图号页码；立方根缩放的原文引用与适用边界（手册说「megaton range」以内）；读图误差（对数坐标 ±3–8%，写区间不写单值保证）；**人口口径整节**：WorldPop release 名 / 年份 / 100 m / 查询半径 25 km 及为何必须 ≥ 21.40 km / 一份 catchment 内每个半径各自累计、不做环减环 / API 端点与抓取日期 / **API 的 R2025A 与可下载 2020 GeoTIFF 在同一城市同一半径上差 6.5%（巴黎 3.22 km：780,593 vs 831,462）**；GeoNames 版本；**「本站没有算什么」清单**（10 条：不做伤亡估计、不做实时人流、不做落尘足迹、不做 3D、不做自由当量滑杆外推、不做地下/水下/高空爆炸、不做多弹头、不做地形遮蔽、不做建筑结构响应、不做辐射剂量）。
- 这一节不许出现「人口还没有发布」这类会过期的句子：城市页一上线，它就是假话。闸门 §23 逐条钉住（`100 m` 与 `1 km grid` 互斥、`10 km` 必带 `25 km`、两个实测数字与 6.5% 必须在场）。
- 含 `data-ledger` 的可读版本（抽查状态表）。
- 工作量：**5 h**

### 4.7 `/about/` `/privacy/`
- about：谁做的、为什么做、数据从哪来、怎么纠错（给一个邮箱，用现有 Agent Mail 或普通邮箱）。
- privacy：无账号、无 cookie、无追踪（GA4/Clarity 先不加，v1 保持 zero-tracking，这也省掉一类合规问题）、CDN 日志说明、外链。
- 工作量：**2 h**

### 4.8 内链契约（四页闭环）

新站没有外链权重，四页之间的内链是爬虫唯一的路径，也是唯一能分配权重的杠杆。所以锚文本写死，不做「多样化」，也不许出现 `click here` / `learn more`：

| 目标 | 唯一允许的锚文本 |
|---|---|
| `/blast-radius/` | `nuclear bomb blast radius` |
| `/nuclear-bomb-map/` | `nuclear bomb map` |
| `/` | `nuke simulator` |
| `/methodology/` | `where these numbers come from` |
| `/nuclear-winter/` | `nuclear winter` |

- **v1.7：这张表从四行变五行。** `/nuclear-winter/` 上线时全站零入链，9,900 月搜的页面只有 sitemap 一条发现路径 —— 那是当时最贵的洞。四个核心页各补一段正文链过去（首页「Where the numbers come from」、`/blast-radius/` 的 "What this table is not"、地图页的 "Where these numbers stop being readable"、`/methodology/` 的 "What this site does not compute"），五个城市页的 "What this page does not say" 各补一句。
- 每页正文出链**恰好覆盖其余四页**，入链 ≥ 2；全部是普通 `<a href>`，无 `rel=nofollow`、无 JS 跳转。
- 每条内链必须落在正文段落 `<p>` 或列表项 `<li>` 里，不许塞页脚、不许只挂在导航上。导航栏保留（那是 UX，不是内链策略），断言只统计 `<main>` 内的正文链接。
- `check_site.py` §17 逐条判定：锚文本、目标集合、段落位置、入链数。锚文本改了就是契约破了，构建失败。
- **§24 是这条规则的一般化版本**（v1.7）：sitemap 里的**每一个** URL 都必须有 ≥ 2 条来自其它页面 `<main>` 的入链，否则构建失败。它按 `dist` 里真实构建出来的页面统计，所以以后每加一页都自动套用，不是只保 `/nuclear-winter/` 这一次；导航和页脚不计入，否则随便哪页都能靠站头混到两条。
- **城市页是叶子，只汇入不参与闭环**：每页至少 3 条回核心页，且必须同时命中 `/blast-radius/` 与 `/nuclear-bomb-map/`（锚文本沿用上表）；地图页反过来链到已发布的城市页，锚文本由页面自己写，但闸门禁止 `click here` / `learn more` 一类空锚文本。四页闭环本身不受城市页数量影响。
- **城市页之间：只连一层，锚文本只有一种写法。** 指向任何城市页的链接，锚文本一律是 `nuclear bomb effects on {City}`（大小写不敏感，闸门逐条比对）；不许多起一套说法。地图页正文链**全部**已发布城市页（未发布的 15 城保持纯文本、不加链接），每个城市页底部再链**其余四个**兄弟页，位置在 `<main>` 里、不进页脚。闸门：每页入链 ≥4（地图页 1 + 兄弟 4，实际 5）；每个城市页到其它城市页的出链恰好 = 已发布城市数 − 1。**明确不做**：城市页互链超过一层、按大洲分组、20 城先铺链接。

### 4.9 承诺台账（title 里的数字必须有到期日）

凡是在 title / H1 里写了一个**尚未交付的数量**，必须在下面这块里登记一行，带到期日与机器可判的兑现条件。`check_site.py` §19 每次构建都读它：到期未兑现即失败；title 里出现 `N Cities` 但台账里没有对应行，同样失败。

<!-- PROMISE-LEDGER
# id | 承诺原文 | 出现位置 | 到期日 | 兑现判据（dist:<glob>>=<N>）
-->

- **2026-11-13 撤回 `map-cities` 那一行**：`/nuclear-bomb-map/` 的 title 不再写 `, 20 Cities`，改成 `Nuclear Bomb Map: Rings on Real Ground at True Scale`。理由不是做不完，是这笔抵押不划算 —— 20 个城市词加起来月搜不到 100，却拿一次构建失败去担保。城市页照 §4.11 做满 20 个，进度记在 §11，不挂在 title 上。
- **台账现在是空的，这是刻意的**：空台账 + 断言里那条「title 有数量就必须有行」= 现在任何页面都不许拿未交付的数量做标题。要重新加承诺，先加行、先写到期日。
- 不允许「先写上、以后再补」的第二种写法：要么有到期日，要么不写数量。
- **2026-11-14 城市页改分批上线：先 5 个（New York 已在 + Los Angeles / London / Tokyo / Paris），其余 15 个等信号。** 理由不是工作量，是这批页面的定位：城市词月搜在个位到二十几，20 页负责的是覆盖和内链，不负责流量。一次铺满换不来流量，只会让「哪一页值得改」变得不可判断。`PUBLISHED_CITY_SLUGS` 是唯一开关，加城仍然是一行。
- **城市页停手条件（不是「待定」，是判定式）**：现五页 description 的前 68 个字符完全相同、title 只差城市名 —— 五页还能算「同一套东西的五个实例」，二十页就是批量页了。所以：
  - **D0** = 这五页进 sitemap、GSC 提交完成的那天。
  - **加第 6 页的唯一条件**：D0 + 28 天内，GSC「网页」报告里这五页**至少一页有 ≥1 次展示**（impressions > 0，不看点击、不看排名）。
  - **零展示则停手**：D0 + 28 天仍全为 0 → 不加第 6 页；改这五页的 title 与首段（每页各改一次），再等 28 天。两轮仍为 0 → 城市页冻结在 5 个，工时转去 §4.10 的查询页。
  - **有展示则按页加，不按批加**：只加「已有展示那一类城市」的下一城，一次 +1 页，加完等 28 天；一次上三页以上即视为批量页，回到本条第一句。
  - 这条写在这里而不是 §11：它是一个**停止条件**（什么情况下不做），不是一个进度。

### 4.10 首月页面清单：53 页（80 页与「约 40 个灾害页」作废）

按美国月搜逐词核过 49 个词，能**诚实交付**（手册里有对应内容）且**真有人搜**的只有 13 个查询页。首月构成固定为：

| 类型 | 页数 | 说明 |
|---|---|---|
| 核心页 | 8 | `/`、`/blast-radius/`、`/nuclear-bomb-map/`、`/methodology/`、`/about/`、`/privacy/`、404、sitemap |
| 城市页 | 20 | §4.11，`/nuclear-bomb-map/{slug}/` |
| 武器 / 历史 | 12 | 第 1 章与第 6 章能撑住的条目（原子弹、氢弹、中子弹、当量谱系、试验史等），逐条按词条做事，不拼凑 |
| 查询页 | 13 | 下表 |
| **合计** | **53** | |

**13 个查询页（主词 | 美国月搜 | 数据来源）**

| URL | 主词 | 月搜 | 数据来源 |
|---|---|---|---|
| `/nuclear-winter/` | nuclear winter | 9,900 | **手册没有核冬天模型，本页不许用手册算**，见下方专门条款 |
| `/neutron-bomb/` | neutron bomb | 8,100 | 第 1 章 |
| `/hydrogen-bomb-vs-atomic-bomb/` | hydrogen bomb vs atomic bomb | 8,100 | 第 1 章 |
| `/fallout-map/` | fallout map | 4,400 | 第 9 章 |
| `/tsar-bomba/` | tsar bomba blast radius | 2,400 | Fig. 3.73c p.115（50 Mt 按 §3.61 立方根缩放，带固定标签） |
| `/thermal-radiation/` | thermal radiation | 1,900 | 第 7 章，Fig. 7.42 p.291 |
| `/hiroshima/` | hiroshima bomb radius | 1,600 | Fig. 3.73c p.115（15 kt，直读） |
| `/how-to-survive-a-nuclear-blast/` | how to survive a nuclear blast | 1,300 | 第 12 章 |
| `/overpressure/` | overpressure | 1,000 | 第 3 章 |
| `/nuclear-strike-map/` | nuclear strike map | 720 | 地图 + 城市页复用，不新造数据 |
| `/nuclear-weapon-effects/` | nuclear weapon effects | 720 | 全手册总览，做内链枢纽 |
| `/blast-wave/` | blast wave | 590 | 第 3 章 |
| `/nuclear-bomb-crater/` | nuclear bomb crater | 480 | 第 6 章 |

**每页硬要求（`check_site.py` §20 逐页判定，页一上线就生效）**

1. ≥700 词英文正文。
2. 4–6 个 `<h2>` 小节。
3. 每节至少一个具体数字，且带印刷页码（`p.NNN`）。
4. 正文里 ≥3 条内链，锚文本只用 §4.8 那五条，且必须命中 `/blast-radius/` 与 `/nuclear-bomb-map/`。
5. 每节 ≥100 词，不堆关键词。**只有下限，没有上限**；单节超 250 词时闸门只打 WARN（提示该拆节），不失败 —— 为了守一个字数删掉有用的事实是本末倒置（v1.7，2026-11-14 改）。

**`/nuclear-winter/` 的专门条款（唯一一页不用手册数据）**

- 手册（1977）**不含核冬天气候模型**，本页不得用手册的任何公式或图表推算温降、烟尘量、减产幅度。
- 只用已发表研究，逐个给「作者 + 期刊 + 年份 + 图/表号或页码/DOI」：TTAPS（Turco et al., *Science*, 1983）作为原始结论来源；Robock, Oman & Stenchikov（*JGR Atmospheres*, 2007）作为现代模式结果来源。**只引述它们自己发表过的数字**，不做任何插值、不做单位换算之外的加工。
- 页面顶部一句明写：本页数字来自上述文献，**不是**本站从手册算出来的；与站点其余部分的数据口径不同。
- 若某个数字找不到可公开核对的出处，就不写，不拿「据说」凑。

**明令不做**（实时数据地图，需接实时源，与本站主题不符）：hurricane tracker / wildfire map / lightning strike map / tornado map / flood map / earthquake map。**不许为了凑页数写没有对应词条的页面。**

### 4.11 城市页规格（20 页，模板一次成型）

- **URL**：`/nuclear-bomb-map/{slug}/`，挂在被它解读的那张地图下面，而不是根路径 `/{slug}/`。理由：根路径的 `/london/`、`/paris/` 是全世界都在抢的词，一个新站拿一页去碰它没有任何胜算；挂在地图下面既有主题归属，也让地图页成为真实的枢纽。slug 沿用 GeoNames 的写法（`new-york`、`sao-paulo`、`new-delhi`、`washington-dc`）。生成物由 `src/lib/cities.ts` 的 `PUBLISHED_CITY_SLUGS` 控制，sitemap 与路由读同一份清单 —— 不在清单里的城市不会出现在 sitemap，也不会生成页面。
- **title 模板**：`Nuclear Bomb Effects on {City}: 15 kt to 1 Mt`。不写 `15 kt, 100 kt, 1 Mt`，那串词与 `/blast-radius/` 的 title 有 6 词重合；城市名承担唯一性。闸门另断言：城市页 title 必须含城市名、彼此不重复、与四个核心页的最长共同词串 ≤3。
- **description 模板**：`What 15 kt, 100 kt and 1 Mt air bursts reach over {City}: 5 psi to {x} km, 1 psi to {y} km, and {N} people inside the 5 psi ring.` —— 数字全部来自数据，不手写。
- **H1**：`Nuclear Bomb Effects on {City} — 15 kt, 100 kt and 1 Mt`。
- **三项数据，来源必须分开写**：

| 项 | 内容 | 来源 | 直取还是现算 |
|---|---|---|---|
| 1 | 15 / 100 / 1000 kt × 5 种效应的距离 | `src/data/effects.json`（`get()` 查表） | **直取**，与 `/blast-radius/` 同一份 JSON，不重算、不四舍五入 |
| 2 | 城市人口（10 km 圆内） | `src/data/city-pop.json`，由 `scripts/build_city_pop.py` 调 WorldPop API 生成 | **现算**（抓数一次、结果入库缓存，构建时只查表） |
| 3 | 5 psi / 1 psi / 火球 / 两档热辐射环内人口 | 同上，同一 catchment 换半径 | **现算**，且**不由大环减小环**、**不拿城市人口减环内人口当存活数** |

- **查询半径：`catchRadiusKm = 25 km`，每城一条记录都带这个字段。** 最大环是 1 Mt 的 1 psi（21.40 km），10 km 的圆装不下它 —— 用 10 km 抓的话，标题写「1 psi 环内人口」而数字其实来自被截断的 10 km 圆，这是本页最不能犯的错。两处断言：抓数脚本在 `CATCH_RADIUS_KM < 最大环` 时拒绝写入；`city-pop.ts` 在构建期算出 `MAX_RING_KM`，任何城市 `catchRadiusKm < MAX_RING_KM` 直接抛错。
- **人口口径句同时写两个半径**（`populationSentence()` 生成，模板里不许手写）：`{N} people live within 10 km of {lat}, {lon} (rings up to 21.4 km counted from the same 25 km catchment) — the GeoNames point for {City} — counted on the WorldPop Global2 R2025A 100 m grid, 2020 estimates, not inside a city boundary.`
- **地标（每页 2–3 个，纯模板页不接受）**：`src/data/city-places.json` ← `scripts/fetch_city_places.py` ← GeoNames 国家级 dump（CC BY 4.0）。五个已发布城市是人工选的、再回 dump 里按名字核对的（`CURATED`），因为「离得最近的公园」这种自动选法会选到邮局网点；其余城市走自动选点（公园 / 水域 / 街区各取一个，距离错开）。页面按 `effects.json` 现算每个地标落在 100 kt 的哪个环里。

- **人口口径句（写死在页面上，原文）**：

  > `{N} people live within 10 km of {lat}, {lon} (rings up to 21.4 km counted from the same 25 km catchment) — the GeoNames point for {City} — counted on the WorldPop Global2 R2025A 100 m grid, 2020 estimates, not inside a city boundary.`

  这句话由 `src/lib/city-pop.ts` 的 `populationSentence()` 生成，数字、坐标、两个半径、数据集名、年份全部来自数据文件，页面模板里不许手写，防止文案和数据各说各话。
  **D4 的分辨率已改判（2026-11-14）：用 100 m，不退 1 km。** 这是对原计划的**改进**，不是妥协：1 km 是原计划自己下载栅格再求和时的分辨率，实际用的是 WorldPop 服务在**原生 100 m** 栅格上做面积分，任何人都能复算；退回 1 km 反而是拿精度去换一个已经不需要的本地管线。页面与 `city-pop.json` 的 `source.note` 都写着 100 m。
- **城市页不做地爆、不做热辐射地爆**：Fig. 7.42 是空爆图（§7.41 p.290 另有路径），所以城市页统一按空爆给数，页面写一句「air burst」。
- **上线节奏**：先发 5 页（`new-york`、`los-angeles`、`london`、`tokyo`、`paris`），看 GSC 曝光再决定剩下 15 个 —— 加不加、怎么加的判定式写在 §4.9「城市页停手条件」，那里是唯一真值。每页必须带 2–3 个该城独有的 GeoNames 地名（见上），且每个地名要写明它落在 100 kt 的哪个环里。已发布城市之间按 §4.8 连一层：地图页链全部五页，每页链其余四页，锚文本一律 `nuclear bomb effects on {City}`。

---

## 5. SEO 落地清单（逐条可勾）

- [ ] 全站静态；JS off 下每页数字/文案/内链都在 HTML（用 `astro build` 后 grep 校验，写进 CI）
- [ ] 首页 SSR 默认值（New York · 100 kt）
- [ ] 一页一词；Title ≠ H1 且都含目标词
- [ ] description 逐页手写
- [ ] og:image **必须是构建期生成的 PNG，尺寸实测 1200×630**（Pillow 打开量，不看文件名）；**SVG 一律不允许**；`og:title` 与 `title` 同源；绝对 URL；`og:image:width/height` 显式写出
- [ ] title / description / H1 不得出现页面上还没有的功能词（当前：`population` 在人口层上线前禁用）
- [ ] JSON-LD：首页 + 各 FAQ 区 `FAQPage`；城市页 `BreadcrumbList`；`/blast-radius/` 加 `Dataset`（可选）
- [x] JSON-LD 的日期（v1.7，`check_site.py` §25）：页面级 `datePublished` 一律取 `site.ts` 的 `SITE_PUBLISHED`（真实发布日 2026-11-13），**手册的 1977 只允许出现在 `isBasedOn` 的 `Book` 节点上**。把 1977 当页面发布日，等于告诉搜索引擎这一页 1977 年就在网上。
- [ ] canonical 全部指向 `https://apocalab.com/...`（构建时断言不含 `vercel.app` / `pages.dev`）
- [ ] `sitemap.xml`（`@astrojs/sitemap`，自动含 20 城）
- [ ] `robots.txt` 指 sitemap
- [x] 内链四页闭环：出链覆盖其余三页、入链 ≥2、锚文本锁死（§4.8，`check_site.py` §17）
- [x] 收录开关按分支条件生成：生产无 `noindex`、预览必带（§3.7，`check_site.py` §16）
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
| **6 内容与法务 + 查询页** | nuclear-winter 2500 词、methodology 定稿、about、privacy、武器页 12、**查询页 13**（§4.10） | 18 h | 引用可点、无自算数字；每页 700 词 / 4–6 H2 / 每节带页码（§20 断言） |
| **7 收口** | sitemap/robots/canonical 断言、Lighthouse、OG 全量核查 | 6 h | 第 5 节清单全绿 |
| — | **阶段二**（12 当量页，等你确认） | 8 h | 复用同套数据与模板 |

总量回到 **70–85 h**，与 v1.0 一致。城市页固定 20 个，不为它追加任何工时。

### 6.1 首月 53 页怎么堆（v1.6：80 页作废）

**先分清两个数**：53 是**首月总页量**，城市页是其中的 **20 页**，不多不少。v1.6 把余量页从「约 40」砍到「13」，因为按美国月搜逐词核过 49 个词后，能诚实交付又真有人搜的只有 13 个（清单与月搜见 §4.10）。

| 组成 | 页数 | 说明 |
|---|---|---|
| 核心页 | 8 | `/`、`/blast-radius/`、`/nuclear-bomb-map/`、`/methodology/`、`/about/`、`/privacy/`、404、sitemap |
| 城市页 | 20 | §4.11，`/nuclear-bomb-map/{slug}/` |
| 武器/历史弹页 | 12 | 第 1 章与第 6 章能撑住的条目 |
| 查询页 | 13 | §4.10 的表，逐条带数据来源 |
| **合计** | **53** | |

**页量来源**：靠有独立搜索量的页面类型补齐，不靠加城市。**不为了凑页数写没有对应词条的页面。**

**城市页的定位**：不负责流量，负责覆盖与内链。它们把「半径数字」落到地理实体上，给核心页提供锚文本入口，同时让站点在地名类长尾里有落点。

**验收标准（不变）**：每页必须同时具备三项——① 三档当量（15 / 100 / 1000 kt）的效应数值（直取 `effects.json`）；② 城市中心 10 km 内的背景人口（WorldPop，写明年份、版本、栅格分辨率）；③ 环内人口（现算，与②分开）。缺任一项 → 该城不生成页面。

**不为城市页追加任何额外工时**：20 页的模板 + 生成门槛 + 文案已含在阶段 5 的 10 h 里。这 20 页只在收录信号确认后按需微调，不设扩张阶段。

一个仍然成立的判断：**不一次铺满 53 页**。信号顺序是收录 → 外链 → 页量 → 排名，页量排在收录后面。核心 8 页 + 20 城市页先上线，看收录，再补 13 个查询页。

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
| R7 | 人口栅格覆盖范围 | 首页选点 | 任意点没有本地栅格可求和 | **已改口径**：不下载栅格，改由 WorldPop 服务在 100 m 原生栅格上积分（§2.5）；页面只发布 20 个预置城市，任意点人口不提供，也不外推 |
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

三条调整同样已落地：`/blast-radius/` 提前到地图之前（6）；关掉地图旋转与俯仰（3.2）；城市页固定 20 个、首月 53 页靠页面类型补齐（6.1）；全站禁 demo 类字样 + 免责恰一行（1）。

**仍待你后续定的两件**（v1.6：查询页清单你已给定 13 个，此项关闭）：阶段二 12 当量页做不做（+8 h）；`/nuclear-bomb-map/` 与首页要不要合并（当前分开，因为两个词各自有量，合并会牺牲其中一个的标题口径）。

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

---

## 12. Pro 与差异化：上线后第 2~3 个月

**这一节是待办，不是待议。** 三条判断已经定了，上线前不实现，实现时不再重新讨论。它与 §3.7 并列而不合并：§3.7 管「怎么上线」，这一节管「上线之后第 2~3 个月做什么」。

### 12.1 免费层一个字都不锁

免费层保留**全部** 2D 模拟器功能。锁掉主功能等于放弃 `nuke simulator`（月搜 12,100）和 `nuclear bomb simulator`（9,900）这两个主词，而这两个词是整个站的排名来源。

### 12.2 付费层只卖一样东西：一次性完整报告

可下载的环图（PNG/SVG）+ 数据表（CSV）。定价参照竞品 Pro：**$5/周、$10/月、$20/季**。**不新增别的套餐形态**——没有终身版、没有团队版、没有点数包。

### 12.3 三样差异化：风场、24 小时落尘、环内人口

这三样是 Pro 的卖点，**前提是先进免费层第一屏**：首页与 `/nuclear-bomb-map/` 上可见、一键可开。摆在代码里不给用户看，等于没有差异化。

### 12.4 上线后第一个产品任务（排在 Pro 之前）

**导出环图为 PNG，图上带 `apocalab.com` 水印。** 这是零成本外链来源，一张能被转发的图就是一条社媒引荐。顺序上它排在 Pro 之前：先有可被转发的产物，再谈让人为一份报告付钱。

---

## 13. 上线前不要做

四项，任一项都不在上线前的范围内：

1. 登录注册
2. 支付集成
3. 任何 analytics 或第三方脚本
4. 把任何现有功能锁进付费墙

理由：这些都会推迟上线；站还没有免费流量之前，任何转化率优化都无从谈起。

---

## 14. 交互差距（上线后第一批）

**来源是线上实测（2026-11-16），不是推断。** 三条事实都可以当场复现，复现方式写在每条后面。排序已定，实现时不再重新讨论；它与 §3.7 并列而不合并：§3.7 管「怎么上线」，这一节管「上线后第一批补什么」。

### 14.1 地图页的交互面：20 × 3 × 2

`/nuclear-bomb-map/` 的状态空间就是 **20 个城市 × 3 档当量（15 / 100 / 1,000 kt）× 2 档爆高（空爆 / 地爆）= 120 种**，到此为止，再多一种都选不出来。
视角是锁死的：源码里 `dragRotate`、`touchPitch`、`pitchWithRotate` 全为 `false`，`maxPitch` 为 `0`，即**北向上、正射平面**——不能旋转、不能俯仰，没有 3D。
复现：`src/data/cities.json` 20 条；`src/data/effects.json` 的当量集合 `{15, 100, 1000}`、爆高集合 `{air, ground}`；`src/scripts/bomb-map.ts` 的四个相机开关。

### 14.2 首页的 query 参数，服务端不消费

`/?city=…&yield=…&burst=…` 交给服务端等于没交。实测 `/` 与 `/?city=chicago&yield=1000&burst=ground` 的响应**字节数完全相同（34,877 B）**，服务端渲染出来的默认状态都是 `New York · 100 kt Air burst`。
所以首页的一切切换**只发生在 island 脚本里**；关掉 JS，全站只有一个状态：纽约 / 100 kt / 空爆。爬虫与关 JS 的访客看到的也是这一个。

### 14.3 竞品的交互面，与 3D 的成本决策（两句写死）

`nukesimulation.com` 首页文案是「Search any city」，交互是 3D 自由 orbit / pan / zoom，外加 fallout 与 estimated casualties；照片级 3D 瓦片放在它的 Pro 项里。

「3D 等订阅覆盖成本」这句话作废，拆成下面两句写死，实现时不再讨论：

- **a. 3D 球体进第一版，不等收入。** 投影切球体 + 自由 orbit / pan / zoom + 俯仰，用开源 MapLibre GL（BSD-3-Clause，免费、无按请求计费）配免费地形数据（实现时定源，条件只有两条：无 API key、无按请求计费）。这不算新增依赖——`/nuclear-bomb-map/` 现在就是动态 `import()` 的 MapLibre；§3.2 那四个相机开关只约束 2D 视图，3D 是第二个视图，自带一套相机参数。理由：竞品把 3D 球体免费给所有人，我们锁着相机等于白送一个零成本能力。
- **b. 照片级建筑瓦片按请求向谷歌计费，等累计收入覆盖累计支出后再开，位置对应竞品的 Pro。** 这条与 §3.3 的「不用 Google、不用任何 API key 服务」是一处**显式例外**，例外只在 b 真被开启那一天生效：开启时必须同批改掉 §3.3 的禁止清单，并写明开启当日的累计收入与累计支出。在那之前 §3.3 一字不让，`_headers` 与 CSP 也不提前放行。
- **3D 是叠在现有真比例圆环之上的第二个视图，不是替换。** 服务端直出的 SVG 环图 + 五个距离（`ResultPanel`，关 JS 仍然在）与地图页自绘的半径圈必须保留，任何情况下不替换；3D 加载失败、被屏蔽、关 JS 时，页面给出的答案仍然是那张 SVG 和那五个数。

**与 §14.4 的排序不冲突，别合并读**：排序量的是「对 `nuke simulator` 这个词的期待的影响」，3D 仍在第 5 位；a 去掉的是**收入门控**，不是排队位置。门控与排队是两件事。

### 14.4 差距排序（按「影响 `nuke simulator` 这个词的期待」排）

1. **任意城市**（现在 20 个）
2. **当量连续可调**（现在 3 档）
3. **地图点击落点**（现在只能选城市，不能点地图定爆心）
4. **环扩散动画**
5. **3D**

排序的判断依据一句话：首页 H1 现在承诺的是「see what a nuclear bomb would do to any city」，而可选城市只有 20 个——**承诺由 H1 说，兑现只有 20 个城市**。第 1 项就是这中间的缺口，所以它排在最前，并且已经在 §3.7 里被写成 ⑤ 的前置闸门：这一项不上线，不翻 `SITE_LIVE`。第 2 至 5 项只影响停留与复访，不拦上线。

**里程碑合并（不改上面顺序）：** 第 1 项「任意城市搜索框」与第 3 项「地图点击落点」放进**同一个里程碑**。两者产出的都只是一个坐标，之后走同一条查表路径，分开做等于把同一段逻辑写两遍、把用例 c 再验一遍。合并的是实现批次，不是排序位置：1 仍排在 3 前面，§3.7 那道闸门仍只认 1 的自测通过。

### 14.5 任意城市 · 验收用例

**这六条是「自测通过」的唯一判据，而且必须先把实际输出贴进本节，才允许把「任意城市搜索」标成通过。** 合并代码、构建通过、本地点了两下没问题，三者都不能代替这一步。
全部用默认状态跑：**100 kt / 空爆**，因为 20 城预设页现在就是这个状态，用来对照最直接。

**用例 a · 输入 Denver 能出环**

- 步骤：打开 `/` 的搜索框 → 输入 `Denver` → 选中结果（或回车）。
- 期望：画出 Denver 的环；环数、颜色、图例与 100 kt 空爆的预设完全一致；页面状态从 New York 变成 Denver。
- 判定：原来显示 `New York` 的那个位置显示 `Denver`。不是页头标题、不是搜索框里的输入值，而是**状态区**那一处。

**用例 b · 环心坐标是 Denver 自己的**

- 步骤：读页面上那行爆心坐标（当前格式 `ring centre 40.7143° N, 74.0060° W`）。
- 期望：**Denver 自己的坐标**（约 `39.74° N, 104.98° W`，以 GeoNames `cities15000` 分片里 `denver` 那条为唯一真值），**不是 `40.7143 / 74.0060`**。
- 判定：与分片里的 `lat` / `lon` **逐位一致**，不许四舍五入到小数点后两位再比，也不许拿第三方百科的坐标替换——分片说什么就是什么，错了改分片、不改页面。

**用例 c · 格式与数值与 20 城预设同构**

- 步骤：同一 yield/burst 下，分别记下 Denver 与 New York 的五个距离。
- 期望：输出与预设同构 —— **五个距离 + burst height + 出处（figure 与 printed page 各一项）**，一项不缺。100 kt / 空爆时的确定值是：

  | 项 | 值 | 出处 |
  |---|---|---|
  | 火球半径 | 0.21 km（694 ft） | 式 (2.127.1)，p.70 |
  | 5 psi | 3.22 km（10,561 ft） | Fig. 3.73c，p.115（§3.61 立方根缩放） |
  | 1 psi | 9.93 km（32,584 ft） | Fig. 3.73c，p.115（同法） |
  | 二度烧伤 | 6.99 km | Fig. 7.42，p.291（直读，不缩放） |
  | 三度烧伤 | 4.02 km | Fig. 7.42，p.291（直读，不缩放） |

  burst height 一项直接取 `effects.json` 的 `hob_ft` / `hob_m`（100 kt 空爆的爆压行是 4,723 ft / 1,439 m），**不重算、不换算、不为整齐改写**。热辐射行的爆高按 Fig. 7.42 自己的口径（1,262 ft），两张图不同源，要各自照排。
- **并且 Denver 的这五个数必须与 New York 逐字相同** —— 理由一句话：环距不依赖城市，同一个 yield/burst 查同一张表，结果就该一样。**第一版不做海拔修正**（Denver 在 1,600 m 上，手册的图是海平面口径；这一版不为此另开计算路径，见 §14.6 第二句），所以「逐字相同」在这里是**要求**，不是巧合。
- 判定：逐字 diff，不是「看起来差不多」。若出现任何一位不同，说明有城市相关的量被混进了半径计算，用例不通过。

**用例 d · 零命中时不许静默回退**

- 步骤：在同一个搜索框里输入一个不在名录里的字符串（`zzzzqqqq`），回车。
- 期望：搜索区出现明确提示 **`not in the gazetteer`**（一句话说明它不在这两万多个地名里，换个写法再试）；**页面其余部分保持原状** —— 环还是进入搜索前那个城市与 yield 的环，标题、五个距离、出处页码一位不变，页头没有变成 `zzzzqqqq`，也没有变成某个「最相近」的城市。
- 判定：提示出现 + 其余不变，两条都要。**禁止静默回退到 New York**，也禁止把输入硬塞进标题或环心（那会产出一个假城市的坐标）。理由一句话：静默回退正是「H1 承诺 any city、兑现只有 20 城」的成因，搜索上线后要把它填掉，不是换个位置再挖一次。
- 补充：`zzzzqqqq` 只是「一定零命中」的样本。另一种零命中是真实存在但不在名录里的地名（小村镇），两种必须走同一条提示——不许一种给提示、一种静默。

**用例 e · 重名城市必须给候选，且标出 admin1**

- 步骤：输入 `Springfield`（必定命中多个同名地名），回车。
- 期望：按人口降序列出**前 5 个候选**，每一条都带 **admin1（州/省）与国家**。这份名录里 `asciiname` **以 `Springfield` 开头的共 10 条**（前缀口径比「恰好同名」多出 `Springfield Gardens` NY 30,515 与 `Springfield Lakes` AU 15,081 两条），前 5 条固定为：

  | # | 城市 | admin1 | 国家 | 人口 |
  |---|---|---|---|---|
  | 1 | Springfield | MO | US | 170,188 |
  | 2 | Springfield | MA | US | 154,341 |
  | 3 | Springfield | IL | US | 114,394 |
  | 4 | Springfield | OR | US | 60,870 |
  | 5 | Springfield | OH | US | 59,680 |

  （第 6 条 `Springfield Gardens` NY 30,515，7–9 是 VA 30,484 / PA 23,363 / TN 16,808，第 10 条 `Springfield Lakes` AU 15,081。列表最多显示 8 条，所以 VA、PA 会出现在列表末尾，TN 与 Lakes 不显示——**这是显示上限，不是「不该存在」**；原来的「共 8 条」是精确同名口径，前缀口径下已改成 10 条，见下面实测记录。）
- 状态区：显示「城市名 + admin1」，例如选中第 3 条时必须是 **`Springfield, IL`**，不是光秃秃的 `Springfield`。**注意别把例子当默认值**：若实现成「默认选中人口最大的」，第 1 条是 MO，状态区就该是 `Springfield, MO`；例子里的 IL 是「选中 IL 那一条」的结果，不是自动选中的结果。
- 判定：命中两个及以上同名地名却不给候选列表 = 失败；静默取人口最大的那个、且状态区不显示 admin1 = 失败。两条任一触发即不通过。
- 理由一句话：同名是这份数据的常态（`Springfield` 一国之内就 8 个），不标 admin1 等于给出一个错误答案。

**用例 f · 非 ASCII 名字必须靠 `asciiname` 才够得着**

- 步骤：输入 `Lodz`（不输入变音符），回车。
- 期望：候选里出现 **`Łódź`**——显示的是 `name`，匹配的是 `asciiname`；状态区 `Łódź, 74`，环心 `51.7706° N, 19.4739° E`。
- 判定：候选里没有 `Łódź` = 失败（说明分桶键取了 `name`，`Ł` 落进 `other`，英文用户永远搜不到）；命中了但显示成 `Lodz` = 失败（要显示 `name`，不是把 ASCII 化后的名字当正文）。
- 理由一句话：`name` 里有 `Łódź` / `Ålesund` 这类非 ASCII 首字母，按 `name` 分桶就是按键盘分桶。

**贴进本节的格式（六条用例都要）**：实际输出原文 + 时间 + 跑的是线上还是本地 + 用的 yield/burst，这四项信息缺一不可。没有这四项的记录不算跑过。

### 14.5.1 实测记录：a–f 六条（2026-11-16 04:53 CST，本地）

- **环境**：`http://127.0.0.1:4322` 的 `dist/` 产物（`astro build` 后未部署），Chromium 157 headless，`node scripts/verify_search.mjs http://127.0.0.1:4322`。
- **线上复跑（2026-11-16 05:02 CST）**：同一脚本对 `https://apocalab.pages.dev` 再跑一遍，六条与三条硬约束的输出**逐项一致**（`Denver, CO` / `39.7392° N, 104.9847° W` / `Łódź, 74` / `not in the gazetteer` / 屏蔽分片后仍是 `New York` + 5 环）；分片以 `application/json` 200 返回，`/data/cities/l.json` 108,974 字节 = 构建产物字节数。
- **线上这一跑抓到过一个本地没暴露的缺陷**：换查询时分片还在飞，上一轮的候选列表仍挂在屏上，用例 f 因此读到的是 Springfield。已修（新查询先把列表清空），修完重跑本地与线上都全绿——这条留着，说明「本地全绿」不等于通过，§3.7 的闸门必须对线上跑。
- **设置**：100 kt / 空爆（默认态），脚本逐条断言，原始输出落盘在同目录 `search-gate.json`。
- **读法**：`head` 是状态区（面板标题），`coords` 是环心那行，`km` 是五个距离，`status` 是搜索框下面那行。

| 用例 | 实际输出（原文） | 判定 |
|---|---|---|
| 起点 | `head: New York`；`coords: 40.7143° N, 74.0060° W`；未输入前分片请求 **0** 次、`fetches: 0` | 通过 |
| a 输入 Denver | `head: Denver, CO`；`status: Ring centre set to Denver (CO · US).`；环 **5** 条、无隐藏 | **通过** |
| b 环心坐标 | `coords: 39.7392° N, 104.9847° W` = 分片 `d.json` 里 Denver 的 `lat 39.73915 / lon -104.9847` 按 4 位小数格式化后的值，逐位一致 | **通过** |
| c 与预设同构 | `km: 0.21 / 3.22 / 9.93 / 6.99 / 4.02`；`hob: printed equation · no burst height input` / `burst height 4,723 ft` / `burst height 7,311 ft` / `1,262 ft · 200·W^0.4 (§7.42)` ×2；五行 `src` 全带印刷页码；`identical_rows: true`、`identical_rings: true` | **通过** |
| d 零命中 | `status: “zzzzqqqq” is not in the gazetteer.`；`head: Denver, CO`、`coords: 39.7392° N, 104.9847° W`、五行读数与 a 完全相同（`state: miss`） | **通过** |
| e 重名候选 | `count: 10`；`shown` 前 5 = `Springfield MO` / `MA` / `IL` / `OR` / `OH`，第 6 `Springfield Gardens NY`、第 7 `VA`、第 8 `PA`；默认 `head: Springfield, MO`；点第 3 条后 `head: Springfield, IL`、`status: Ring centre set to Springfield, IL.` | **通过**（条数由 8 改为 10，见用例 e 的修正说明） |
| f Lodz → Łódź | `head: Łódź, 74`；`coords: 51.7706° N, 19.4739° E`；`applied.name: Łódź`；请求的桶是 `/data/cities/l.json` | **通过** |

**另外三条硬约束也一并验了（不属于 a–f，但 §15 写死了，所以一起跑）**

| 项 | 实际输出 | 判定 |
|---|---|---|
| 首屏不取分片、不做预取 | 起点前 `fetches: 0`，网络里 `/data/cities/` 请求 0 条 | 通过 |
| 同桶只取一次 | 依次输入 `Denver` / `zzzzqqqq` / `Springfield` / `Lodz` / `york` / `ork` → 6 个桶各 1 次，重复输入 `Denver` 再 0 次（`refetch_on_retype: 0`） | 通过 |
| 分片失败不降级 | 屏蔽 `/data/cities/*` 后输入 `Osaka`：`status: Search is unavailable right now. The panel below is unchanged.`，`head: New York`、环 5 条、SVG 仍在、无空环 | 通过 |
| 匹配语义（前缀，非子串） | `york` → 5 条（York GB / York PA / York University Heights / Yorkville / Yorkton），**没有 New York**；`ork` → 只有 `Orkney` ZA，没有 York | 通过 |
| 地图页同一套 | `/nuclear-bomb-map/` 输入 `Denver`：`place: {name: Denver, lat: 39.73915, gazetteer: true}`、`label: Denver, CO`、环 5 条、读数 5 行 | 通过 |

### 14.6 任意城市的第一版边界（两句写死 + 一条禁令）

- **第一版只保证「五个距离 + burst height + 出处页码」。环内人口只对现有 20 个预设城市提供，其余城市显示 `population not tabulated for this city`——不显示 0，不给估算值。** 理由：人口是离线预算数据，任意城市现算会引入新的数据依赖和误差，先把搜索打通。
- **不得用 GeoNames 的 `population` 字段冒充环内人口。** 两者口径不同：GeoNames 那个是**城市本身的（行政区）人口**，环内人口是 **WorldPop 在半径圆内的统计**，同一个城市两个数能差一个量级。搜索命中的城市若不在 20 城预设里，就显示上面那句提示，不拿地名库的字段顶上——那不是在补数据，是在给一个错的数。
- **三种 yield × 两种 burst 全部走现有查表，任意城市不得新增任何物理计算路径。** 新增城市只改变「在哪儿量」，不改变「量什么、怎么算」。

---

## 15. 数据准备清单（**已定案，进入实现**）

这五项是「任意城市搜索」的前置工作，顺序就是下面这个顺序，每一步都写明「做什么」与「不许做什么」，因为这一步最容易顺手把运行时复杂度引进静态站。**体积与分片已在 2026-11-16 实测定案，本节结尾有停止标记：不再追加内容。**

**文件与字段（确定口径，不用再猜）**

- **文件**：`cities15000.zip` 实测 **3,367,206 字节（3.2 MB）**；解压出的 `cities15000.txt` 实测 **8,551,097 字节 / 34,214 行 / 19 列**，UTF-8、制表符分隔、无表头。
- **范围：全文件 34,214 条照收，禁止任何形式的截断** —— 不按人口截到 25,000、不按 name 去重、不按国家筛。理由：「2.5 万」指的是**文件档位**（`cities15000`）不是条目数，这一版实测是 **34,214 行**（第 19 列修改日期 2026-04-13）；截断会丢掉文件本来包含的小人口首都——实测人口低于 15,000 的 **45 条**里，**40 条是 `PPLC` 首都**、**5 条是 `PPLG` 政府所在地**，正是被截断先丢掉的那批。
- **收录口径说明（这是文件的规则，不是我们的筛选条件）**：文件自己的入选条件是人口 > 15,000，或首都，或政府所在地。我们照单全收，不再套一层过滤——所以「cities15000 就是两万五千个人口过万的城市」这个理解是错的：它含首都与政府所在地，且条目数比 2.5 万多。
- **列位（1-based，照这个用，别靠肉眼数）**：`latitude` 第 **5** 列、`longitude` 第 **6** 列、`population` 第 **15** 列、`timezone` 第 **18** 列。其余：1 `geonameid`、2 `name`、3 `asciiname`、4 `alternatenames`、7 feature class、8 feature code、9 国家码、19 修改日期。
- **脏数据不许手删**：文件里有明显不合理的条目（`Liberpolis` 人口 63、`Thomas Magena home` 人口 0）。删行等于改源、也等于下次重建对不上；正确做法是保留原行，让搜索排序保证这类条目永远进不了首位（同名取人口大的那条，见下面第 2 项）。
- **搜索只做本地名称匹配**：不接 GeoNames 在线 API、不发任何第三方请求，与 §13 第 3 项同一条约束。**匹配只用第 3 列（`asciiname`），第 2 列（`name`）只负责显示**——`name` 用来显示才看得到 `Łódź`，用来匹配就会把非 ASCII 首字母分到错误的桶里（见下面实现口径 ①）；`alternatenames`（第 4 列）整列不进索引——体量最大且多为非英语变体（见下面的实测占比），进来就会把首屏体积和匹配噪声一起放大。坐标与人口只从第 5/6/15 列取，不从别名里推。

**第 0 步（已做，2026-11-16 实测）：先量体积，再定分片。** 没有这组数不许定分片粒度——禁止凭感觉。

- **全量 34,214 条、只保留搜索需要的字段**（`geonameid` / `name` / `asciiname` / `latitude` / `longitude` / `population` / `admin1` / 国家码）序列化成 JSON：**2,348,515 字节**（紧凑数组、UTF-8、无空格）；gzip 后 **886,209 字节**。同一批数据写成对象数组是 4,127,643 字节 / gzip 972,405 字节——光键名就多 1.78 MB，所以产物用紧凑数组。
- **三列在原始文件里的占比**（全文件 8,551,097 字节）：`name` **321,579 字节（3.76%）**、`asciiname` **311,689 字节（3.65%）**、`alternatenames` **4,873,358 字节（56.99%）**。`alternatenames` 有值的行 30,897 / 34,214，合计 358,036 段。
- **三列在 payload 里的占比**（2,348,515 字节）：`name` 424,221 字节（18.06%）、`asciiname` 414,331 字节（17.64%）；`alternatenames` 若进 payload 要 4,976,000 字节，是 payload 的 **211.88%**——这是「整列不进索引」的量化理由，不是偏好。
- **可省但未省 → 2026-11-16 已否掉（三种写法都量过 gzip，不是拿 414 KB 未压缩数下的结论）**：`name` 与 `asciiname` 在 **27,089 行（79.2%）完全相同**。去掉重复那一份的三种改法实测（分片求和口径，现版 **949,335 字节**）：`null` 占位 **888,010**、空串占位 **883,677**、整列拆成「行数组 + 稀疏下标映射」**896,682**。**最大只省 65,658 字节（6.9%），不到 100 KB → 不值得。** 这点传输量换的是索引结构改一遍、每次匹配多一条「这行有没有第二份名字」的分支判断，以及用例 e 核对候选时多一层解引用。**结论：一行都不合并，`name` 与 `asciiname` 两个字段照原样都进索引。**
- **按 `asciiname` 首字母切 29 个桶，逐桶独立 gzip（level 9）实测**：只保留上述 8 个字段的紧凑数组。最大三桶 **S 268,331 字节 / gzip 103,144 字节（3,737 行）**、**B 192,888 / 76,572（2,838 行）**、**M 182,182 / 72,781（2,677 行）**；29 个桶 gzip **中位 22,734 字节**、最小 84 字节。逐桶求和 2,348,543 / **949,335 字节**，比单文件 886,209 字节多 **63,126 字节（+7.1%）**——这是 29 份独立压缩字典的固定代价，不是误差，也是分片唯一要付的钱。（29 桶里有 3 个非字母桶：`'` 42 行、`` ` `` 6 行、`6` 1 行，共 49 行；这组数字**不含 `timezone` 第 18 列**，若实现时确认要带，必须重跑 `scripts/measure_shards.py` 重贴，不许拿现在这列当含时区的数。）

**实现口径（2026-11-16 落地时写死，两条，不再改）**

- **① 分桶键取 `asciiname`，不取 `name`。** 桶名 = `asciiname` 首字符大写后的小写字母，非 A–Z 一律进 `other`。理由：`name` 里有 `Łódź` / `Ålesund`，首字符是 `Ł` / `Å`，按 `name` 分桶会把它们扔进 `other`，英文用户在 L / A 桶里永远搜不到。`asciiname` 本身就是纯 ASCII，所以**构建期不需要任何字符折叠**；折叠只发生在输入侧——用户粘贴 `Łódź` 时，先 NFD 去掉组合符，再用一张小表补 `Ł→L` / `Ø→O` / `Þ→T` 这类不分解的字母，最后取首字符。（用例 f 就是这条的验收。）
  落地：`scripts/build_city_shards.py` → `public/data/cities/{a…z,other}.json`，**27 个文件**。3 个非字母桶（`'` 42 行、`` ` `` 6 行、`6` 1 行）并成 `other`（49 行），所以逐桶求和是 **949,192 字节**，比 29 桶的 949,335 少 143 字节——并桶只影响这个和，任何单桶数不变。
- **② 只做前缀匹配，不做子串匹配。** `asciiname` 从头比，忽略大小写。理由：按首字母分桶就决定了只能前缀，否则回答一个 `york` 得先把 866 KiB 全量取下来，分片就白分了。**`york` 搜不到 `New York` 是写下来的已知行为，不是 bug**：`york` 实测命中 5 条（York GB / York PA / York University Heights / Yorkville / Yorkton），`ork` 只命中 `Orkney` ZA，两个方向都验过。要搜到 New York 就打 `new` 或 `new y`——`New York` 的 `asciiname` 就是它本身。

1. **GeoNames 免费地名分片成静态 JSON：按首字母切，用户开始输入时才懒加载。** 现有 20 城本来就来自 GeoNames `cities15000`（`scripts/build_cities.py`，CC BY 4.0），所以这是把同一份来源从 20 条扩成分片，不是换源。**方案写死（依据是上面第 0 步的 gzip 列，不是感觉）**：产物 **27 个文件 = 26 个字母桶 + 1 个 `other`**（`'`/`` ` ``/`6` 三个非字母桶 49 行并成一个），**首屏不加载任何分片**。理由一句话：全量 gzip **886,209 字节（约 865 KiB）**放首屏，等于让每个访客先背一份他可能一次都用不到的数据；按首字母懒加载后**单次只取一个桶，中位 22,734 字节、最大 S 桶 103,144 字节**，同桶取过一次就留在内存里不再请求。**触发条件写死**：输入框拿到焦点且已有至少 1 个字符时才发请求，不做预取（首屏预取、`mouseenter` 预取、`requestIdleCallback` 预热都不行——预取等于把全量体积换个名字背回来）。**不许做**：为了压体积丢掉 `timezone` 与 `population`（用例 a–e 之后还要按它们排序与展示）。
2. **索引就是分片本身，另存的人口序已经取消（2026-11-16 落地口径）。** 匹配索引 = 每个桶的紧凑数组，按 `asciiname` 前缀逐个比；「同名取人口大的那个」不另建一份排序文件，而是在**命中集合内**按 `population` 降序排一次——命中通常是个位数到几十条，排序成本可以忽略，再存一份全量人口序等于把同一批数据在磁盘上放两遍。**不许做**：把同名条目合并成一条——合并会让「同名取大的」这条规则失去判断依据，也让用例 e 的候选列表无法成立。
3. **搜索框只做本地前缀匹配，不接外部 API。** 不调 GeoNames 的搜索接口、不调任何 geocoding 服务：一次请求就能换来的响应速度，值得用本地索引换，而且外部 API 会把「站能不能打开」变成「别人的服务在不在」。**（原来的「前缀/包含」已按上面实现口径 ② 收窄成只有前缀——两份口径不许同时存在。）**
4. **构建期生成，不打进运行时包（落地口径：由独立脚本生成并提交，`astro build` 只负责原样发布）。** `scripts/build_city_shards.py` 产出 `public/data/cities/*.json`，脚本开头就校验单文件 2,348,515 / gzip 886,209 这两个基线，对不上直接退出——所以分片不是 `astro build` 里现算的，也就不会被一次构建意外改写。它们不塞进首页或地图 island 的 JS 里：首页现在的体积是 40 KB 级，为了一个搜索框塞进几百 KB 的字典，等于把首屏换掉。
5. **署名与许可（上线前必检项）。** 数据是 **CC BY 4.0**，站上必须有 **GeoNames 的署名与链接**（页脚一行即可，与现有免责并列），这一条列进上线前必检清单：**缺署名不发布**。许可证文本不改写、不缩写，链到 `https://www.geonames.org/`。

**分片方案的硬约束（与第 1 项同一轮实现，不是可选项）**

- **搜索失败或分片加载失败时，页面必须仍然显示默认状态（New York 100 kt）与原来那张 SVG**：分片请求失败、超时、HTTP 非 200、JSON 解析失败、匹配过程抛异常，一律按这一条处理。**不许出现空环、不许白屏、不许把地图换成骨架屏或「加载中」占位。** 可行的做法只有一个方向：默认状态在静态 HTML 里就已经渲染好，JS 只在匹配成功后替换它，失败时什么都不做——**首次渲染不得依赖任何分片是否到达**，这条同时是 §14 里「搜索是增强，不是页面前提」的实现口径。

**停止标记**

> **§14 / §15 冻结，进入实现。此后除非实现中发现用例自相矛盾，不再向这两节追加内容。**

---

## 16. 地图点击落点：任意一点画五环并给环内人口（2026-11-17 实现）

这是 §14.4 排序里的第 3 项，与第 1 项同一个里程碑（§14.4 已写死「合并的是实现批次，不是排序位置」）。**本轮只加了这一件事**：五距离数值、combos 表、sitemap、页面既有文案一个字都没动。

### 16.1 七条需求的落地口径

| 需求 | 落地 | 代码位置 |
|---|---|---|
| 1 点击即圆心，不询问地理编码 | 一个 `pointerup` 监听挂在 `#map-frame`，位移 ≤6 px（触摸 ≤12 px）才算点击；有底图用 `map.unproject`，无底图用自写反投影。**全程零请求。** | `src/scripts/bomb-map.ts` 的 `onPoint()` |
| 2 五距离沿用 combos | 点击只改圆心，`rowsNow()` 不动，读数直接复用同一份 island | 同上，`drawRings()` |
| 3 浏览器端按瓦片求和 | 10°×10° 瓦片、1/24° 格、每格 1 字节对数档；点击只取所在瓦片，跨边界最多 4 个；取过的（含失败的）留在内存，同会话不重复请求 | `loadTile()` / `tilesFor()` / `sumInside()` |
| 4 状态区给坐标与 `near` | 点击后隐藏「GeoNames 点」那行，改显 `47.1999° N, 8.2000° E · near —`；`near` 是**占位**，不做反向地名查询 | `renderPoint()` |
| 5 5 km 内吸附 | 圆心距 20 城任一 < 5 km，整列改用 `city-pop.json` 的值，并显示 `snapped to <City> — tabulated city` | `snappedCity()` / `tabulatedFor()` |
| 6 不改 URL | 点击路径**不调用** `apply()`，因此不碰 `history.replaceState`；canonical 是构建期静态值 | 点击走 `onPoint()`，不走 `apply()` |
| 7 降级 | 瓦片 404 / 超时（6 s）/ 长度不对 → 环照画，人口列全 `—`，并显示 `circle population unavailable at this point` | `loadTile()` 返回 `null` → `{kind:'unavailable'}` |
| 8 服务端直出保留 | 地图不可用时 `.map-figure` 整块 `display:none`，五个距离与出处仍在 `#map-readout` 的静态 HTML 里 | 未改 |

### 16.2 数据：为什么是 1 km 可下载版，不是 API 的 100 m

**一句话：100 m 全球放不进这个站。** 全球 100 m 栅格按国家分发是几十 GB 级；可下载的 1 km 全球版
**实测 248 个文件 / 892.5 MB**（`ATA` 无文件），聚合后压成 1 字节格网是 **37,324,800 字节**。API 的 100 m 面只覆盖 20 个城市，且 102,642 次 POST 才能铺满 GeoNames 全量（§14 审计已量过），不能当作瓦片源。

- **来源**：`https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/{ISO3}/{iso}_ppp_2020_1km_Aggregated.tif`，249 个国家目录，缺文件的记 `absent`（如 `ATA`）。同一产品家族（WorldPop 2020 估算），但是**可下载版**，不是 API 回的那份 `R2025A 100 m`——两面的差异已经由 §/methodology/ 的巴黎实测（6.5%）写在明处，本轮不再造第二个差值说法。
- **格网**：1/24° × 1/24°，等于源数据 5×5 格（30″）；赤道 **4.63 km**、60°N **2.32 km**。经纬网做不到处处 5 km，所以格网按度数定义、地面尺寸照实报，不假装它是 5 km。
- **瓦片**：10°×10°，每边 240 格，**648 个 = 36×18**，每个 57,600 字节，命名 `x{00..35}y{00..17}.bin`，行主序、北到南。总量 **37,324,800 字节（35.6 MiB）**，首屏 0 字节——不发请求就不占带宽。
- **聚合**：按源格**中心**归入 1/24° 格（`np.bincount`），总量守恒，脚本对全球总量做 `6.5e9 < 总人口 < 9.5e9` 的硬校验，不达标直接拒绝写盘。
- **档位**：`floor=1`、`top=3,000,000`、255 档、**`ratio=1.0602309442`**（相邻档差 6.02%），解码取档位几何中点 `floor·ratio^(i-0.5)`，所以单格误差界是 `sqrt(ratio)-1 = 2.968%`（要求 ≤3%）。实测全球最大格 **1,630,235 人**（最高档用到 245/254，**没有触顶**，超顶直接报错、不裁剪）。低于 1 人的格记 0。
- **重跑**：`python scripts/fetch_worldpop_1km.py` → `python scripts/build_pop_tiles.py`，产物 `public/data/pop/*.bin` + `src/data/pop-meta.json`。瓦片是生成物，和 `effects.json` 一样**改数据必须改脚本重跑**。

### 16.3 求和：按圆-格重叠面积，不按「格心落在圆内」

5 km 级的格遇到 0.10 / 0.21 / 0.53 km 这三个小火球环时，「格心在圆内」要么整格算进来（把 4.6 km 格的人口塞进 0.21 km 圆），要么一个都不算（显示 0）。所以每个格按**它与圆的交集面积占比**加权：对格子在 y 方向切 48 条弦、每条弦用圆的解析半宽裁剪，误差远小于 0.5%。这样小火球环自动退化成「格内密度 × 圆面积」，不会跳变。

### 16.4 三处需要你拍板的口径（我没有替你决定）

1. **搜索到的城市仍然不给人口。** §14.6 写死「环内人口只对 20 个预设城市提供，其余显示 population not tabulated」，本轮没改这条：搜 Denver 仍然不出人口列，**但点 Denver 同样的坐标会出瓦片估算**。功能上自相矛盾，改法只有一行（把 `resolvePop()` 里 `gz ? null :` 去掉），但那是改一条已经写死的规则，留给你。
2. **地图页多了两行字**（都是新元素的文案，不是改既有句子）：图上的 `Click the map to move the rings to that point.`，以及人口列头上的`Population inside each ring · …`（含 `snapped to … — tabulated city`）。不想要第一行就删 `#map-hint` 那个 `<p>`。
3. **/methodology/ 新增了一节** `#clicked`（Ring populations at a clicked point）。原因是站上出现第二个面就必须有第二处出处说明；§23 那条「人口节里不许出现 1 km」的断言我没动，新节在 population 节之外，两节各说一个面。

### 16.5 验收 a–g：实测记录

**运行环境**：Windows 11，headless Chrome（CDP `127.0.0.1:9333`，`--headless=new`），页面由
`python -m http.server 4322 --directory dist` 发出，`dist/` 是
`CF_PAGES_BRANCH=main node node_modules/astro/astro.js build` 的产物（日志
`_headers: production (CF_PAGES_BRANCH=main) [SITE_LIVE=true]`，11 页，34.58 s）。
`check_site.py --expect main` 同时为 `PASS 1598 FAIL 0 WARN 0`。
**时间**：2026-11-17 23:48 CST（a–g 与吸附边界）；瓦片重建 2026-11-18 01:37 CST 后重跑同一套，`verdict.ok` 仍为 `true`。
**当量/爆高**：默认态 **100 kt · air burst**（a、b、f、h 与参考态同态）。
**栅格状态**：全球数据已到齐——**248 个国家级 1 km 栅格 / 892.5 MB / 0 个下载错误**，只有 `ATA`（南极洲）
本来就没有 1 km 文件。瓦片为无 `--partial-ok` 的正式产物：**648 个 tile / 37,324,800 字节 /
量化前 7,969,633,182 人 / 量化后 7,970,067,253 人（+0.005%）**，`pop-meta.json` 里已无 `partial` 字段。
**原始输出**：`click-gate.json`（已 gitignore），由 `node scripts/verify_click.mjs http://127.0.0.1:4322` 写出；
闸门通过条件写死在脚本里，`verdict.ok` 必须为 `true`。

| 用例 | 断言 | 实测 |
|---|---|---|
| a | 任意点出五环，五距离与同当量预设城市版逐字相同 | 点 `46.9998° N, 8.0004° E` → `0.21km / 3.22km / 9.93km / 6.99km / 4.02km`，与 New York 100 kt air 参考态逐字相同（`same_distances: true`）；`rings: 5`，`ring_pixels: 23908` |
| b | 点 20 城之一 → 出人口且与阶段 1 预计算值完全一致 | 点 `40.7143° N, 74.0056° W` → `kind: tabulated`、`city: New York`、`snapped: true`、文案 `Population inside each ring · snapped to New York — tabulated city`；五行 `2,451 / 490,885 / 3,704,149 / 1,895,355 / 749,418`，与 island 里 `pop['new-york']` 逐字相同（`identical: true`） |
| c | 大洋/沙漠显示 0 或 unavailable，不报错不白屏 | 大洋 `0.0000° N, 29.9996° W` → 五行全 `0`；沙漠 `23.0000° N, 12.0004° E` → 五行全 `0`。两者 `kind: tiles`、`rings: 5`、无异常。**是 0 而不是 unavailable**，因为瓦片确实取到了、取到的就是空海面/空沙地 |
| d | 点击后地址栏与 canonical 均不变 | `href` 前后同为 `http://127.0.0.1:4322/nuclear-bomb-map/`；`canonical` 前后同为 `https://apocalab.com/nuclear-bomb-map/`；同期 `heading` 已变成 `Clicked point · 100 kt · air burst`，证明点击确实生效了（不是没点着） |
| e | 单次点击请求数：瓦片 ≤4，其余 0 | 逐用例计**本次点击期间**新发的请求：a=1（`x18y04`）、同瓦片第二次点击=0、吸附点击=0、大洋=4（`x14y09/x15y09/x14y08/x15y08`，正是 10° 角点跨四格的边界情形）、沙漠=1、404 用例=2（被拦）、移动端=1；**每个用例 `base: []`、`other: []`** |
| f | 瓦片 404 时环仍在、人口显示 unavailable | `Network.setBlockedURLs: */data/pop/*` 下点 `36.5000° N, 140.0004° E` → `kind: unavailable`、文案逐字 `circle population unavailable at this point`、五行人口为 `null`（渲染为 `—`，**不是 0**）、`ring_pixels: 22909` 五环照画、距离仍 `0.21/3.22/9.93/6.99/4.02`。**同一位置再点一次 → 新请求 0 个、状态仍 `unavailable`**：失败也进了缓存，不会每点一次重试一次 404 |
| g | 移动端 tap 与桌面 click 行为一致 | 同一像素（`195,422`，375×667 视口）先 click 后 tap：两条路径都 `kind: tiles`、`rings: 5`、各发 1 个瓦片请求、状态区都出现 `near —`。圆心差 `lat 0.00027° / lon 0`，五个数最大相对差 **0.41%**（Chrome touch adjustment 对整数触点仍会做亚像素修正，所以判据是同像素同状态机 + 数值带内一致，不是逐位相等） |

**附加一项（不在 a–g 内，但属于第 8 条需求）**：把底图域名整段 block 掉再点 → `mode: outline`
（走随包 Natural Earth 轮廓），五环仍出、`kind: tiles`、人口照给（`76 / 20,091 / 193,770 / 91,972 / 32,253`），
`base: []`。说明点击路径不依赖 MapLibre。

**另一项（第 5 条的边界，b 只测了纽约不够）**：在**巴黎**做两点。东 3 km（`2.3898° E`）→
`kind: tabulated`、`city: Paris`、0 个瓦片请求、五行与 `pop['paris']` 逐字相同
（`2,361 / 780,593 / 4,653,886 / 3,100,485 / 1,257,703`）；东 8 km（`2.4578° E`）→ `kind: tiles`。
所以 5 km 是**执行中的判定**，不是文案；吸附也不是只对纽约成立。

**同批跑的其它闸门**：`verify_map.mjs` → `{ok:true, problems:[]}`（5 态降级路径未破）；
`verify_pop_tiles.py` → **PASS 9 FAIL 0**，648 个瓦片尺寸正确、解码总量与元数据一致、最高档 245 ≤ 254
（未触顶）、档位误差 2.968% < 3%、误差界与 `sqrt(ratio)-1` 自洽，浏览器与脚本在 20 个档位上 **Δ 全为 0**
（逐档打印在 `pop-gate.json`）。

**两套人口面差多少（必须写出来，别让读者自己发现）**：拿 20 城 5 个环逐城复算瓦片面，与已发布的
100 m API 表值对比——**环 ≥ 5 km 的 160 档平均差 −3.0%，最大 +53.8%**（Johannesburg @ 5.28 km：
表 353,207 / 瓦片 543,400）；**环 < 5 km 的 160 档最大差 +32,229.9%**（Washington DC @ 0.21 km：
表 2 人 / 瓦片 647 人）。后者的意思是「小于一格的环只能按格内密度折算」，不是测出来的，
`/methodology/#clicked` 已经写明这一点；前者说明**离城市 5 km 以外再画同一个环，数字会和城市页不一样**，
这正是「5 km 内吸附到表值」这条规则存在的理由。

**未完成项**：§16.4 三条口径仍等你拍板。数据侧已无欠账。

## 17. 武器预设：把三档当量扩成十二个认得出的弹名（2026-11-16 实现）

### 17.1 十二条需求怎么落的（逐条口径）

1. **选择器**是原生 `<select name="preset">`，两个 `<optgroup>`：`Yields printed in the manual`（15 / 100 / 1,000 kt）与 `Weapons`（12 条）。没有组件库、没有新增运行时依赖、没有第二个控件。
2. **默认态未变**：仍是 `New York · 100 kt · air burst`，`selected` 落在 `y100` 上，服务端直出；关 JS 时六个数字与页码原样在页面上。
3. **状态**从 `{city, y, b}` 改成 `{city, preset, b}`，当量由 `ktNow()` 从 preset 派生（`y*` → 数字，弹名 → 该弹 kt）。分享参数仍写当量本身（`w=15000`），所以老链接 `?yield=15` / `?y=15` 照样能开。
4. **十二条预设数据**在 `src/data/weapons.json`：`name / country / year / kt / note / source{label,url} / quote_yield / quote_year`。页面上逐条渲染成一张表，外链 `target="_blank" rel="noopener"`，**没有加 `nofollow`**（按你的要求，权威来源不 nofollow）。

### 17.2 两套距离口径：按来源分，不按数值大小分

| 档 | 当量 | 取数 | 页面标注 |
|---|---|---|---|
| 查表档 | 15 / 100 / 1,000 kt（air 与 ground 都有） | 直接读 `effects.json` 的 combos，一个字都不重算 | `tabulated from Fig. 3.73c (p. 115), Fig. 7.42 (p. 291), Eq. (2.127.1) (p. 70)` —— 列的是**这一档实际用到的**图/公式，随当量与爆型变 |
| 缩放档 | 其余 11 条预设 | `R = R(100 kt) × (W/100)^(1/3)`，锚点就是 combos 里的 100 kt 值 | `scaled by the cube-root law, §3.61 (p. 101), anchored on the 100 kt tabulated value — the two overpressure rings; the fireball comes from Eq. (2.127.1), and above 10 Mt Fig. 7.42 has no curve to read` |

两行是两个 `<p>`，`hidden` 互斥，没有合并成一句。第二行确实长了，但它不是含糊：把「哪两个环是缩放的 / 火球为什么不缩放 / 超过 10 Mt 为什么没有热辐射环」三件事分开说了。合成一句话就只能说「scaled」，那等于骗人。

六个环实际走三条路：

1. **火球**：公式直算。空爆 `110·W^0.4 ft`（Eq. 2.127.1, p.70），地爆 `145·W^0.4 ft`（Eq. 2.127.2, p.71）。这两个系数不许混用。
2. **三个超压环**（1 / 5 / 20 psi）：立方根缩放。20 psi 的 1 kt 基准来自 Fig. 3.73b（p.113），不是 3.73c——后者只印到 10 psi（见 §18）。手册在 §3.61 立这条律（Eq. 3.61.2, p.101），原文 `Full-scale tests have shown this relationship between distance and energy yield to hold for yields up to (and including) the megaton range.`
3. **两个热辐射环**：**不缩放**，在 Fig. 7.42（p.291）上按每个预设自己的列直读 4.5 与 10 cal/cm² 两条等值线。该图横轴止于 10,000 kt。

### 17.3 三处与你给的数字/出处不一致（已于 2026-11-18 拍板）

| # | 项 | 你给的 | 来源原文 | 最终采用 | 为什么 |
|---|---|---|---|---|---|
| 1 | W76-2 当量 | 8 kt | `5-7 kT (Mod 2)` | **6 kt**（区间中位） | 8 落在来源区间外。改为取 5–7 区间中位 6 kt，并在页面、台账、`weapons.json` 三处写明「5–7 kt published estimate; radii computed at the 6 kt midpoint」 |
| 2 | W88 当量 | 455 kt | `475 kT` | **475 kt** | 旧资料流通过 455 kt 的估计，来源页印的是 475。`note` 里原来那句「some charts still print the older 455 kt estimate」已改写为不含具体数字的说法，全树不再出现 455 |
| 3 | 立方根出处 | `§2.127` | `§3.61`, Eq. (3.61.2), p.101 | **§3.61** | §2.127 是**火球尺寸**那一节（Eq. 2.127.1 / 2.127.2, p.70 / p.71），原文第一句是 `2.127 The size of the fireball increases with the energy yield of the explosion.` 不是立方根定律。手册在 §3.61 立这条律，§3.62（缩放爆高 + 地面距离）与 §3.63（时间/时长/冲量）复述并扩展它。见 §19.1 的本机 PDF 核对 |

三处都已在 2026-11-18 落地。**注意第 3 项不能理解成「全树 2.127 一律改成 3.61」**：现存 `2.127` 的全部命中都是火球公式（`Eq. (2.127.1)` / `(2.127.2)`，p.70–71），把这些改成 §3.61 会把火球的出处标错。`verify_data.py` 的 S 组现在把两节的归属钉死：火球条目必须引 §2.127 且公式号与爆型对应，非火球条目一律不许引 §2.127。

每条的 `quote_yield` / `quote_year` 是**来源自己的措辞**，进了 `weapons.json`，页面上以 `<q>` 显示。这样「页面采用值」和「来源原话」是两份数据：以后谁想改数字，必须先改 quote 那一行，改不动就说明来源不支持这个数字。

### 17.4 数据与脚本

| 文件 | 是什么 | 生成的还是手写的 |
|---|---|---|
| `src/data/weapons.json` | 12 条预设（含来源与原文引用） | **手写**，是输入 |
| `scripts/build_weapon_radii.py` | 预设当量 → 六个半径，三条取数路径，自带自检 | 脚本 |
| `src/data/weapon-radii.json` | 每预设 air / ground 两组半径 + 图上像素坐标 + 取数方法 | 生成物，不要手改 |
| `weapon-ledger.csv` | 132 行 = 12 预设 ×（6 effect × 2 爆型，热辐射地爆与 >10 Mt 记空），每行记方法 / 值 / detail / citation / `source_url` / `yield_note` | 生成物 |
| `src/lib/weapons.ts` | 预设表、`isTabulated()`、`radiiOf()`、两行标注的文案 | 手写访问层 |
| `scripts/verify_weapons.mjs` | 0–f 闸门，写 `weapon-gate.json`（已 gitignore） | 脚本 |

生成器里两个自检，不过就不写文件：一是把 15 / 100 / 1,000 kt 的 18 个已知等值线点在图上重读一遍（容差 2.5 px；1000 kt 的 15 cal/cm² 点与网格线合流，实测偏 2.00 px ≈ slant range 0.7%，仍远小于图自身 ±6% 的口径）；二是 100 kt 走立方根路径必须**逐位**返回 combos 的表值。

### 17.5 验收 a–f 实测

> 本节记的是**五环时**（2026-11-16）的实测输出，保留原样作为当时证据。§18 把环数改成六之后，同一批用例已重跑，结果见 §18.5；下面表里的「五行」现在读作「当年的五行」。

**运行环境**：Windows 11，headless Chrome（CDP `127.0.0.1:9333`，`--headless=new --window-size=1400,900`），页面由本地静态服务在 `:4322` 发出，`dist/` 是 `CF_PAGES_BRANCH=main node node_modules/astro/astro.js build` 的产物（`_headers: production … [SITE_LIVE=true]`，11 页，36.01 s）。**时间**：2026-11-16 04:4x CST，本地，**未部署**。
**原始输出**：`weapon-gate.json`，由 `node scripts/verify_weapons.mjs http://127.0.0.1:4322` 写出，`verdict.ok` 必须为 `true`。

| 用例 | 断言 | 实测 |
|---|---|---|
| a | 12 条逐个选，五距离都出数，查表档与现有值完全一致 | 选择器共 **15 个 option**（3 档 + 12 弹）。`little-boy 15 kt` 走查表档，五行与 `y15` **逐字相同**（`0.10 / 1.71 / 5.28 / 3.37 / 1.77`）；其余 11 条走缩放档，与 `weapon-radii.json` 逐位相同（同一份数据，误差 0）。抽样：`fat-man 21` = `0.11 / 1.91 / 5.90 / 3.87 / 2.08`；`w87 300` = `0.33 / 4.64 / 14.32 / 10.67 / 6.35`；`b53 9000` = `1.28 / 14.43 / 44.51 / 32.12 / 23.94`；`tsar-bomba 50000` = `2.54 / 25.55 / 78.83 / — / —`（3 个数字 + 2 行 absent，见下） |
| b | 15 kt 走查表档、50,000 kt 走缩放档，两种标注都在页面上 | `at15`：`tabHidden=false`、`scaleHidden=true`；`at50000`：`tabHidden=true`、`scaleHidden=false`。两行文本逐字见 §17.2 表格 |
| c | 缩放档的 100 kt 与查表值完全相同（锚点自检） | `scaled_at_100 = [0.21, 3.22, 9.93, 6.99, 4.02]`，`tabulated_at_100 = ['0.21','3.22','9.93','6.99','4.02']`，**逐位相同**；生成器里同一断言也过（含地爆 `1.93 / 5.42 / 0.28`） |
| d | 禁 JS 打开 `/nuclear-bomb-map/` 仍有 New York 五距离与 SVG | 五行仍在，且每行带页码：`0.21 km`←`Eq. (2.127.1) · p. 70`、`3.22 km`/`9.93 km`←`Ch. 3 · Fig. 3.73c · p. 115`、`6.99 km`/`4.02 km`←`Ch. 7 · Fig. 7.42 · p. 291`；`heading = New York · 100 kt · air burst`；`.map-figure` 为 `display:none`、提示块 `block`；首页内联 SVG 计数 1 |
| e | `?w=15000&b=air&lat=51.5&lon=-0.12` 状态恢复，canonical 不变 | `state = {city:'new-york', y:15000, b:'air'}`、`preset = castle-bravo / Castle Bravo / 12 条`、圆心 `51.5, -0.12`（`Clicked point`），标注切到缩放档。带参数与不带参数**返回完全相同的 HTML**（`share_same_html: true`，同一份构建、同一个文件）。canonical 恒为 `https://apocalab.com/nuclear-bomb-map/`。从该页再改当量，写回 `?w=25000&b=air&lat=51.50000&lon=-0.12000`，仍是 `replaceState`，不新增历史条目 |
| f | sitemap 条数不变 | `locs = 10`，与加预设前一致；参数页不进 sitemap，`robots.txt` 未改，也没有为参数加任何规则 |

**本轮新加的第 0 组断言**（不在 a–f 里，因为它是这一轮踩出来的，见 §17.6）：默认页 `centre = New York / 40.7143° N, 74.0060° W`、`zoom = 10.39`、`location.search` 为空、环像素 `29880`。

**同批跑的其它闸门**：`verify_data.py` → PASS 354 FAIL 0；`check_site.py --expect main` → **PASS 1598 FAIL 0 WARN 0**；`check_urls.py` → PASS 68 FAIL 0；`verify_map.mjs` → `{ok:true}`（五态未破）；`verify_click.mjs` → `{ok:true}`（a–h 未破）。

### 17.6 途中发现的两个既有缺陷（不是本轮需求，但会毁掉默认页）

两个都是上一轮加「任意点点击 / 分享参数」时留下的，都只在**没有任何 URL 参数的默认访问**这条路上发作，所以点选闸门与地图降级闸门当时都是绿的。

1. **`Number(null) === 0`**。`readUrl()` 原来写 `const lat = Number(p.get('lat'))`，再判 `Number.isFinite(lat)`；没有 `?lat=` 时 `p.get` 返回 `null`，`Number(null)` 是 `0`，判定通过 → 每次打开 `/nuclear-bomb-map/` 都变成「0°N 0°E 的点击点」。后果不是文案错：`apply()` 里有「点击点不移动相机」的分支，于是环被画到几内亚湾外海，页面上五个环一个都看不见，只剩五个标签（环像素 **12701 = 全是标签**）。修法：先判参数在不在（`null` 与空串一律 NaN），`?lat=0&lon=0` 仍然是合法点。
2. **`view.zoom` 早于布局**。`view = viewFor(...)` 在模块作用域就算好了，而它依赖画布 `w/h`；那一刻 `frame` 还没有尺寸，`zoomForRadius()` 直接落进 `clamp(..., 1, 16)` 的下界 → `zoom = 1`，而 MapLibre 自己的最小缩放是 2。修法：`resize()` 之后调一次 `refit()`，并在 `ResizeObserver` 里跟着 `resize()` 一起重拟合。`refit()` 只用 `view` 现有的经纬度重算比例，**不动中心**，所以点选点和平移结果都不会被拉回去。

修完实测：圆心回到 `40.7143° N, 74.0060° W`，`zoom 10.39`（与 MapLibre 实际比例一致，`512·2^zoom` 世界像素下 9.93 km = 224 px = `0.4 × 560`），环像素 `12701 → 29880`。

### 17.7 未完成项

1. ~~§17.3 三条等你拍板~~ —— 2026-11-18 已拍板并落地（6 kt 中位 / 475 kt / §3.61），见 §19。
2. **`> 10 Mt` 的四条（Ivy Mike / Castle Bravo / B41 / Tsar Bomba）没有热辐射环**：显示 `—`，理由是 `Fig. 7.42 stops at 10 Mt: no thermal radius is read above it.`，**不显示 0、不外推**。这一条要不要在结果区之外再加一句独立说明，等你定。
3. **非查表当量下的「城市态」人口列**：显示 `tabulated at 15, 100 and 1,000 kt only, not at 50,000 kt`，不给瓦片估算。理由是瓦片人口与城市页 API 人口是两套口径，不能混在同一列里（§16 已写死这个差别）。这也是新口径，待确认。
4. 本轮**没有提交、没有部署**；上线与否等你 §17.3 拍完再说。


## 18. 第六环 20 psi：先判条件，再改环数（2026-11-16 实现）

### 18.1 条件判定的答案：有，所以做

阶段 0 第 5 项当时的回答是「Fig. 3.73c 上没有 20 psi」。这句话是对的，但它不等于「手册没有」：

- **Fig. 3.73c（p.115，低压段）** 的印字标号是 1 / 2 / 4 / 6 / 8 / 10 psi。没有 20 psi，也没有 5 psi。
- **Fig. 3.73b（p.113，中压段）** 的印字标号是 10 / 15 / 20 / 30 / 50 / 100 / 200 psi。**20 psi 是图上一条真实印刷的等压线。**

所以条件成立，做。并且这一步**没有用任何公式反推**：20 psi 的 1 kt 基准是在 3.73b 上读出来的，唯一的乘法仍是手册自己的 §3.61 立方根律，与 1 / 5 psi 用的是同一条律、同一个标签。

### 18.2 读数：1 kt 基准（600 dpi 渲染 p113_600.png，4,320 × 3,136）

标定取自等距网格线，两个方向各自独立：

```text
x_px = 348.5 + 2.2467 · d_ft      100 ft = 224.67 px（0–1,500 ft，15 格）
y_px = 2521.5 − 2.2540 · h_ft     100 ft = 225.40 px（0–1,000 ft，10 格）
```

| 爆型 | 1 kt 基准 | 爆高 | 像素 | 怎么读的 |
|---|---|---|---|---|
| 空爆 | **927.9 ft** | 611 ft | (2433.1, 1144.0) | 20 psi 等压线峰值；±40 ft 邻域内抛物线拟合顶点，原始采样 928.5 ft @ HOB 608 |
| 地爆 | **720.2 ft** | 0 | (1966.5, 2521.5) | 底边：HOB 30 ft 处 725.5 ft，局部斜率 0.178 ft/ft，外推最后 30 ft |

缩放后（× W^(1/3)）：

| 当量 | 空爆 | 地爆 |
|---|---|---|
| 15 kt | 0.70 km（2,288 ft，HOB 1,507 ft） | 0.54 km（1,776 ft） |
| 100 kt | 1.31 km（4,307 ft，HOB 2,836 ft） | 1.02 km（3,343 ft） |
| 1 Mt | 2.83 km（9,279 ft，HOB 6,110 ft） | 2.19 km（7,202 ft） |

### 18.3 两处独立校验（写进 cross_checks，页面表格自动渲染）

| id | 手册原话 | 本图读数 | 差 |
|---|---|---|---|
| G5 | p.112 算例：地面距离 400 ft、爆高 500 ft 处峰值超压 50 psi | 410 ft | **+2.5%** |
| （非锚点） | Fig. 3.73a（p.111）上 100 psi 环鼻尖约 360 ft @ HOB 190 | 363 ft @ HOB 210 | **<1%** |

G5 进 `cross_checks`（`verify_data.py` C 组会查编号必须是 G1–G5、且 G5 的 400/410 不得漂移）；100 psi 那条只写在 methodology 正文里，因为它是图对图，不是「手册用文字写死的数」——把它伪装成锚点会破坏锚点的定义。

### 18.4 数据层与页面改了什么

| 位置 | 改动 |
|---|---|
| `scripts/build_effects.py` | 新增 `BLAST20_AIR` / `BLAST20_GND` / `CIT3B`，生成 6 条 `overpressure_20psi`（3 当量 × 空/地）；签核分支把 20 psi 放最前，`checked_by=None` → 页面带 `*` |
| `src/data/effects.json` | 24 → **30** 条；citation 为 `Fig. 3.73b, p.113`，`base.factor` 与 `base.px` 可复算 |
| `data-ledger.csv` | 24 → **30** 行 |
| `src/lib/effects.ts` | `EffectId` 加 `overpressure_20psi`；`EFFECT_ROWS` 改为**半径降序六行**：1 psi → thermal 2nd → thermal 3rd → 5 psi → 20 psi → fireball |
| `src/lib/panel.ts` | 20 psi 环色 `#ff4d6d`（与 5 psi `#f0b64a`、火球 `#ff7a29` 三者互不相同）；副标题 `peak of the 20 psi contour · Fig. 3.73b` |
| `src/scripts/bomb-map.ts` | `scaledRows()` 不再硬编码 effect 顺序，改为从 island 的锚点行取 order（客户端不能 import effects.json） |
| `scripts/build_weapon_radii.py` | `EFFECT_ORDER` 同步六环；每条预设 air/ground 从 5 个半径变 **6 个**；`weapon-ledger.csv` 110 → **132** 行 |
| `scripts/build_city_pop.py` | 半径集合从 `effects.json` 自动派生 → 20 个半径，**20 城全部重取** |
| `src/data/city-pop.json` | 每城多 `0.700` / `1.310` / `2.830`（15/100/1,000 kt 的 20 psi）三档；旧值未漂移 |

页面文案的「五环 → 六环」是一次全树清扫，不是逐页手改：首页、/blast-radius/、/nuclear-bomb-map/、五个城市页、/methodology/、BombMap/ResultPanel 注释，最后用 `check_site.py` 的 G-e 组反向断言 **`five rings` / `five distances` / `five radii` / `five effects` / `five contours` 一个都不许再出现**。保留原样的 `five` 有三类，都不指环数：`five spot-checked`（签核记录）、`five city pages`（已发布城市页数）、`five source pixels`（瓦片一格由 5 个源像素合成）。

### 18.5 验收 a–c 实测（2026-11-16，本地 `CF_PAGES_BRANCH=main` 产物）

| 用例 | 断言 | 实测 |
|---|---|---|
| a | 20 psi 距离与手册图逐值一致 | 空爆 1 kt **927.9 ft @ HOB 611** → 0.70 / 1.31 / 2.83 km；地爆 **720.2 ft @ HOB 0** → 0.54 / 1.02 / 2.19 km；`verify_data.py` 的 P2 组逐条比对 `EXPECT20` 六个整数（2288 / 4307 / 9279 / 1776 / 3343 / 7202），全过 |
| b | 六环图例顺序正确 | 图例 `.nm` 六个名字按 `1 psi → Thermal · 2nd-degree → Thermal · 3rd-degree → 5 psi → 20 psi → Fireball` 排列；六个 `.dot` 颜色互不相同，20 psi `#ff4d6d` ≠ 5 psi `#f0b64a`；`verify_map` A/B 两态 `rings = 6` |
| c | 20 城人口表含新环 | `city-pop.json` 每城 20 个半径。纽约实测：0.700 km → **40,065**、1.310 km → **124,692**、2.830 km → **391,022**；旧值未漂移（3.220 km 仍 **490,885**） |

闸门实跑（全部非零退出即视为失败）：

```text
python scripts/verify_data.py            PASS 511  FAIL 0
python scripts/check_site.py --expect main   PASS 1765 FAIL 0  （含新增 G-e 组 11 条）
python scripts/check_urls.py             PASS 68   FAIL 0
python scripts/verify_pop_tiles.py       PASS 9    FAIL 0
node scripts/verify_map.mjs      → {"ok": true}
node scripts/verify_click.mjs    → {"ok": true}
node scripts/verify_weapons.mjs  → {"ok": true}
node scripts/verify_search.mjs   → {"ok": true}
```

改闸门时踩到的一个坑，记下来免得下次再犯：`verify_map` / `verify_click` / `verify_weapons` / `verify_search` 里环数与读数列都是**硬编码的 5**，还各自带着一个「按显示顺序写死」的距离数组。环数从 5 变 6 之后，这些数组不只是长度不对，**顺序也全错**（20 psi 插在 5 psi 与火球之间）。所以改法不是把 5 换成 6：`verify_click` 的 `rowKeys` 与 `verify_weapons` / `verify_search` 的 `D_VALUES` 都重排成了 `9.93 / 6.99 / 4.02 / 3.22 / 1.31 / 0.21`。只改长度不改顺序，闸门会绿着放过一个错序的页面。

超过 10 Mt 的四条预设现在每条有 **4** 个数字（1 / 5 / 20 psi + 火球），热辐射两行仍是 `—` + `Fig. 7.42 stops at 10 Mt`，`verify_weapons` 的期望值随之从 3 改成 4。

### 18.6 未完成项

1. **六行 20 psi 没有签核**，页面与表上带 `*`。签字条件与其余行同一条：对 p.113 重新渲染、把 20 psi 等压线再读一次，实测值与原值差在读数误差内才落日期。现在的背书只有 §18.3 那两条独立校验。
2. `methodology` 的 `#verification` 一节现在写「24 of 30 signed，未签的 6 行全是 20 psi」，并解释了为什么未签——这一句是从 `entries` 里算出来的（`{checked} of {total}`），不是手写数字。
3. 本轮**没有提交、没有部署**。§17.3 的三处待拍板仍然待拍板（W76-2 7 vs 8、W88 475 vs 455、立方根标 §3.61 还是 §2.127）。

## 19. 三处已知错的收口（2026-11-18）

### 19.1 §3.61 核对：编号是对的，但「全树 2.127 一律改 3.61」不成立

**PDF 版本**：《The Effects of Nuclear Weapons》，Third Edition，Compiled and edited by Samuel Glasstone and Philip J. Dolan，United States Department of Defense + Department of Energy，1977（封面编号 TID-28061）。本机文件 `EoNW/6852629.pdf`，662 页；第 3 章 PDF 页 = 印刷页 + 9。

| 节 | 印刷页 | 原文（逐字） |
|---|---|---|
| §3.60 `SCALING LAWS` | 100 | `In order to calculate the characteristic properties of the blast wave from an explosion of any given energy if those for another energy are known, appropriate scaling laws are applied.` |
| §3.61 | 100 起，续 101 | `3.61 Theoretically, a given pressure will occur at a distance from an explosion that is proportional to the cube root of the energy yield. Full-scale tests have shown this relationship between distance and energy yield to hold for yields up to (and including) the megaton range.`；式 `(3.61.2)` `D = D₁ × W^(1/3)` 印在 **p.101** |
| §3.62 | 102 | 缩放爆高；`cube root scaling law may be applied to distances from ground zero`，式 `(3.62.1)` |
| §3.63 | 102 | 同一律推广到冲击波到达时间、正相时长、正相冲量 |

结论：**3.61 确实是立方根那一节，3.62 / 3.63 属于同一组**。工作区里所有立方根引用本来就已是 §3.61（`weapons.ts` 的 `SCALED_LAW`、`SOURCE_PREFIX.blast`、缩放台账行、`effects.json` 的 `scaled_label`），没有一处把立方根标成 2.127。

但「全树 2.127 命中 0」不能做，做了是错的。现存 `2.127` 的命中**全部是火球公式**：p.70 首句 `2.127 The size of the fireball increases with the energy yield of the explosion.`，p.71 印 `R (at breakaway) for contact surface burst = 145 W^0.4 (2.127.2)`。把这些改成 §3.61，等于让火球半径的出处指向一条与火球无关的缩放律。

所以本轮**没有替换这 62 处**，改为把归属钉进闸门（`verify_data.py` 的 S 组，+60 条断言）：火球条目必须引 §2.127 且公式号与爆型配对（空 (2.127.1) p.70 / 地 (2.127.2) p.71），非火球条目一律不许引 §2.127，缩放条目必须带 §3.61。以后谁再想一键替换，闸门会先红。

### 19.2 两处当量

| 项 | 改前 | 改后 | 落点 |
|---|---|---|---|
| W76-2 | 7 kt（区间上端） | **6 kt**（5–7 区间中位） | `weapons.json` 增 `kt_range: [5,7]` 与 `yield_note`；页面 Yield 列渲染 `6 kt (5–7 kt range)`，说明列写 radii computed at the 6 kt midpoint；台账 12 行带同一句 |
| W88 | 475 kt（已对） | **475 kt** | 只删掉 note 里那句引用旧低位估计的表述，全树不再出现那个旧数字 |

### 19.3 来源 URL

12 条全部有可点开来源，2026-11-18 实测全部 200，`quote_yield` 逐条比对原文命中；**无 MISSING**；无 `nukesimulation` / `nukeblastsimulator`。台账新增 `source_url` 列（132 行全部非空）与 `yield_note` 列（仅 W76-2 有值）。

顺手修的一处：三条测试页引文少了冒号后的空格（JSON 里 `Yield:10.4 Mt`，原文 `Yield: 10.4 Mt`），已按原文补齐——页面与闸门都声称「The quoted line is what the page actually says」，差一个空格就不成立。

### 19.4 重算与验收

`build_weapon_radii.py` 重跑：自检 18 个已知点最大偏差 2.00 px，100 kt 锚点自洽，132 行台账重写。

手算对账（`R100(m) × (W/100)^(1/3)`，W88 因子 1.680988 / W76-2 因子 0.391487）：

| 环 | W88 475 空爆 | W76-2 6 kt 空爆 |
|---|---|---|
| 1 psi | 9932 m × f = 16695.6 → **16.70 km** | 9932 × 0.391487 = 3888.2 → **3.89 km** |
| 5 psi | 3219 × f = 5411.1 → **5.41 km** | 3219 × f = 1260.2 → **1.26 km** |
| 20 psi | 1313 × f = 2207.1 → **2.21 km** | 1313 × f = 514.0 → **0.51 km** |
| 火球 | 110·475^0.4 = 1294 ft → **0.40 km** | 110·6^0.4 = 225 ft → **0.07 km** |

地爆同理（9.11 / 3.24 / 1.71 / 0.52 km 与 2.12 / 0.75 / 0.40 / 0.09 km），热辐射两行是 Fig. 7.42 直读、不参与立方根，两个 6 kt / 475 kt 的读数列与图上一致。

闸门实跑（本轮）：`verify_data` PASS **571**、`check_site --expect main` PASS **1765**、`check_urls` PASS **68**、`verify_map` / `verify_click` / `verify_search` / `verify_weapons` / `verify_js_off` / `verify_layout` / `verify_share_url` 全绿，FAIL 0。

首屏请求集未变：同源 5 条（文档 + `blast-radius.*.css` + `BombMap...js` + `ne_110m_land.geojson` + `maplibre-gl.*.js`），跨域 7 条（底图瓦片 6 + 1）。环数仍 6，顺序仍 `1 psi → thermal 2nd → thermal 3rd → 5 psi → 20 psi → fireball`（`verify_weapons` 的 `D_VALUES` 逐值比对通过）。

### 19.5 一个环境坑

四个浏览器闸门共用同一个 CDP 页面（9333 上的同一个 target），**并行跑会互相改状态**：本轮把 `verify_map` 与 `verify_click` 同时启动，结果 `verify_click` 读到 4 环（地被另一条脚本切成了 ground burst，两个热辐射行因此为空）+ 距离不一致，`verify_map` 报降级态环像素 0。串行重跑全绿。以后要么串行，要么各起一个浏览器实例。

### 19.6 待确认

1. §2.127 要不要按字面清成 0 命中。我建议不要（理由见 19.1）；若坚持，只能把火球出处降级成「Ch. 2 · p. 70 / p. 71」并丢掉公式号，每格少一个可核对锚点。
2. 本轮未提交、未部署。

## 20. 20 psi 六行的签核判定：重读、图对图、外部区间（2026-11-18）

结论先写：**verdict = unsigned**。六行继续带 `*`，方法页的「24 of 30」不动，数据、文案、环数一字未改。
它不是「数据错了」，而是**你给的四条判定里第 1、2 条按字面无法闭环**，我不拿拟合去凑。

### 20.1 读数表（p113_600.png，600 dpi，标定沿用上一轮 X0=348.5 / 2.2467 px/ft / Y0=2521.5 / 2.2540 px/ft）

方法：HOB 行横扫，带高 ±9 行、阈值 120，取该交点墨迹的**左沿 / 中心（墨量加权）/ 右沿**三点；
极差判据用你给的笔画宽度 20 px。

| 行 | 取点 | 像素 x | 折算 ft | 折算 km(1 kt) | 极差 |
|---|---|---|---|---|---|
| **HOB 500**（y=1394） | 左沿 | 2297.6 | 867.7 | 0.2645 | **17 px**（< 20，可用） |
| | 中心 | 2306.5 | **871.5** | 0.2656 | |
| | 右沿 | 2315.3 | 875.3 | 0.2668 | |
| **HOB 300**（y=1845） | 左沿 | 2097.9 | 778.7 | 0.2373 | **13 px**（< 20，可用） |
| | 中心 | 2104.5 | **781.6** | 0.2382 | |
| | 右沿 | 2111.1 | 784.5 | 0.2391 | |
| **峰值**（HOB 612） | 中心 | 2433.3 / y 1142.0 | **928.0** | 0.2828 | 转折点，见 20.4 |
| **地爆 HOB 0**（上一轮定稿值） | 底边外推 | 1966.5 / y 2521.5 | **720.2** | 0.2195 | 独立复核见下 |

阈值 100 / 120 / 150 × 带高 ±7 / ±9 / ±12 九种组合下，中心值稳定在 870.9–871.5 与 781.5–781.6，
即**读数本身可复现**（变化 ≤ 0.6 ft = 1.3 px）。

地爆 720.2 的独立复核：同一曲线下支 HOB 20/30/40 读到 724.0 / 725.5 / 727.0 ft，
线性外推到 HOB=0 得 **720.9 ft**，与 720.2 差 **+0.1%**。

### 20.2 第 1 条为什么过不去：立方根律折不了 HOB 行

你要求「把 d500、d300 按立方根律折到地爆 1 kt 等效距离再比」。本机 PDF 核对的结果是**这条折算不存在**：

- §3.61 Eq. (3.61.2)（p.101）：`D = D₁ × W^(1/3)`，**缩的是当量**。
- §3.62 Eq. (3.62.1)（p.102）：`d = d₁ × W^(1/3)`，且前置条件是*同一个 scaled height of burst*，
  即整条 (h, d) 等值线按 `(h·W^(1/3), d·W^(1/3))` 整体缩放。
- §3.73（p.112）复述：`h = h₁·W^(1/3)`、`d = d₁·W^(1/3)`。

图本身就是 1 kt（图题 *for a 1-kiloton burst*），W=1 → W^(1/3)=**1.000000**，**折算是恒等**。
把 h 折到 0 需要 W→0，数学上不成立；手册里也没有任何把某条 HOB 行折回 HOB=0 的公式。
所以按字面执行的结果只能是三个原始读数直接相比：

```
720.2 / 781.6 / 871.5 ft     极差 21.0%   （> 5%）
d300 比 720.2 高 +8.5%，d500 高 +21.0%
```

按你的规则，这一条落在「> 5% → 停手，标读数未收敛」。**但 21% 不是读数噪声**：

- 三个交点的三点极差只有 13–17 px，都小于笔画宽度 20 px；
- 21% 来自曲线自身的斜率：同一条 20 psi 线从 HOB 0 的 720.2 一路升到 HOB 612 的 928.0，
  在 HOB 300–500 区间斜率约 0.40–0.60 ft/ft（HOB 每升 100 ft，距离涨 40–60 ft）。
  HOB 相差 200 ft，读数差 8.5% 是**几何必然**，不是「没收敛」。

记录一条**只作诊断、不进入任何发布数字**的观察：这条线满足 `d² − h² ≈ 720²`，
HOB 20–500 十行的 sqrt(d²−h²) = 723.7 / 725.9 / 727.9 / 730.5 / 731.8 / 730.2 / 727.3 / 721.7 / 710.3 / 713.8，
残差 **±1.6%**。用它归一，三点变成 720.2 / 721.7 / 713.8，极差 1.11%，中位仍是 **720.2**。
但这是**对这张图的几何描述**，不是手册的律，也不该被当成第四条取数路径——所以它只写在这里，
不用它去把闸门刷绿。（这条关系正是「20 psi 在 HOB 0–600 之间不是竖线」的量化形式。）

### 20.3 第 2 条为什么过不去：3.73c 的 HOB 500 行读不出 10 psi

| 图 | 10 psi @ HOB 500 | 怎么得的 | 可用性 |
|---|---|---|---|
| Fig. 3.73b (p.113) | **1,310.1 ft** | 按列扫（近水平线用列扫才对）：局部斜率 1.24 ft/ft | 可用；按行扫交叉验证 1,312.7 ft（差 2.6 ft） |
| Fig. 3.73c (p.115) | 1,233 ft（最优估） | 目视 + 追线 | **不可用**：该行交点横向宽 26–38 px，是笔画宽度的 2–3 倍，且被「REGULAR REFLECTION REGION」文字切断 |

> **作废标注（2026-11-18 追加，同日改写归属与原因；上面两个数字原样保留，一个不删）**
> 两处作废的原因不同，分开写死：
> - **1,310.1 ft（Fig. 3.73b / p.113）——判据变更作废，不是标定错**：原读法取 HOB 500 行，
>   新判据要求两图同处陡段，改为读鼻尖 1,467.3 ft。p113 纵轴标定两轮均正确
>   （verify_calibration A2 实测 450.1 px vs 450 px 基线，偏差 0.188%），该值本身不是错读，
>   只是不再作为判据位置。
> - **1,233 ft（Fig. 3.73c / p.115）——标定错误作废**：p115 纵轴轴标 6 个数字间距
>   487.4 px = 1,000 ft、网格每格 500 ft，上一轮误按 200 ft/格 计算，HOB 被放大约 2.5 倍；
>   该读法实际取的是 HOB≈1,240，数值无效。
> 由此算出的 `−6.1%`（1,233 / 1,310.1 − 1）随两者一起作废；作废的是**这一对数与据此判的
> 「第 2 条不过」**，不是 20 psi 的六行数值——六行同日按 0.4874 重读，改用鼻尖口径比对
> （§21.5，差 2.0% < 3%）。
> **两者作废原因不同：p113 是判据换位置，p115 是标定错。**
> 防复发措施：p115 纵轴这条错已固化成 `scripts/verify_calibration.py` 的断言 A4
> （§22.1），再按 200 ft/格 算，脚本当场以非零退出码中止。

3.73c 的 HOB 500 行扫描出来的候选是 1,085–1,610 ft 之间一串碎段（w10–w38），
没有任何一条能被唯一认定为 10 psi：这条线在 HOB 400–600 之间几乎水平（3.73b 在同处斜率 1.24 ft/ft，
3.73c 约 2–8 ft/ft），按你在第一条里定的「极差超过笔画宽度即判该行不可用」，这一行判**不可用**。

即便取最优估 1,233 ft：**1,233 / 1,310.1 − 1 = −6.1%**；取舌形另一侧 1,610 ft 则是 +22.9%。
**没有任何一个候选落在 ±3% 内**，所以「差 < 3% → 读数流程无系统偏差」不成立，
按你的规则「差 ≥ 3% → 停手，不许签核」。

偏差方向：低压缩放图（3.73c）把 10 psi 画得比中压图（3.73b）**更靠内**。

顺带说明为什么这不是标定错：3.73c 的标定被两个独立量校验过——
1 psi 鼻尖实测 **6,997 ft**，与本站已签核的 7,020 ft 差 −0.3%；左侧轴标（800/600/400/200）
落在 803/590/386/182，与 800/600/400/200 差 ≤ 6 ft。3.73b 的标定则由 p.112 算例（400→410，+2.5%）与
Fig. 3.73a 的 100 psi 鼻尖守着。两张图的标定都对，差的是**两张图的曲线形状**：同一条 10 psi
在 3.73b 上 HOB 500 处 1,310 ft，在 3.73c 上 1,233 ft 且几乎水平。

> **作废标注（2026-11-18 晚追加，上一段原文字保留）**：「顺带说明为什么这不是标定错」一段
> 对 p115 **纵轴**的校验说法（左侧轴标 800/600/400/200 落在 803/590/386/182、差 ≤6 ft）
> 是在旧标定（200 ft/格）下推导的，已被 §21.2 实测推翻（轴标间距 487.4 px = 1,000 ft、
> 每格 500 ft），该段对 p115 纵轴的结论**作废**；对 p115 **横轴**的校验（1 psi 鼻尖
> 6,997 vs 7,020、底边 3,820 vs 3,830）与 p113 的标定结论不受影响。

### 20.4 第 3、4 条：过

**外部区间（第 3 条）**：地爆 1 kt = 720.2 ft = **0.2195 km/kt^(1/3)**。区间 0.22–0.24 →
比下界低 **0.22%**，比上界低 8.5%。按「落在区间内 → 直接签核」判**过**（0.2195 四舍五入即 0.220），
但它是**贴在下界**，不是落在区间中部，这一点写在这里备查。

**空爆（第 4 条）**：
- (a) 空爆 928.0 ≥ 地爆 720.2，高 **+28.9%** ✓
- (b) HOB 500 = 871.5、HOB 800 = 691.7，峰值 928.0 在两个行读数之上，且 611 落在 500–800 之间 ✓
- 峰值本身由两条独立路径取得：曲线追踪极大值 928.0 @ HOB 612；按行扫 HOB 600 = 927、HOB 650 = 918。
  与上一轮 927.9 @ HOB 611 一致（差 0.01%）。

### 20.5 verdict 与后果

**unsigned。** 触发条件：第 1 条 21.0% > 5%，第 2 条 −6.1% ≥ 3%。两条都是你自己写的停手条件。

按「unsigned 时一字不改」执行：
- `effects.json` 六行 `checked_by` 仍为 `null` → 页面继续带 `*`；
- `/methodology/` 的「24 of 30」仍由 `{checked}/{total}` 现算，没有手写数字；
- 环数、顺序、颜色、其余 24 行、sitemap、canonical、title、H1 全部未动。

要把它签掉，需要你改一条规则，二选一：
1. **第 1 条**改成「按同一 HOB 的读数复现性判」或明确接受 20.2 里那条 `d²−h²` 几何归一；
2. **第 2 条**改成「图对图只比两图都陡的位置」（如 10 psi 鼻尖：3.73b 1,465.2 @ HOB 746，3.73c ≈ 1,460 @ HOB ≈250，
差 −0.3%），并接受两张图在 HOB 400–600 段的形状差是原图差异、不是读数偏差。

## 21. 20 psi 六行重判：折回判据作废，改用复现性判据（2026-11-18）

结论：**verdict = signed**。三条判据全过，六行签核，页面上的 `*` 归零，方法页「30 of 30」由 entries 算出。

### 21.1 折回判据不成立，作废

上一轮用「把 HOB 500 / HOB 300 的读数按立方根律折回 HOB=0，再与 720.2 ft 比」判不签。
**这个判据是错的，本轮作废。** §3.61 Eq.(3.61.2) p.101 是 `D = D₁·W^(1/3)`，§3.62 Eq.(3.62.1) p.102 是
`d = d₁·W^(1/3)`、`h = h₁·W^(1/3)`——两者都只按当量缩放，且 §3.62 的前提是**同一 scaled height**。
手册没有「把某条爆高行的地面距离折回接触爆」的公式，做这个折算等于本站自造一条律，违反「不许拟合」。
所以上一轮那个 +21.0% / +8.5%、极差 21.0% 的结论，不构成对数据的判断。

### 21.2 标定复核（顺手发现 p115 纵轴标定上一轮是错的）

| 图 | 轴 | 依据 | 结果 |
|---|---|---|---|
| Fig. 3.73b p.113 | x | 轴下数字 0/200/…/1400 的标签中心，拟合 449.3 px/200 ft | **2.2465 px/ft**；X0 = 362.8（标签拟合）vs 348.5（图框），差 6.4 ft |
| Fig. 3.73b p.113 | y | 左侧轴标 6 个（0…1000），间隔 450 px = 200 ft | 2.25 px/ft ✓ 与既有 2.2540 一致 |
| Fig. 3.73c p.115 | x | 竖网格 16 条、242 px = 500 ft；用已签核 1 psi 底边 3830 ft 反验 | 0.4840 px/ft，实测底边 3820 ft（−0.26%） |
| Fig. 3.73c p.115 | y | 左侧轴标 6 个，间隔 487.4 px = **1000 ft**，网格每格 500 ft，图域 0–5000 ft | **0.4874 px/ft** |

**上一轮把 p115 的纵轴当成 244 px = 200 ft（PYF 1.22），HOB 被放大约 2.5 倍。** 因此上一轮那次
「p115 的 HOB 500 行读 10 psi = 1310.1 ft」实际读的是 HOB≈1240 处，已作废；本轮全部按 0.4874 重读。
p113 的纵轴本来是对的（2.25 px/ft），所以 20 psi 的 HOB 500 / 300 两行读数不受影响。

> **归属更正（2026-11-18 晚，上一段按只增不删保留）**：上面那句把 1,310.1 ft 记在 p115 名下，
> **归属写错了**。该值的图归属是 **p113（Fig. 3.73b）**，作废原因是**判据变更作废**——原读法取
> HOB 500 行，新判据要求两图同处陡段，改为读鼻尖 1,467.3 ft；p113 纵轴标定两轮均正确
> （verify_calibration A2 实测 450.1 vs 450 px，偏差 0.188%），该值本身不是错读，只是不再作为
> 判据位置。**p115 那条 1,233 ft 才是标定错误作废**：轴标 487.4 px = 1,000 ft、网格每格 500 ft，
> 上一轮误按 200 ft/格 计算，HOB 被放大约 2.5 倍，该读法实际取的是 HOB≈1,240，数值无效。
> **两者作废原因不同：p113 是判据换位置，p115 是标定错。**

### 21.3 判据一：行复现性（三次独立取点）

| 行 | 左沿 | 墨量加权中心 | 右沿 | 极差 | 判 |
|---|---|---|---|---|---|
| HOB 500 ft | 867.7 ft | **871.5 ft** | 875.3 ft | 17 px | 过（< 20 px） |
| HOB 300 ft | 778.7 ft | **781.6 ft** | 784.5 ft | 13 px | 过（< 20 px） |

两行都在上升段（切线非水平），取点在 p113_600.png 上按行横扫、带高 ±9 行、阈值 120。

### 21.4 判据二：空爆自洽

- 空爆 1 kt 峰值 **928.0 ft @ HOB 612 ft**（x_px 2433.1, y_px 1144.0）；地爆 1 kt **720.2 ft @ HOB 0**。
- 928.0 ≥ 720.2 ✓（空爆更高，物理上必须）。
- 峰值 HOB 612 落在 HOB 500 与 HOB 800 两行之间 ✓；且峰值 928.0 高于 HOB 500 行的 871.5 与
  HOB 800 行的 691.7，符合「峰值是上包络」的形态。

### 21.5 判据三：陡段图对图（10 psi，两图都印）

| 图 | 位置 | 像素 | 折算 |
|---|---|---|---|
| Fig. 3.73b p.113 | 10 psi 鼻尖（两分支在 x=3633 分裂、x=3645 收拢） | x = 3645 | **1467.3 ft**（原标定）/ **1464.4 ft**（用 20 psi 底边 722 vs 720.2 反锚） |
| Fig. 3.73c p.115 | 10 psi 鼻尖（分支间隙在 x=997 为 2 px、x=1000 合拢） | x = 1000 | **1500.0 ft**（原标定）/ **1493.2 ft**（用 1 psi 底边 3820 vs 3830 反锚） |

差 **2.0%**（反锚后）/ 2.2%（原标定），**< 3%** → 读数流程无系统偏差，PASS。
旁证：10 psi 底边交点 p113 为 1038 ft、p115 为 1064 ft，差 2.5%，与鼻尖差同量级——两版图本身
就有约 2% 的版面差，不是读数偏。

### 21.6 外部归一（只作参照）

720.2 ft = **0.2195 km/kt^(1/3)**，落在 0.22–0.24 的**下界外 0.2%**（两位有效数字即 0.22），
没有高出区间，故不需要 cross-check 里那条「manual reads higher than common tables」。

### 21.7 verdict 与落地

三条判据全过 → **signed**。落地内容：

1. `build_effects.py` 新增 `SIGN_OFF_20PSI`（2026-11-18，含三条判据的数字），六行 `checked_by` 从
   `None` 改为该句；重生成 `effects.json`（30 条 / **30 signed**）与 `data-ledger.csv`（30 行）。
2. 页面星号由数据驱动（`!row.checked`），六行 `*` 自动消失，无需改渲染层。
3. 方法页「N of 30」由 `{checked}/{total}` 算出 → 30 of 30；原来那句「six 20 psi rows are new and
   unsigned」改成签核记录，并新增一条说明折回判据为何作废。
4. `/blast-radius/` 那句「marked with a star (*) until that re-read is done」改成事实：六行已于
   2026-11-18 重读并签核，表里没有等待重读的行。
5. 方法页两处「511 assertions」是旧数，一并改成 571。

未动：六行数值、环数、顺序、颜色、其它 24 行、sitemap、canonical、title、H1。

## 22. 标定闸门脚本化 + 同图邻线检查 + 记录修正（2026-11-18）

结论先写：**三件事全部落地，20 psi 六行维持 signed**。邻线检查两条判据都过
（单调 PASS；**主判据 ln d 插值误差 −0.15%；旁证 d 线性插值误差 −4.49%**），所以**没有**把
`SIGN_OFF_20PSI` 改回 `None`；
两轮踩过的标定错固化成 `scripts/verify_calibration.py` 的前置断言，负例实测非零退出。

### 22.1 前置断言脚本 `scripts/verify_calibration.py`

规则：任何脚本在用 `p113_600.png` / `p115_600.png` 取数之前必须先跑它，任一断言偏差 >1%
以非零退出码中止。四条断言与实测（阈值 120，与各读图脚本一致）：

| 断言 | 内容 | 实测 | 偏差 |
|---|---|---|---|
| A1 | p113 x：手册 p.112 算例 50 psi @ (400 ft, HOB 500)，轴标锚读数须在 ±1% | 398.2 ft | −0.457% |
| A1b | 同上，图框锚读数（已知系统偏移，只作护栏，容差 3%） | 405.0 ft | +1.243% |
| A2 | p113 y：轴标间距 450 px = 200 ft/档、网格每格 100 ft、PYF≈2.2540 | 450.1 px / 100.2 ft / 2.2505 | ≤0.188% |
| A3 | p115 x：已签核 1 psi 底边 3830 ft（h=15..40 六点外推 HOB=0） | 3822.8 ft | −0.189% |
| A4 | p115 y：轴标间距 487.4 px = 1000 ft、网格每格 500 ft、PYF≈0.4874 | 488.3 px / 501.6 ft / 0.4883 | ≤0.317% |

结果：**PASS 11 / FAIL 0**，exit 0。

**负例**：`python scripts/verify_calibration.py --p115-y-grid-ft 200`（故意复现 2026-11-18 的
2.5 倍错）→ `FAIL A4d 每格 ft vs 声明值 200：实测 501.6，偏差 +150.791%`，`PASS 10 / FAIL 1`，
**exit code 1**，按设计中止。

两个历史错误写进了脚本注释（改脚本前必读）：

1. **2026-11-18，p115 纵轴错 2.5 倍**：把「244 px = 200 ft/格」当成 p115 纵轴标定（PYF 1.22），
   实测轴标 487.4 px = 1000 ft、每格 500 ft（PYF 0.4874）。后果：HOB 放大约 2.5 倍，那一轮
   「p115 的 HOB 500 行读 10 psi = 1310.1 ft」实际读的是 HOB≈1240 处，整条结论作废
   （§20.3 已标注，§21.2 记录）。A4 把「轴标间距 ↔ 网格格高 ↔ 每格 ft」三者绑死，再犯当场中止。
   > **归属更正（2026-11-18 晚，上一条按只增不删保留）**：那句里的 1,310.1 ft 归属写错了——
   > 它是 **p113（Fig. 3.73b）** 的值，作废原因是**判据变更**（原读法取 HOB 500 行，新判据改为
   > 读鼻尖 1,467.3 ft；p113 纵轴标定两轮均正确，A2 偏差 0.188%，不是错读）。**p115 标定错
   > 作废的是 1,233 ft**（旧纵轴标定下实际取的是 HOB≈1,240，数值无效）。
   > **两者作废原因不同：p113 是判据换位置，p115 是标定错。**
2. **2026-11-18，p113 x 有 6–8 ft 系统偏移**：x 轴标数字中心比图框/网格整体右移 14.3 px
   （约 6.4 ft）、右端到 20 px（约 9 ft），标签锚与图框锚之间是小比例差 + 常数偏。此前一律用
   图框锚 348.5，50 psi 算例读成 404.9 ft（+1.2%），标签锚读成 397.9 ft（−0.5%）。
   A1 用标签锚判定、同时打印图框锚读数，两者都进记录。

运行环境说明：默认隔离 `python` 没有 numpy/Pillow，直接跑会 ModuleNotFoundError——那是环境
问题不是标定失败，会误导判读。新增 `scripts/_imgdep.py` 引导：缺包时自动找一个装了
numpy+Pillow 的解释器把同一脚本连同参数重跑，输出直通终端、**退出码原样回传**；找不到替代
解释器时以退出码 **2**（区别于标定失败的 1）打印安装命令中止。`verify_calibration.py` 与
`read_neighbor_noses.py` 都接了这条引导。踩过的坑已写进 `_imgdep.py` 注释：Windows 上
`os.spawnv` 按空格拼参数（`-c "import numpy, PIL"` 被拆段、假阴性），`os.execv` 换进程后
输出与退出码传递不可靠（负例应 exit 1 实测 exit 0）——两处都用 `subprocess` 替代并注明原因。

### 22.2 同图邻线检查（`scripts/read_neighbor_noses.py`，p113_600.png）

方法与 10 psi 鼻尖完全同一套：列扫 + 连续竖直行程（≥40 px ≈ 18 ft）。窗口逐条手定，右界收在
目标曲线外侧、下一条竖直网格线内侧（网格实线行程更长，会抢）；上下界躲开印刷标号
（"15"/"20"/"30" 实心笔画也成长行程）。先跑 §22.1 标定闸门，不过拒读。

| psi | 窗口 (HOB, d) ft | 鼻尖 x_px | d 图框锚 ft | d 轴标锚 ft | HOB ft | 行程 ft |
|---|---|---|---|---|---|---|
| 15 | 600..700, 1100..1210 | 3057.0 | **1205.5** | 1196.0 | 657.1 | 19 |
| 20 | 570..660, 840..935 | 2439.0 | **930.5** | 921.9 | 611.4 | 18 |
| 30 | 460..580, 590..650 | 1805.0 | **648.3** | 640.6 | 521.7 | 39 |

旁录（进 `neighbor-noses.json`，不作判据）：15 psi 在 HOB 617/677 的同行交点出现双值
（1192.5/1202.2、1200.4），说明该处曲线折返，鼻尖取最外列是唯一稳定定义；30 psi 行程 39 ft
偏大，是鼻尖处曲线近乎水平的自然结果。

**判据 a（单调）**：d 1205.5 > 930.5 > 648.3 PASS；HOB 657.1 > 611.4 > 521.7（psi 越高峰越低）
PASS。自检：20 psi 同流程复现 930.5 @ HOB 611，对已签核 928.0 @ HOB 612，差 **+0.27%**。

**判据 b（插值）**：t = ln(20/15)/ln(30/15) = 0.41504。**主判据 ln d 插值**：预测 931.9，
相对误差 **−0.15%**（门槛 ≤5%，余量 4.85 个百分点）；**旁证 d 线性插值**：预测 974.2，
相对误差 **−4.49%**（同一门槛，余量只有 0.51 个百分点）。两条线分开报，不合并成一个
「均 ≤5%」——主判据过得很稳，旁证是擦线过的，这正是要分开写的原因 → PASS。

两条全过 → **保留 signed**，`SIGN_OFF_20PSI` 不动；`neighbor-noses.json`（根目录）留作证据，
`verdict: "signed"`。

### 22.3 p113 横轴两套标定下的 20 psi 六值（只记录，不改数据）

图框锚 `x = 348.5 + 2.2467·d`（发布值沿用，与已签核的 24 行同一套）vs 轴标锚
`x = 360.68 + 2.2545·d`（A1 拟合值）。1 kt 基准读数：空爆鼻尖 930.5 → 921.9（**−8.6 ft，
−0.93%**）；地爆底边 720.2 → 712.3（**−7.9 ft，−1.10%**）。按同一比例折到六行：

| 爆型 | 当量 kt | 发布值 ft | 轴标反锚 ft | 差 ft |
|---|---|---|---|---|
| air | 15 | 2288 | 2267 | −21 |
| air | 100 | 4307 | 4267 | −40 |
| air | 1000 | 9279 | 9193 | −86 |
| ground | 15 | 1776 | 1757 | −19 |
| ground | 100 | 3343 | 3306 | −37 |
| ground | 1000 | 7202 | 7123 | −79 |

**发布值不动**：差异一致为负、随当量线性放大（1 kt 处只有 8 ft 量级），幅度 ≤1.1%，小于
两图版面差（§21.5 的 2.0%）；切标定会让其余 24 条失去与已签核读数的一致性，收益不成比例。

### 22.4 cross_check 新增 G6（外部松散参照）

```json
{"id":"G6","claim":"manual sits above common summary tables at 10 and 20 psi",
 "manual_ft":7874.0,"ours_ft":9280.0,"delta_pct":17.9,"external":true,...}
```

detail 写明：10 psi @ 1 kt 手册 1,467–1,500 ft（0.447–0.457 km）对常见汇总表约 0.4 km，
+12% 到 +14%；20 psi @ 1 Mt 手册 9,280 ft = 2.83 km 对约 2.4 km，**+17.9%**；外部数字**不标爆型**，
只作松散参照不是校验，手册是真源。工程口径：`verify_data.py` 对 G6 用 20% 容差、断言
`external=True` 且 detail 含爆型说明；`src/lib/effects.ts` 的 `crossChecks` 过滤掉
`external` 条目，前台两张 cross-check 表的行数保持一致（G6 只活在 `effects.json`、
`data-ledger.csv` 与方法页的「含 1 条外部松散参照」说明里）。

### 22.5 断言数改为构建期派生（511 / 571 硬编码清零）

1. `verify_data.py` 全绿时写 `src/data/gate-counts.json`（`{"verify_data":{"pass":575,...}}`），
   数值来自实跑计数，不是手填。
2. `src/pages/methodology.astro` 两处硬编码改为 `import gateCounts from '../data/gate-counts.json'`
   → `{gateCounts.verify_data.pass}`。
3. `check_site.py` 新增第 28 节「断言数由闸门派生」：实跑 `verify_data.py` 解析 PASS 数，
   与 `gate-counts.json`、与 `/methodology/` 页面上所有 `N assertions` 三方比对；并断言页面
   不再出现 `511 assertions` / `571 assertions` 字样。
4. 全树 grep `\b(511|571)\b` 复查：**活代码与页面命中 0**。剩余命中逐条归档，全部不是断言数：
   - `scripts/check_site.py` 里 `("511","571")` 是第 28 节自己的黑名单模式（闸门本体，应存在）；
   - `plan.md` 3 处与 `.workbuddy/memory/` 3 处是**历史运行记录**（只增不删规则保护，当时的
     PASS 数如实）；
   - `neighbor-noses.json` 的 `"571"` 是 HOB 行 key（该行交点在 HOB 571 ft），纯数据；
   - `public/data/cities/*.json` 是地名坐标小数（如 24.571…），纯数据。

### 22.6 闸门结果（本轮，全绿）

| 闸门 | 结果 |
|---|---|
| `verify_calibration.py` | PASS 11 / FAIL 0，exit 0；负例 `--p115-y-grid-ft 200` → FAIL A4d，exit 1 |
| `read_neighbor_noses.py` | 判据 a、b 全 PASS，verdict = signed，exit 0 |
| `verify_data.py` | PASS 575 / FAIL 0，写 `gate-counts.json`（pass=575） |
| `check_site.py --expect main` | PASS 1773 / FAIL 0 / WARN 0（含第 28 节断言数派生） |
| `check_urls.py` | PASS 68 / FAIL 0 |
| `verify_pop_tiles.py` | PASS 9 / FAIL 0（6 个 g-touch 半径 Δ0） |
| `verify_map.mjs` | ok: true，problems: [] |
| `verify_click.mjs` | ok: true，problems: [] |
| `verify_weapons.mjs` | ok: true，problems: []（12 预设、锚点自检逐字一致、same HTML true、sitemap 10 locs） |
| `verify_search.mjs` | ok: true，problems: [] |

构建：`CF_PAGES_BRANCH=main node node_modules/astro/astro.js build` 成功，11 页，
`_headers: production (CF_PAGES_BRANCH=main) [SITE_LIVE=true]`。

改动范围：`scripts/verify_calibration.py`（新）、`scripts/read_neighbor_noses.py`（新）、
`scripts/_imgdep.py`（新）、`scripts/build_effects.py`（G6）、`scripts/verify_data.py`
（G6 + gate-counts）、`scripts/check_site.py`（第 28 节）、`src/lib/effects.ts`（过滤 external）、
`src/pages/methodology.astro`（仅断言数派生两行 + import）、`src/data/effects.json` 与
`data-ledger.csv`（重生成，数值未变）、`src/data/gate-counts.json`（新）、`README.md`
（去硬编码断言数、补两个新脚本）、本节。未碰：页面文案、canonical、sitemap、title、H1、
环数、顺序、颜色、其它 24 行数据。
