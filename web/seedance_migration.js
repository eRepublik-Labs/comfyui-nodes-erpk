// ABOUTME: Frontend onConfigure migration for Seedance 2.0 t2v and i2v node widget reorder.
// ABOUTME: Detects older widget layouts by widgets_values length and remaps stored values to new slots.

import { app } from "../../../scripts/app.js";

// --- Image-to-Video target layout (10 widgets; client is a non-widget input slot) ---
// 0: model
// 1: prompt
// 2: start_frame    (was: image)
// 3: end_frame      (was: last_image)
// 4: duration
// 5: aspect_ratio
// 6: resolution
// 7: seed
// 8: enable_web_search
// 9: generate_audio
//
// Reference image/video/audio widgets were removed in 2026-05-13 after live API tests
// proved WaveSpeed silently ignores reference_images on the i2v endpoint.

function migrateI2V(node, oldValues) {
    if (!Array.isArray(oldValues)) return false;
    const w = node.widgets;
    if (!w) return false;

    // v2026.4.x layout: 7 widgets [model, prompt, image, duration, aspect_ratio, resolution, seed]
    if (oldValues.length === 7) {
        w[2].value = oldValues[2];   // start_frame ← image
        w[3].value = "";             // end_frame default
        w[4].value = oldValues[3];   // duration
        w[5].value = oldValues[4];   // aspect_ratio
        w[6].value = oldValues[5];   // resolution
        w[7].value = oldValues[6];   // seed
        // enable_web_search, generate_audio keep defaults
        return true;
    }

    // WIP intermediate layout: 11 widgets [model, prompt, image, duration, aspect_ratio,
    //   resolution, seed, last_image, reference_image_urls, enable_web_search, generate_audio]
    if (oldValues.length === 11) {
        w[2].value = oldValues[2];   // start_frame ← image
        w[3].value = oldValues[7];   // end_frame ← last_image
        // oldValues[8] (reference_image_urls) discarded — field removed
        w[4].value = oldValues[3];   // duration
        w[5].value = oldValues[4];   // aspect_ratio
        w[6].value = oldValues[5];   // resolution
        w[7].value = oldValues[6];   // seed
        w[8].value = oldValues[9];   // enable_web_search
        w[9].value = oldValues[10];  // generate_audio
        return true;
    }

    // WIP-with-refs layout: 13 widgets [model, prompt, start_frame, end_frame,
    //   reference_images, reference_videos, reference_audios, duration, aspect_ratio,
    //   resolution, seed, enable_web_search, generate_audio]
    if (oldValues.length === 13) {
        w[2].value = oldValues[2];   // start_frame stays
        w[3].value = oldValues[3];   // end_frame stays
        // oldValues[4..6] (reference_images/videos/audios) discarded — fields removed
        w[4].value = oldValues[7];   // duration
        w[5].value = oldValues[8];   // aspect_ratio
        w[6].value = oldValues[9];   // resolution
        w[7].value = oldValues[10];  // seed
        w[8].value = oldValues[11];  // enable_web_search
        w[9].value = oldValues[12];  // generate_audio
        return true;
    }

    return false;
}

// --- Text-to-Video target layout (11 widgets) ---
// 0: model
// 1: prompt
// 2: reference_images
// 3: reference_videos
// 4: reference_audios
// 5: duration
// 6: aspect_ratio
// 7: resolution
// 8: seed
// 9: enable_web_search
// 10: generate_audio

function migrateT2V(node, oldValues) {
    if (!Array.isArray(oldValues)) return false;
    const w = node.widgets;
    if (!w) return false;

    // v2026.4.x layout: 6 widgets [model, prompt, duration, aspect_ratio, resolution, seed]
    if (oldValues.length === 6) {
        w[2].value = "";             // reference_images default
        w[3].value = "";             // reference_videos default
        w[4].value = "";             // reference_audios default
        w[5].value = oldValues[2];   // duration
        w[6].value = oldValues[3];   // aspect_ratio
        w[7].value = oldValues[4];   // resolution
        w[8].value = oldValues[5];   // seed
        // enable_web_search, generate_audio keep defaults
        return true;
    }

    // Pre-reorder WIP layout: 9 widgets [model, prompt, duration, aspect_ratio, resolution,
    //   seed, reference_image_urls, enable_web_search, generate_audio]
    if (oldValues.length === 9) {
        w[2].value = oldValues[6];   // reference_images ← reference_image_urls
        w[3].value = "";             // reference_videos default
        w[4].value = "";             // reference_audios default
        w[5].value = oldValues[2];   // duration
        w[6].value = oldValues[3];   // aspect_ratio
        w[7].value = oldValues[4];   // resolution
        w[8].value = oldValues[5];   // seed
        w[9].value = oldValues[7];   // enable_web_search
        w[10].value = oldValues[8];  // generate_audio
        return true;
    }

    return false;
}

const NODE_MIGRATIONS = {
    "Seedance20ImageToVideoNode": migrateI2V,
    "Seedance20TextToVideoNode": migrateT2V,
};

app.registerExtension({
    name: "erpk.seedance_migration",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        const migrate = NODE_MIGRATIONS[nodeData.name];
        if (!migrate) return;

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);
            const oldValues = info?.widgets_values;
            const migrated = migrate(this, oldValues);
            if (migrated) {
                console.log(`[ERPK] Migrated ${nodeData.name} widget layout (had ${oldValues.length} values)`);
            }
            return result;
        };
    },
});
