// ABOUTME: JavaScript extension for the ERPK_ConcatenateStrings node.
// ABOUTME: Provides add/remove buttons for input slots while maintaining connectability.

import { app } from "../../../scripts/app.js";

const NODE_ID = "ERPK_ConcatenateStrings";
const MAX_INPUTS = 10;
const INITIAL_INPUTS = 2;

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
            // If properties.activeInputCount exists, we're loading from a saved workflow
            const isLoading = this.properties?.activeInputCount !== undefined;
            this.activeInputCount = this.properties?.activeInputCount || INITIAL_INPUTS;
            this.properties = this.properties || {};
            this.properties.activeInputCount = this.activeInputCount;

            // Delay to ensure widgets exist
            setTimeout(() => {
                this._setupUI(isLoading);
            }, 50);

            return result;
        };

        // Restore state when loading workflow
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);

            if (info.properties?.activeInputCount) {
                this.activeInputCount = info.properties.activeInputCount;
            }

            setTimeout(() => {
                this._setupUI(true);  // true = loading, don't override saved size
            }, 100);

            return result;
        };

        // Setup the UI with proper visibility and buttons
        nodeType.prototype._setupUI = function (isLoading = false) {
            this._removeControlWidgets();
            this._styleInputsHeader();
            this._updateInputVisibility();
            this._addControlWidgets();
            // NOTE: Do NOT reorder widgets - ComfyUI serializes by index, not by name
            // Reordering breaks save/load. Control widgets appear at end but data is safe.
            if (!isLoading) {
                this._resizeNode();
            }
        };

        // Remove all control widgets (buttons and spacers)
        nodeType.prototype._removeControlWidgets = function () {
            if (!this.widgets) return;
            this.widgets = this.widgets.filter(w => {
                if (w.name === "\u2795 Add Input") return false;
                if (w.name === "\u2796 Remove Last Input") return false;
                if (w.name.startsWith("_spacer_")) return false;
                return true;
            });
        };

        // Update visibility of text/label widgets and inputs
        nodeType.prototype._updateInputVisibility = function () {
            if (!this.widgets) return;

            for (const widget of this.widgets) {
                const textMatch = widget.name.match(/^Text (\d+)$/);
                const labelMatch = widget.name.match(/^Label (\d+)$/);

                if (textMatch) {
                    const idx = parseInt(textMatch[1]);
                    widget.hidden = idx > this.activeInputCount;
                } else if (labelMatch) {
                    const idx = parseInt(labelMatch[1]);
                    widget.hidden = idx > this.activeInputCount;
                }
            }

            // Hide/show input slots (connection points) based on active count
            // Use hidden flag instead of filtering to preserve state across serialize/deserialize
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

        // Add control widgets (buttons and spacers)
        nodeType.prototype._addControlWidgets = function () {
            if (!this.widgets) return;
            const self = this;

            // Spacer before buttons
            const addSpacer = this.addWidget(
                "text",
                "_spacer_add",
                "",
                null,
                { serialize: false }
            );
            addSpacer.disabled = true;
            addSpacer.computeSize = () => [0, 10];
            addSpacer._isAddSpacer = true;
            addSpacer.draw = () => {};

            // Add "Add Input" button if not at max
            if (this.activeInputCount < MAX_INPUTS) {
                this.addWidget(
                    "button",
                    "\u2795 Add Input",
                    null,
                    () => {
                        self._addInput();
                    },
                    { serialize: false }
                );
            }

            // Add "Remove Last Input" button if more than 1 input
            if (this.activeInputCount > 1) {
                this.addWidget(
                    "button",
                    "\u2796 Remove Last Input",
                    null,
                    () => {
                        self._removeLastInput();
                    },
                    { serialize: false }
                );
            }

            // Bottom spacer for margin
            const bottomSpacer = this.addWidget(
                "text",
                "_spacer_bottom",
                "",
                null,
                { serialize: false }
            );
            bottomSpacer.disabled = true;
            bottomSpacer.computeSize = () => [0, 8];
            bottomSpacer._isBottomSpacer = true;
            bottomSpacer.draw = () => {};
        };

        // Add a new input slot
        nodeType.prototype._addInput = function () {
            if (this.activeInputCount < MAX_INPUTS) {
                this.activeInputCount++;
                this.properties.activeInputCount = this.activeInputCount;

                // Clear the newly revealed input's values to ensure it starts fresh
                const textWidget = this.widgets?.find(w => w.name === `Text ${this.activeInputCount}`);
                const labelWidget = this.widgets?.find(w => w.name === `Label ${this.activeInputCount}`);
                if (textWidget) textWidget.value = "";
                if (labelWidget) labelWidget.value = "";

                this._setupUI();
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
            this._setupUI();
        };

        // Resize node to fit content (only grows, never shrinks user's manual resize)
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
            headerWidget.draw = function (ctx, node, widgetWidth, y, widgetHeight) {
                const lineColor = "#555";
                const textColor = "#888";
                const padding = 15;
                const lineY = y + widgetHeight / 2;

                ctx.save();

                // Draw left line
                ctx.strokeStyle = lineColor;
                ctx.lineWidth = 1;
                ctx.font = "11px Arial";
                const text = "Inputs";
                const textWidth = ctx.measureText(text).width;
                const textX = (widgetWidth - textWidth) / 2;

                ctx.beginPath();
                ctx.moveTo(padding, lineY);
                ctx.lineTo(textX - 8, lineY);
                ctx.stroke();

                // Draw right line
                ctx.beginPath();
                ctx.moveTo(textX + textWidth + 8, lineY);
                ctx.lineTo(widgetWidth - padding, lineY);
                ctx.stroke();

                // Draw text
                ctx.fillStyle = textColor;
                ctx.fillText(text, textX, lineY + 4);
                ctx.restore();
            };
        };

        return nodeType;
    },
});
