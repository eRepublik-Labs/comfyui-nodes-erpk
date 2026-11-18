# ABOUTME: Seedream image-generation bodies and per-model gating, against the ModelArk docs.
# ABOUTME: Expected bodies and per-image prices are literals from the API study.

import pytest

from erpk.byteplus.byteplus_api.seedream import ImageOptions, build_image_body, image_cost_usd

V55 = "dola-seedream-5-5-261028"
PRO = "dola-seedream-5-0-pro-260628"
FLASH = "dola-seedream-5-0-flash-260915"
LITE = "seedream-5-0-260128"
V45 = "seedream-4-5-251128"
V40 = "seedream-4-0-250828"
IMG = "data:image/png;base64,AAAA"


def test_text_to_image_on_5_5_with_transparent_png_sends_watermark_false():
    body = build_image_body(V55, " a red kite ", (), ImageOptions(output_format="png", background="transparent"))
    assert body == {
        "model": V55,
        "prompt": "a red kite",
        "size": "2K",
        "response_format": "url",
        "watermark": False,
        "optimize_prompt_options": {"mode": "standard"},
        "output_format": "png",
        "background": "transparent",
    }


def test_sequential_edit_on_4_0_with_custom_size_and_fast_mode():
    options = ImageOptions(size="custom", width=1920, height=1080, sequential="auto", max_images=4,
                           optimize_prompt_mode="fast", response_format="b64_json", watermark=True)
    body = build_image_body(V40, "four panels", (IMG, IMG), options, endpoint_id="ep-1")
    assert body == {
        "model": "ep-1",
        "prompt": "four panels",
        "size": "1920x1080",
        "response_format": "b64_json",
        "watermark": True,
        "optimize_prompt_options": {"mode": "fast"},
        "image": [IMG, IMG],
        "sequential_image_generation": "auto",
        "sequential_image_generation_options": {"max_images": 4},
    }


def test_layer_decomposition_on_5_5_sends_one_image_and_layer_options():
    options = ImageOptions(size="auto", layer_decomposition=True, layer_max_images=12, text_recognition=True,
                           safety_identifier="user-hash")
    body = build_image_body(V55, "", (IMG,), options)
    assert body == {
        "model": V55,
        "size": "auto",
        "response_format": "url",
        "watermark": False,
        "optimize_prompt_options": {"mode": "standard"},
        "image": IMG,
        "layer_decomposition": True,
        "layer_decomposition_options": {"max_images": 12, "text_recognition": True},
        "safety_identifier": "user-hash",
    }
    pro_body = build_image_body(PRO, "", (IMG,), ImageOptions(layer_decomposition=True))
    assert pro_body["layer_decomposition"] is True and "layer_decomposition_options" not in pro_body


