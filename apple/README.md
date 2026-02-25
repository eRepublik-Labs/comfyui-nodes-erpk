# ABOUTME: Documentation for Apple ML models integration.
# ABOUTME: Covers SHARP for single-image 3D Gaussian view synthesis.

# Apple ML Models - ComfyUI Custom Nodes

**Version:** 2026.2.15 (CalVer)
**Category:** ERPK/Apple/SHARP
**Namespace:** ERPK Organization Custom Nodes

Part of the [ERPK Custom Nodes Collection](../README.md) for ComfyUI.

---

## Overview

Integration of Apple's open-source machine learning models for ComfyUI.

## SHARP - Single-Image View Synthesis

SHARP converts a single photograph into a 3D Gaussian splat representation that can be rendered from novel viewpoints. The model runs in under one second on GPU.

**Paper:** [SHARP: Sharpening Latents for Real Pseudo-3D Gaussian Representations](https://machinelearning.apple.com/research/sharp)
**Code:** [github.com/apple/ml-sharp](https://github.com/apple/ml-sharp)

### Nodes

| Node | Description | Requirements |
|------|-------------|--------------|
| **SHARP Predict (Image to 3D Gaussian)** | Convert image to 3D Gaussian splat (.ply) | GPU recommended |
| **SHARP Render Views** | Render novel views from .ply | CUDA required |
| **SHARP Render Video** | Render orbit video from .ply | CUDA required |

### SHARP Predict

Converts a single image into a 3D Gaussian splat representation.

**Inputs:**
- `image` - Input image (any resolution)
- `focal_length_px` - Focal length in pixels (0 = auto-estimate from width)
- `output_dir` - Output directory (empty = ComfyUI output folder)
- `filename_prefix` - Prefix for .ply filename
- `device` - Device for inference (auto/cuda/mps/cpu)

**Outputs:**
- `ply_path` - Path to saved .ply file
- `gaussians` - Gaussian data (for chaining to render nodes)

### SHARP Render Views

Renders multiple novel views from a 3D Gaussian splat.

**Inputs:**
- `ply_path` - Path to .ply file from SHARP Predict
- `num_views` - Number of views to render (1-64)
- `resolution` - Output image resolution (256-2048)
- `max_disparity` - Maximum camera disparity for view synthesis (0.01-0.5)

**Outputs:**
- `images` - Batch of rendered images

### SHARP Render Video

Renders an orbit video from a 3D Gaussian splat.

**Inputs:**
- `ply_path` - Path to .ply file
- `num_frames` - Number of frames (10-300)
- `resolution` - Video resolution (256-2048)
- `fps` - Frames per second (15-60)
- `max_disparity` - Camera orbit radius / disparity
- `output_dir` - Output directory
- `filename_prefix` - Prefix for video filename

**Outputs:**
- `video_path` - Path to saved .mp4 file
- `frames` - All rendered frames as IMAGE batch (for preview)

## Installation

### Prerequisites

SHARP requires the `sharp` package from Apple:

```bash
pip install git+https://github.com/apple/ml-sharp.git
```

### Dependencies

The SHARP package will install its dependencies automatically:
- torch, torchvision, timm
- gsplat (for Gaussian splatting)
- plyfile (for .ply I/O)
- imageio[ffmpeg] (for video encoding)

### Hardware Requirements

| Operation | CPU | MPS (Apple Silicon) | CUDA |
|-----------|-----|---------------------|------|
| Predict (image to .ply) | Slow | Fast | Fast |
| Render Views | N/A | N/A | Required |
| Render Video | N/A | N/A | Required |

**Note:** Rendering requires CUDA due to the gsplat library dependency.

### CUDA Toolkit Requirement

The render nodes use gsplat which performs JIT (Just-In-Time) compilation of CUDA kernels. This requires the **CUDA Toolkit** (specifically `nvcc` compiler) to be installed on your system.

**Check if CUDA Toolkit is installed:**
```bash
nvcc --version
```

**Install CUDA Toolkit (Debian/Ubuntu):**
```bash
# Add NVIDIA repository (example for Debian 13)
wget https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install cuda-toolkit-12-8
```

**Configure environment (add to ~/.bashrc or ~/.zshrc):**
```bash
export PATH=/usr/local/cuda-12.8/bin:$PATH
export CUDA_HOME=/usr/local/cuda-12.8
export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH
```

**For systemd services**, add these to the service file's `[Service]` section:
```ini
Environment="PATH=/usr/local/cuda-12.8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="CUDA_HOME=/usr/local/cuda-12.8"
Environment="LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64"
```

## Usage

### Basic Workflow

1. Add **SHARP Predict** node
2. Connect an image input
3. Get .ply file output
4. (Optional) Connect to **SHARP Render Views** or **SHARP Render Video**

### Example: Image to Novel Views

```
[Load Image] -> [SHARP Predict] -> [SHARP Render Views] -> [Preview Image]
```

### Example: Image to Video

```
[Load Image] -> [SHARP Predict] -> [SHARP Render Video] -> [Video output]
```

## Model Information

- **Model size:** ~500MB (downloads automatically on first use)
- **Internal resolution:** 1536x1536
- **Output:** 3D Gaussian splat in .ply format
- **License:** Apple Sample Code License

## Troubleshooting

### "SHARP is not installed"

Install the SHARP package:
```bash
pip install git+https://github.com/apple/ml-sharp.git
```

### "Rendering requires CUDA"

The render nodes use gsplat which only supports CUDA. For non-CUDA systems:
- Use only SHARP Predict to generate .ply files
- Render the .ply files on a CUDA-capable machine or viewer

### "gsplat: No CUDA toolkit found. gsplat will be disabled"

gsplat requires the CUDA Toolkit for JIT compilation. See [CUDA Toolkit Requirement](#cuda-toolkit-requirement) above.

**Common symptoms:**
- PyTorch CUDA works (`torch.cuda.is_available()` returns True)
- But gsplat fails with "No CUDA toolkit found"

This happens because PyTorch ships pre-compiled CUDA binaries, but gsplat needs `nvcc` to compile kernels at runtime.

### "viewmats must be a CUDA tensor"

This error occurs when camera tensors are on CPU instead of GPU. The SHARP library's internal camera computations can sometimes return CPU tensors. This is handled automatically in version 2026.1.3+.

### Model download fails

The model downloads from Apple's CDN. If it fails:
1. Check your internet connection
2. Try downloading manually and place in torch hub cache

### Psychedelic / wrong colors in rendered output

If colors look extremely saturated or wrong, ensure you're using version 2026.1.6+ which properly converts spherical harmonics coefficients to RGB values.

## License

- SHARP model and code: Apple Sample Code License
- This integration: MIT License
