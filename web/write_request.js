// ABOUTME: Sends a request to an ERPK write route with the server's per-process write token.
// ABOUTME: Shared by the shared-workflow dialogs and the API key settings.

import { api } from "../../scripts/api.js";

// Write and delete routes require the server's per-process token so a
// cross-site page cannot reach them. Fetched once, refreshed if the server
// restarted (a 403 on a write).
let writeToken = null;

async function fetchWriteToken() {
    const resp = await api.fetchApi("/erpk/write_token");
    if (!resp.ok) throw new Error(`write token request failed: ${resp.status}`);
    writeToken = (await resp.json()).token;
    return writeToken;
}

export async function writeRequest(path, options = {}) {
    const send = async () => {
        const token = writeToken ?? (await fetchWriteToken());
        return api.fetchApi(path, {
            ...options,
            headers: { ...(options.headers ?? {}), "X-ERPK-Write-Token": token },
        });
    };
    let resp = await send();
    if (resp.status === 403) {
        writeToken = null;
        resp = await send();
    }
    return resp;
}
