---
name: langchain-dartmouth
description: Build Python LLM applications with the `langchain_dartmouth` package, Dartmouth's LangChain integration for Dartmouth-hosted and Dartmouth-provided models. Use when writing or debugging code that imports langchain_dartmouth (DartmouthLLM, ChatDartmouth, DartmouthEmbeddings, DartmouthReranker, DartmouthDecisions), when choosing which Dartmouth model class or model name to use, when wiring authentication (DARTMOUTH_API_KEY / DARTMOUTH_CHAT_API_KEY), or when building chains, RAG pipelines, agents, or decision-model calls on Dartmouth's AI resources.
type: Agent Skill
title: langchain_dartmouth — library usage guide
tags: [langchain-dartmouth, langchain, python, llm, rag, embeddings, decision-models]
generated: { by: kilo/zai-org.glm-5.3-flash, at: 2026-11-05T13:00:00-05:00 }
status: draft
sources:
  - id: lcd-repo
    resource: https://github.com/dartmouth/langchain-dartmouth
    title: langchain-dartmouth GitHub repository
  - id: lcd-docs
    resource: https://dartmouth.github.io/langchain-dartmouth/
    title: langchain-dartmouth documentation (API reference)
  - id: lcd-cookbook
    resource: https://github.com/dartmouth/langchain-dartmouth-cookbook
    title: langchain-dartmouth-cookbook GitHub repository
  - id: lcd-cookbook-docs
    resource: https://dartmouth.github.io/langchain-dartmouth-cookbook/
    title: langchain-dartmouth-cookbook rendered notebooks
---

# langchain_dartmouth

