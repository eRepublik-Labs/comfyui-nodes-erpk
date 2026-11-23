<!-- ABOUTME: Help documentation for the BytePlus API Client ComfyUI node. -->
<!-- ABOUTME: Optional config node that hands a BytePlus ModelArk API key to the BytePlus nodes. -->

# BytePlus API Client

Provides a BytePlus ModelArk API key to the Seedance and Seedream nodes. The node is optional: with nothing connected, each BytePlus node resolves the key itself.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| api_key | String | (empty) | ModelArk API key from the ap-southeast-1 (Johor) console (optional). A key typed here is visible to every user of this ComfyUI: it is saved in the workflow, the queue history and image metadata. |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | BYTEPLUS_API_CLIENT | Connect to the `client` input of any BytePlus node. A preview node shows the key as `ApiKey(set)`. |

## Notes

- Key priority is ComfyUI Settings (Settings > ERPK > API Keys > BytePlus ModelArk API Key), then this widget, then `byteplus/config.ini`. Environment variables are not read.
- When you set the Settings key, the frontend greys out this node's `api_key` widget.
- Keys and model activation are per region. These nodes call `ap-southeast-1`; a key from another region fails with an authentication error.
- Activate each model on the ModelArk Model activation page first; an inactive model returns `ModelNotOpen`.
