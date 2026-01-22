// ABOUTME: JavaScript extension for dynamic text input widgets in the ERPK_ConcatenateStrings node.
// ABOUTME: Provides add/remove buttons, multiline text areas, and label fields with proper serialization.

import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

const NODE_ID = "ERPK_ConcatenateStrings";

app.registerExtension({
    name: "erpk.utils.concat_strings",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== NODE_ID) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = async function () {
            const result = onNodeCreated?.apply(this, arguments);

            // Initialize state from properties or defaults
            this.entries = this.properties?.entries || [{ label: "", text: "" }, { label: "", text: "" }];
            this.delimiterValue = this.properties?.delimiter || "\\n";
            this.includeNames = this.properties?.includeNames || false;
            this.labelOnSameLine = this.properties?.labelOnSameLine !== false; // default true

            // Store in properties for serialization
            this.properties = this.properties || {};
            this.properties.entries = this.entries;
            this.properties.delimiter = this.delimiterValue;
            this.properties.includeNames = this.includeNames;
            this.properties.labelOnSameLine = this.labelOnSameLine;

            this._rebuildWidgets();
            return result;
        };

        // Handle deserialization when loading a workflow
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);

            if (info.properties) {
                this.entries = info.properties.entries || [{ label: "", text: "" }, { label: "", text: "" }];
                this.delimiterValue = info.properties.delimiter || "\\n";
                this.includeNames = info.properties.includeNames || false;
                this.labelOnSameLine = info.properties.labelOnSameLine !== false;

                // Update properties
                this.properties.entries = this.entries;
                this.properties.delimiter = this.delimiterValue;
                this.properties.includeNames = this.includeNames;
                this.properties.labelOnSameLine = this.labelOnSameLine;

                this._rebuildWidgets();
            }

            return result;
        };

        // Serialize widget values for execution
        const onSerialize = nodeType.prototype.onSerialize;
        nodeType.prototype.onSerialize = function (o) {
            const result = onSerialize?.apply(this, arguments);

            // Ensure properties are up to date
            o.properties = o.properties || {};
            o.properties.entries = this.entries;
            o.properties.delimiter = this.delimiterValue;
            o.properties.includeNames = this.includeNames;
            o.properties.labelOnSameLine = this.labelOnSameLine;

            return result;
        };

        // Provide hidden input values to Python
        const getExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (canvas, options) {
            const result = getExtraMenuOptions?.apply(this, arguments);
            return result;
        };

        // Override serialize to pass data to Python execution
        const origGetInnerNodes = nodeType.prototype.getInnerNodes;
        nodeType.prototype.serialize = function () {
            // Update hidden widget values before serialization
            this._updateHiddenWidgets();
            return LGraphNode.prototype.serialize.call(this);
        };

        // Rebuild all widgets from current state
        nodeType.prototype._rebuildWidgets = function () {
            // Remove all existing widgets
            if (this.widgets) {
                for (let i = this.widgets.length - 1; i >= 0; i--) {
                    this.widgets[i].onRemove?.();
                }
                this.widgets.length = 0;
            }

            // Hidden widget for entries (JSON serialized) - this gets passed to Python
            const entriesWidget = this.addWidget(
                "text",
                "entries",
                JSON.stringify(this.entries),
                (v) => {
                    try {
                        this.entries = JSON.parse(v);
                        this.properties.entries = this.entries;
                    } catch (e) {}
                },
                { serialize: true, hidden: true }
            );
            entriesWidget.computeSize = () => [0, -4]; // Hide the widget visually

            // Hidden widget for delimiter
            const delimWidget = this.addWidget(
                "text",
                "delimiter",
                this.delimiterValue,
                (v) => {
                    this.delimiterValue = v;
                    this.properties.delimiter = v;
                },
                { serialize: true, hidden: true }
            );
            delimWidget.computeSize = () => [0, -4];

            // Hidden widget for includeNames
            const includeWidget = this.addWidget(
                "toggle",
                "includeNames",
                this.includeNames,
                (v) => {
                    this.includeNames = v;
                    this.properties.includeNames = v;
                },
                { serialize: true, hidden: true }
            );
            includeWidget.computeSize = () => [0, -4];

            // Hidden widget for labelOnSameLine
            const sameLineWidget = this.addWidget(
                "toggle",
                "labelOnSameLine",
                this.labelOnSameLine,
                (v) => {
                    this.labelOnSameLine = v;
                    this.properties.labelOnSameLine = v;
                },
                { serialize: true, hidden: true }
            );
            sameLineWidget.computeSize = () => [0, -4];

            // Visible: Include names toggle
            this.addWidget(
                "toggle",
                "Include Labels in Output",
                this.includeNames,
                (v) => {
                    this.includeNames = v;
                    this.properties.includeNames = v;
                    this._updateHiddenWidgets();
                },
                { serialize: false }
            );

            // Visible: Label on same line toggle
            this.addWidget(
                "toggle",
                "Label on Same Line",
                this.labelOnSameLine,
                (v) => {
                    this.labelOnSameLine = v;
                    this.properties.labelOnSameLine = v;
                    this._updateHiddenWidgets();
                },
                { serialize: false }
            );

            // Visible: Delimiter input
            this.addWidget(
                "text",
                "Delimiter",
                this.delimiterValue,
                (v) => {
                    this.delimiterValue = v;
                    this.properties.delimiter = v;
                    this._updateHiddenWidgets();
                },
                { serialize: false }
            );

            // Separator
            const sep = this.addWidget("button", "───── Inputs ─────", null, () => {}, { serialize: false });
            sep.disabled = true;

            // Add each entry (label + text pair)
            for (let i = 0; i < this.entries.length; i++) {
                this._addEntryWidgets(i);
            }

            // Spacer before add button
            const addSpacer = this.addWidget("text", " ", "", null, { serialize: false });
            addSpacer.disabled = true;
            addSpacer.computeSize = () => [0, 10];

            // Add "+" button at the bottom
            this.addWidget(
                "button",
                "+ Add Input",
                null,
                () => {
                    this._addEntry();
                },
                { serialize: false }
            );

            // Resize node to fit widgets
            const sz = this.computeSize();
            this.setSize([Math.max(sz[0], 300), sz[1]]);
            this.setDirtyCanvas(true, true);
        };

        // Update hidden widgets with current state
        nodeType.prototype._updateHiddenWidgets = function () {
            if (!this.widgets) return;

            for (const w of this.widgets) {
                if (w.name === "entries") {
                    w.value = JSON.stringify(this.entries);
                } else if (w.name === "delimiter") {
                    w.value = this.delimiterValue;
                } else if (w.name === "includeNames" && w.options?.hidden) {
                    w.value = this.includeNames;
                } else if (w.name === "labelOnSameLine" && w.options?.hidden) {
                    w.value = this.labelOnSameLine;
                }
            }
        };

        // Add widgets for a single entry
        nodeType.prototype._addEntryWidgets = function (index) {
            const entry = this.entries[index];
            const self = this;

            // Label input (single line)
            this.addWidget(
                "text",
                `Label ${index + 1}`,
                entry.label,
                (v) => {
                    self.entries[index].label = v;
                    self.properties.entries = self.entries;
                    self._updateHiddenWidgets();
                },
                { serialize: false }
            );

            // Text input (multiline) using ComfyWidgets
            const textWidget = ComfyWidgets["STRING"](
                this,
                `Text ${index + 1}`,
                ["STRING", { multiline: true }],
                app
            ).widget;
            textWidget.value = entry.text;
            textWidget.callback = (v) => {
                self.entries[index].text = v;
                self.properties.entries = self.entries;
                self._updateHiddenWidgets();
            };
            textWidget.options = textWidget.options || {};
            textWidget.options.serialize = false;

            // Remove button (only show if more than one entry)
            if (this.entries.length > 1) {
                this.addWidget(
                    "button",
                    "Remove",
                    null,
                    () => {
                        self._removeEntry(index);
                    },
                    { serialize: false }
                );
            }

            // Spacer between entry groups (except after the last one)
            if (index < this.entries.length - 1) {
                const spacer = this.addWidget("text", " ", "", null, { serialize: false });
                spacer.disabled = true;
                spacer.computeSize = () => [0, 10];
            }
        };

        // Add a new empty entry
        nodeType.prototype._addEntry = function () {
            this.entries.push({ label: "", text: "" });
            this.properties.entries = this.entries;
            this._rebuildWidgets();
        };

        // Remove an entry by index
        nodeType.prototype._removeEntry = function (index) {
            if (this.entries.length > 1) {
                this.entries.splice(index, 1);
                this.properties.entries = this.entries;
                this._rebuildWidgets();
            }
        };

        return nodeType;
    },
});
