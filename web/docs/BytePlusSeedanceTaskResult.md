<!-- ABOUTME: Help documentation for the BytePlus Seedance Task Result ComfyUI node. -->
<!-- ABOUTME: Reads a Seedance task's status and result URLs from BytePlus ModelArk by task ID. -->

# BytePlus Seedance Task Result

Fetches a Seedance task's video URL, last-frame URL and status by task ID. Use it to collect a video after a run was cancelled, timed out or lost its connection: the task keeps running on ModelArk and bills either way. Reading a task is free.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| task_id | String | (empty) | ModelArk task ID (`cgt-...`), from a Seedance node's `task_id` output, its console log, or the ModelArk console |
| client | BYTEPLUS_API_CLIENT | none | BytePlus API Client (optional when the key is in Settings or config.ini) |
| wait | Boolean | true | On: poll every 8 s until the task finishes, and raise with ModelArk's code and message if it failed or expired. Off: read the status once |
| seed | Int | -1 | Cache control only, never sent. Randomize reads the task again on every queue; a fixed value reuses the last answer, even a `queued` or `running` status from before the task finished |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | Video URL once the task succeeded, else empty. Valid 24 h (a 2.5 URL allows at most 100 downloads) |
| last_frame_url | String | Final-frame image URL (PNG when measured on 2026-11-18) if the task was created with `return_last_frame`, else empty |
| status | String | `queued`, `running`, `succeeded`, `failed`, `expired` or `cancelled` |

## Notes

- The node only reads the task, so it starts nothing and bills nothing.
- Pressing Cancel while it waits only stops the wait. The node never cancels or deletes a task, whatever its status, and the console says the task is untouched.
- With `wait` off, a `failed`, `expired` or `cancelled` status is returned rather than raised, and the console prints ModelArk's reason.
- With `wait` off, keep `seed` on randomize until the task has finished. With a fixed seed, ComfyUI serves the cached answer, so a `queued` or `running` status never refreshes and the URLs stay empty. Any new seed value reads the task again.
- A task ID stays valid for 7 days from creation; a 2.5 draft ID created since 2026-10-28 stays valid for 14. ModelArk deletes a `cancelled` task's record after 24 hours. The video URL itself is valid for 24 hours, so fetch it within a day.
