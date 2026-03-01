<!-- ABOUTME: Help documentation for the Concatenate Strings (ERPK) ComfyUI node. -->
<!-- ABOUTME: Joins multiple text inputs with configurable delimiters and optional labels. -->

# Concatenate Strings (ERPK)

Concatenates up to 10 text inputs into a single output string. Supports configurable delimiters, escape sequences, and optional labels for each input.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| Delimiter | String | \n | Separator between texts (optional). Use \\n for newlines, \\t for tabs |
| Include Labels | Boolean | False | Prefix each text with its label (optional) |
| Label on Same Line | Boolean | True | Place label on same line as text, or on a separate line (optional) |
| Label 1–10 | String | (empty) | Label for each text input (optional). Only used when Include Labels is enabled |
| Text 1–10 | String | (empty) | Text inputs to concatenate (optional). Connect STRING outputs from other nodes |

## Output

| Output | Type | Description |
|--------|------|-------------|
| STRING | String | Concatenated result |

## Notes

- Empty text inputs are skipped — only non-empty values are joined
- Connect STRING outputs from other nodes to the Text inputs for dynamic concatenation
- When labels are enabled with "Label on Same Line", output looks like: `Label: text`
- When labels are on separate lines: label appears above its text
