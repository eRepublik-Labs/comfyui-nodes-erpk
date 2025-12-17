# ABOUTME: Documentation for background removal nodes package.
# ABOUTME: Covers all three backends: rembg, InSPyReNet, and BiRefNet.

# Background Removal - ComfyUI Custom Nodes

**Version:** 2025.12.18 (CalVer)
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

**Models:**
| Model | Description |
|-------|-------------|
| `u2net` | General purpose (default) |
| `u2netp` | Lightweight, faster |
| `u2net_human_seg` | Human segmentation |
| `u2net_cloth_seg` | Clothing parsing |
| `silueta` | Compact u2net (43MB) |
| `isnet-general-use` | General purpose ISNet |
| `isnet-anime` | Anime characters |
| `sam` | Segment Anything Model |
| `birefnet-general` | BiRefNet general |
| `birefnet-general-lite` | BiRefNet lightweight |
| `birefnet-portrait` | BiRefNet portraits |
| `birefnet-dis` | BiRefNet DIS |
| `birefnet-hrsod` | BiRefNet high-res |
| `birefnet-cod` | BiRefNet camouflaged |
| `birefnet-massive` | BiRefNet largest |

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

Each backend has its own dependencies. Install only what you need:

**rembg (ONNX):**
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

- **rembg**: Use `onnxruntime-gpu` instead of `onnxruntime` for CUDA support
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
