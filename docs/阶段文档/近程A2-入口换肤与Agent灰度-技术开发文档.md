# 近程 A2 · 入口换肤与 Agent 灰度 · 技术开发文档

> 对应 PRD V0.4；决策见 [近程增强-决策纪要](./近程增强-决策纪要.md)。  
> 依赖 A1 已交付。**不上线**。配置控件仍仅验收可见。

## 一、目标（产品语言）

换到不同入口后，客户看到的体验会不一样：

1. **欢迎语**按入口变化  
2. **浅／深主题、主色、Logo** 按入口变化  
3. **是否用 Agent**：全局总闸 **并且** 该入口默认打开，才会启用  

客户页面仍然**看不到**任何开关。

## 二、已锁定决策

| 项 | 结论 |
| --- | --- |
| 换肤深度 | 主题＋欢迎语＋主色＋Logo（Q10=B） |
| Agent | 总闸 ∧ 入口开关；访客不可见（Q11=A） |
| Logo | 本地静态 `/entries/*.svg`（本阶段不接外网上传） |

## 三、范围

| 改 | 不改 |
| --- | --- |
| 应答：`effective_agent = 总闸 AND 入口.agent_enabled` | 上线／运营台上传 Logo |
| 前端按入口应用 theme／accent／logo／欢迎语 | 访客展示 Agent／入口开关 |
| 验收顶栏只读展示「本入口 Agent 默认／实际是否启用」 | RAG、统计面板（B1／C1） |
| Logo 仅允许 `/entries/` 下相对路径 | 任意外链图片 |

## 四、逻辑说明

### Agent

| 总闸 | 入口 agent_enabled | 实际 |
| --- | --- | --- |
| 关 | 任意 | 不用 Agent |
| 开 | 关（通用入口默认） | 不用 Agent |
| 开 | 开（信用卡专窗默认） | 可用 Agent |

关闭原因写入事件：`disabled`（总闸）／`entry_disabled`（入口关）。

### 换肤

- `theme`：`default`／`ink` → 整页主题类  
- `accent`：写入 CSS 变量 `--accent`（仅 `#RRGGBB`）  
- `logo_url`：数字人画面展示入口 Logo；非法路径忽略  

## 五、主要文件

| 位置 | 文件 |
| --- | --- |
| 后端 | `app/services/entries.py`（`effective_agent_enabled`） |
| 后端 | `app/services/sessions.py`、`app/api/routes.py` |
| 后端测试 | `tests/test_stage40_entry_agent_gate.py` |
| 前端 | `entries.ts`、`SessionWorkspace.tsx`、`AvatarPanel.tsx`、`ConfigBar.tsx`、`globals.css` |
| 静态资源 | `frontend/public/entries/general.svg`、`credit.svg` |
| 前端测试 | `tests/entries.test.ts` |

## 六、产品经理验收（照着点）

1. http://127.0.0.1:3050/ 强制刷新  
2. **验收模式**选「信用卡专窗」→ 创建会话  
   - 欢迎语应为专窗文案（含「信用卡咨询专窗」）  
   - 画面出现信用卡风格 Logo；主色偏青蓝  
3. 再选「通用金融咨询」→ 创建会话  
   - 欢迎语恢复通用；Logo 换为通用标识  
4. 总闸 Agent **关闭** → 两入口会话都不应走 Agent（验收顶栏「实际不启用」）  
5. 总闸 **打开** + 信用卡专窗 → 顶栏「实际会启用」；通用入口仍「实际不启用」  
6. **访客模式**：仍无入口／Agent 控件；开始咨询有默认入口欢迎语与 Logo  

## 七、阶段闸门是否表

| # | 检查项 | 是／否 |
| --- | --- | --- |
| 1 | 仅本阶段范围，未做 RAG／统计后台 | 是 |
| 2 | 自动化测试通过 | 是（后端 stage39+40：8/8；含 Agent 组合与 compose-reply 409） |
| 3 | 真实模型冒烟 | N/A／可选（Agent 开时） |
| 4 | 前端测试通过 | 是（43/43） |
| 5 | 密钥未进仓 | 是 |
| 6 | 数据可恢复 | N/A |
| 7 | 窄屏 Logo／主色可读 | 待手测 |
| 8 | README／状态／路线图已更新 | 是 |
| 9 | 项目状态已更新 | 是 |
| 10 | 证据包已交 | 是（手测待勾） |

## 八、证据包

`docs/evidence/近程A2-入口换肤与Agent灰度/`
