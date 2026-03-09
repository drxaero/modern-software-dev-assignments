import re
from collections import Counter
from dotenv import load_dotenv
from ollama_client import call_api

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in! Try to get as close to 100% correctness across all runs as possible.
YOUR_SYSTEM_PROMPT = """
You are an extremely careful and precise mathematical reasoner. Your only goal is to solve the word problem correctly — never guess, never assume missing information, never skip steps.

Follow this exact step-by-step thinking style every time:

1. Read the problem slowly and identify every number and every distance relationship mentioned.
2. Write down what each sentence actually means in plain mathematical language.
3. Draw a number line or list the segments in order from start → finish.
4. Assign variables or directly label every important point (start, first stop, second stop, end).
5. Calculate every segment length one by one. Show every subtraction or addition.
6. Double-check that the sum of all segments equals the total distance given.
7. If you find any contradiction, stop and restart the reasoning from step 1.
8. Only after you are 100 percent certain write the final answer.

Rules you must never break:
- Do NOT do mental math — write every calculation.
- Do NOT combine steps that skip intermediate distances.
- The phrase "before the end" means remaining distance to the finish line.
- Final answer format must be exactly: Answer: <number>
  (nothing else on that line)

Solve the problem using only the information explicitly stated."""

USER_PROMPT = """
Solve this problem, then give the final answer on the last line as "Answer: <number>".

Henry made two stops during his 60-mile bike trip. He first stopped after 20
miles. His second stop was 15 miles before the end of the trip. How many miles
did he travel between his first and second stops?
"""

EXPECTED_OUTPUT = "Answer: 25"


def extract_final_answer(text: str) -> str:
    """Extract the final 'Answer: ...' line from a verbose reasoning trace.

    - Finds the LAST line that starts with 'Answer:' (case-insensitive)
    - Normalizes to 'Answer: <number>' when a number is present
    - Falls back to returning the matched content if no number is detected
    """
    matches = re.findall(r"(?mi)^\s*answer\s*:\s*(.+)\s*$", text)
    if matches:
        value = matches[-1].strip()
        num_match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if num_match:
            return f"Answer: {num_match.group(0)}"
        return f"Answer: {value}"
    return text.strip()


def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt NUM_RUNS_TIMES, majority-vote on the extracted 'Answer: ...' lines.

    Prints "SUCCESS" if the majority answer equals EXPECTED_OUTPUT.
    """
    answers: list[str] = []
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = call_api(
            model="llama3.1:8b",
            sys_prompt = system_prompt,
            usr_prompt=USER_PROMPT,
            temperature= 1,
        )
        output_text = response
        final_answer = extract_final_answer(output_text)
        print(f"Run {idx + 1} answer: {final_answer}")
        answers.append(final_answer.strip())

    if not answers:
        print("No answers produced.")
        return False

    counts = Counter(answers)
    majority_answer, majority_count = counts.most_common(1)[0]
    print(f"Majority answer: {majority_answer} ({majority_count}/{len(answers)})")

    if majority_answer.strip() == EXPECTED_OUTPUT.strip():
        print("SUCCESS")
        return True

    # Print distribution for debugging when majority does not match expected
    print(f"Expected output: {EXPECTED_OUTPUT}")
    print("Answer distribution:")
    for answer, count in counts.most_common():
        print(f"  {answer}: {count}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)


