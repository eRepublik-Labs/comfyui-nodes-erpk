// ABOUTME: Pure operations on the image grid's ordered filename list, plus the text it shows.
// ABOUTME: No DOM, app, or api imports, so plain node can exercise every function here.
// @ts-check

export const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp"];
export const ACCEPTED_LABEL = "PNG, JPG, WEBP";

/**
 * Read the `grid_images` widget value. A value that is not a JSON list of filenames
 * is reported rather than repaired, so a broken workflow stays visible.
 * @param {unknown} value
 * @returns {{ names: string[], error: string | null }}
 */
export function parseStoredList(value) {
    let parsed;
    try {
        parsed = typeof value === "string" ? JSON.parse(value) : value;
    } catch {
        return { names: [], error: unreadable(value) };
    }
    if (Array.isArray(parsed) && parsed.every((name) => typeof name === "string" && name !== "")) {
        return { names: parsed, error: null };
    }
    return { names: [], error: unreadable(value) };
}

function unreadable(value) {
    return `Could not read the saved image list ${JSON.stringify(value)}. Adding images replaces it.`;
}

/**
 * @typedef {{ model_widget: string | null, caps: Record<string, number> }} GridCaps
 *   One node's entry from /erpk/grid_caps: the model combo's name and the most images each model takes.
 * @typedef {{ cap: number, model: string | null }} GridLimit
 *   The most images the grid takes, and the model when that model's own limit is what sets it.
 */

/**
 * The grid_max_images value, lowered to the selected model's cap. On a tie the model
 * is named, as utils/image_grid.py load_grid_images does: raising grid_max_images would not help.
 * @param {number} widgetCap
 * @param {GridCaps | undefined} caps
 * @param {unknown} model the model widget's value; unused when the node has no model widget
 * @returns {GridLimit}
 */
export function gridLimit(widgetCap, caps, model) {
    if (!caps) return { cap: widgetCap, model: null };
    const cap = modelCap(caps.caps, String(model));
    if (caps.model_widget === null || cap > widgetCap) return { cap: Math.min(cap, widgetCap), model: null };
    return { cap, model: String(model) };
}

/**
 * Mirrors grid_cap_for in utils/image_grid.py: the model's own entry, else "*", else the largest.
 * @param {Record<string, number>} table @param {string} model
 */
function modelCap(table, model) {
    if (Object.hasOwn(table, model)) return table[model];
    if (Object.hasOwn(table, "*")) return table["*"];
    return Math.max(...Object.values(table));
}

/**
 * The red notice while the grid holds more images than the selected model takes, else null.
 * @param {number} count @param {GridLimit} limit
 */
export function modelLimitText(count, { cap, model }) {
    if (model === null || count <= cap) return null;
    return `${model} takes up to ${plural(cap, "image")}, remove ${count - cap}`;
}

export function remainingSlots(count, cap) {
    return Math.max(cap - count, 0);
}

export function removeAt(names, index) {
    return names.filter((_, i) => i !== index);
}

/**
 * Move the item at `from` so it lands before the item now at `insertAt`
 * (`insertAt === names.length` appends). Returns the list and the item's new index.
 */
export function moveItem(names, from, insertAt) {
    const next = names.slice();
    const [item] = next.splice(from, 1);
    const index = insertAt > from ? insertAt - 1 : insertAt;
    next.splice(index, 0, item);
    return { names: next, index };
}

/** Keyboard move: shift the item at `from` by `delta` places, clamped to the list. */
export function moveBy(names, from, delta) {
    const target = Math.min(Math.max(from + delta, 0), names.length - 1);
    return moveItem(names, from, target > from ? target + 1 : target);
}

/** The name ComfyUI's upload route answered with, in the form the node resolves. */
export function storedName({ name, subfolder }) {
    return subfolder ? `${subfolder}/${name}` : name;
}

/** The ComfyUI /view path that serves a stored name from the input directory. */
export function viewPath(stored) {
    const slash = stored.lastIndexOf("/");
    const query = new URLSearchParams({
        filename: stored.slice(slash + 1),
        type: "input",
        subfolder: slash === -1 ? "" : stored.slice(0, slash),
    });
    return `/view?${query}`;
}

/**
 * Split picked or dropped files into the ones to upload now and the ones
 * left out, given how many slots are filled or already uploading.
 * @template {{ type: string }} T
 * @param {T[]} files
 * @param {number} filled
 * @param {number} cap
 */
export function planAdd(files, filled, cap) {
    const images = files.filter((file) => ACCEPTED_TYPES.includes(file.type));
    const room = remainingSlots(filled, cap);
    return {
        take: images.slice(0, room),
        overflow: Math.max(images.length - room, 0),
        wrongType: files.length - images.length,
    };
}

export function plural(count, noun) {
    return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

export function countLabel(count, cap) {
    return `${count} of ${cap}`;
}

/** @param {number} count @param {GridLimit} limit */
export function capacityText(count, { cap, model }) {
    if (count > cap) {
        const fix = model === null ? `remove ${count - cap} or raise grid_max_images` : `remove ${count - cap}`;
        return `${countLabel(count, cap)} · ${fix}`;
    }
    const left = remainingSlots(count, cap);
    if (left === 0) return `${countLabel(count, cap)} · grid is full`;
    return `${countLabel(count, cap)} · ${left} more can be dropped`;
}

/**
 * Copy for the drag-over overlay. `imageCount` is null when the browser does
 * not reveal what is being dragged until the drop.
 * @param {number | null} imageCount
 */
export function dropPrompt(imageCount, count, cap) {
    const left = remainingSlots(count, cap);
    if (left === 0) {
        return { full: true, title: `Grid is full, ${countLabel(count, cap)}.`, detail: "Remove one first." };
    }
    if (imageCount === 0) {
        return { full: true, title: "Nothing to add", detail: `Only ${ACCEPTED_LABEL} files can be dropped.` };
    }
    const title = imageCount === null
        ? "Drop to add images"
        : `Drop to add ${plural(Math.min(imageCount, left), "image")}`;
    return { full: false, title, detail: `${left} of ${cap} slots left · extra files are ignored` };
}

/** The notice shown after an add: what went in, what was left out, and why. */
export function addSummary({ added, overflow, wrongType, failures }) {
    const parts = [];
    if (added) parts.push(`Added ${plural(added, "image")}.`);
    if (overflow) parts.push(`${plural(overflow, "file")} ignored, the grid is full.`);
    if (wrongType) parts.push(`${plural(wrongType, "file")} skipped, only ${ACCEPTED_LABEL} can be added.`);
    parts.push(...failures);
    return parts.join(" ");
}