`langchain_dartmouth` connects [LangChain](https://python.langchain.com) to Dartmouth's generative AI resources: on-premises models (free, no per-token cost) and third-party cloud models (e.g. OpenAI GPT, Google Gemini) billed through the user's Dartmouth Chat token budget. All classes subclass standard LangChain base classes, so they drop in anywhere a LangChain model does.

References:

- Library source: https://github.com/dartmouth/langchain-dartmouth (`src/langchain_dartmouth/`)
- API documentation: https://dartmouth.github.io/langchain-dartmouth/
- Cookbook (worked notebooks): https://github.com/dartmouth/langchain-dartmouth-cookbook
- Rendered cookbook: https://dartmouth.github.io/langchain-dartmouth-cookbook/

When in doubt about a parameter or behavior, check the API documentation or read the source; the cookbook notebooks show end-to-end patterns.

## Authentication

Two different keys, kept as environment variables — never hard-code keys in code:

| Variable | Where to get it | Used by |
|---|---|---|
| `DARTMOUTH_CHAT_API_KEY` | [Dartmouth Chat](https://chat.dartmouth.edu) | `ChatDartmouth`, `DartmouthEmbeddings`, `DartmouthReranker`, `DartmouthDecisions` |
| `DARTMOUTH_API_KEY` | [developer.dartmouth.edu](https://developer.dartmouth.edu/keys) | `DartmouthLLM` (on-prem TGI endpoints) |

For notebooks and scripts, load a `.env` file (gitignore it!) at the top:

```python
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
```

Every class also accepts the key explicitly (`dartmouth_chat_api_key=...` or `dartmouth_api_key=...`). Base URLs can be overridden with `LCD_*_BASE_URL` environment variables (see [`definitions.py`](https://github.com/dartmouth/langchain-dartmouth/blob/main/src/langchain_dartmouth/definitions.py)).

## Choosing a model class

- **`ChatDartmouth`** (`llms.py`) — the default for almost everything. Chat and instruction-tuned models, both on-prem (e.g. `meta.llama-3.2-11b-vision-instruct`, `openai.gpt-oss-120b`) and paid cloud (e.g. `openai.gpt-4.1-mini-2025-04-14`). Subclasses `ChatOpenAI`; prompt templates are handled for you.
- **`DartmouthLLM`** (`llms.py`) — raw on-prem base (non-instruct) models like `codellama-13b-hf` for text completion. It does **not** apply any chat template: the string you pass is exactly what the model receives. Subclasses `HuggingFaceTextGenInference`; use `max_new_tokens` (not `max_tokens`).
- **`DartmouthEmbeddings`** (`embeddings.py`) — embedding models, default `baai.bge-large-en-v1-5`. Subclasses `OpenAIEmbeddings`; supports `dimensions`.
- **`DartmouthReranker`** (`retrievers/document_compressors.py`) — reranks retrieved documents, default `bge-reranker-v2-m3`. Call `compress_documents(query=..., documents=[...])`.
- **`DartmouthDecisions`** (`decisions.py`) — typed, calibrated judgments (binary/categorical/ordinal) instead of free-form text. See below.

Deprecated names `DartmouthChatModel` and `ChatDartmouthCloud` still work but emit warnings; map them to `DartmouthLLM`/`ChatDartmouth`.

Always discover model names at runtime instead of guessing — model lists change:

```python
ChatDartmouth.list()   # chat + cloud models, with feature/cost info
DartmouthLLM.list()    # on-prem base models
DartmouthDecisions.list()
```

## Basic usage

```python
from langchain_dartmouth.llms import ChatDartmouth

llm = ChatDartmouth(model_name="openai.gpt-oss-120b", temperature=0.7, max_tokens=512)
response = llm.invoke("Hi there!")
print(response.content)
```

Quirks to know:

- OpenAI reasoning models (`openai.o*`, `openai.gpt-5*`, `openai_responses.*`) force `temperature=1` and switch to the Responses API automatically (with a warning). Don't fight this.
- `DartmouthLLM` re-authenticates transparently on auth failures; a wrong model name surfaces as `ModelNotFoundError` — the fix is to re-run the class's `list()`.

## Chains, memory, RAG

Because the classes are standard LangChain components, use ordinary LangChain patterns — the [rendered cookbook](https://dartmouth.github.io/langchain-dartmouth-cookbook/) has complete worked examples for each task:

| Task | Recipe |
|---|---|
| Streaming | [04-streaming](https://dartmouth.github.io/langchain-dartmouth-cookbook/04-streaming.html) |
| Output parsing | [05-output-parsing](https://dartmouth.github.io/langchain-dartmouth-cookbook/05-output-parsing.html) |
| Messages & prompt basics | [06-prompt-basics](https://dartmouth.github.io/langchain-dartmouth-cookbook/06-prompt-basics.html) |
| Prompt templates | [07-prompt-templates](https://dartmouth.github.io/langchain-dartmouth-cookbook/07-prompt-templates.html) |
| Chains (LCEL) | [08-building-chains](https://dartmouth.github.io/langchain-dartmouth-cookbook/08-building-chains.html) |
| Conversational memory | [09-conversational-memory](https://dartmouth.github.io/langchain-dartmouth-cookbook/09-conversational-memory.html) |
| Embeddings | [10-embeddings](https://dartmouth.github.io/langchain-dartmouth-cookbook/10-embeddings.html) |
| Similarity search | [11-similarity-search](https://dartmouth.github.io/langchain-dartmouth-cookbook/11-similarity-search.html) |
| RAG | [12-rag](https://dartmouth.github.io/langchain-dartmouth-cookbook/12-rag.html) |
| Tool calling | [13-tool-calling](https://dartmouth.github.io/langchain-dartmouth-cookbook/13-tool-calling.html) |
| Agents | [14-agents](https://dartmouth.github.io/langchain-dartmouth-cookbook/14-agents.html) |
| Structured output | [15-structured-output](https://dartmouth.github.io/langchain-dartmouth-cookbook/15-structured-output.html) |
| LangGraph orchestration | [16-langgraph-orchestration](https://dartmouth.github.io/langchain-dartmouth-cookbook/16-langgraph-orchestration.html) |
| Multi-agent | [17-multi-agent](https://dartmouth.github.io/langchain-dartmouth-cookbook/17-multi-agent.html) |

Typical RAG shape (the [12-rag recipe](https://dartmouth.github.io/langchain-dartmouth-cookbook/12-rag.html) has the full version):

```python
from langchain_dartmouth.embeddings import DartmouthEmbeddings
from langchain_dartmouth.retrievers.document_compressors import DartmouthReranker
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma

docs = TextLoader("document.txt").load()
chunks = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", chunk_size=512, chunk_overlap=0
).split_documents(docs)

vectorstore = Chroma.from_documents(chunks, DartmouthEmbeddings())
retriever = vectorstore.as_retriever()
```

Insert a `DartmouthReranker` as a `ContextualCompressionRetriever` document compressor when the vector search needs a second-pass rerank.

## Decision models

`DartmouthDecisions` asks typed questions about a piece of state and returns probabilities — no prompt-and-parse. Three question types:

- **`Noul`** — binary yes/no, returns a probability (`response.nouls[name].noul`). Use when the probability itself drives logic.
- **`Choice`** — pick one label from `criteria` (dict of label → description); returns `choice`, per-label `probabilities`, and `confidence`. Use for routing/classification.
- **`Score`** — ordinal rubric (list of level descriptions, numbered from 0); returns an expected-value `score` (can be fractional), `legend`, and `probabilities`. Use for severity/urgency-like spectra.

One `invoke` can combine several questions, and results arrive synchronously (`invoke`) or async (`ainvoke`):

```python
from langchain_dartmouth.decisions import DartmouthDecisions, Choice, Score, Noul

decisions = DartmouthDecisions()  # model_name defaults to "cloudflare.clef"
response = decisions.invoke({
    "state": "Stripe fails whenever I connect my account.",
    "questions": {
        "department": Choice(
            instructions="Which team should handle this request?",
            criteria={
                "billing": "Payment, invoice, or subscription issues.",
                "technical": "Product bugs or integration failures.",
                "sales": "Pricing or purchasing questions.",
            },
        ),
        "urgent": Noul(instructions="Does this need an urgent response?"),
    },
})
print(response.choices["department"].choice, response.choices["department"].confidence)
print(response.nouls["urgent"].noul)
```

Gate actions on `confidence`/probability thresholds and route low-confidence cases to humans. Errors map to `InvalidKeyError`, `ModelNotFoundError`, `DecisionRateLimitError` (carries `retry_after_ms`), and `DecisionAPIError`. The cookbook's [18-decision-models recipe](https://dartmouth.github.io/langchain-dartmouth-cookbook/18-decision-models.html) has a full walkthrough.

## Writing code with this library

1. Ask (or infer) whether the user has their keys set up (`DARTMOUTH_CHAT_API_KEY`, and `DARTMOUTH_API_KEY` only if using `DartmouthLLM`); scaffold `.env` + `load_dotenv` rather than inline keys.
2. Call `.list()` (or have the user run it) to pick real model names instead of inventing them.
3. Default to `ChatDartmouth`; reach for `DartmouthLLM` only for base completion models, and for `DartmouthDecisions` when the task is a judgment that maps to Noul/Choice/Score rather than text generation.
4. Compose with stock LangChain/LangChain-Community pieces (loaders, splitters, vectorstores, parsers, `RunnableWithMessageHistory`) — the Dartmouth classes are drop-ins.
5. When behavior surprises, check the [API documentation](https://dartmouth.github.io/langchain-dartmouth/) or the [source on GitHub](https://github.com/dartmouth/langchain-dartmouth/tree/main/src/langchain_dartmouth) before guessing.
