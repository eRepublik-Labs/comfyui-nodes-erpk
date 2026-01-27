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
            this.activeInputCount = this.properties?.activeInputCount || INITIAL_INPUTS;
            this.properties = this.properties || {};
            this.properties.activeInputCount = this.activeInputCount;

            // Delay to ensure widgets exist, then set up UI once
            setTimeout(() => {
                this._styleInputsHeader();
                this._updateInputVisibility();
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

            // On load, update visibility and restore size after LiteGraph's async resize
            setTimeout(() => {
                this._updateInputVisibility();
                this._updateControlWidgetVisibility();

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
                    widget.hidden = idx > this.activeInputCount;
                } else if (labelMatch) {
                    const idx = parseInt(labelMatch[1]);
                    widget.hidden = idx > this.activeInputCount;
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

            // Spacer before buttons
            const addSpacer = this.addWidget(
                "text",
                "_spacer_add",
                "",
                () => {},
                { serialize: false }
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

            // Bottom spacer for margin
            const bottomSpacer = this.addWidget(
                "text",
                "_spacer_bottom",
                "",
                () => {},
                { serialize: false }
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
                this._addInputBtn.hidden = this.activeInputCount >= MAX_INPUTS;
            }
            if (this._removeInputBtn) {
                this._removeInputBtn.hidden = this.activeInputCount <= 1;
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
