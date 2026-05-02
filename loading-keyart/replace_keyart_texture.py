from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image


WORK_ROOT = Path(r"D:\SCUM_LoadingKeyArt_Replace")
SOURCE_IMAGE = Path(r"C:\Users\aleks\Downloads\523097c9-ff12-4783-a1bf-55ada0518492.png")
EXTRACT_ROOT = WORK_ROOT / "extract"
STAGE_ROOT = WORK_ROOT / "stage"
BACKUP_ROOT = WORK_ROOT / "backup_original_assets"
OUTPUT_ROOT = WORK_ROOT / "dist"

TEXTURE_NAME = "SCUM_TheLongHaul_KeyArt"
UASSET_SOURCE = EXTRACT_ROOT / f"{TEXTURE_NAME}.uasset"
UEXP_SOURCE = EXTRACT_ROOT / f"{TEXTURE_NAME}.uexp"
UASSET_STAGE = STAGE_ROOT / f"{TEXTURE_NAME}.uasset"
UEXP_STAGE = STAGE_ROOT / f"{TEXTURE_NAME}.uexp"
PREVIEW_IMAGE = WORK_ROOT / f"{TEXTURE_NAME}_new_3840x2160_preview.png"
SUMMARY_JSON = WORK_ROOT / "replace_keyart_summary.json"

WIDTH = 3840
HEIGHT = 2160
BYTES_PER_PIXEL = 4
PIXEL_OFFSET = 0xF0
PIXEL_SIZE = WIDTH * HEIGHT * BYTES_PER_PIXEL
UEXP_EXPECTED_SIZE = PIXEL_OFFSET + PIXEL_SIZE + 32


def sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")


def center_crop_to_aspect(image: Image.Image, target_aspect: float) -> Image.Image:
    width, height = image.size
    source_aspect = width / height
    if abs(source_aspect - target_aspect) < 0.0001:
        return image

    if source_aspect < target_aspect:
        crop_height = round(width / target_aspect)
        top = (height - crop_height) // 2
        box = (0, top, width, top + crop_height)
    else:
        crop_width = round(height * target_aspect)
        left = (width - crop_width) // 2
        box = (left, 0, left + crop_width, height)
    return image.crop(box)


def build_bgra_pixels(source_image: Path) -> tuple[bytes, dict[str, object]]:
    with Image.open(source_image) as image:
        original_size = image.size
        image = image.convert("RGBA")
        cropped = center_crop_to_aspect(image, WIDTH / HEIGHT)
        cropped_size = cropped.size
        resized = cropped.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

        # SCUM's current asset is PF_B8G8R8A8. Keep alpha opaque to match loading art behavior.
        opaque = Image.new("RGBA", resized.size, (0, 0, 0, 255))
        opaque.alpha_composite(resized)
        opaque.save(PREVIEW_IMAGE)
        raw_bgra = opaque.tobytes("raw", "BGRA")

    if len(raw_bgra) != PIXEL_SIZE:
        raise RuntimeError(f"Unexpected BGRA byte count: {len(raw_bgra)} != {PIXEL_SIZE}")

    return raw_bgra, {
        "source_image": str(source_image),
        "source_size": list(original_size),
        "crop_size": list(cropped_size),
        "output_size": [WIDTH, HEIGHT],
        "preview_image": str(PREVIEW_IMAGE),
        "pixel_format": "PF_B8G8R8A8",
        "pixel_offset": PIXEL_OFFSET,
        "pixel_size": PIXEL_SIZE,
    }


def main() -> None:
    for path in (SOURCE_IMAGE, UASSET_SOURCE, UEXP_SOURCE):
        require_file(path)

    if UEXP_SOURCE.stat().st_size != UEXP_EXPECTED_SIZE:
        raise RuntimeError(
            f"Unexpected .uexp size: {UEXP_SOURCE.stat().st_size} != {UEXP_EXPECTED_SIZE}. "
            "Do not patch blindly because the texture serialization changed."
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    STAGE_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    backup_uasset = BACKUP_ROOT / f"{TEXTURE_NAME}.before_{timestamp}.uasset"
    backup_uexp = BACKUP_ROOT / f"{TEXTURE_NAME}.before_{timestamp}.uexp"
    shutil.copy2(UASSET_SOURCE, backup_uasset)
    shutil.copy2(UEXP_SOURCE, backup_uexp)

    raw_bgra, image_info = build_bgra_pixels(SOURCE_IMAGE)

    original_uexp = UEXP_SOURCE.read_bytes()
    header = original_uexp[:PIXEL_OFFSET]
    trailer = original_uexp[PIXEL_OFFSET + PIXEL_SIZE :]
    if len(trailer) != 32:
        raise RuntimeError(f"Unexpected trailer size: {len(trailer)} != 32")

    patched_uexp = header + raw_bgra + trailer
    if len(patched_uexp) != len(original_uexp):
        raise RuntimeError("Patched .uexp size changed; refusing to write invalid texture asset.")

    shutil.copy2(UASSET_SOURCE, UASSET_STAGE)
    UEXP_STAGE.write_bytes(patched_uexp)

    summary = {
        "task": "Replace SCUM loading key art texture pixels while preserving Unreal asset structure.",
        "texture_name": TEXTURE_NAME,
        "uasset_source": str(UASSET_SOURCE),
        "uexp_source": str(UEXP_SOURCE),
        "uasset_stage": str(UASSET_STAGE),
        "uexp_stage": str(UEXP_STAGE),
        "backup_uasset": str(backup_uasset),
        "backup_uexp": str(backup_uexp),
        "source_uexp_sha1": sha1(UEXP_SOURCE),
        "patched_uexp_sha1": sha1(UEXP_STAGE),
        "uasset_sha1": sha1(UASSET_STAGE),
        "image": image_info,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
