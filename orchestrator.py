from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, List
from urllib import request

from math_mas.agents.autogen_agents import run_autogen_loop
from math_mas.config import LLMConfig, load_llm_config
from math_mas.graph.research_loop import LLMHooks, ResearchState, build_research_graph


DEFAULT_TOPIC = (
    "An explicit asymptotic framework for the small-inertia limit of a nonlinear Langevin equation "
    "under regularized white noise, combining regular and homotopy perturbation with rigorous "
    "mean-square convergence guarantees for peer-review-level validation."
)

PAPER_WORK_LTEXT_PATH = Path(__file__).resolve().parents[1] / "paper_work" / "paper_work.ltex"
PAPER_WORK_TEX_PATH = Path(__file__).resolve().parents[1] / "paper_work" / "paper_work.tex"
MAS_BEGIN_MARKER = "% MAS_GENERATED_BEGIN"
MAS_END_MARKER = "% MAS_GENERATED_END"


def _extract_json_block(text: str) -> str:
    """Extract JSON from plain text or fenced markdown block."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _chat_completion(llm_cfg: LLMConfig, system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI-compatible chat completions endpoint using workspace model config."""
    endpoint = f"{llm_cfg.base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": llm_cfg.model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_cfg.api_key}",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    choices = body.get("choices", [])
    if not choices:
        raise RuntimeError(f"LLM returned no choices: {body}")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if not content:
        raise RuntimeError(f"LLM returned empty content: {body}")
    return content.strip()


def _chat_completion_json(
    llm_cfg: LLMConfig, system_prompt: str, user_prompt: str
) -> dict[str, Any]:
    text = _chat_completion(llm_cfg, system_prompt, user_prompt)
    json_text = _extract_json_block(text)
    return json.loads(json_text)


def _motivation_fn(llm_cfg: LLMConfig, topic: str, literature: List[str]) -> str:
    lit_text = literature[0] if literature else "No literature snippets were provided."
    return _chat_completion(
        llm_cfg,
        "You are a mathematical research reviewer writing concise, rigorous motivation paragraphs.",
        (
            "Write one compact motivation paragraph (120-180 words) for a peer-review context.\n"
            f"Topic:\n{topic}\n\n"
            f"Literature snippets:\n{lit_text}\n\n"
            "Focus on: gap, novelty, and why validation/verification loop matters."
        ),
    )


def _ideation_fn(
    llm_cfg: LLMConfig, topic: str, motivation: str, implementation_results: List[str]
) -> List[str]:
    results_text = "\n".join(f"- {r[:280]}" for r in implementation_results) or "- None"
    obj = _chat_completion_json(
        llm_cfg,
        (
            "You are a computational mathematics ideation agent. "
            "Return strict JSON only."
        ),
        (
            "Generate 2-4 verifiable candidate checks for the topic.\n"
            "Return JSON object with key `ideas` as a string array.\n"
            "Each item must start with `sympy:` or `lean:`.\n"
            "Use mostly `sympy:` algebraic identities for robustness.\n"
            f"Topic:\n{topic}\n\n"
            f"Motivation:\n{motivation}\n\n"
            f"Previous implementation results:\n{results_text}\n"
        ),
    )
    ideas = obj.get("ideas", [])
    if not isinstance(ideas, list):
        raise RuntimeError(f"Invalid LLM ideation JSON format: {obj}")
    normalized = [str(item).strip() for item in ideas if str(item).strip()]
    if not normalized:
        raise RuntimeError("LLM ideation returned an empty idea list.")
    return normalized


def _theorem_fn(llm_cfg: LLMConfig, topic: str, ideas: List[str], results: List[str]) -> str:
    ideas_text = "\n".join(f"- {i}" for i in ideas)
    results_text = "\n".join(f"- {r[:280]}" for r in results)
    return _chat_completion(
        llm_cfg,
        "You are a theorem-extraction assistant for mathematical manuscripts.",
        (
            "Synthesize a cautious theorem-style statement and assumptions from candidate checks.\n"
            "Do not overclaim; if evidence is partial, state it explicitly.\n"
            f"Topic:\n{topic}\n\n"
            f"Candidate ideas:\n{ideas_text}\n\n"
            f"Verification results:\n{results_text}\n"
        ),
    )


