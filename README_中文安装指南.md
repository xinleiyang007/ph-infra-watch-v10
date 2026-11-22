# PH Infra Watch V10.0 — 完整新仓库部署说明

> 目标：用多个公开媒体、官方公告与政府 PDF/Excel 获取信息，并在 GitHub Pages 展示、中文／英文切换、核对时效、去重、筛选、地图和导出。
>
> **这是可部署的完整源码和基础数据库，不是「全菲律宾所有公开项目」的完整事实库。** 首次部署之前新闻候选数据为空；后台需要首次联网运行才能生成。已收录的 266 条项目是历史公开来源快照，不能自动等同当前在建或招标。

## 1. 三个最重要的按钮

- **刷新信息**：浏览器立即重新请求本站 `data/*.json`，并附带缓存规避参数；**只读取最近一次成功部署的数据，不会现场爬取新闻**。上一次后台采集何时成功，可以看顶部的“最近后台采集”。
- **中文 / EN**：一键切换中英文操作界面和**已生成**的翻译。若某篇文章没有中文译文，则在中文版展示英文原文和“待翻译”提示。翻译是离线机器翻译或可选 AI 模型生成，**绝不把英文复制到中文字段后假装翻译成功**。
- **去 GitHub 执行采集**：跳到当前仓库 GitHub Actions 工作流页面。必须有仓库操作权限，登录 GitHub 后点击 **Run workflow → main → Run workflow**。静态页面不存储 GitHub Token，所以不能匿名直接启动远程采集。

## 2. 用户能看到的时效性

- **最近后台采集时间**：`data/media_status.json.generated_at`；与打开网页的时间分开。
- **最新新闻发布时间**：所有已存新闻的 `published_at` 最大值。该时间可能远早于采集时间，不能混淆。
- **来源成功率**：本次成功请求入口数 / 配置入口总数，失败原因在「来源与时效」页面里。
- **中文翻译覆盖率**：已有 `title_zh` 的文章数 / 全部文章数，不代表 AI 摘要质量。
- **超过 24 小时**：页面显示醒目的数据过期提示。定时工作流延迟、来源临时不可达也会造成不新鲜。

## 3. V10 完整目录（所有文件已在 ZIP 里）

```text
ph-infra-watch-v10/
├── index.html                  # 入口：首页是新闻情报流
├── assets/
│   ├── app.js                 # 过滤、翻译切换、刷新、地图、企业、CSV
│   └── style.css              # 响应式工作台
├── data/
│   ├── projects.json          # 266 个已收录项目
│   ├── companies.json         # 227 个历史企业/主体档案
│   ├── media_leads.json       # 新闻候选种子，首次运行前 0 条
│   ├── media_status.json      # 25 组来源采集状态
│   ├── document_leads.json    # PDF/Excel 摘录
│   ├── document_status.json   # 文档源状态
│   ├── translation_status.json
│   └── ai_status.json
├── config/
│   ├── news_sources.json      # 新闻和官方公开索引的25组入口
│   └── document_sources.json  # 公开 PDF 地址；可扩展 Excel
├── scripts/
│   ├── collect_news.py        # RSS 自动采集与标题去重
│   ├── restore_previous.py    # 从上次 Pages 成功快照恢复历史
│   ├── collect_documents.py   # PDF 和 XLSX 提取
│   ├── link_candidates.py     # 保守关联建议；不改项目主库
│   ├── translate_news.py      # Argos 离线英译中
│   ├── ai_enrich.py           # 可选 Gemini 双语摘要
│   └── validate_data.py
├── .github/workflows/
│   └── collect-and-deploy.yml # 自动采集、翻译与 Pages 发布
├── tests/
│   └── test_pipeline.py
├── docs/                       # 来源说明、验收清单及预览
└── README_中文安装指南.md
```

## 4. 重新创建全新 GitHub Repository

你此前每次升级都建立新仓库，因此推荐此版使用 **`ph-infra-watch-v10`**，旧 V7–V9 不必删除。

1. 在 **GitHub Desktop** 中选择 `File → New repository`，Name 填写 `ph-infra-watch-v10`，Local path 选择 `文档\GitHub`；**不要**克隆旧版本后再覆盖。
2. 下载 ZIP、右键全部解压。进入解压后的 **PH_Infra_Watch_V10 文件夹内部**，全选 `index.html`、`assets`、`data`、`config`、`scripts`、`.github` 等内容，**复制内容本身**到 `文档\GitHub\ph-infra-watch-v10`，不要将外层文件夹再复制一次。
3. GitHub Desktop 显示 changed files 后，Summary 写 `Add complete PH Infra Watch V10`，点 **Commit to main**。
4. 点 **Publish repository**，如果用 GitHub Free 免费 Pages，请设为 **Public**。检查文件内没有私人密码或 API 密钥后再公开。
5. 浏览器打开 `https://github.com/xinleiyang007/ph-infra-watch-v10/settings/pages`，在 **Build and deployment → Source** 选择 **GitHub Actions**，不用创建 Static HTML 模板工作流。
6. 打开 `https://github.com/xinleiyang007/ph-infra-watch-v10/actions/workflows/collect-and-deploy.yml`，点击 **Run workflow → main → Run workflow**。首次运行会尝试联网获取 25 组新闻索引、2 份官方 PDF 并执行离线翻译。
7. 查看 `collect-translate-deploy` 中 `Configure GitHub Pages`、`Upload static artifact`、`Deploy to GitHub Pages` 都显示成功后，预计访问：`https://xinleiyang007.github.io/ph-infra-watch-v10/`。
8. 回到网页点击 **刷新信息**；「来源与时效」会显示最近一次采集时间、实际成功来源数和具体失败信息。

