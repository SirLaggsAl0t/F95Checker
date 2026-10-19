"""Copy brand icons from resources/ into the client, resized for the web."""

import pathlib
import sys

from PIL import Image

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / "web" / "client" / "public"
BRAND = OUT / "brand"


def main():
    BRAND.mkdir(parents=True, exist_ok=True)
    icon = Image.open(REPO / "resources" / "icons" / "icon.png").convert("RGBA")

    for size in (32, 180, 192, 512):
        name = "apple-touch-icon.png" if size == 180 else f"icon-{size}.png"
        icon.resize((size, size), Image.LANCZOS).save(BRAND / name)

    (BRAND / "logo.png").write_bytes((REPO / "resources" / "icons" / "logo.png").read_bytes())
    icon.resize((64, 64), Image.LANCZOS).save(
        OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
    )

    # Same MDI version as the database glyphs; TabIcon renders the raw char with it.
    fonts = OUT / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    source = next((REPO / "resources" / "fonts").glob("materialdesignicons-webfont.*.ttf"))
    (fonts / "materialdesignicons-webfont.ttf").write_bytes(source.read_bytes())
    print(f"Wrote {BRAND}, {OUT / 'favicon.ico'} and {fonts}")


if __name__ == "__main__":
    sys.exit(main())
