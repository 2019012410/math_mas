from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from math_mas.tools.arxiv_search import search_arxiv
from math_mas.tools.lean_verifier import verify_lean
from math_mas.tools.sympy_test import run_sympy_check


@dataclass
class AutoGenBundle:
    user_proxy: Any
    manager: Any
    agents: List[Any]


def _llm_config(config_list: List[Dict[str, str]]) -> Dict[str, Any]:
    return {"config_list": config_list, "temperature": 0.2}


def build_research_agents(config_list: List[Dict[str, str]], max_round: int = 8) -> AutoGenBundle:
    try:
        from autogen import (  # type: ignore[reportMissingImports]
            AssistantAgent,
            GroupChat,
            GroupChatManager,
            UserProxyAgent,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Package 'pyautogen' is required. Install dependencies first."
        ) from exc

    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    literature_agent = AssistantAgent(
        name="LiteratureAgent",
        system_message=(
            "你负责检索 arXiv 上的相关数学文献。"
            "当需要检索时使用 search_arxiv，并给出标题、摘要、开放问题线索。"
        ),
        llm_config=_llm_config(config_list),
    )
    literature_agent.register_for_llm(name="search_arxiv", description="检索 arXiv")(
        search_arxiv
    )

    ideation_agent = AssistantAgent(
        name="IdeationAgent",
        system_message=(
            "你是一位研究构思专家。基于文献输出可验证的猜想和实验方案。"
            "若验证失败，必须修改猜想或假设，并解释改动原因。"
        ),
        llm_config=_llm_config(config_list),
    )

    implementation_agent = AssistantAgent(
        name="ImplementationAgent",
        system_message=(
            "你负责执行验证。优先使用 run_sympy_check 验证符号结论，"
            "如需形式化证明，调用 verify_lean。返回通过/失败与关键日志。"
        ),
        llm_config=_llm_config(config_list),
    )
    implementation_agent.register_for_llm(
        name="run_sympy_check", description="运行 Sympy 符号验证"
    )(run_sympy_check)
    implementation_agent.register_for_llm(
        name="verify_lean", description="运行 Lean 编译验证"
    )(verify_lean)

    reviewer_agent = AssistantAgent(
        name="ReviewerAgent",
        system_message=(
            "你是严格审稿人。检查逻辑漏洞、证据不足与可复现性问题。"
            "若结果不可信，明确指出回退到哪一步。"
        ),
        llm_config=_llm_config(config_list),
    )

    groupchat = GroupChat(
        agents=[
            user_proxy,
            literature_agent,
            ideation_agent,
            implementation_agent,
            reviewer_agent,
        ],
        messages=[],
        max_round=max_round,
        speaker_selection_method="round_robin",
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=_llm_config(config_list))

    return AutoGenBundle(
        user_proxy=user_proxy,
        manager=manager,
        agents=[literature_agent, ideation_agent, implementation_agent, reviewer_agent],
    )


def run_autogen_loop(config_list: List[Dict[str, str]], topic: str, rounds: int = 8) -> None:
    bundle = build_research_agents(config_list=config_list, max_round=rounds)
    bundle.user_proxy.initiate_chat(
        bundle.manager,
        message=(
            f"围绕主题“{topic}”执行闭环流程：文献检索 -> 猜想生成 -> 验证 -> 审稿。"
            "如果验证或审稿失败，继续迭代，直到得到可接受结论或轮次耗尽。"
        ),
    )
