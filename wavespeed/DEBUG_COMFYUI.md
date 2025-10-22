# WaveSpeed ComfyUI Node Debugging Guide

## Problem Solved
The WaveSpeed custom nodes were not appearing in ComfyUI due to a missing torch import fallback in the `wavespeed_api/utils.py` file.

## The Issue
The `wavespeed_api/utils.py` file was importing `torch` at the module level without any error handling. When ComfyUI tried to import the wavespeed module, if torch wasn't available in the Python path at that exact moment, the entire module would fail to load silently.

## The Fix Applied
Modified `wavespeed_api/utils.py` to:
1. Wrap the torch import in a try/except block
2. Use lazy loading for torch (import it when actually needed)
3. Add proper type hints that don't depend on torch being available

## How to Verify the Fix is Working

### 1. Check Module Import
Run this in your ComfyUI environment:
```python
import wavespeed
print(f"Nodes loaded: {len(wavespeed.NODE_CLASS_MAPPINGS)}")
print("Available nodes:", list(wavespeed.NODE_CLASS_MAPPINGS.keys()))
```

Expected output: 11 nodes should be loaded.

### 2. In ComfyUI Interface
1. Restart ComfyUI completely
2. Right-click in the workflow area
3. Look for "WaveSpeedAI" category in the "Add Node" menu
4. You should see these nodes:
   - WaveSpeed Client
   - WaveSpeed Preview Video
   - WaveSpeed Save Audio
   - WaveSpeed Upload Image
   - WaveSpeed Bytedance Seedream V4
   - WaveSpeed Bytedance Seedream V4 Edit
   - WaveSpeed Bytedance Seedream V4 Sequential
   - WaveSpeed Bytedance Seedream V4 Edit Sequential
   - WaveSpeed Qwen Image Text-to-Image
   - WaveSpeed Qwen Image Edit
   - WaveSpeed Qwen Image Edit Plus

### 3. Check ComfyUI Logs
Look for these messages in the ComfyUI console:
```
[WaveSpeed] Loaded 11 nodes:
  - WaveSpeed Custom Client
  - WaveSpeed Custom Preview Video
  ... (and so on)
```

## Troubleshooting Steps

If the nodes still don't appear:

### 1. Check Installation Location
Ensure the wavespeed folder is directly inside ComfyUI's `custom_nodes` directory:
```
ComfyUI/
  custom_nodes/
    wavespeed/          ← This folder
      __init__.py
      nodes.py
      ...
```

### 2. Check Python Dependencies
Install required dependencies:
```bash
cd ComfyUI/custom_nodes/erpk/wavespeed
pip install -r requirements.txt
```

### 3. Check for Import Errors
In ComfyUI's directory, run:
```python
python -c "import sys; sys.path.insert(0, 'custom_nodes'); from erpk import wavespeed; print('Success!')"
```

### 4. Enable Verbose Logging
Start ComfyUI with verbose logging to see any error messages:
```bash
python main.py --verbose
```

### 5. Check File Permissions
Ensure all files are readable:
```bash
ls -la ComfyUI/custom_nodes/erpk/wavespeed/
```

## Common Issues and Solutions

### Issue: "No module named 'torch'"
**Solution**: This is now handled by the lazy loading fix. The warning message is normal and doesn't prevent the nodes from loading.

### Issue: "No module named 'pydantic'"
**Solution**: Install the requirements:
```bash
pip install pydantic requests numpy pillow
```

### Issue: Nodes load but don't work
**Solution**: Ensure you have:
1. A valid WaveSpeed API key
2. Created the API client node first in your workflow
3. Connected the client output to other WaveSpeed nodes

### Issue: Import errors for relative imports
**Solution**: This has been fixed. The module now uses proper relative imports that work when loaded as a package by ComfyUI.

## Testing Without ComfyUI

To test if the module structure is correct without running ComfyUI:

```python
#!/usr/bin/env python3
import sys
import os

# Add parent directory to simulate ComfyUI's import
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(parent_dir))

# Try to import as ComfyUI would
import wavespeed

# Check what was loaded
print(f"Loaded {len(wavespeed.NODE_CLASS_MAPPINGS)} nodes")
for name in wavespeed.NODE_CLASS_MAPPINGS:
    print(f"  - {name}")
```

## Node Registry Names

The nodes are registered with these internal names (used in workflow JSON):
- `WaveSpeed Custom Client`
- `WaveSpeed Custom Preview Video`
- `WaveSpeed Custom Save Audio`
- `WaveSpeed Custom Upload Image`
- `WaveSpeed Custom SeedreamV4`
- `WaveSpeed Custom SeedreamV4Edit`
- `WaveSpeed Custom SeedreamV4Sequential`
- `WaveSpeed Custom SeedreamV4EditSequential`
- `WaveSpeed Custom QwenImageT2I`
- `WaveSpeed Custom QwenImageEdit`
- `WaveSpeed Custom QwenImageEditPlus`

## Summary

The main fix was adding proper error handling for the torch import in `wavespeed_api/utils.py`. The module now:
1. Loads successfully even if torch isn't immediately available
2. Imports torch lazily when actually needed
3. Provides clear warning messages for debugging
4. Maintains full compatibility with ComfyUI's node system