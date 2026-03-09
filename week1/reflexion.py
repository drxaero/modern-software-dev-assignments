import re
from typing import Callable

from dotenv import load_dotenv
from ollama_client import call_api

load_dotenv()

NUM_RUNS_TIMES = 1

SYSTEM_PROMPT = """
You are a coding assistant. Output ONLY a single fenced Python code block that defines
the function is_valid_password(password: str) -> bool. No prose or comments.
Keep the implementation minimal.
"""

# TODO: Fill this in!
YOUR_REFLEXION_PROMPT = """
You are a professional Python3 code-repair assistant.

Goal:
Repair the previously generated function `is_valid_password(password: str) -> bool`
so it passes all provided failing test diagnostics.

Required password policy:
- length >= 8
- contains at least one lowercase letter
- contains at least one uppercase letter
- contains at least one digit
- contains at least one special character from: !@#$%^&*()-_
- contains no whitespace

Important logic constraints:
- Do NOT use `password.isalnum()` or `not password.isalnum()`.
    Reason: the policy requires at least one special character, so alnum-only checks are contradictory.
- Implement each policy as an independent boolean check and return their conjunction.
- Keep the function pure and deterministic.
- Do NOT classify lowercase with `c.lower()` in range checks (e.g. `'a' <= c.lower() <= 'z'`).
    Reason: uppercase letters will be misclassified as lowercase.
- Prefer `c.islower()`, `c.isupper()`, and `c.isdigit()`.
- If using a loop, avoid mutually-exclusive `elif` chains for category flags; categories should be checked independently.

Output rules:
- Return ONLY one fenced Python code block.
- No explanation, no comments, no extra text.
- Define exactly one function named `is_valid_password(password: str) -> bool`.
- Keep implementation minimal and deterministic.
- Ensure return value is strictly bool.

Use the failure diagnostics to fix logic errors, not to change the function signature.
"""


# Ground-truth test suite used to evaluate generated code
SPECIALS = set("!@#$%^&*()-_")
TEST_CASES: list[tuple[str, bool]] = [
    ("Password1!", True),       # valid
    ("password1!", False),      # missing uppercase
    ("Password!", False),       # missing digit
    ("Password1", False),       # missing special
]


def extract_code_block(text: str) -> str:
    m = re.findall(r"```python\n([\s\S]*?)```", text, flags=re.IGNORECASE)
    if m:
        return m[-1].strip()
    m = re.findall(r"```\n([\s\S]*?)```", text)
    if m:
        return m[-1].strip()
    return text.strip()


def load_function_from_code(code_str: str) -> Callable[[str], bool]:
    namespace: dict = {}
    exec(code_str, namespace)  # noqa: S102 (executing controlled code from model for exercise)
    func = namespace.get("is_valid_password")
    if not callable(func):
        raise ValueError("No callable is_valid_password found in generated code")
    return func


def evaluate_function(func: Callable[[str], bool]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for pw, expected in TEST_CASES:
        try:
            result = bool(func(pw))
        except Exception as exc:
            failures.append(f"Input: {pw} → raised exception: {exc}")
            continue

        if result != expected:
            # Compute diagnostic based on ground-truth rules
            reasons = []
            if len(pw) < 8:
                reasons.append("length < 8")
            if not any(c.islower() for c in pw):
                reasons.append("missing lowercase")
            if not any(c.isupper() for c in pw):
                reasons.append("missing uppercase")
            if not any(c.isdigit() for c in pw):
                reasons.append("missing digit")
            if not any(c in SPECIALS for c in pw):
                reasons.append("missing special")
            if any(c.isspace() for c in pw):
                reasons.append("has whitespace")

            failures.append(
                f"Input: {pw} → expected {expected}, got {result}. Failing checks: {', '.join(reasons) or 'unknown'}"
            )

    return (len(failures) == 0, failures)


def generate_initial_function(system_prompt: str) -> str:
    response = call_api(
        model="llama3.1:8b",
        sys_prompt=system_prompt,
        usr_prompt="Provide the implementation now.",
        temperature= 0.2,
    )
    return extract_code_block(response)


def your_build_reflexion_context(prev_code: str, failures: list[str]) -> str:
    """TODO: Build the user message for the reflexion step using prev_code and failures.

    Return a string that will be sent as the user content alongside the reflexion system prompt.
    """
    failure_lines = "\n".join(f"- {f}" for f in failures) if failures else "- (no failures provided)"
    return (
        "Previous implementation to repair:\n"
        "```python\n"
        f"{prev_code.strip()}\n"
        "```\n\n"
        "Observed failing tests and diagnostics:\n"
        f"{failure_lines}\n\n"
        "Repair checklist (must satisfy all):\n"
        "- Allow special characters from !@#$%^&*()-_ (do not reject them).\n"
        "- Reject if length < 8.\n"
        "- Reject if missing lowercase.\n"
        "- Reject if missing uppercase.\n"
        "- Reject if missing digit.\n"
        "- Reject if missing special from !@#$%^&*()-_.\n"
        "- Reject if any whitespace exists.\n"
        "- Do not use isalnum checks.\n\n"
        "Known bug to avoid from previous attempt:\n"
        "- `'a' <= c.lower() <= 'z'` marks uppercase letters as lowercase.\n"
        "- Do not use that pattern. Use `c.islower()` and `c.isupper()` instead.\n"
        "- Do not rely on `elif` that can block uppercase detection after lowercase detection.\n\n"
        "Task:\n"
        "Rewrite the function so all listed failures are fixed while preserving the same function name/signature.\n"
        "Return ONLY a single fenced Python code block with the corrected function."
    )


def apply_reflexion(
    reflexion_prompt: str,
    build_context: Callable[[str, list[str]], str],
    prev_code: str,
    failures: list[str],
) -> str:
    reflection_context = build_context(prev_code, failures)
    print(f"REFLECTION CONTEXT: {reflection_context}, {reflexion_prompt}")
    response = call_api(
        model="llama3.1:8b",
        sys_prompt = reflexion_prompt,
        usr_prompt=reflection_context,
        temperature= 0.2,
    )
    return extract_code_block(response)


def run_reflexion_flow(
    system_prompt: str,
    reflexion_prompt: str,
    build_context: Callable[[str, list[str]], str],
) -> bool:
    # 1) Generate initial function
    initial_code = generate_initial_function(system_prompt)
    print("Initial code:\n" + initial_code)
    func = load_function_from_code(initial_code)
    passed, failures = evaluate_function(func)
    if passed:
        print("SUCCESS (initial implementation passed all tests)")
        return True
    else:
        print(f"FAILURE (initial implementation failed some tests): {failures}")

    # 2) Single reflexion iteration
    improved_code = apply_reflexion(reflexion_prompt, build_context, initial_code, failures)
    print("\nImproved code:\n" + improved_code)
    improved_func = load_function_from_code(improved_code)
    passed2, failures2 = evaluate_function(improved_func)
    if passed2:
        print("SUCCESS")
        return True

    print("Tests still failing after reflexion:")
    for f in failures2:
        print("- " + f)
    return False


if __name__ == "__main__":
    run_reflexion_flow(SYSTEM_PROMPT, YOUR_REFLEXION_PROMPT, your_build_reflexion_context)
