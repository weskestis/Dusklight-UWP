#!/usr/bin/env python3
"""Draw original, geometric package icons; no game artwork is included."""
from pathlib import Path
from PIL import Image, ImageDraw

out = Path(__file__).resolve().parents[1] / "platforms/uwp/Assets"
out.mkdir(parents=True, exist_ok=True)
for name, size in {"StoreLogo": (50, 50), "Square150x150Logo": (150, 150),
                   "Square44x44Logo": (44, 44), "SplashScreen": (620, 300)}.items():
    image = Image.new("RGB", size, (16, 37, 45))
    draw = ImageDraw.Draw(image)
    w, h = size
    radius = min(w, h) * .31
    x, y = w / 2, h / 2
    draw.polygon([(x-radius, y), (x, y-radius), (x, y+radius)], fill=(108, 197, 193))
    draw.polygon([(x+radius, y), (x, y-radius), (x, y+radius)], fill=(233, 205, 138))
    draw.line([(x, y-radius), (x, y+radius)], fill=(16, 37, 45), width=max(1, int(radius*.13)))
    image.save(out / f"{name}.png")
