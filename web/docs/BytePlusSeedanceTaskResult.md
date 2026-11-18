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
| seed | Int | -1 | Cache control only, never sent. -1 reads the task again on every queue; a fixed value reuses the last answer |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | Video URL once the task succeeded, else empty. Valid 24 h (a 2.5 URL allows at most 100 downloads) |
| last_frame_url | String | Final-frame JPEG URL if the task was created with `return_last_frame`, else empty |
| status | String | `queued`, `running`, `succeeded`, `failed`, `expired` or `cancelled` |

## Notes

- The node only reads the task, so it starts nothing and bills nothing.
- Pressing Cancel while it waits behaves like the Seedance nodes: a task still `queued` is deleted, which cancels it; a `running` task cannot be cancelled and finishes and bills.
- With `wait` off, a `failed`, `expired` or `cancelled` status is returned rather than raised, and the console prints ModelArk's reason.
- Task IDs stay valid for 7 days (2.5 draft IDs for 14). The video URL itself is valid for 24 hours, so fetch it within a day.