@pytest.mark.parametrize("model, prompt, images, options, message", [
    (V45, "x", (), ImageOptions(size="1K"),
     "seedream-4-5-251128 takes size 2K, 4K or custom, not 1K."),
    (V55, "x", (), ImageOptions(size="custom", width=640, height=640),
     "dola-seedream-5-5-261028 needs 921600-4624220 total pixels, got 640x640 = 409600."),
    (V55, "x", (), ImageOptions(size="custom", width=4096, height=240),
     "dola-seedream-5-5-261028 needs an aspect ratio within 1/16-16, got 4096x240."),
    (FLASH, "x", (), ImageOptions(size="custom", width=240, height=4096),
     "dola-seedream-5-0-flash-260915 needs an aspect ratio within 1/16-16, got 240x4096."),
    (LITE, "x", (), ImageOptions(size="custom", width=8000, height=461),
     "seedream-5-0-260128 needs an aspect ratio within 1/16-16, got 8000x461."),
    (V40, "x", (), ImageOptions(size="custom", width=4000, height=240),
     "seedream-4-0-250828 needs an aspect ratio within 1/16-16, got 4000x240."),
    (V55, "x", ("/tmp/a.png",), ImageOptions(),
     "Reference image '/tmp/a.png' must start with one of https://, http://, data:image/"),
    (PRO, "x", ("data:image/jpeg;base64,AAAA",), ImageOptions(background="transparent", output_format="png"),
     "dola-seedream-5-0-pro-260628 makes a transparent image only from a reference that carries alpha, and an "
     "inline image without a mask is sent as JPEG. Connect a mask to images."),
    (V55, "x", (), ImageOptions(sequential="auto"),
     "dola-seedream-5-5-261028 has no sequential generation; it returns one image per request."),
    (LITE, "x", (IMG,) * 12, ImageOptions(sequential="auto", max_images=4),
     "Reference images plus max_images must be at most 15, got 12 + 4."),
    (V40, "x", (), ImageOptions(output_format="png"),
     "seedream-4-0-250828 outputs jpeg only, not png."),
    (V55, "x", (), ImageOptions(output_format="jpeg", background="transparent"),
     "A transparent background needs png output, not jpeg."),
    (PRO, "x", (), ImageOptions(background="transparent"),
     "dola-seedream-5-0-pro-260628 makes transparent images only from exactly one reference image with alpha."),
    (PRO, "x", (), ImageOptions(background="auto"),
     "dola-seedream-5-0-pro-260628 takes background opaque or transparent, not auto."),
    (LITE, "x", (), ImageOptions(background="opaque"),
     "seedream-5-0-260128 has no background option."),
    (FLASH, "x", (), ImageOptions(optimize_prompt_mode="fast"),
     "dola-seedream-5-0-flash-260915 has no fast prompt optimization; it is on 5.0 pro and 4.0 only."),
    (V55, "x", (IMG,) * 11, ImageOptions(),
     "dola-seedream-5-5-261028 takes at most 10 reference images, got 11."),
    (LITE, "", (IMG,), ImageOptions(layer_decomposition=True),
     "seedream-5-0-260128 has no layer decomposition; use Seedream 5.5, 5.0 pro or 5.0 flash."),
    (V55, "", (IMG, IMG), ImageOptions(layer_decomposition=True),
     "Layer decomposition takes exactly one image, got 2."),
    (V55, "", (IMG,), ImageOptions(layer_decomposition=True, background="opaque"),
     "Layer decomposition does not take a background option."),
    (V55, "", (IMG,), ImageOptions(layer_decomposition=True, size="custom"),
     "Layer decomposition takes a size preset or auto, not a custom size."),
    (PRO, "", (IMG,), ImageOptions(layer_decomposition=True, text_recognition=True),
     "dola-seedream-5-0-pro-260628 has no layer text recognition; it is on Seedream 5.5 only."),
    (V55, "x", (), ImageOptions(size="auto"),
     "Size auto is for layer decomposition only."),
    (V55, "", (), ImageOptions(), "Image generation needs a prompt."),
])
def test_combinations_the_model_rejects_raise_before_any_call(model, prompt, images, options, message):
    with pytest.raises(ValueError) as excinfo:
        build_image_body(model, prompt, images, options)
    assert str(excinfo.value) == message


def test_transparent_output_on_5_0_flash_from_one_png_reference_with_alpha():
    body = build_image_body(FLASH, "cut out the cup", (IMG,), ImageOptions(background="transparent",
                                                                            output_format="png"))
    assert body["background"] == "transparent" and body["image"] == [IMG]


def test_cost_uses_the_pixel_tier_and_input_image_price():
    # 5.5: $0.020 up to 2,601,123.84 px, $0.035 above; $0.008 per input image.
    assert image_cost_usd(V55, [(2048, 2048)], input_images=0) == pytest.approx(0.035)
    assert image_cost_usd(V55, [(1024, 1024), (1600, 1600)], input_images=2) == pytest.approx(0.056)
    # 5.0 pro: first input free then $0.003; layers $0.0225 / $0.045.
    assert image_cost_usd(PRO, [(2048, 2048)], input_images=3) == pytest.approx(0.096)
    assert image_cost_usd(PRO, [(1024, 1024)] * 2, input_images=1, layers=True) == pytest.approx(0.045)
    assert image_cost_usd(V45, [(2048, 2048)] * 3, input_images=5) == pytest.approx(0.12)
