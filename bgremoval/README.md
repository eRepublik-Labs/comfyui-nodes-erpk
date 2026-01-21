# ABOUTME: Documentation for background removal nodes package.
# ABOUTME: Covers all three backends: rembg, InSPyReNet, and BiRefNet.

# Background Removal - ComfyUI Custom Nodes

**Version:** 2026.1.20 (CalVer)
**Category:** ERPK/Background Removal
**Namespace:** ERPK Organization Custom Nodes

Part of the [ERPK Custom Nodes Collection](../README.md) for ComfyUI.

---

## Overview

Background removal nodes with multiple backend options for different quality/speed/memory tradeoffs. All backends are MIT licensed and safe for commercial use.

## Nodes

| Node | Backend | Runtime | Speed | Quality | Memory |
|------|---------|---------|-------|---------|--------|
| **Remove Background (rembg)** | ONNX | CPU/GPU | Fast | Good | Low-Med |
| **Remove Background (InSPyReNet)** | PyTorch | GPU | Medium | Very Good | Medium |
| **Remove Background (BiRefNet)** | PyTorch/HF | GPU | Slower | Excellent | High |

## Node Details

### Remove Background (rembg)

ONNX-based background removal with 14+ model options. Best for versatility and CPU support.

**Model Selection Guide:**

| Model | Best For | Speed | Quality | Size |
|-------|----------|-------|---------|------|
| `u2net` | General photos, simple backgrounds | Fast | Good | 176MB |
| `u2netp` | Quick processing, resource-limited environments | Fastest | Moderate | 4MB |
| `u2net_human_seg` | People, portraits, full-body shots | Fast | Good | 176MB |
| `u2net_cloth_seg` | Fashion, apparel, clothing isolation | Fast | Good | 176MB |
| `silueta` | General use with storage constraints | Fast | Good | 43MB |
| `isnet-general-use` | Complex backgrounds, multiple objects | Medium | Very Good | 179MB |
| `isnet-anime` | Anime, manga, stylized illustrations | Medium | Excellent | 179MB |
| `sam` | Interactive segmentation with prompts | Slow | Variable | Large |
| `birefnet-general` | High-quality general use, fine details | Slower | Excellent | 973MB |
| `birefnet-general-lite` | Balanced quality/speed tradeoff | Medium | Very Good | ~200MB |
| `birefnet-portrait` | Professional portraits, headshots | Slower | Excellent | 973MB |
| `birefnet-dis` | Precise foreground/background separation | Slower | Excellent | 973MB |
| `birefnet-hrsod` | High-resolution salient objects | Slower | Excellent | 973MB |
| `birefnet-cod` | Camouflaged or hidden objects | Slower | Excellent | 973MB |
| `birefnet-massive` | Maximum quality, diverse subjects | Slowest | Best | ~1GB |

**Model Details:**

#### U2-Net Family
Multi-scale architecture that analyzes images at different zoom levels simultaneously. Works well for single subjects with clear separation from background.

- **u2net**: Default general-purpose model. Good balance of speed and quality for typical photos.
- **u2netp**: Lightweight version (~4MB). Use when speed matters more than edge precision.
- **u2net_human_seg**: Trained specifically on human subjects. Best for portraits and people.
- **u2net_cloth_seg**: Parses clothing into 3 categories (upper body, lower body, full body). Ideal for fashion/e-commerce.
- **silueta**: Same architecture as u2net but compressed to 43MB. Good for deployment with storage limits.

#### ISNet Family
Two-step "intermediate supervision" approach: first suppresses background, then refines edges. Excels with cluttered or noisy backgrounds.

- **isnet-general-use**: Modern general-purpose model. Better edge quality than u2net on complex scenes (IoU 0.82 vs 0.39 on DIS5K dataset).
- **isnet-anime**: High-accuracy segmentation trained on anime/manga. Handles stylized art with clean lines.

#### SAM (Segment Anything)
Meta's versatile segmentation model. Designed for interactive use with prompts/input points. Not recommended for automatic background removal - produces lower accuracy on unprompted tasks.

#### BiRefNet Family
Bilateral Reference Network with bidirectional refinement. Achieves highest accuracy (IoU 0.87, Dice 0.92) by validating fine details against global context. Best for professional results.

- **birefnet-general**: Best overall quality for diverse subjects. Handles fine details like hair, fur, bicycle spokes.
- **birefnet-general-lite**: Lighter backbone (swin_v1_tiny). Good quality/speed tradeoff.
- **birefnet-portrait**: Optimized for human portraits with alpha matting support.
- **birefnet-dis**: Dichotomous Image Segmentation. Precise binary foreground/background masks.
- **birefnet-hrsod**: High-Resolution Salient Object Detection. Best for large images (trained on 2048x2048).
- **birefnet-cod**: Camouflaged Object Detection. Finds objects that blend into backgrounds.
- **birefnet-massive**: Trained on combined datasets. Maximum quality at cost of speed.

