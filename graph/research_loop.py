from __future__ import annotations

from typing import Callable, List, Literal, TypedDict

from math_mas.tools.arxiv_search import search_arxiv
from math_mas.tools.lean_verifier import verify_lean
from math_mas.tools.sympy_test import run_sympy_check


class ResearchState(TypedDict):
    topic: str
    literature: List[str]
    motivation: str
    ideas: List[str]
    implementation_results: List[str]
    theorem: str
    paper_draft: str
    failure_types: List[str]
    last_failure_hint: str
    retry_count: int
    max_retry: int


class LLMHooks(TypedDict):
    motivation_fn: Callable[[str, List[str]], str]
    ideation_fn: Callable[[str, str, List[str]], List[str]]
    theorem_fn: Callable[[str, List[str], List[str]], str]
    writing_fn: Callable[[str, str, List[str], str], str]


def literature_node(state: ResearchState) -> ResearchState:
    summary = search_arxiv(state["topic"], max_results=3)
    return {"literature": [summary]}


def motivation_node(state: ResearchState, hooks: LLMHooks) -> ResearchState:
    motivation = hooks["motivation_fn"](state["topic"], state["literature"])
    return {"motivation": motivation}


def ideation_node(state: ResearchState, hooks: LLMHooks) -> ResearchState:
    ideas = hooks["ideation_fn"](state["topic"], state["motivation"], state["implementation_results"])
    return {"ideas": ideas}


def implementation_node(state: ResearchState) -> ResearchState:
    results: List[str] = []
    for idea in state["ideas"]:
        if idea.lower().startswith("lean:"):
            results.append(verify_lean(idea[5:].strip()))
            continue
        if idea.lower().startswith("sympy:"):
            results.append(run_sympy_check(idea[6:].strip()))
            continue
        # Fallback: treat plain text as symbolic expression.
        results.append(run_sympy_check(idea))
    return {"implementation_results": results}


def _classify_failure(result: str) -> str:
    text = result.lower()
    if "timeout" in text or "超时" in text:
        return "timeout"
    if (
        "syntax" in text
        or "parse" in text
        or "编译错误" in text
        or "语法" in text
        or "error" in text
        or "错误" in text
    ):
        return "syntax"
    # Default non-error but non-passing outputs to mathematical invalidation.
    if "通过" not in text and "simplified:" in text:
        return "counterexample"
    return "pass"


def classify_failure_node(state: ResearchState) -> ResearchState:
    kinds = [_classify_failure(r) for r in state["implementation_results"]]
    return {"failure_types": kinds}


def decision_node(
    state: ResearchState,
) -> Literal["syntax_retry", "counterexample_retry", "timeout_retry", "extract"]:
    if state["retry_count"] >= state["max_retry"]:
        return "extract"

    kinds = state.get("failure_types", [])
    if any(k == "syntax" for k in kinds):
        return "syntax_retry"
    if any(k == "timeout" for k in kinds):
        return "timeout_retry"
    if any(k == "counterexample" for k in kinds):
        return "counterexample_retry"
    return "extract"


def retry_increment_node(state: ResearchState) -> ResearchState:
    return {"retry_count": state["retry_count"] + 1}


def syntax_retry_node(state: ResearchState) -> ResearchState:
    return {
        "last_failure_hint": (
            "FailureType=syntax: fix parser/compiler issues first; "
            "regenerate runnable sympy/lean expressions with valid syntax."
        ),
        "implementation_results": state["implementation_results"]
        + [
            "[ROUTER] Syntax failure detected; next ideation must prioritize syntactic correctness."
        ],
    }


def counterexample_retry_node(state: ResearchState) -> ResearchState:
    return {
        "last_failure_hint": (
            "FailureType=counterexample: refine assumptions or weaken claim; "
            "propose a narrower, testable conjecture."
        ),
        "implementation_results": state["implementation_results"]
        + [
            "[ROUTER] Mathematical invalidation detected; next ideation should revise hypothesis."
        ],
    }


def timeout_retry_node(state: ResearchState) -> ResearchState:
    return {
        "last_failure_hint": (
            "FailureType=timeout: reduce computational complexity, split checks, "
            "or use simpler symbolic statements."
        ),
        "implementation_results": state["implementation_results"]
        + [
            "[ROUTER] Timeout detected; next ideation should reduce complexity and runtime."
        ],
    }


def extract_node(state: ResearchState, hooks: LLMHooks) -> ResearchState:
    theorem = hooks["theorem_fn"](
        state["topic"], state["ideas"], state["implementation_results"]
    )
    return {"theorem": theorem}


def writing_node(state: ResearchState, hooks: LLMHooks) -> ResearchState:
    draft = hooks["writing_fn"](
        state["topic"],
        state["motivation"],
        state["implementation_results"],
        state["theorem"],
    )
    return {"paper_draft": draft}


def build_research_graph(hooks: LLMHooks):
    try:
        from langgraph.graph import END, StateGraph  # type: ignore[reportMissingImports]
    except ImportError as exc:
        raise RuntimeError(
            "Package 'langgraph' is required. Install dependencies first."
        ) from exc

    workflow = StateGraph(ResearchState)

    workflow.add_node("literature", literature_node)
    workflow.add_node("motivation", lambda s: motivation_node(s, hooks))
    workflow.add_node("ideation", lambda s: ideation_node(s, hooks))
    workflow.add_node("implementation", implementation_node)
    workflow.add_node("classify_failure", classify_failure_node)
    workflow.add_node("syntax_retry", syntax_retry_node)
    workflow.add_node("counterexample_retry", counterexample_retry_node)
    workflow.add_node("timeout_retry", timeout_retry_node)
    workflow.add_node("retry_increment", retry_increment_node)
    workflow.add_node("extract", lambda s: extract_node(s, hooks))
    workflow.add_node("writing", lambda s: writing_node(s, hooks))

    workflow.set_entry_point("literature")
    workflow.add_edge("literature", "motivation")
    workflow.add_edge("motivation", "ideation")
    workflow.add_edge("ideation", "implementation")
    workflow.add_edge("implementation", "classify_failure")

    workflow.add_conditional_edges(
        "classify_failure",
        decision_node,
        {
            "syntax_retry": "syntax_retry",
            "counterexample_retry": "counterexample_retry",
            "timeout_retry": "timeout_retry",
            "extract": "extract",
        },
    )

    workflow.add_edge("syntax_retry", "retry_increment")
    workflow.add_edge("counterexample_retry", "retry_increment")
    workflow.add_edge("timeout_retry", "retry_increment")
    workflow.add_edge("retry_increment", "ideation")
    workflow.add_edge("extract", "writing")
    workflow.add_edge("writing", END)

    return workflow.compile()
