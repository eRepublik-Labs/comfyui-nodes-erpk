// ABOUTME: JavaScript extension for the ERPK_ConcatenateStrings node.
// ABOUTME: Provides add/remove buttons for input slots while maintaining connectability.

import { app } from "../../../scripts/app.js";

const NODE_ID = "ERPK_ConcatenateStrings";
const MAX_INPUTS = 10;
const INITIAL_INPUTS = 2;

// Classic LiteGraph checks widget.hidden; Nodes 2.0 (Vue) checks widget.options.hidden.
// Set both so visibility works in either renderer.
function setWidgetHidden(widget, hidden) {
    widget.hidden = hidden;
    if (!widget.options) widget.options = {};
    widget.options.hidden = hidden;
}

app.registerExtension({
    name: "erpk.utils.concat_strings",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== NODE_ID) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = async function () {
            const result = onNodeCreated?.apply(this, arguments);

            // Track active input count
            this.activeInputCount = this.properties?.activeInputCount || INITIAL_INPUTS;
            this.properties = this.properties || {};
            this.properties.activeInputCount = this.activeInputCount;

            // Delay to ensure widgets and DOM elements exist, then set up UI once
            setTimeout(() => {
                this._styleInputsHeader();
                this._updateInputVisibility();
                this._setupResizableInputs();
                this._createControlWidgets();  // Create once, never remove
                if (!this._isLoadingWorkflow) {
                    this._resizeNode();
                } else if (this._savedSize) {
                    // Immediately restore size after widget creation
                    this.size[0] = this._savedSize[0];
                    this.size[1] = this._savedSize[1];
                }
            }, 50);

            return result;
        };

        // Restore state when loading workflow
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            // Set flag SYNCHRONOUSLY - onNodeCreated's setTimeout will see this
            this._isLoadingWorkflow = true;

            // Save the original size from workflow JSON
            if (info.size) {
                this._savedSize = [info.size[0], info.size[1]];
            }

            const result = onConfigure?.apply(this, arguments);

            if (info.properties?.activeInputCount) {
                this.activeInputCount = info.properties.activeInputCount;
            }

            // On load, update visibility, restore input heights, and restore size
            setTimeout(() => {
                this._updateInputVisibility();
                this._updateControlWidgetVisibility();
                this._restoreInputHeights();

                // Restore saved size after LiteGraph's requestAnimationFrame resize
                if (this._savedSize) {
                    const savedSize = this._savedSize;
                    const node = this;
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            node.size[0] = savedSize[0];
                            node.size[1] = savedSize[1];
                            node.setDirtyCanvas(true, true);
                        });
                    });
                }
            }, 100);

            return result;
        };

        // Update visibility of text/label widgets and inputs
        nodeType.prototype._updateInputVisibility = function () {
            if (!this.widgets) return;

            for (const widget of this.widgets) {
                const textMatch = widget.name.match(/^Text (\d+)$/);
                const labelMatch = widget.name.match(/^Label (\d+)$/);

                if (textMatch) {
                    const idx = parseInt(textMatch[1]);
                    setWidgetHidden(widget, idx > this.activeInputCount);
                } else if (labelMatch) {
                    const idx = parseInt(labelMatch[1]);
                    setWidgetHidden(widget, idx > this.activeInputCount);
                }
            }

            // Hide/show input slots (connection points) based on active count
            if (this.inputs) {
                for (const input of this.inputs) {
                    const textMatch = input.name.match(/^Text (\d+)$/);
                    const labelMatch = input.name.match(/^Label (\d+)$/);

                    if (textMatch) {
                        input.hidden = parseInt(textMatch[1]) > this.activeInputCount;
                    } else if (labelMatch) {
                        input.hidden = parseInt(labelMatch[1]) > this.activeInputCount;
                    }
                }
            }
        };

        // Create control widgets once (called only from onNodeCreated)
        nodeType.prototype._createControlWidgets = function () {
            if (!this.widgets || this._controlWidgetsCreated) return;
            this._controlWidgetsCreated = true;

            const self = this;

            // Spacer before buttons (canvas-only; hidden from Nodes 2.0)
            const addSpacer = this.addWidget(
                "text",
                "_spacer_add",
                "",
                () => {},
                { serialize: false, hidden: true }
            );
            addSpacer.disabled = true;
            addSpacer.computeSize = () => [0, 10];
            addSpacer.draw = () => {};

            // Add Input button (always create, control visibility)
            const addBtn = this.addWidget(
                "button",
                "\u2795 Add Input",
                null,
                () => { self._addInput(); },
                { serialize: false }
            );
            this._addInputBtn = addBtn;

            // Remove Last Input button (always create, control visibility)
            const removeBtn = this.addWidget(
                "button",
                "\u2796 Remove Last Input",
                null,
                () => { self._removeLastInput(); },
                { serialize: false }
            );
            this._removeInputBtn = removeBtn;

            // Bottom spacer for margin (canvas-only; hidden from Nodes 2.0)
            const bottomSpacer = this.addWidget(
                "text",
                "_spacer_bottom",
                "",
                () => {},
                { serialize: false, hidden: true }
            );
            bottomSpacer.disabled = true;
            bottomSpacer.computeSize = () => [0, 8];
            bottomSpacer.draw = () => {};

            // Set initial visibility
            this._updateControlWidgetVisibility();
        };

        // Update control widget visibility based on activeInputCount
        nodeType.prototype._updateControlWidgetVisibility = function () {
            if (this._addInputBtn) {
                setWidgetHidden(this._addInputBtn, this.activeInputCount >= MAX_INPUTS);
            }
            if (this._removeInputBtn) {
                setWidgetHidden(this._removeInputBtn, this.activeInputCount <= 1);
            }
        };

        // Add a new input slot
        nodeType.prototype._addInput = function () {
            if (this.activeInputCount < MAX_INPUTS) {
                this.activeInputCount++;
                this.properties.activeInputCount = this.activeInputCount;

                // Clear the newly revealed input's values
                const textWidget = this.widgets?.find(w => w.name === `Text ${this.activeInputCount}`);
                const labelWidget = this.widgets?.find(w => w.name === `Label ${this.activeInputCount}`);
                if (textWidget) textWidget.value = "";
                if (labelWidget) labelWidget.value = "";

                this._updateInputVisibility();
                this._updateControlWidgetVisibility();
                this._resizeNode();
            }
        };

        // Remove the last input slot
        nodeType.prototype._removeLastInput = function () {
            if (this.activeInputCount <= 1) return;

            // Clear the last input's values
            const lastText = this.widgets.find(w => w.name === `Text ${this.activeInputCount}`);
            const lastLabel = this.widgets.find(w => w.name === `Label ${this.activeInputCount}`);
            if (lastText) lastText.value = "";
            if (lastLabel) lastLabel.value = "";

            // Disconnect any links to the last input
            if (this.inputs) {
                const textInput = this.inputs.find(inp => inp.name === `Text ${this.activeInputCount}`);
                const labelInput = this.inputs.find(inp => inp.name === `Label ${this.activeInputCount}`);
                if (textInput && textInput.link != null) {
                    app.graph.removeLink(textInput.link);
                }
                if (labelInput && labelInput.link != null) {
                    app.graph.removeLink(labelInput.link);
                }
            }

            this.activeInputCount--;
            this.properties.activeInputCount = this.activeInputCount;
            this._updateInputVisibility();
            this._updateControlWidgetVisibility();
            this._resizeNode();
        };

        // Check if a DOM element is actually visible on screen
        function isVisible(el) {
            if (!el || !el.offsetParent) return false;
            const style = window.getComputedStyle(el);
            return style.display !== "none" && style.visibility !== "hidden";
        }

        // Find the textarea element for a widget across both renderers.
        // In Nodes 2.0, widget.element points to the classic-mode textarea (not visible).
        // The visible textarea is rendered separately by WidgetTextarea.vue.
        function findTextarea(widget) {
            // Check widget references first — works in classic mode
            const candidates = [
                widget.element?.tagName === "TEXTAREA" ? widget.element : null,
                widget.element?.querySelector?.("textarea"),
                widget.inputEl?.tagName === "TEXTAREA" ? widget.inputEl : null,
            ].filter(Boolean);

            // Return the first visible candidate
            for (const el of candidates) {
                if (isVisible(el)) return el;
            }

            // Nodes 2.0: WidgetTextarea.vue renders its own textarea with a <label>
            // showing the widget name. Find it via the label text.
            const labels = document.querySelectorAll("label");
            for (const label of labels) {
                if (label.textContent.trim() !== widget.name) continue;
                const container = label.parentElement;
                if (!container) continue;
                const ta = container.querySelector("textarea");
                if (ta && isVisible(ta)) return ta;
            }

            // Fallback: return first candidate even if not visible (setup in progress)
            return candidates[0] || null;
        }

        // Enable vertical resize on Text N textareas and persist heights.
        // Retries to handle async DOM rendering in Nodes 2.0.
        nodeType.prototype._setupResizableInputs = function (attempt = 0) {
            if (!this.widgets) return;
            this.properties.inputHeights = this.properties.inputHeights || {};
            if (!this._resizeObservers) this._resizeObservers = [];
            const node = this;
            let pending = false;

            for (const widget of this.widgets) {
                if (!widget.name.match(/^Text \d+$/)) continue;
                if (widget._resizeSetup) continue;

                const textarea = findTextarea(widget);
                if (!textarea || !isVisible(textarea)) {
                    pending = true;
                    continue;
                }

                // Inline !important overrides both Tailwind's resize-none class
                // and the design-system's resize:none rule
                textarea.style.setProperty("resize", "vertical", "important");
                textarea.style.setProperty("overflow-y", "auto", "important");
                textarea.style.setProperty("min-height", "40px", "important");
                textarea.style.setProperty("height", "auto", "important");

                // Restore saved height (after setting height:auto)
                const savedHeight = this.properties.inputHeights[widget.name];
                if (savedHeight) {
                    textarea.style.setProperty("height", savedHeight + "px", "important");
                }

                // Track resize and persist
                const observer = new ResizeObserver((entries) => {
                    for (const entry of entries) {
                        const h = Math.round(entry.contentRect.height);
                        node.properties.inputHeights[widget.name] = h;
                        if (widget.computeSize) {
                            widget.computeSize = () => [0, h + 10];
                        }
                        node.setDirtyCanvas?.(true, true);
                    }
                });
                observer.observe(textarea);
                this._resizeObservers.push(observer);
                widget._resizeSetup = true;
            }

            // Retry if some textareas weren't available yet (Vue async rendering)
            if (pending && attempt < 10) {
                setTimeout(() => this._setupResizableInputs(attempt + 1), 200);
            }
        };

        // Restore textarea heights from saved properties (used on workflow load)
        nodeType.prototype._restoreInputHeights = function () {
            const heights = this.properties?.inputHeights;
            if (!heights || !this.widgets) return;

            for (const widget of this.widgets) {
                if (!widget.name.match(/^Text \d+$/)) continue;
                const h = heights[widget.name];
                if (!h) continue;

                const textarea = findTextarea(widget);
                if (textarea) {
                    textarea.style.setProperty("height", h + "px", "important");
                }
            }
        };

        // Resize node to fit content (only grows, never shrinks)
        nodeType.prototype._resizeNode = function () {
            const minSize = this.computeSize();
            const currentSize = this.size || [0, 0];
            this.setSize([
                Math.max(minSize[0], currentSize[0], 300),
                Math.max(minSize[1], currentSize[1])
            ]);
            this.setDirtyCanvas(true, true);
        };

        // Style the inputs header separator widget
        nodeType.prototype._styleInputsHeader = function () {
            if (!this.widgets) return;

            const headerWidget = this.widgets.find(w => w.name === "_inputs_header");
            if (!headerWidget) return;

            headerWidget.disabled = true;
            headerWidget.computeSize = () => [0, 24];
            // Canvas-only custom draw; hide from Nodes 2.0 Vue renderer
            if (!headerWidget.options) headerWidget.options = {};
            headerWidget.options.hidden = true;
            headerWidget.draw = function (ctx, node, widgetWidth, y, widgetHeight) {
                const lineColor = "#555";
                const textColor = "#888";
                const padding = 15;
                const lineY = y + widgetHeight / 2;

                ctx.save();

                ctx.strokeStyle = lineColor;
                ctx.lineWidth = 1;
                ctx.font = "11px Arial";
                const text = "Inputs";
                const textWidth = ctx.measureText(text).width;
                const textX = (widgetWidth - textWidth) / 2;

                // Left line
                ctx.beginPath();
                ctx.moveTo(padding, lineY);
                ctx.lineTo(textX - 8, lineY);
                ctx.stroke();

                // Right line
                ctx.beginPath();
                ctx.moveTo(textX + textWidth + 8, lineY);
                ctx.lineTo(widgetWidth - padding, lineY);
                ctx.stroke();

                // Text
                ctx.fillStyle = textColor;
                ctx.fillText(text, textX, lineY + 4);
                ctx.restore();
            };
        };

        return nodeType;
    },
});
