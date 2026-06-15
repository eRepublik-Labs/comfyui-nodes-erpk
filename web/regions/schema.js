// ABOUTME: Pure serializer/deserializer between the region editor's in-memory
// ABOUTME: region array and the versioned regions_data document the prompt builder parses.
// @ts-check

// Mirrors utils/region_contract.py: deserializeRegions reads a v1 list or a v2
// document into the editor's flat in-memory region shape, and serializeRegions
// emits a v2 document whose fields region_contract.parse() accepts. Masks carry
// only the base64 string; the editor decodes them for display and never encodes.

const SCHEMA_VERSION = 2;
const MIN_REGION_EXTENT = 0.005;
const REGION_KINDS = new Set(["object", "text"]);
const MASK_ENC = "png-b64";

function clamp(value, lower, upper) {
    return Math.min(Math.max(value, lower), upper);
}

function round4(value) {
    return Math.round(value * 10000) / 10000;
}

// Parse and clamp a normalized box mapping, or null if unusable or sub-extent.
function coerceBox(value) {
    if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
    const nums = [value.x, value.y, value.w, value.h].map((v) => Number(v ?? 0));
    if (!nums.every(Number.isFinite)) return null;
    const x = clamp(nums[0], 0, 1);
    const y = clamp(nums[1], 0, 1);
    const w = clamp(nums[2], 0, 1 - x);
    const h = clamp(nums[3], 0, 1 - y);
    if (w <= MIN_REGION_EXTENT || h <= MIN_REGION_EXTENT) return null;
    return { x, y, w, h };
}

function coerceStr(value) {
    return typeof value === "string" ? value : "";
}

function coerceOptionalStr(value) {
    return typeof value === "string" && value ? value : null;
}

function coerceKind(value) {
    return typeof value === "string" && REGION_KINDS.has(value) ? value : "object";
}

// A bind reads its stable socket slot; booleans and non-numbers carry no slot.
function coerceBindSlot(value) {
    if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
    const slot = value.slot;
    if (typeof slot === "boolean") return null;
    const n = Number(slot);
    return Number.isFinite(n) ? Math.trunc(n) : null;
}

function isPlainObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

// Read a v1 list or v2 document into a depth-ordered list of in-memory regions.
export function deserializeRegions(jsonString) {
    let data;
    try {
        data = typeof jsonString === "string" ? JSON.parse(jsonString) : jsonString;
    } catch (_) {
        return [];
    }
    let regions;
    if (Array.isArray(data)) {
        regions = parseV1(data);
    } else if (isPlainObject(data)) {
        regions = parseV2(data);
    } else {
        return [];
    }
    repairParentLinks(regions);
    return regions;
}

function parseV1(entries) {
    const regions = [];
    for (const entry of entries) {
        const region = parseV1Entry(entry);
        if (region) regions.push(region);
    }
    return regions;
}

function parseV1Entry(entry) {
    if (!isPlainObject(entry)) return null;
    const box = coerceBox(entry);
    if (!box) return null;
    const region = {
        x: box.x, y: box.y, w: box.w, h: box.h,
        kind: coerceKind(entry.kind),
        desc: coerceStr(entry.desc),
        text: coerceStr(entry.text),
    };
    // Scan-produced optionals: a box-relative base64 PNG mask, a class label,
    // and the origin box. Absent for hand-drawn regions.
    if (typeof entry.mask === "string" && entry.mask) region.mask = entry.mask;
    if (typeof entry.group === "string" && entry.group) region.group = entry.group;
    const id = coerceOptionalStr(entry.id);
    if (id) region.id = id;
    const parent = coerceOptionalStr(entry.parent);
    if (parent) region.parent = parent;
    if (entry.hidden === true) region.hidden = true;
    if (entry.cutout === true) region.cutout = true;
    const src = coerceBox(entry.src);
    if (src) region.src = src;
    // A scanned region with no recorded origin has not moved: its current box
    // is its origin, so the move preview stays comparable.
    if (region.mask && !region.src) {
        region.src = { x: box.x, y: box.y, w: box.w, h: box.h };
    }
    return region;
}

function parseV2(doc) {
    const raw = doc.regions;
    if (!Array.isArray(raw)) return [];
    const parsed = [];
    const byId = new Map();
    for (const entry of raw) {
        const region = parseV2Entry(entry);
        if (!region) continue;
        parsed.push(region);
        if (region.id && !byId.has(region.id)) byId.set(region.id, region);
    }
    const order = doc.order;
    if (!Array.isArray(order)) return parsed;
    // order[] carries depth back-to-front, decoupled from the regions array.
    const ordered = [];
    const seen = new Set();
    for (const rid of order) {
        const region = byId.get(rid);
        if (region && !seen.has(region)) {
            ordered.push(region);
            seen.add(region);
        }
    }
    for (const region of parsed) {
        if (!seen.has(region)) {
            ordered.push(region);
            seen.add(region);
        }
    }
    return ordered;
}