def _writing_fn(
    llm_cfg: LLMConfig, topic: str, motivation: str, results: List[str], theorem: str
) -> str:
    results_text = "\n".join(f"- {item[:200]}" for item in results)
    return _chat_completion(
        llm_cfg,
        "You are an academic writing assistant preparing peer-review-ready LaTeX drafts.",
        (
            "Write a concise LaTeX snippet with sections/subsections: Topic, Motivation, Evidence, "
            "Claim, Limitations, Next Experiments.\n"
            "Keep tone formal and reviewer-friendly.\n"
            "Output pure LaTeX only, no markdown fences.\n"
            f"Topic:\n{topic}\n\n"
            f"Motivation:\n{motivation}\n\n"
            f"Verification results:\n{results_text}\n\n"
            f"Extracted claim:\n{theorem}\n"
        ),
    )


def _ensure_paper_work_ltex(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(
        "\n".join(
            [
                "% Auto-generated aggregate display file for paper sections",
                "% MAS_GENERATED_BEGIN",
                "\\section*{MAS Generated Updates}",
                "% (MAS will overwrite this block.)",
                "% MAS_GENERATED_END",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _upsert_mas_generated_block(path: Path, latex_snippet: str) -> None:
    _ensure_paper_work_ltex(path)
    content = path.read_text(encoding="utf-8")
    block = "\n".join(
        [
            MAS_BEGIN_MARKER,
            "\\section*{MAS Generated Updates}",
            latex_snippet.strip(),
            MAS_END_MARKER,
        ]
    )
    if MAS_BEGIN_MARKER in content and MAS_END_MARKER in content:
        start = content.index(MAS_BEGIN_MARKER)
        end = content.index(MAS_END_MARKER) + len(MAS_END_MARKER)
        updated = content[:start] + block + content[end:]
    else:
        updated = content.rstrip() + "\n\n" + block + "\n"
    path.write_text(updated, encoding="utf-8")


def _sync_ltex_to_tex(ltex_path: Path, tex_path: Path) -> None:
    """Mirror display .ltex file to a compilable .tex entry file."""
    _ensure_paper_work_ltex(ltex_path)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(ltex_path.read_text(encoding="utf-8"), encoding="utf-8")


def run_langgraph_loop(topic: str, llm_cfg: LLMConfig, max_retry: int = 2) -> ResearchState:
    hooks: LLMHooks = {
        "motivation_fn": lambda topic, literature: _motivation_fn(
            llm_cfg, topic, literature
        ),
        "ideation_fn": lambda topic, motivation, implementation_results: _ideation_fn(
            llm_cfg, topic, motivation, implementation_results
        ),
        "theorem_fn": lambda topic, ideas, results: _theorem_fn(
            llm_cfg, topic, ideas, results
        ),
        "writing_fn": lambda topic, motivation, results, theorem: _writing_fn(
            llm_cfg, topic, motivation, results, theorem
        ),
    }
    app = build_research_graph(hooks)

    initial_state: ResearchState = {
        "topic": topic,
        "literature": [],
        "motivation": "",
        "ideas": [],
        "implementation_results": [],
        "theorem": "",
        "paper_draft": "",
        "failure_types": [],
        "last_failure_hint": "",
        "retry_count": 0,
        "max_retry": max_retry,
    }
    return app.invoke(initial_state)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-agent research loop")
    parser.add_argument("--mode", choices=["autogen", "langgraph"], default="langgraph")
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help="Research topic; defaults to the core content of 1D_1.tex",
    )
    parser.add_argument("--rounds", type=int, default=8, help="AutoGen max rounds")
    parser.add_argument("--max-retry", type=int, default=2, help="LangGraph retry limit")
    args = parser.parse_args()
    llm_cfg = load_llm_config()

    if args.mode == "autogen":
        run_autogen_loop(
            config_list=llm_cfg.as_autogen_config_list(), topic=args.topic, rounds=args.rounds
        )
        return

    final_state = run_langgraph_loop(
        topic=args.topic,
        llm_cfg=llm_cfg,
        max_retry=args.max_retry,
    )
    print("===== LangGraph Final Draft =====")
    print(final_state["paper_draft"])
    _upsert_mas_generated_block(PAPER_WORK_LTEXT_PATH, final_state["paper_draft"])
    _sync_ltex_to_tex(PAPER_WORK_LTEXT_PATH, PAPER_WORK_TEX_PATH)
    print(f"===== Written To =====\n{PAPER_WORK_LTEXT_PATH}")
    print(f"===== Compilable TeX =====\n{PAPER_WORK_TEX_PATH}")


if __name__ == "__main__":
    main()
