# ABOUTME: Monkey-patches PromptQueue.task_done to auto-clear job history entries.
# ABOUTME: Controlled by the ERPK.AUTO_CLEAR_HISTORY setting (off by default).

import threading
import time
import types

from settings import get_comfy_setting

# Lazy-imported in install() to avoid import errors outside ComfyUI
PromptServer = None


def make_wrapped_task_done(original_fn):
    """Wrap task_done to optionally delete history entries after completion."""

    def wrapped_task_done(self, item_id, *args, **kwargs):
        # Extract prompt_id from currently_running before original clears it
        prompt_id = None
        with self.mutex:
            item = self.currently_running.get(item_id)
            if item and len(item) > 1:
                prompt_id = item[1]

        # Always call the original to avoid stuck queue state
        original_fn(item_id, *args, **kwargs)

        if not prompt_id:
            return

        if not get_comfy_setting("ERPK.AUTO_CLEAR_HISTORY", default=False):
            return

        def delayed_delete():
            # Give frontend time to fetch /history/{prompt_id} on completion
            time.sleep(5)
            with self.mutex:
                self.history.pop(prompt_id, None)
            try:
                self.server.queue_updated()
            except Exception:
                pass

        threading.Thread(target=delayed_delete, daemon=True).start()

    return wrapped_task_done


def install():
    """Patch PromptQueue.task_done. Call once at import time."""
    global PromptServer
    try:
        from server import PromptServer as _PS
        PromptServer = _PS

        queue = PromptServer.instance.prompt_queue
        queue.task_done = types.MethodType(
            make_wrapped_task_done(queue.task_done), queue
        )
        print("[ERPK] Installed job history auto-clear patch")
    except ImportError:
        pass
    except Exception as e:
        print(f"[ERPK] Warning: Could not install history cleaner: {e}")
