import os
import re
from typing import Callable
from dotenv import load_dotenv
from ollama_client import call_api

load_dotenv()

NUM_RUNS_TIMES = 5

DATA_FILES: list[str] = [
    os.path.join(os.path.dirname(__file__), "data", "api_docs.txt"),
]


def load_corpus_from_files(paths: list[str]) -> list[str]:
    corpus: list[str] = []
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    corpus.append(f.read())
            except Exception as exc:
                corpus.append(f"[load_error] {p}: {exc}")
        else:
            corpus.append(f"[missing_file] {p}")
    return corpus


# Load corpus from external files (simple API docs). If missing, fall back to inline snippet
CORPUS: list[str] = load_corpus_from_files(DATA_FILES)

QUESTION = (
    "Write a Python function `fetch_user_name(user_id: str, api_key: str) -> str` that calls the documented API "
    "to fetch a user by id and returns only the user's name as a string."
)


# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """
You are a precise Python coding assistant. Use ONLY the provided context.
If context includes API docs, follow them exactly:
* Base URL, endpoint path, and auth header names must match the docs.
* Return one fenced Python code block only, with imports plus exactly one function:
  fetch_user_name(user_id: str, api_key: str) -> str.
* Use requests.get with URL built as '<base_url>/users/{id}', pass header 'X-API-Key',
* call response.raise_for_status(), parse JSON, and return only the user's name string
* Do not include explanations or extra text outside the code block.
"""


# For this simple example
# For this coding task, validate by required snippets rather than exact string
REQUIRED_SNIPPETS = [
    "def fetch_user_name(",
    "requests.get",
    "/users/",
    "X-API-Key",
    "return",
]


def YOUR_CONTEXT_PROVIDER(corpus: list[str]) -> list[str]:
    """TODO: Select and return the relevant subset of documents from CORPUS for this task.

    For example, return [] to simulate missing context, or [corpus[0]] to include the API docs.
    """
    if not corpus:
        return []

    keywords = [
        "api reference",
        "base url",
        "x-api-key",
        "get /users/{id}",
        "name",
    ]

    ranked: list[tuple[int, str]] = []
    for doc in corpus:
        text = doc.lower()
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            ranked.append((score, doc))

    if not ranked:
        return []

    ranked.sort(key=lambda item: item[0], reverse=True)
    top_score = ranked[0][0]
    return [doc for score, doc in ranked if score == top_score]


def make_user_prompt(question: str, context_docs: list[str]) -> str:
    if context_docs:
        context_block = "\n".join(f"- {d}" for d in context_docs)
    else:
        context_block = "(no context provided)"
    return (
        f"Context (use ONLY this information):\n{context_block}\n\n"
        f"Task: {question}\n\n"
        "Requirements:\n"
        "- Use the documented Base URL and endpoint.\n"
        "- Send the documented authentication header.\n"
        "- Raise for non-200 responses.\n"
        "- Return only the user's name string.\n\n"
        "Output: A single fenced Python code block with the function and necessary imports.\n"
    )


def extract_code_block(text: str) -> str:
    """Extract the last fenced Python code block, or any fenced code block, else return text."""
    # Try ```python ... ``` first
    m = re.findall(r"```python\n([\s\S]*?)```", text, flags=re.IGNORECASE)
    if m:
        return m[-1].strip()
    # Fallback to any fenced code block
    m = re.findall(r"```\n([\s\S]*?)```", text)
    if m:
        return m[-1].strip()
    return text.strip()


def test_your_prompt(system_prompt: str, context_provider: Callable[[list[str]], list[str]]) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT."""
    context_docs = context_provider(CORPUS)
    user_prompt = make_user_prompt(QUESTION, context_docs)

    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = call_api(
            model="llama3.1:8b",
            sys_prompt=system_prompt,
            usr_prompt=user_prompt,
            temperature= 0.0,
        )
        output_text = response
        code = extract_code_block(output_text)
        missing = [s for s in REQUIRED_SNIPPETS if s not in code]
        if not missing:
            print(output_text)
            print("SUCCESS")
            return True
        else:
            print("Missing required snippets:")
            for s in missing:
                print(f"  - {s}")
            print("Generated code:\n" + code)
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT, YOUR_CONTEXT_PROVIDER)
