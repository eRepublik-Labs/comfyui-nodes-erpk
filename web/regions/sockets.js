// ABOUTME: Manages the node's desc_N / ref_N input sockets that bind to regions by depth slot.
// ABOUTME: Exposes, removes, labels, and styles the per-region description and reference-image inputs.

import {
    REGION_DESC_INPUTS,
    REGION_REF_INPUTS,
    ACTIVE_GREEN,
    ACTIVE_GREEN_BORDER,
} from "./constants.js";

export function installSockets(E) {
    const { node, state } = E;

    // Socket families: desc_N strings override a region's description, ref_N
    // images attach a numbered reference. A connected socket owns its
    // region's slot; the node face only carries sockets that are exposed or
    // wired, since the Vue renderer ignores input.hidden, so unexposed
    // sockets are physically removed and re-added on demand (removeInput
    // fixes up link slot indices; wired sockets are never removed). Labels
    // carry the region's text so a depth reorder visibly remaps the wires.
    const SOCKET_FAMILIES = {
        desc: { ioType: "STRING", max: REGION_DESC_INPUTS, key: "erpk_region_desc" },
        ref: { ioType: "IMAGE", max: REGION_REF_INPUTS, key: "erpk_region_ref" },
    };

    function socketWiredFor(prefix, box) {
        const index = state.boxes.indexOf(box);
        if (index < 0) return false;
        const input = node.inputs?.find((i) => i.name === `${prefix}_${index + 1}`);
        return input?.link != null;
    }

    function exposedSocketSet(prefix) {
        const saved = node.properties?.[SOCKET_FAMILIES[prefix].key];
        return new Set(Array.isArray(saved) ? saved : []);
    }

    function persistExposedSockets(prefix, set) {
        if (!node.properties) node.properties = {};
        node.properties[SOCKET_FAMILIES[prefix].key] = [...set].sort((a, b) => a - b);
    }

    function syncFamilySockets(prefix) {
        if (!node.inputs) return;
        const family = SOCKET_FAMILIES[prefix];
        const pattern = new RegExp(`^${prefix}_(\\d+)$`);
        const exposed = exposedSocketSet(prefix);
        let changed = false;
        for (const input of node.inputs) {
            const match = input.name?.match(pattern);
            if (match && input.link != null && !exposed.has(+match[1])) {
                exposed.add(+match[1]);
                changed = true;
            }
        }
        for (let i = node.inputs.length - 1; i >= 0; i--) {
            const input = node.inputs[i];
            const match = input.name?.match(pattern);
            if (match && !exposed.has(+match[1]) && input.link == null) {
                node.removeInput(i);
            }
        }
        for (const n of [...exposed].sort((a, b) => a - b)) {
            if (n < 1 || n > family.max) continue;
            if (!node.inputs.some((i) => i.name === `${prefix}_${n}`)) {
                node.addInput(`${prefix}_${n}`, family.ioType);
            }
        }
        for (const input of node.inputs) {
            const match = input.name?.match(pattern);
            if (!match) continue;
            const n = +match[1];
            const box = state.boxes[n - 1];
            const text = box ? (box.desc || box.text || `region ${n}`) : "unused";
            input.label = `${prefix} ${n} · ${text.length > 18 ? text.slice(0, 17) + "…" : text}`;
        }
        if (changed) persistExposedSockets(prefix, exposed);
        const computed = node.computeSize?.();
        if (computed && node.size[1] < computed[1]) {
            node.setSize([node.size[0], computed[1]]);
        }
    }

    function toggleFamilySocket(prefix) {
        const index = E.primaryIndex();
        if (index < 0 || index >= SOCKET_FAMILIES[prefix].max) return;
        if (socketWiredFor(prefix, state.primary)) return;
        const n = index + 1;
        const exposed = exposedSocketSet(prefix);
        if (exposed.has(n)) exposed.delete(n);
        else exposed.add(n);
        persistExposedSockets(prefix, exposed);
        syncFamilySockets(prefix);
        node.setDirtyCanvas?.(true, true);
        E.render();
    }

    function descWiredFor(box) {
        return socketWiredFor("desc", box);
    }

    function refWiredFor(box) {
        return socketWiredFor("ref", box);
    }

    function syncRegionSockets() {
        syncFamilySockets("desc");
        syncFamilySockets("ref");
    }

    function onPlugToggle() {
        toggleFamilySocket("desc");
    }

    function onRefToggle() {
        toggleFamilySocket("ref");
    }

    // Styles a ⌁/▣ socket toggle for the given region: active green when the
    // socket is exposed or wired, disabled past the socket-family cap.
    function syncSocketToggle(btn, prefix, box) {
        const wiredFor = prefix === "desc" ? descWiredFor : refWiredFor;
        const cap = prefix === "desc" ? REGION_DESC_INPUTS : REGION_REF_INPUTS;
        const noun = prefix === "desc" ? "description" : "reference image";
        const index = box ? state.boxes.indexOf(box) : -1;
        const wired = !!box && wiredFor(box);
        const wireable = index >= 0 && index < cap;
        const plugged = wireable
            && (wired || exposedSocketSet(prefix).has(index + 1));
        btn.disabled = !wireable || wired;
        btn.style.opacity = wireable ? "1" : "0.45";
        btn.classList.toggle("erpk-btn-active", plugged);
        btn.style.color = plugged
            ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
        btn.style.borderColor = plugged
            ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
        btn.dataset.tip = wired
            ? `The ${noun} is wired — disconnect the input to unplug`
            : plugged
                ? `Hide this region's ${noun} input`
                : wireable
                    ? prefix === "desc"
                        ? "Expose this region's description as an input"
                        : "Attach a reference image input to this region"
                    : `Only regions 1–${cap} can take a ${noun} input`;
    }

    Object.assign(E, {
        descWiredFor,
        refWiredFor,
        syncRegionSockets,
        syncSocketToggle,
        onPlugToggle,
        onRefToggle,
        toggleFamilySocket,
    });
}
