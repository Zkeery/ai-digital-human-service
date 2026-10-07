# Tool list（调用工具表）

| tool_id | 名称 | 描述 | 输入 | 输出 | 副作用 | 权限 | 超时建议 | 一期 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | get_session_meta | 读会话元数据 | session_id | 分流、形象、dh 标记 | 无 | 只读本会话 | 200ms | ✅ |
| T02 | get_faq_answer | 取 FAQ／图文模板 | faq_id／intent | template_ref、标准口播候选 | 无 | 只读 | 300ms | ✅ |
| T03 | map_action_intent | 意图→动作配置 | intent 枚举 | action_id | 无 | 只读配置 | 100ms | ✅ |
| T04 | get_special_script | 特殊指令口播 | script_id | 文本＋动作 | 无 | 只读 | 100ms | ✅ |
| T05 | suggest_transfer | 转人工建议 | reason_code | 建议结构 | 无执行 | 写建议字段 | 50ms | ✅ |
| T06 | search_knowledge | RAG 检索 | query | passages[] | 无 | 只读知识库 | 500ms | 二期 |
| T07 | create_ticket | 建单 | … | … | 写 | 需人工确认闸门 | — | ❌ 放弃／远期 |

## 调用规则

1. 每轮工具次数上限：建议 ≤4  
2. 并行：仅只读可并行；写类禁止  
3. 失败：工具错误不得捏造结果；可回退无工具生成或转人工建议  
