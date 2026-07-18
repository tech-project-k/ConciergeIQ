import pathlib
import sys
import time

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from utils.llm import invoke_with_timeout


class BlockingLLM:
    def invoke(self, prompt):
        time.sleep(0.2)
        raise RuntimeError("should not have completed")


def test_invoke_with_timeout_falls_back_on_timeout():
    llm = BlockingLLM()

    result = invoke_with_timeout(
        llm,
        "prompt",
        timeout=0.05,
        fallback=lambda prompt: "fallback-result",
    )

    assert result == "fallback-result"
