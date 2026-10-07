"""Agent 旁路：金融提示词与 mock 结构。"""

from app.services import agent as agent_svc
from app.core.config import Settings


def test_mock_agent_reply_structure():
    settings = Settings(llm_mock=True, llm_api_key="")
    hit = {
        "spoken_text": "您好。",
        "action_intent": "wave",
        "graphic_template_ref": "faq:greeting",
    }
    out = agent_svc.compose_agent_reply(settings, "你好", hit)
    assert out is not None
    assert out["action_intent"] in agent_svc.ALLOWED_ACTIONS
    assert "Agent 旁路已润色" in out["spoken_text"]


def test_agent_prompt_is_finance_oriented():
    import inspect

    src = inspect.getsource(agent_svc.compose_agent_reply)
    assert "零售金融" in src
    assert "怎么退货" not in src
