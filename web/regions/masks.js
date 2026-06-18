// ABOUTME: Segmentation-mask decode and cache helpers for display — decode base64 PNGs into images.
// ABOUTME: Pure of app and editor state; the render callback and source image are passed in.
// @ts-check

// Lazily decode a region's stored mask into the _erpkMaskImg cache, which is
// runtime-only and so empty after a reload. Re-renders once it loads, so the
// mask silhouette (cut-out checker, move ghost) appears instead of falling
// back to the whole box. Returns the image (possibly not yet complete).
export function ensureMaskImg(box, render) {
    if (!box || !box.mask) return null;
    let img = box._erpkMaskImg;
    if (!img) {
        img = new Image();
        img.addEventListener("load", () => render(), { once: true });
        // A corrupt/empty base64 mask never fires `load`; flag it so callers fall
        // back to a full-box crop (mirroring the Python composite's except-pass)
        // instead of staying stuck showing the untouched source.
        img.addEventListener("error", () => { box._erpkMaskFailed = true; render(); }, { once: true });
        img.src = "data:image/png;base64," + box.mask;
        box._erpkMaskImg = img;
    }
    return img;
}

// SAM masks are opaque grayscale PNGs: brightness encodes the shape but
// alpha is 1 everywhere, so compositing against the raw image clips
// nothing. This converts luminance into a real alpha channel (thresholded
// like the Python composite) once per region.
export function maskAlphaCanvas(box) {
    if (box._erpkMaskAlpha) return box._erpkMaskAlpha;
    const img = box._erpkMaskImg;
    if (!img || !img.complete || !img.naturalWidth) return null;
    const off = document.createElement("canvas");
    off.width = img.naturalWidth;
    off.height = img.naturalHeight;
    const offCtx = off.getContext("2d", { willReadFrequently: true });
    offCtx.drawImage(img, 0, 0);
    const data = offCtx.getImageData(0, 0, off.width, off.height);
    const px = data.data;
    for (let i = 0; i < px.length; i += 4) {
        px[i + 3] = px[i] > 127 ? 255 : 0;
    }
    offCtx.putImageData(data, 0, 0);
    box._erpkMaskAlpha = off;
    return off;
}

// 14px transparency-checker tile, built once and shared as a pattern.
let checkerTile = null;
export function checkerPattern(target) {
    if (!checkerTile) {
        checkerTile = document.createElement("canvas");
        checkerTile.width = 14;
        checkerTile.height = 14;
        const tctx = checkerTile.getContext("2d");
        tctx.fillStyle = "rgba(186, 186, 186, 0.92)";
        tctx.fillRect(0, 0, 14, 14);
        tctx.fillStyle = "rgba(118, 118, 118, 0.92)";
        tctx.fillRect(0, 0, 7, 7);
        tctx.fillRect(7, 7, 7, 7);
    }
    return target.createPattern(checkerTile, "repeat");
}

// The erase-preview at a moved region's origin: a transparency checker
// clipped to the object's silhouette, reading as "already cut out".
// Rebuilt only when the rendered size changes.
export function ghostCheckerFor(box, gw, gh) {
    const pw = Math.max(1, Math.round(gw));
    const ph = Math.max(1, Math.round(gh));
    const cached = box._erpkGhostChecker;
    if (cached && cached.width === pw && cached.height === ph) return cached;
    const alpha = maskAlphaCanvas(box);
    if (!alpha) return null;
    const off = document.createElement("canvas");
    off.width = pw;
    off.height = ph;
    const offCtx = off.getContext("2d");
    offCtx.fillStyle = checkerPattern(offCtx);
    offCtx.fillRect(0, 0, pw, ph);
    offCtx.globalCompositeOperation = "destination-in";
    offCtx.drawImage(alpha, 0, 0, pw, ph);
    box._erpkGhostChecker = off;
    return off;
}

// The object pixels cropped from the source image at the region's source box,
// for the relocation preview of a moved region and the occluder re-stamp of a
// static one. With a decodable mask the crop is clipped to the silhouette; a
// maskless region (or one whose mask failed to decode) yields the FULL source
// rectangle, mirroring the Python composite's alpha=ones fallback. Built once
// per region (cached on the box). Returns null only while a present mask is
// still decoding, or when the source image / source box is unavailable.
export function cutoutFor(box, img, render) {
    if (box._erpkCutout) return box._erpkCutout;
    if (!img || !img.complete || !img.naturalWidth || !box.src) return null;
    let alpha = null;
    if (box.mask && !box._erpkMaskFailed) {
        const maskImg = ensureMaskImg(box, render);
        if (!maskImg.complete || !maskImg.naturalWidth) {
            // Still decoding (ensureMaskImg's load/error listeners re-render).
            if (!box._erpkMaskFailed) return null;
        } else {
            alpha = maskAlphaCanvas(box);
        }
    }
    const pw = Math.max(1, Math.round(box.src.w * img.naturalWidth));
    const ph = Math.max(1, Math.round(box.src.h * img.naturalHeight));
    const off = document.createElement("canvas");
    off.width = pw;
    off.height = ph;
    const offCtx = off.getContext("2d");
    offCtx.drawImage(
        img,
        box.src.x * img.naturalWidth, box.src.y * img.naturalHeight,
        pw, ph, 0, 0, pw, ph,
    );
    if (alpha) {
        offCtx.globalCompositeOperation = "destination-in";
        offCtx.drawImage(alpha, 0, 0, pw, ph);
    }
    box._erpkCutout = off;
    return off;
}

// True when the region's segmentation covers the point, false when the
// point falls in the empty part of the mask, null when there is no usable
// mask. Pixel data decodes once per region into a cached ImageData.
export function maskPixelHit(box, p) {
    if (!box.mask) return null;
    let img = box._erpkMaskImg;
    if (!img) {
        img = new Image();
        img.src = "data:image/png;base64," + box.mask;
        box._erpkMaskImg = img;
    }
    if (!img.complete || !img.naturalWidth) return null;
    if (!box._erpkMaskData) {
        const off = document.createElement("canvas");
        off.width = img.naturalWidth;
        off.height = img.naturalHeight;
        const offCtx = off.getContext("2d", { willReadFrequently: true });
        offCtx.drawImage(img, 0, 0);
        box._erpkMaskData = offCtx.getImageData(0, 0, off.width, off.height);
    }
    const u = (p.x - box.x) / box.w;
    const v = (p.y - box.y) / box.h;
    if (u < 0 || u > 1 || v < 0 || v > 1) return false;
    const data = box._erpkMaskData;
    const col = Math.min(data.width - 1, Math.floor(u * data.width));
    const row = Math.min(data.height - 1, Math.floor(v * data.height));
    return data.data[(row * data.width + col) * 4] > 127;
}
