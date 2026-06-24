# handoff 子能力 · 策划版验收清单生成器

> AIGD 包 `aigd-handoff`(定稿后)的一项产出。把**工程版 Gherkin 验收用例 + 配置真值**自动翻成「策划/QA 拿着游戏逐条勾」的清单(md + xlsx)。
> 产物形如 `<系统目录>/<系统名>-05验收用例-策划版.md / .xlsx`(已试跑通过)。

## 定位
- 同一份验收真源,多受众:**工程版**(Gherkin,字段引用,喂测试自动化)↔ **策划版**(真值代入,大白话,喂人工验收)。
- 属交接包、平台无关(md/xlsx);不碰技术栈。

## 输入(从 manifest 跨层索引取)
- 该系统工程版 `-05验收用例`(Gherkin,挂 R-编号)
- 该系统引用的配置表 + LocalizationText(manifest「数据层 / 引用共享」栏)

## 产物(双份)
- `<系统>-05验收用例-策划版.md` —— 人读:分功能表,每条 = 测试点 / 前置 / 操作 / 预期(真实数值) / 实测 / 通过
- `<系统>-05验收用例-策划版.xlsx` —— QA 勾选:**说明页**(用法 / 测试对象 / 更新记录 / 待确认 / 进度统计公式)+ **清单页**(下拉 通过/不通过/待测,冻结表头 + 筛选)

## 配方(可复现步骤)
1. **解析配置**:用 `references/scripts/xlsx_dump.py` dump 相关表(openpyxl 会因 `Colors must be aRGB` 报错,脚本走 zipfile+xml 直解);`resolve_loc.py` 解 LocalizationText 文本 id→中文。
2. **代入**:工程版断言里的字段引用(如 `levelTable[50].value`)换成真值(如 `500`),翻成大白话操作步骤。
3. **留痕**:每条挂 R-编号;预期里括号附「来源字段」——数值变只需照字段刷新,**逻辑不动**。
4. **出双份**:md(人读)+ xlsx(QA)。xlsx 直接跑 `references/scripts/gherkin_to_checklist.py <…-05acceptance.md>` 生成(自动抽场景→清单页 + 说明页 + 通过下拉 + 进度公式 COUNTA/COUNTIF/IF,范围已覆盖全部行);md 人读版另排。

## 再同步(配置更新时,已验证)
- 重 dump → 与上次**逐行 diff** → **只改受影响的数字**,其余不动;变化记进「更新记录」。
- 字段引用化是根因:数值表没变时清单数字自动仍有效(如某次更新只补了进化链命名、数值零变化,清单数字自动仍有效)。

## 副作用价值:自动抓配置矛盾
- 代入真值会暴露「策划案 ↔ 配置」不一致 → 直接产出 `[待确认]`。
- 实例:某进化组配 3 阶,但品质表里该品质的"可进化次数"=1 → 第 2 阶之后不可达。

## 读写契约(配合脊柱)
- **读**:manifest 该系统跨层索引(规则 / 验收 / 配置 / 引用共享)。
- **写**:两份策划版文件;发现矛盾时在 manifest 该系统「待重验 / 待确认」栏记一笔。

## 参考实现（已毕业进包）
- **`references/scripts/gherkin_to_checklist.py`** —— 可移植版:`python gherkin_to_checklist.py <…-05acceptance.md> [out.xlsx]`,**从 Gherkin 场景自动抽用例**(不再手列 CASES)→ 出说明页 + 清单页 xlsx。已在多个系统验证。
- 配套 `xlsx_dump.py` / `resolve_loc.py`(解配置表 / 文本 id→中文)。
- **脚本只做"抽场景 → 清单结构"**:断言里的字段引用(`levelTable[50].value`)的**真值代入仍需配合配置**(查 `resolve_loc` / 配表,人工或后续增强),脚本保留原始断言文本不臆造数值。

## 限制
- Windows 无 LibreOffice 时,xlsx 公式校验脚本跑不了(依赖 Unix socket);公式平凡,Excel/WPS 打开自动重算即可。
