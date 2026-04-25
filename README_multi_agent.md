# 多智能体闭环配置（AutoGen + LangGraph）

## 目录结构

- math_mas/agents: AutoGen 角色定义
- math_mas/graph: LangGraph 闭环状态图
- math_mas/tools: arXiv/Sympy/Lean 工具
- math_mas/orchestrator.py: 统一启动入口
- paper_work/sections: 按章节拆分的 LaTeX 文件
- paper_work/paper_work.ltex: 汇总显示文件（含 MAS 自动更新区块）

## 1) 安装依赖

```bash
pip install -r requirements.txt
```

## 2) 配置环境变量

参考 .env.example 设置：

- MAS_MODEL
- MAS_API_KEY
- MAS_BASE_URL
- LEAN_BIN（可选）

已提供 `.env` 模板文件（项目根目录），请把 `MAS_API_KEY` 改成你的真实密钥。

### 从 `.env` 加载并运行（PowerShell）

```powershell
Get-Content .env | ForEach-Object {
	if ($_ -match '^(MAS_MODEL|MAS_API_KEY|MAS_BASE_URL|DEEPSEEK_API_KEY|DEEPSEEK_BASE_URL|LEAN_BIN)=(.*)$') {
		[Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
	}
}

python -m math_mas.orchestrator --mode langgraph --max-retry 2
```

### DeepSeek v4 部署示例（PowerShell）

```powershell
$env:MAS_MODEL="deepseek-v4"
$env:MAS_API_KEY="<YOUR_DEEPSEEK_API_KEY>"
$env:MAS_BASE_URL="https://api.deepseek.com/v1"
```

说明：LangGraph 节点和 AutoGen Agent 共享同一套模型配置（同一个 DeepSeek v4 API）。

## 3) 运行 LangGraph 闭环（推荐先跑）

```bash
python -m math_mas.orchestrator --mode langgraph --max-retry 2
```

说明：`--topic` 现在可省略，默认使用 `1D_1.tex` 的核心内容主题。

LangGraph 流程：

1. literature -> motivation -> ideation -> implementation
2. 若实现失败且未超出 max_retry，则回到 ideation
3. 成功后 extract -> writing，输出论文草稿

运行后，MAS 会自动把最新生成内容写入 `paper_work/paper_work.ltex` 的如下标记区块：

- `% MAS_GENERATED_BEGIN`
- `% MAS_GENERATED_END`

## 4) 运行 AutoGen 对话闭环

```bash
python -m math_mas.orchestrator --mode autogen --rounds 10
```

如需自定义主题，可显式传入：

```bash
python -m math_mas.orchestrator --mode langgraph --topic "你的研究主题"
```

AutoGen 角色：

- LiteratureAgent: 文献检索
- IdeationAgent: 猜想生成
- ImplementationAgent: Sympy/Lean 验证
- ReviewerAgent: 审稿与回退建议

## 5) 扩展建议

- 将 graph/research_loop.py 中 hooks 替换为真实 LLM 调用。
- 给 ImplementationAgent 增加更多数学工具（Sage、NumPy、Lean REPL）。
- 给 ReviewerAgent 增加打分规则，驱动自动是否回退。
