# ABOUTME: Optional multi-worker prompt queue patch. Spawns extra prompt_worker
# ABOUTME: threads when ERPK.PARALLEL_WORKERS > 1, enabling concurrent prompt execution.

import threading
import time

from .settings import get_comfy_setting

_SENTINEL_ATTR = "_erpk_parallel_workers_installed"
_DEFAULT_WORKERS = 1
_MAX_WORKERS = 8


def _clamp_worker_count(value):
    """Coerce and clamp the setting value to [1, _MAX_WORKERS].

    Returns _DEFAULT_WORKERS for non-numeric inputs so the system never
    crashes on a malformed setting — single-worker (off) is the safe fallback.
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        return _DEFAULT_WORKERS
    if n < 1:
        return 1
    if n > _MAX_WORKERS:
        return _MAX_WORKERS
    return n


def _erpk_worker_loop(q, server_instance):
    """Mirror of ComfyUI's main.prompt_worker, simplified for the extra workers.

    Each instance owns its PromptExecutor and event loop. The shared queue's
    RLock+Condition makes concurrent get() calls safe.
    """
    import execution
    try:
        import comfy.model_management
        from comfy.cli_args import args
    except ImportError:
        return

    cache_ram = args.cache_ram
    if cache_ram < 0:
        cache_ram = min(32.0, max(4.0, comfy.model_management.total_ram * 0.25 / 1024.0))

    cache_type = execution.CacheType.CLASSIC
    if args.cache_lru > 0:
        cache_type = execution.CacheType.LRU
    elif cache_ram > 0:
        cache_type = execution.CacheType.RAM_PRESSURE
    elif args.cache_none:
        cache_type = execution.CacheType.NONE

    e = execution.PromptExecutor(
        server_instance,
        cache_type=cache_type,
        cache_args={"lru": args.cache_lru, "ram": cache_ram},
    )

    while True:
        try:
            queue_item = q.get(timeout=1000.0)
            if queue_item is None:
                continue
            item, item_id = queue_item

            prompt_id = item[1]
            server_instance.last_prompt_id = prompt_id

            sensitive = item[5]
            extra_data = item[3].copy()
            for k in sensitive:
                extra_data[k] = sensitive[k]

            e.execute(item[2], prompt_id, extra_data, item[4])

            remove_sensitive = lambda prompt: prompt[:5] + prompt[6:]
            q.task_done(
                item_id,
                e.history_result,
                status=execution.PromptQueue.ExecutionStatus(
                    status_str="success" if e.success else "error",
                    completed=e.success,
                    messages=e.status_messages,
                ),
                process_item=remove_sensitive,
            )

            if server_instance.client_id is not None:
                server_instance.send_sync(
                    "executing",
                    {"node": None, "prompt_id": prompt_id},
                    server_instance.client_id,
                )
        except Exception as ex:
            # One bad prompt mustn't kill the worker thread.
            print(f"[ERPK] parallel worker error: {ex}")
            time.sleep(0.1)


def install():
    """Spawn extra prompt_worker threads when ERPK.PARALLEL_WORKERS > 1.

    Default is 1 (preserve ComfyUI's single-worker behavior). Idempotent via
    sentinel on the prompt_queue. No-op (silent) when ComfyUI's server isn't
    importable — keeps test environments clean.

    SAFETY WARNING (visible at startup when enabled): local-diffusion
    workflows will race on GPU memory under multi-worker mode. Intended for
    API-only deployments where the heavy work runs on remote services.
    """
    try:
        raw_setting = get_comfy_setting("ERPK.PARALLEL_WORKERS", default=_DEFAULT_WORKERS)
        n_workers = _clamp_worker_count(raw_setting)
        if n_workers <= 1:
            return

        from server import PromptServer
        if PromptServer is None:
            return
        queue = PromptServer.instance.prompt_queue
        server_instance = PromptServer.instance

        if getattr(queue, _SENTINEL_ATTR, False):
            return

        extras = n_workers - 1
        for i in range(extras):
            t = threading.Thread(
                target=_erpk_worker_loop,
                args=(queue, server_instance),
                daemon=True,
                name=f"erpk-prompt-worker-{i + 1}",
            )
            t.start()

        setattr(queue, _SENTINEL_ATTR, True)
        print(
            f"[ERPK] Spawned {extras} extra prompt worker(s) (total: {n_workers}). "
            f"WARNING: local-diffusion workflows will race on GPU under multi-worker mode."
        )
    except ImportError:
        pass
    except Exception as e:
        print(f"[ERPK] Warning: Could not install parallel workers: {e}")
