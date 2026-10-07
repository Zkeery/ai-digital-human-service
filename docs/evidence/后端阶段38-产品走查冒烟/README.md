# 证据 · 后端阶段 38（产品走查冒烟）

## 自动化

```bash
cd backend && ../.venv/bin/pytest tests/test_stage38_product_walkthrough.py -q
```

结果：1 passed（覆盖产品走查 #1～#8 接口层）

## 请产品经理抽测

http://127.0.0.1:3050/

1. 开始咨询 → 见零售金融欢迎  
2. 「查余额」→ 有选项  
3. 转人工 → 评价可提交或跳过  

## 结果

产品经理抽测通过（2026-10-03）；自动化 1 passed。
