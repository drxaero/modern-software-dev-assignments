import re

import requests
from dotenv import load_dotenv
from ollama_client import call_api

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """You are a rigorous mathematician who always thinks step by step, verifies every calculation, and restarts from the beginning if verification fails.

Your sole task is to follow the user's prompt precisely using rigorous mathematical methods. Compute the result, then place the final answer on the very last line starting with your response in this exact format:
Answer: <the number you calculated>
"""

USER_PROMPT = """
Solve this problem, then give the final answer on the last line as "Answer: <number>".

what is 3^{12345} (mod 100)?
"""


# For this simple example, we expect the final numeric answer only
EXPECTED_OUTPUT = "Answer: 43"


def extract_final_answer(text: str) -> str:
    """Extract the final 'Answer: ...' line from a verbose reasoning trace.

    - Finds the LAST line that starts with 'Answer:' (case-insensitive)
    - Normalizes to 'Answer: <number>' when a number is present
    - Falls back to returning the matched content if no number is detected
    """
    matches = re.findall(r"(?mi)^\s*answer\s*:\s*(.+)\s*$", text)
    if matches:
        value = matches[-1].strip()
        # Prefer a numeric normalization when possible (supports integers/decimals)
        num_match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if num_match:
            return f"Answer: {num_match.group(0)}"
        return f"Answer: {value}"
    return text.strip()


def test_your_prompt(sys_prompt: str) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        
        # Combine system and user prompts
        try:
            output_text = call_api("llama3.1:8b", sys_prompt, USER_PROMPT, temperature=0.3)
            # print(f"LM output: {output_text}")
            final_answer = extract_final_answer(output_text)
            if final_answer.strip() == EXPECTED_OUTPUT.strip():
                print("SUCCESS")
                return True
            else:
                print(f"Expected output: {EXPECTED_OUTPUT}")
                print(f"Actual output: {final_answer}")
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return False
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)