**Options:**
- `alpha_matting`: Enable alpha matting refinement
- `alpha_matting_foreground_threshold`: Foreground threshold (0-255)
- `alpha_matting_background_threshold`: Background threshold (0-255)
- `alpha_matting_erode_size`: Erode kernel size

### Remove Background (InSPyReNet)

PyTorch-based via transparent-background package. Good balance of quality and speed.

**Options:**
- `torchscript_jit`: Enable TorchScript JIT for faster inference after first run

### Remove Background (BiRefNet)

HuggingFace transformers-based. Highest quality dichotomous image segmentation.

**Variants:**
| Variant | Description |
|---------|-------------|
| `ZhengPeng7/BiRefNet` | Default model |
| `ZhengPeng7/BiRefNet_HR` | High resolution (2048x2048) |
| `ZhengPeng7/BiRefNet-matting` | Alpha matting |
| `ZhengPeng7/BiRefNet_HR-matting` | HR alpha matting |
| `ZhengPeng7/BiRefNet-COD` | Camouflaged object detection |
| `ZhengPeng7/BiRefNet_512x512` | Fast (lower resolution) |

**Options:**
- `resolution`: Processing resolution (256-2048, HR variant can use 2048)

## Outputs

All nodes output:
- `IMAGE`: RGB image with background removed (composited on black)
- `MASK`: Alpha mask for further compositing

## Installation

### Prerequisites

Background removal nodes are included in the ERPK Custom Nodes package. Install the main package first:

```bash
cd /path/to/ComfyUI/custom_nodes/
git clone https://github.com/eRepublik-Labs/comfyui-nodes-erpk.git erpk
cd erpk
pip install -r requirements.txt
```

### Backend-Specific Dependencies

All background removal dependencies are now included in the main package. If installing via ComfyUI Manager or Registry, dependencies are installed automatically.

For manual installation:

**rembg (ONNX with GPU):**
```bash
pip install "rembg[gpu]>=2.0.50"
```

**rembg (CPU only, for macOS or systems without CUDA):**
```bash
pip install rembg>=2.0.50 onnxruntime>=1.16.0
```

**InSPyReNet (transparent-background):**
```bash
pip install transparent-background>=1.2.0
```

**BiRefNet (HuggingFace):**
```bash
pip install transformers>=4.36.0 torchvision>=0.16.0
```

### GPU Acceleration

- **rembg**: The `[gpu]` extra installs `onnxruntime-gpu` for CUDA acceleration on Windows/Linux. macOS users get CPU-only `onnxruntime` automatically.
- **InSPyReNet**: Automatically uses CUDA if available
- **BiRefNet**: Automatically uses CUDA or MPS (Apple Silicon) if available

## Usage

### Basic Usage

1. Add any background removal node to your workflow
2. Connect an image input
3. Select model/variant (optional)
4. Execute to get image with background removed and mask

### Choosing a Backend

**Use rembg when:**
- You need CPU-only support
- You want the widest model selection
- Memory is limited
- You need alpha matting refinement

**Use InSPyReNet when:**
- You want good quality with moderate speed
- You have GPU available
- You want TorchScript optimization

**Use BiRefNet when:**
- You need the highest quality
- You're working with high-resolution images (use HR variant)
- You need specialized detection (camouflaged objects, matting)

## Troubleshooting

### Nodes Not Appearing

1. Check that dependencies are installed:
```bash
python -c "import rembg; print('rembg OK')"
python -c "from transparent_background import Remover; print('InSPyReNet OK')"
python -c "from transformers import AutoModelForImageSegmentation; print('BiRefNet OK')"
```

2. Check ComfyUI console for import errors

3. Restart ComfyUI after installing dependencies

### Model Download Issues

- **rembg**: Models download automatically on first use to `~/.u2net/`
- **InSPyReNet**: Models download automatically on first use
- **BiRefNet**: Models download from HuggingFace on first use

### Memory Issues

- Use `u2netp` or `silueta` models for lower memory usage
- Use `ZhengPeng7/BiRefNet_512x512` for faster/smaller BiRefNet
- Process images one at a time instead of batches

## License

MIT License - All backends (rembg, transparent-background, BiRefNet) are MIT licensed.

## References

- [rembg](https://github.com/danielgatis/rembg) - ONNX-based background removal
- [transparent-background](https://github.com/plemeri/transparent-background) - InSPyReNet wrapper
- [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) - Bilateral Reference Network
