# 市场支持与边界

## 日本/韩国个股 suffix-only MVP（Issue #1718，Refs #1718）

当前阶段支持手动输入日本、韩国股票的 Yahoo Finance 后缀代码，进入既有个股分析、历史保存和基础报告展示链路。Web 自动补全内置一批常用日股/韩股种子索引，支持按 suffix 代码、中英文名称或常用别名搜索。

支持格式：

- 日本：`7203.T`、`6758.T`
- 韩国 KOSPI：`005930.KS`
- 韩国 KOSDAQ：`035720.KQ`

约束与边界：

- 手动输入裸代码时会先检索本地/远程股票池；若 `005930`、`000660` 等裸码命中 `005930.KS`、`000660.KS` 等日韩条目，则按命中的市场提交分析；若股票池未命中，仍按既有 6 位数字代码规则默认落到 A 股语义。
- 日股/韩股日线和基础实时/近实时行情只走 `YfinanceFetcher`，不尝试 AkShare、Tushare、Efinance、Pytdx、Baostock 等 A 股专属数据源。
- 基本面复用既有 offshore yfinance 轻量路径；A 股专属资金流、龙虎榜、板块等能力按 `not_supported` 降级。
- 报告 Prompt 已增加日股/韩股市场语义，避免套用 A 股涨跌停、北向资金、龙虎榜、融资融券等概念。
- 交易日历注册 `jp: XTKS / Asia/Tokyo` 与 `kr: XKRX / Asia/Seoul`。若本地 `exchange-calendars` 版本缺少对应日历，既有 fail-open/fail-closed 语义保持不变。

不承诺项：

- 不承诺实时行情；Yahoo Finance 数据可能延迟或字段缺失。
- 不承诺完整基本面、行业/板块、市场宽度、涨跌家数或日韩大盘复盘。
- 不承诺完整日韩全市场股票列表；Web 自动补全当前仅覆盖仓内种子索引中的常用标的，未命中时仍可手动输入 suffix 代码。
- 不补齐 Portfolio 的 JPY/KRW 汇率、成本、市值完整口径；相关字段仅放开市场类型以避免前后端校验拒绝。

回滚方式：移除 `jp/kr` 市场识别、交易日历注册、YFinance 路由扩展、Web/API 类型放行、`scripts/stock_index_seeds/` 日韩种子索引，并删除本文档中的能力声明。

## 台湾个股 suffix-only MVP

当前阶段支持手动输入台湾股票的 Yahoo Finance 后缀代码，进入既有个股分析、历史保存和基础报告展示链路。Web 自动补全内置全量台股种子索引（上市/上柜普通股、创新板与 4 位代码 ETF，约 1900+ 条，来源为 TWSE ISIN 登记快照，由 `scripts/fetch_tw_stock_list.py` 生成），支持按裸代码（`2330`）、简繁体名称（`台积电` / `台積電`）或常用别名（`TSMC`）搜索。

支持格式：

- 台湾 TWSE（上市）：`2330.TW`、`2317.TW`
- 台湾 TPEX（上柜 / OTC）：`6488.TWO`、`8069.TWO`
- base 取 4-5 位数字，覆盖常见个股（4 位，如 `2330`）与热门高股息 ETF（5 位，如 `00878`）。

约束与边界：

- 手动输入裸代码时会先检索本地/远程股票池；若 `2330`、`1101`、`5347` 等裸码唯一命中 `2330.TW`、`1101.TW`、`5347.TWO` 等台股条目，则按命中的市场处理。**裸码在多个市场同时命中时不自动解析**（如 `6861` 同时对应日股 `6861.T` 与台股 `6861.TW`），需输入完整后缀消歧。
- **5 位台股 ETF（如 `00878`）不进入种子索引与裸码解析**：5 位裸码语义已被港股占用（如 `00878` 对应港股 `00878.HK`），为避免劫持既有港股裸码行为，5 位台股标的仅支持完整后缀代码输入。
- 台股日线和基础实时/近实时行情只走 `YfinanceFetcher`，不尝试 AkShare、Tushare、Efinance、Pytdx、Baostock 等 A 股专属数据源。
- 基本面复用既有 offshore yfinance 轻量路径；A 股专属资金流、龙虎榜、板块等能力按 `not_supported` 降级。
- 报告 Prompt 已增加台股市场语义（新台币、央行政策、半导体/电子产业链、T+2 交割、±10% 涨跌幅限制），避免套用 A 股涨跌停板、北向资金、龙虎榜、融资融券等概念。
- 交易日历注册 `tw: XTAI / Asia/Taipei`。若本地 `exchange-calendars` 版本缺少对应日历，既有 fail-open/fail-closed 语义保持不变。
- 主要指数仅接入加权指数 TAIEX（`^TWII`）；上柜指数等暂不承诺。

不承诺项：

- 不承诺实时行情；Yahoo Finance 数据可能延迟或字段缺失。
- 不承诺完整基本面、行业/板块、市场宽度、涨跌家数或台股大盘复盘。
- 种子索引为 TWSE ISIN 登记的静态快照，不含兴柜、特别股、权证、TDR、ETN 与 5 位及以上代码 ETF；新上市标的需重新运行 `scripts/fetch_tw_stock_list.py` 刷新，未命中时仍可手动输入 suffix 代码。
- 不补齐 Portfolio 的 TWD 汇率、成本、市值完整口径；相关字段仅放开市场类型以避免前后端校验拒绝（默认计价币种沿用既有 fallback）。

回滚方式：移除 `tw` 市场识别、交易日历注册、YFinance 路由与指数扩展、Web/API 类型放行、`scripts/fetch_tw_stock_list.py`、`scripts/stock_index_seeds/stock_list_tw.csv` 种子索引及 `stocks.index.json` 台股条目，并删除本文档中的台股能力声明（与上方 `jp/kr` 回滚段同构）。
