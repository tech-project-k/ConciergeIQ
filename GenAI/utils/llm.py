import concurrent.futures
import threading
from typing import Any, Callable, Optional


class LLMTimeoutError(RuntimeError):
    pass


def invoke_with_timeout(
    llm: Any,
    prompt: str,
    timeout: float = 5.0,
    fallback: Optional[Callable[[str], Any]] = None,
) -> Any:
    """Run an LLM invoke call with a hard timeout and fallback."""
    if llm is None:
        if fallback is not None:
            return fallback(prompt)
        raise LLMTimeoutError("LLM client is unavailable")

    def _run() -> Any:
        return llm.invoke(prompt)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            if fallback is not None:
                return fallback(prompt)
            raise LLMTimeoutError("LLM call timed out") from exc
