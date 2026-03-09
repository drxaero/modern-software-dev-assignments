from dotenv import load_dotenv
from ollama_client import call_api

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """
You are a precise instruction-following machine that performs exactly one narrow transformation and outputs **nothing else**.

Rules you must follow without exception:
1. Output **only** the final transformed result
2. Do not output any explanation, prefix, suffix, note, space, newline, punctuation, or quotation marks
3. Do not repeat the original text
4. Do not say "the answer is", "reversed:", "here:", etc.
5. If the task is to reverse the letters of a single word, produce exactly the letters in reverse order — and nothing more
6. Preserve exact case (upper/lower)
7. Never add or remove any character

Examples of correct behavior:

Input: abcdef
Output: fedcba

Input: Hello
Output: olleH

Input: 12345
Output: 54321

Input: httpstatus
Output: sutatsptth

Begin.
"""

USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"

def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = call_api(
            model="mistral-nemo:12b",
            sys_prompt=system_prompt,
            usr_prompt=USER_PROMPT,
            temperature= 0.5,
        )
        output_text = response.strip()
        print(f"LM output: {output_text}")
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)