**如果首次运行出现 `Get Pages site failed · Not Found`：**确认仓库 Public 且 Pages Source 为 GitHub Actions；如 Pages 仍未初始化，可在 Pages 暂切 `Deploy from a branch → main/(root)` 并保存，然后再切回 GitHub Actions，再**启动一个全新** Run workflow。不要修改文件夹层次，也不用重复新建仓库。若仍不行，应查具体工作流日志。

## 5. 后台运行模式与 GitHub Desktop 冲突

- 默认时间：每个菲律宾日期约 **08:17 / 14:17 / 20:17**（GitHub schedule 使用 UTC，可能延迟或偶尔跳过）。
- 自动采集的数据只进入本次 **Pages 发布产物**，不会自动向 GitHub 的 `main` 分支提交。**GitHub Desktop 不会因为每次定时采集而不断遇到 fetch-first 冲突**。
- 下次任务从上一次成功发布的 Pages `data/media_leads.json` 获取历史记录，再添加去重后的新线索；如果无法获取历史，可能丢失尚未另行备份的旧新闻。需要长期档案时应定期导出 CSV，或以后改为专用持久数据库。
- RSS 采用原始网站公开内容或 Google News 定向索引。**配置了 25 组不等于 25 组都能成功采集**。新闻本站只保存短摘录与原文链接，不复制整篇受版权保护的文章。

## 6. 中英文翻译与 AI 简述：两种模式

**默认无需付费 API：** GitHub Actions 将尝试安装 [Argos Translate](https://github.com/argosopentech/argos-translate) 的 English → Chinese 模型，对新采集标题和短 RSS 摘录进行离线翻译。首次运行可能需下载模型；下载失败、没有模型、翻译异常时会在 `data/translation_status.json` 留错误，网页保留原文并标记“待翻译”。离线翻译质量有限，必须与原文核对。

**可选 AI 双语摘要：** 在仓库 **Settings → Secrets and variables → Actions → New repository secret** 中新增 `GEMINI_API_KEY`。工作流可在服务器端基于新闻标题+短摘要生成 `summary_zh` 和 `summary_en`，会注明**仅基于 RSS 摘录，而非全文阅读**。无需密钥时这一步自动跳过，不影响新闻采集与网站发布。根据 Google 的 API 当前价格、免费额度、配额及地区限制，有可能产生费用；请先在 Google AI Studio 设置预算和限制。**绝不可把密钥粘贴在 HTML、JS、仓库公开文件中。**

注意：新闻正文没有自动抓取，源网站文章如果 404 或无法全文解析，摘要依然只可能依据标题与 RSS 摘要；生成内容不可当成 EPC 或投资方的确认证据。

## 7. 项目地图与 PDF/Excel 信息处理

- `projects.json` 保留 266 条原项目（DOE 数据为主），地图标记是**省／市镇参考位置**，不是实际工地坐标。
- 采集新闻后 `link_candidates.py` 只在名称高度吻合时生成 `candidate_project_ids`，这是**待核验关联建议**，不能自动把新闻推入正式项目库。
- `collect_documents.py` 可实际下载并解析 `config/document_sources.json` 中启用的 PDF；也支持 `.xlsx`，需要你填入真实公开 Excel URL 并设 `format: "xlsx"`。默认配置了两份 DOE PDF；没有预装一个未经确认的 Excel 地址。
- 文档抽取仅保存页码、表格行信息与短摘录，不自动将内容当成真实 EPC 中标或新项目。
- 新闻线索和项目台账均支持 CSV 导出；项目数据与机器翻译不可代替原始官方证据。

## 8. 发布后验收清单

请在网页核实：

1. 网站首页显示 **10.0 / AI 情报聚合**，不再默认只有地图。
2. 右上角 **刷新信息** 能触发重新请求 `data/*.json`，显示已发布快照刷新提醒。
3. **中文 / EN** 能切换菜单与中文已译新闻；无译文的英文新闻标注待翻译。
4. 顶部能看到后台采集时间，右侧「来源与时效」能查看每源状态。
5. 进入项目地图能看到有坐标的项目；不能加载外部瓦片时不影响项目列表。
6. 项目台账显示 266 条记录（若没有新增正式项目），企业关系可按公司角色查找。
7. 新闻与项目筛选后 CSV 导出正确；没有未经证实的新闻自动进入正式项目主库。
8. 若新闻仍是 0 条，查看 `data/media_status.json`，区分首次采集未运行、来源失败或确实没有匹配新闻。

**务必注意：本交付包的自动化运行、实时源成功率及第一次正式翻译成功率，仍需要你部署到 GitHub Actions 后才能最终确认。本地测试使用了标明为模拟的测试新闻，不会作为事实数据交付。**
