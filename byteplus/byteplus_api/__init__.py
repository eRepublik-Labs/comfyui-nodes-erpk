# ABOUTME: byteplus_api package: emit (flushed console lines). Submodules: client (ModelArk HTTP + task
# ABOUTME: polling), seedance and seedream (per-model capability tables, request builders, prices), media.


def emit(message: str) -> None:
    """Print one [BytePlus] line and flush it. ComfyUI's stdout is not line buffered when redirected
    to a file, and a task ID or a recovered file's path must survive a crash."""
    print(f"[BytePlus] {message}", flush=True)
