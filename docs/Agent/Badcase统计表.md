# Agent Badcase 统计表

> 用于 POC／灰度期归类。本批无真实 badcase 行，仅定表结构与枚举。

## 1. 字段

| 字段 | 说明 |
| --- | --- |
| bad_id | B-日期-序号 |
| case_id | 评测或线上关联 |
| severity | P0／P1／P2 |
| category | 幻觉／越权／不一致／超时／映射失败／其它 |
| symptom | 现象 |
| root_cause | 归因 |
| fix | 提示／工具／规则／产品 |
| status | open／fixed／wontfix |
| owner | 负责人 |

## 2. 分类计数（待填）

| category | 数量 | P0 |
| --- | --- | --- |
| 幻觉 | 0 | 0 |
| 越权 | 0 | 0 |
| 口播图文不一致 | 0 | 0 |
| 超时 | 0 | 0 |
| 映射失败 | 0 | 0 |

## 3. 明细（待填）

| bad_id | severity | category | symptom | status |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |
