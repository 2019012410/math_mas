# math_mas

A Python-based multi-agent research workflow for exploring topics, generating ideas, validating implementation feasibility, and drafting research output.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/AutoGen-Enabled-5C2D91?style=for-the-badge" alt="AutoGen enabled" />
  <img src="https://img.shields.io/badge/LangGraph-Workflow-FF6B6B?style=for-the-badge" alt="LangGraph workflow" />
</p>

## Overview

`math_mas` is an open-source research assistant scaffold built around a multi-agent collaboration pattern. It is designed to help teams or individuals move from a raw research question to a structured workflow that can:

- explore relevant literature and background information,
- generate promising research directions,
- validate feasibility and implementation considerations,
- produce draft summaries or research write-ups.

The project combines AutoGen for agent orchestration and LangGraph for workflow control, making the design easy to extend with new agents, tools, and domain-specific tasks.

## Features

- Multi-agent task decomposition
- Research-oriented workflow orchestration
- Topic exploration and context gathering
- Idea generation and candidate evaluation
- Feasibility checking and implementation review
- Draft generation for reports or notes
- Modular architecture for custom tools and agents

## Architecture

The project is organized around a small set of responsibilities:

- Agent layer: Responsible for specialized roles and tasks
- Workflow layer: Coordinates execution order, transitions, and state updates
- Tool layer: Connects the workflow to external data sources or utilities
- Output layer: Converts intermediate results into structured reports or drafts

This separation makes it easier to extend the project for new domains without disrupting the overall execution flow.

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── agents/
│   ├── workflows/
│   ├── tools/
│   ├── prompts/
│   └── config/
├── tests/
├── notebooks/
└── docs/
```

> Note: the exact structure may evolve as the workflow grows. The main idea is to keep agent logic, workflow orchestration, and supporting tools clearly separated.

## Getting Started

### Prerequisites

- Python 3.10+
- A working virtual environment
- Access to an LLM provider or a compatible local model runtime

### Installation

```bash
git clone https://github.com/2019012410/math_mas.git
cd math_mas
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configuration

Create a local environment file or export the required environment variables before running the project.

Example:

```bash
export OPENAI_API_KEY="your-api-key"
```

If the project uses additional providers or settings, follow the configuration pattern used in the codebase and keep secrets out of version control.

## Typical Workflow

1. Define a research topic or problem statement.
2. Launch the exploration stage to gather background and relevant references.
3. Generate candidate ideas or directions.
4. Evaluate feasibility and implementation constraints.
5. Produce a structured draft or next-step summary.

## Development Guide

- Keep agent responsibilities focused and explicit.
- Use structured inputs and outputs between agents.
- Prefer small, testable workflow nodes.
- Log intermediate results for debugging and iteration.
- Validate model outputs before passing them into downstream steps.

## Contributing

Contributions are welcome. If you would like to improve this project, please open an issue or submit a pull request with a clear explanation of the change.

Recommended contribution flow:

1. Fork the repository
2. Create a feature branch
3. Make focused changes
4. Add or update tests where appropriate
5. Submit a pull request with a summary of the improvement

## Roadmap

Potential future directions include:

- richer agent roles for literature review, coding, and writing
- configurable workflow templates
- stronger validation and evaluation pipelines
- more robust prompt and tool abstraction layers
- documentation and examples for common research tasks

## License

This project does not currently declare a license. If you plan to use or distribute it beyond personal experimentation, please confirm the repository's licensing status before publishing or sharing the code.

## Contact

For questions or collaboration opportunities, open an issue in this repository.
