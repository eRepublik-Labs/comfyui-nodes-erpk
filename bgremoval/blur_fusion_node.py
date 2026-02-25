# ABOUTME: ComfyUI V3 node for foreground edge refinement using blur-based color estimation.
# ABOUTME: Reduces color bleeding from background at semi-transparent edges.

from typing import Tuple

from comfy_api.latest import IO


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (0, 0, 0)
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


class BlurFusionForegroundEstimation(IO.ComfyNode):
    """
    Refine foreground edges using blur-based color estimation.

    Uses fast-foreground-estimation method to produce cleaner foregrounds
    by estimating true foreground colors at semi-transparent edges.
    Reduces color bleeding from background.

    Reference: https://github.com/Photoroom/fast-foreground-estimation
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BlurFusionForegroundEstimation",
            display_name="Foreground Refinement (BlurFusion)",
            category="ERPK/Background Removal",
            description="Refine foreground edges using blur-based color estimation. Reduces color bleeding.",
            inputs=[
                IO.Image.Input("image"),
                IO.Mask.Input("mask"),
                IO.Int.Input("blur_radius", default=90, min=1, max=255, step=1, optional=True,
                             tooltip="Primary blur radius for foreground estimation."),
                IO.Int.Input("blur_radius_secondary", default=6, min=1, max=255, step=1, optional=True,
                             tooltip="Secondary blur radius for edge refinement."),
                IO.Boolean.Input("fill_background", default=False, optional=True,
                                 tooltip="Fill background with solid color instead of transparent."),
                IO.String.Input("background_color", default="#000000", optional=True,
                                tooltip="Hex color for background fill (e.g., #00FF00 for green)."),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.Mask.Output("mask"),
            ],
        )

    @classmethod
    def execute(
        cls,
        image,
        mask,
        blur_radius=90,
        blur_radius_secondary=6,
        fill_background=False,
        background_color="#000000",
        **kwargs,
    ):
        import numpy as np
        import cv2
        from PIL import Image
        from tqdm import tqdm
        from .utils import tensor_to_pil, pil_rgba_to_tensor, pil_to_tensor

        # Convert inputs
        pil_images = tensor_to_pil(image)

        # Handle mask dimensions
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)

        result_images = []

        for i, pil_img in enumerate(tqdm(pil_images, desc="[BGRemoval] BlurFusion")):
            # Get corresponding mask
            mask_idx = min(i, mask.shape[0] - 1)
            mask_np = (mask[mask_idx].cpu().numpy() * 255).astype(np.uint8)

            # Resize mask if needed
            if mask_np.shape[:2] != (pil_img.height, pil_img.width):
                mask_np = cv2.resize(mask_np, (pil_img.width, pil_img.height), interpolation=cv2.INTER_LINEAR)

            # Convert image to numpy
            img_np = np.array(pil_img).astype(np.float32)

            # Estimate foreground using blur fusion
            foreground = _blur_fusion_foreground(
                img_np, mask_np, blur_radius, blur_radius_secondary
            )

            # Create output
            if fill_background:
                # Parse hex color
                bg_rgb = hex_to_rgb(background_color)
                # Composite onto background
                alpha = mask_np.astype(np.float32) / 255.0
                alpha = alpha[:, :, np.newaxis]
                bg = np.full_like(foreground, bg_rgb, dtype=np.float32)
                result = foreground * alpha + bg * (1 - alpha)
                result_pil = Image.fromarray(result.astype(np.uint8), mode="RGB")
            else:
                # RGBA output
                result_pil = Image.fromarray(foreground.astype(np.uint8), mode="RGB")
                result_pil.putalpha(Image.fromarray(mask_np, mode="L"))

            result_images.append(result_pil)

        # Convert back to tensors
        if fill_background:
            image_tensor = pil_to_tensor(result_images)
        else:
            image_tensor = pil_rgba_to_tensor(result_images)

        # Return original mask
        return IO.NodeOutput(image_tensor, mask)


def _blur_fusion_foreground(image, mask, blur_radius, blur_radius_secondary):
    """
    Estimate foreground using blur fusion method.

    This reduces color bleeding at edges by estimating true foreground colors.
    """
    import numpy as np
    import cv2

    # Ensure odd kernel sizes
    blur_radius = blur_radius if blur_radius % 2 == 1 else blur_radius + 1
    blur_radius_secondary = blur_radius_secondary if blur_radius_secondary % 2 == 1 else blur_radius_secondary + 1

    # Normalize mask to 0-1
    alpha = mask.astype(np.float32) / 255.0
    alpha_3d = alpha[:, :, np.newaxis]

    # Blur the image weighted by alpha
    weighted_img = image * alpha_3d
    blurred_weighted = cv2.GaussianBlur(weighted_img, (blur_radius, blur_radius), 0)
    blurred_alpha = cv2.GaussianBlur(alpha, (blur_radius, blur_radius), 0)

    # Avoid division by zero
    blurred_alpha = np.maximum(blurred_alpha, 1e-6)

    # Estimate foreground
    foreground_estimate = blurred_weighted / blurred_alpha[:, :, np.newaxis]

    # Secondary refinement pass
    refined_weighted = foreground_estimate * alpha_3d
    blurred_refined = cv2.GaussianBlur(refined_weighted, (blur_radius_secondary, blur_radius_secondary), 0)
    blurred_alpha_secondary = cv2.GaussianBlur(alpha, (blur_radius_secondary, blur_radius_secondary), 0)
    blurred_alpha_secondary = np.maximum(blurred_alpha_secondary, 1e-6)

    foreground_refined = blurred_refined / blurred_alpha_secondary[:, :, np.newaxis]

    # Blend based on alpha
    # Use original image where alpha is high, estimated where alpha is low
    blend_factor = alpha_3d ** 2  # Quadratic blend for smoother transition
    result = image * blend_factor + foreground_refined * (1 - blend_factor)

    # Clip to valid range
    result = np.clip(result, 0, 255)

    return result
