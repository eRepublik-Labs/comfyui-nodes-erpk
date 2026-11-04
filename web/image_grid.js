// ABOUTME: Registers the drop-and-reorder image grid on every node in GRID_NODES, uploading
// ABOUTME: picked or dropped files to ComfyUI's input folder and showing thumbnails served from it.
// @ts-check

// app.js and api.js are resolved by ComfyUI at runtime; they are not present at type-check time.
// @ts-ignore
import { app } from "../../../scripts/app.js";
// @ts-ignore
import { api } from "../../../scripts/api.js";

import { storedName, viewPath } from "./image_grid/grid_list.js";
import { installImageGrid } from "./image_grid/mount.js";

const GRID_NODES = ["ImageGridLoader"];

/** @param {File} file */
async function uploadToInput(file) {
    const body = new FormData();
    body.append("image", file);
    body.append("type", "input");
    const response = await api.fetchApi("/upload/image", { method: "POST", body });
    if (response.status !== 200) {
        throw new Error(`Upload of "${file.name}" failed: ${response.status} ${response.statusText}.`);
    }
    // The route renames on a name clash and reuses an identical file, so the
    // answered name, not the local one, is what lands in the list.
    return storedName(await response.json());
}

const gridIO = {
    upload: uploadToInput,
    imageUrl: (/** @type {string} */ stored) => api.apiURL(viewPath(stored)),
};

app.registerExtension({
    name: "erpk.imageGrid",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (GRID_NODES.includes(nodeData?.name)) installImageGrid(nodeType, gridIO);
    },
});
