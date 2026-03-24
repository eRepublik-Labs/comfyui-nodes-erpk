// ABOUTME: Frontend extension that rewrites old V1 node type names to V3 node IDs in workflows.
// ABOUTME: Prevents "missing nodes" dialog when loading workflows saved before the V3 migration.

import { app } from "../../scripts/app.js";

// V1 node type → V3 node_id. Must match _NODE_REPLACEMENTS in __init__.py.
const NODE_REPLACEMENTS = {
    // WaveSpeed
    "WaveSpeed Custom Client": "WaveSpeedAIAPIClient",
    "WaveSpeed Custom Preview Video": "PreviewVideo",
    "WaveSpeed Custom Save Audio": "SaveAudio",
    "WaveSpeed Custom Upload Image": "UploadImage",
    "WaveSpeed Custom SeedreamV4": "SeedreamV4Node",
    "WaveSpeed Custom SeedreamV4Edit": "SeedreamV4EditNode",
    "WaveSpeed Custom SeedreamV4Sequential": "SeedreamV4SequentialNode",
    "WaveSpeed Custom SeedreamV4EditSequential": "SeedreamV4EditSequentialNode",
    "WaveSpeed Custom SeedreamV4_5": "SeedreamV4_5Node",
    "WaveSpeed Custom SeedreamV4_5Edit": "SeedreamV4_5EditNode",
    "WaveSpeed Custom SeedreamV4_5Sequential": "SeedreamV4_5SequentialNode",
    "WaveSpeed Custom SeedreamV4_5EditSequential": "SeedreamV4_5EditSequentialNode",
    "WaveSpeed Custom QwenImageT2I": "QwenImageTextToImageNode",
    "WaveSpeed Custom QwenImageEdit": "QwenImageEditNode",
    "WaveSpeed Custom QwenImageEditPlus": "QwenImageEditPlusNode",
    // Apple ML
    "ERPK SHARP Predict": "SHARPPredict",
    "ERPK SHARP Render Views": "SHARPRenderViews",
    "ERPK SHARP Render Video": "SHARPRenderVideo",
};

app.registerExtension({
    name: "erpk.node_migration",

    async setup() {
        const original = app.loadGraphData.bind(app);
        app.loadGraphData = async function (graphData, ...args) {
            if (graphData?.nodes) {
                let migrated = 0;
                for (const node of graphData.nodes) {
                    const replacement = NODE_REPLACEMENTS[node.type];
                    if (replacement) {
                        node.type = replacement;
                        migrated++;
                    }
                }
                if (migrated > 0) {
                    console.log(`[ERPK] Migrated ${migrated} node(s) from V1 to V3 IDs`);
                }
            }
            return original(graphData, ...args);
        };
    },
});