function parseV2Entry(entry) {
    if (!isPlainObject(entry)) return null;
    const box = coerceBox(entry.box);
    if (!box) return null;
    const region = {
        x: box.x, y: box.y, w: box.w, h: box.h,
        kind: coerceKind(entry.kind),
        desc: "",
        text: "",
    };
    if (isPlainObject(entry.content)) {
        region.desc = coerceStr(entry.content.desc);
        region.text = coerceStr(entry.content.text);
    }
    const id = coerceOptionalStr(entry.id);
    if (id) region.id = id;
    if (entry.op === "cutout") region.cutout = true;
    if (entry.edit_by === "model") region.edit_by = "model";
    const bindSlot = coerceBindSlot(entry.bind);
    if (bindSlot !== null) region.bind_slot = bindSlot;
    if (isPlainObject(entry.ui)) {
        const parent = coerceOptionalStr(entry.ui.parent);
        if (parent) region.parent = parent;
        if (entry.ui.hidden === true) region.hidden = true;
        if (entry.ui.collapsed === true) region.collapsed = true;
    }
    applyV2Source(region, entry.source, box);
    return region;
}

function applyV2Source(region, source, box) {
    if (!isPlainObject(source)) return;
    // A source mapping always pins an origin: a missing or unusable box means
    // the scanned region sits where it was found, so its box is its origin.
    const srcBox = coerceBox(source.box);
    region.src = srcBox || { x: box.x, y: box.y, w: box.w, h: box.h };
    const label = coerceOptionalStr(source.label);
    if (label) region.group = label;
    const mask = source.mask;
    if (isPlainObject(mask) && typeof mask.data === "string" && mask.data) {
        region.mask = mask.data;
    }
}

// Make every parent link valid and acyclic. Dangling links (target gone) are
// dropped, and parent cycles are broken by cutting the back-edge that closes
// them. The chain-walkers (descendantsOf, isDescendantOf, effectiveHidden) loop
// on the parent pointers with no cycle guard, so a hand-edited or crafted
// workflow with a loop (a -> b -> a) would hang the tab on load without this.
function repairParentLinks(regions) {
    const byId = new Map();
    for (const region of regions) {
        if (region.id) byId.set(region.id, region);
    }
    for (const region of regions) {
        if (region.parent && !byId.has(region.parent)) delete region.parent;
    }
    for (const region of regions) {
        const seen = new Set();
        let cur = region;
        while (cur && cur.parent) {
            seen.add(cur);
            const parent = byId.get(cur.parent);
            if (!parent) break;
            if (seen.has(parent)) {
                delete cur.parent;  // back-edge into the chain: cut it
                break;
            }
            cur = parent;
        }
    }
}

// Render the in-memory region list into a v2 document string for regions_data.
export function serializeRegions(regions) {
    const ids = assignIds(regions);
    return JSON.stringify({
        version: SCHEMA_VERSION,
        order: ids.slice(),
        regions: regions.map((region, index) => regionToEntry(region, ids[index])),
    });
}

// Give every id-less region a stable id unique within the document, returning
// the ids aligned to the regions array without mutating the regions.
function assignIds(regions) {
    const ids = regions.map((r) => (typeof r.id === "string" && r.id ? r.id : ""));
    const used = new Set(ids.filter(Boolean));
    let counter = 0;
    for (let i = 0; i < ids.length; i++) {
        if (ids[i]) continue;
        let candidate = `r${counter}`;
        while (used.has(candidate)) {
            counter += 1;
            candidate = `r${counter}`;
        }
        ids[i] = candidate;
        used.add(candidate);
        counter += 1;
    }
    return ids;
}

function regionToEntry(region, id) {
    const entry = {
        id,
        kind: coerceKind(region.kind),
        box: {
            x: round4(region.x), y: round4(region.y),
            w: round4(region.w), h: round4(region.h),
        },
        content: { desc: coerceStr(region.desc), text: coerceStr(region.text) },
    };
    // source{} only rides along for scanned regions: a mask, a class label, or
    // a recorded origin box marks the region as scanned rather than hand-drawn.
    if (region.mask || region.group || region.src) {
        const origin = region.src ? region.src : region;
        entry.source = {
            box: {
                x: round4(origin.x), y: round4(origin.y),
                w: round4(origin.w), h: round4(origin.h),
            },
            mask: region.mask
                ? { enc: MASK_ENC, w: 0, h: 0, data: region.mask }
                : null,
            label: coerceStr(region.group),
        };
    }
    entry.op = region.cutout ? "cutout" : "normal";
    // Default ("node") stays out so node-applied regions serialize as before.
    if (region.edit_by === "model") entry.edit_by = "model";
    entry.bind = (typeof region.bind_slot === "number" && Number.isFinite(region.bind_slot))
        ? { slot: Math.trunc(region.bind_slot) }
        : null;
    entry.ui = {
        parent: coerceOptionalStr(region.parent),
        hidden: region.hidden === true,
        collapsed: region.collapsed === true,
    };
    return entry;
}
