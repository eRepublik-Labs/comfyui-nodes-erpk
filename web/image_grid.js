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

// Each node here declares the grid's input with grid_input() from utils/image_grid.py
// and registers its caps there with register_grid_caps().
// `socket` names the input that, when linked, the node sends instead of the grid.
/** @type {{ nodeId: string, socket?: string }[]} */
const GRID_NODES = [
    { nodeId: "ImageGridLoader" },
    { nodeId: "OpenAIImageEdit", socket: "image" },
    { nodeId: "GrokImageEdit", socket: "image" },
    { nodeId: "GeminiImageEdit", socket: "image" },
    { nodeId: "QwenImageMaxEditNode", socket: "reference_images" },
    { nodeId: "QwenImage20EditNode", socket: "reference_images" },
    { nodeId: "QwenImage30EditNode", socket: "reference_images" },
    { nodeId: "QwenImageEditPlusNode", socket: "reference_images" },
    { nodeId: "QwenImageEditPlusLoraNode", socket: "reference_images" },
    { nodeId: "QwenImageMultipleAnglesNode", socket: "reference_images" },
    { nodeId: "SeedreamV4EditNode", socket: "images" },
    { nodeId: "SeedreamV4EditSequentialNode", socket: "images" },
    { nodeId: "SeedreamV4_5EditNode", socket: "images" },
    { nodeId: "SeedreamV4_5EditSequentialNode", socket: "images" },
    { nodeId: "SeedreamV5LiteEditNode", socket: "images" },
    { nodeId: "SeedreamV5LiteEditSequentialNode", socket: "images" },
    { nodeId: "SeedreamV5ProEditNode", socket: "images" },
    { nodeId: "MinimaxH3ImageEditNode", socket: "images" },
];

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
    fullImageUrl: (/** @type {string} */ stored) => api.apiURL(viewPath(stored, { preview: false })),
};

/** @type {Promise<Record<string, import("./image_grid/grid_list.js").GridCaps>> | null} */
let gridCaps = null;

// Fetched once, by the first grid node type to register. A failed fetch rejects
// every grid node's registration, which ComfyUI logs, rather than leaving the
// grid to accept more images than the selected model takes.
function loadGridCaps() {
    gridCaps ??= api.fetchApi("/erpk/grid_caps").then(async (/** @type {Response} */ response) => {
        if (response.status !== 200) {
            throw new Error(`Loading the image grid caps failed: ${response.status} ${response.statusText}.`);
        }
        return response.json();
    });
    return gridCaps;
}

app.registerExtension({
    name: "erpk.imageGrid",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        const gridNode = GRID_NODES.find((entry) => entry.nodeId === nodeData?.name);
        if (!gridNode) return;
        const caps = (await loadGridCaps())[gridNode.nodeId];
        if (!caps) throw new Error(`${gridNode.nodeId} registers no image grid caps; see register_grid_caps.`);
        installImageGrid(nodeType, gridIO, { socket: gridNode.socket, caps, nodeName: nodeData.display_name ?? nodeData.name });
    },
});
