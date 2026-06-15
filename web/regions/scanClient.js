// ABOUTME: Vision-scan network calls and cost formatting for the region editor.
// ABOUTME: Pure of app and editor state — callers own state, the canvas, and result handling.
// @ts-check

// --- Scan cost readout ------------------------------------------------
// The scan response carries {usd, input_tokens, output_tokens, ...}. usd is
// null when the model has no price on file (then we say "price n/a" rather
// than imply free). The figure is a paid-tier estimate; free-tier scans bill
// nothing, which the docs note.
export function fmtUsd(usd) {
    if (usd == null) return "n/a";
    if (usd === 0) return "$0";
    // A scan is a few cents; show enough precision to read sub-cent figures.
    return usd < 0.1 ? `$${usd.toFixed(4)}` : `$${usd.toFixed(2)}`;
}

export function costLine(cost) {
    if (!cost) return "Scan cost unavailable";
    const tokens = (cost.input_tokens || 0) + (cost.output_tokens || 0);
    if (cost.usd == null) {
        return `Scan: ${tokens.toLocaleString()} tokens · price n/a`;
    }
    return `Scan: ${fmtUsd(cost.usd)} · ${tokens.toLocaleString()} tokens`;
}

// POST a scan request, returning the HTTP ok/status and the parsed body. A
// non-JSON body decodes to {} so callers can fall back on res.ok/status.
export async function postScan(body, signal) {
    const res = await fetch("/erpk/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal,
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
}

// A scan can hang on a slow segmenter or a dropped connection; without a cap it
// pins the busy state forever. Generous enough that a real CPU SAM pass finishes.
export const SCAN_TIMEOUT_MS = 120000;

// postScan with a client-side timeout. The caller owns the AbortController (kept
// in state so destroy and a cancel re-click can abort the same request); this
// arms a timer that aborts it. Returns the normal {ok,status,json} on completion,
// or {timedOut:true} when the timer fired and {aborted:true} when the caller
// aborted (cancel/destroy) — letting callers tell a timeout from a cancel.
export async function postScanWithTimeout(body, controller, timeoutMs = SCAN_TIMEOUT_MS) {
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
    try {
        return await postScan(body, controller.signal);
    } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
            return timedOut ? { timedOut: true } : { aborted: true };
        }
        throw err;
    } finally {
        clearTimeout(timer);
    }
}

// The scan model list, or null when the fetch fails or returns nothing usable;
// callers keep the previous list (or the server default) on null.
export async function fetchScanModels() {
    try {
        const res = await fetch("/erpk/scan/models");
        const json = await res.json();
        if (json && Array.isArray(json.models) && json.models.length) return json;
    } catch (_) { /* fall through to the default-only list */ }
    return null;
}

// The segmenter list, or null when the fetch fails or returns nothing usable.
export async function fetchScanSegmenters() {
    try {
        const res = await fetch("/erpk/scan/segmenters");
        const json = await res.json();
        if (json && Array.isArray(json.segmenters)) return json;
    } catch (_) { /* fall through to the default-only list */ }
    return null;
}
