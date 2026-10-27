import os
import logging
from config import GROQ_COMPLETION_TOKENS
from groq_client import request_completion, log_failure, GroqGenerationError

def main():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key and os.path.exists("secret.txt"):
        with open("secret.txt", encoding="utf-8") as key_file:
            api_key = key_file.read().strip()

    if not api_key:
        raise SystemExit("No Groq API key found. Add secret.txt or set GROQ_API_KEY.")

    try:
        result = request_completion(api_key,
            [{"role": "user", "content": "Reply with exactly: Groq connection works"}],
            max_completion_tokens=GROQ_COMPLETION_TOKENS["test_api.py"], json_mode=False, temperature=0)
        if result.content != "Groq connection works":
            raise GroqGenerationError("Final content did not match the expected connection response", result.diagnostics)
    except GroqGenerationError as exc:
        log_failure(logging.getLogger("test_api"), "test_api.py", exc)
        raise SystemExit("FAIL: " + str(exc)) from None
    print("Status: 200")
    print("PASS: Groq connection works")


if __name__ == "__main__":
    main()
