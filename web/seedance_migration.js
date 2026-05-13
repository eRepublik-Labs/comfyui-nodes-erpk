// ABOUTME: Frontend onConfigure migration for Seedance 2.0 t2v and i2v node widget reorder.
// ABOUTME: Detects older widget layouts by widgets_values length and remaps stored values to new slots.

import { app } from "../../../scripts/app.js";

// --- Image-to-Video target layout (v2026.5.4+) ---
// Widget positions in widgets_values:
// 0: start_frame_url      (String)
// 1: end_frame_url        (String)
// 2: model                (Combo, value like "Seedance 2.0")
// 3: prompt               (String, multiline)
// 4: duration             (Int)
// 5: aspect_ratio         (Combo)
// 6: resolution           (Combo)
// 7: seed                 (Int)
// 8: control_after_generate companion (auto-emitted from seed's IO.Int)
// 9: enable_web_search    (Boolean)
// 10: generate_audio      (Boolean)
//
// Input slots (non-widget): start_frame (IMAGE), end_frame (IMAGE), client (CUSTOM).
//
// Layout history shipped:
//   v2026.4.x: [model, prompt, image, duration, aspect, res, seed, [control]]
//   WIP-intermediate: [model, prompt, image, duration, aspect, res, seed, [control], last_image, ref_image_urls, ews, ga]
//   WIP-with-refs:    [model, prompt, start_frame, end_frame, ref_imgs, ref_vids, ref_auds, duration, aspect, res, seed, [control], ews, ga]
//   v2026.5.1–5.3:    [model, prompt, start_frame_url, end_frame_url, duration, aspect, res, seed, [control], ews, ga]
//   v2026.5.4 (this): [start_frame_url, end_frame_url, model, prompt, duration, aspect, res, seed, [control], ews, ga]
//
// Detection uses value sniffing (model name regex at known position) rather than length
// because IO.Int.control_after_generate emits an invisible companion widget that shifts
// every widgets_values length by +1.

const SEEDANCE_MODEL_RE = /^Seedance/;

function migrateI2V(node, oldValues) {
    if (!Array.isArray(oldValues)) return false;
    const w = node.widgets;
    if (!w || w.length < 4) return false;

    // Target layout: model name is at position 2. Skip migration.
    if (typeof oldValues[2] === "string" && SEEDANCE_MODEL_RE.test(oldValues[2])) {
        return false;
    }

    // All pre-reorder layouts have model name at position 0.
    if (!(typeof oldValues[0] === "string" && SEEDANCE_MODEL_RE.test(oldValues[0]))) {
        return false;
    }

    const pos3 = oldValues[3];

    // pos[3] is a string → either v2026.5.1–5.3 (post-rename) or WIP-with-refs.
    // Disambiguate by pos[4]: number = duration (5.1+ layout), string = reference_images (WIP-with-refs).
    if (typeof pos3 === "string") {
        if (typeof oldValues[4] === "number") {
            // v2026.5.1/5.2/5.3 → target reorder: move URLs to positions 0-1, model+prompt to 2-3.
            w[0].value = oldValues[2];    // start_frame_url
            w[1].value = oldValues[3];    // end_frame_url
            w[2].value = oldValues[0];    // model
            w[3].value = oldValues[1];    // prompt
            for (let i = 4; i < oldValues.length && i < w.length; i++) {
                w[i].value = oldValues[i];
            }
            return true;
        }
        if (typeof oldValues[4] === "string") {
            // WIP-with-refs: skip ref_imgs/videos/audios at indexes 4-6.
            w[0].value = oldValues[2];    // start_frame_url ← start_frame URL
            w[1].value = oldValues[3];    // end_frame_url ← end_frame URL
            w[2].value = oldValues[0];    // model
            w[3].value = oldValues[1];    // prompt
            // Source positions for duration/aspect/res/seed/[control]/ews/ga are 7..end
            const offset = 3; // skip 3 reference fields (4,5,6)
            for (let i = 4; i < w.length && (i + offset) < oldValues.length; i++) {
                w[i].value = oldValues[i + offset];
            }
            return true;
        }
        return false;
    }

    // pos[3] is a number (duration) → v2026.4.x legacy or WIP-intermediate (pre-rename).
    if (typeof pos3 === "number") {
        const hasControl = typeof oldValues[7] === "string"
            && /^(randomize|increment|decrement|fixed)$/.test(oldValues[7]);
        const postSeedIdx = hasControl ? 8 : 7;
        const isWipIntermediate = oldValues.length > postSeedIdx + 1;

        w[0].value = oldValues[2];                                       // start_frame_url ← image
        w[1].value = isWipIntermediate ? oldValues[postSeedIdx] : "";    // end_frame_url ← last_image or default
        w[2].value = oldValues[0];                                       // model
        w[3].value = oldValues[1];                                       // prompt
        w[4].value = oldValues[3];                                       // duration
        w[5].value = oldValues[4];                                       // aspect_ratio
        w[6].value = oldValues[5];                                       // resolution
        w[7].value = oldValues[6];                                       // seed

        if (isWipIntermediate) {
            // WIP-intermediate had ews/ga after [last_image, ref_image_urls]. Skip ref_image_urls.
            const ewsIdx = postSeedIdx + 2;
            const gaIdx  = postSeedIdx + 3;
            const ewsW = w.find(x => x.name === "enable_web_search");
            const gaW  = w.find(x => x.name === "generate_audio");
            if (ewsW && oldValues[ewsIdx] !== undefined) ewsW.value = oldValues[ewsIdx];
            if (gaW  && oldValues[gaIdx]  !== undefined) gaW.value  = oldValues[gaIdx];
        }
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
