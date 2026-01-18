#!/usr/bin/env python3
"""Create a rocket icon for MyLauncher."""

import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Installing Pillow...")
    subprocess.run(["pip", "install", "Pillow"], check=True)
    from PIL import Image, ImageDraw


def create_rocket_icon(size: int = 1024) -> Image.Image:
    """Create a simple rocket icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle - gradient blue
    margin = int(size * 0.05)
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(41, 98, 255, 255),  # Vibrant blue
    )

    # Rocket body (white/light gray)
    center_x = size // 2
    rocket_width = int(size * 0.25)
    rocket_height = int(size * 0.5)
    rocket_top = int(size * 0.18)

    # Rocket nose cone (triangle)
    nose_height = int(size * 0.15)
    draw.polygon([
        (center_x, rocket_top),
        (center_x - rocket_width // 2, rocket_top + nose_height),
        (center_x + rocket_width // 2, rocket_top + nose_height),
    ], fill=(255, 255, 255, 255))

    # Rocket body (rectangle with rounded feel)
    body_top = rocket_top + nose_height - 5
    body_bottom = rocket_top + rocket_height
    draw.rectangle([
        center_x - rocket_width // 2,
        body_top,
        center_x + rocket_width // 2,
        body_bottom,
    ], fill=(255, 255, 255, 255))

    # Window (porthole) - dark circle
    window_y = body_top + int(rocket_height * 0.25)
    window_r = int(size * 0.06)
    draw.ellipse([
        center_x - window_r,
        window_y - window_r,
        center_x + window_r,
        window_y + window_r,
    ], fill=(41, 98, 255, 255))

    # Fins (left and right triangles)
    fin_width = int(size * 0.12)
    fin_height = int(size * 0.18)
    fin_top = body_bottom - fin_height

    # Left fin
    draw.polygon([
        (center_x - rocket_width // 2, fin_top),
        (center_x - rocket_width // 2 - fin_width, body_bottom),
        (center_x - rocket_width // 2, body_bottom),
    ], fill=(255, 100, 100, 255))  # Red accent

    # Right fin
    draw.polygon([
        (center_x + rocket_width // 2, fin_top),
        (center_x + rocket_width // 2 + fin_width, body_bottom),
        (center_x + rocket_width // 2, body_bottom),
    ], fill=(255, 100, 100, 255))  # Red accent

    # Flame (orange/yellow gradient effect)
    flame_top = body_bottom - 5
    flame_height = int(size * 0.22)
    flame_width = int(size * 0.15)

    # Outer flame (orange)
    draw.polygon([
        (center_x - flame_width, flame_top),
        (center_x, flame_top + flame_height),
        (center_x + flame_width, flame_top),
    ], fill=(255, 150, 50, 255))

    # Inner flame (yellow)
    inner_width = int(flame_width * 0.6)
    inner_height = int(flame_height * 0.7)
    draw.polygon([
        (center_x - inner_width, flame_top),
        (center_x, flame_top + inner_height),
        (center_x + inner_width, flame_top),
    ], fill=(255, 220, 100, 255))

    return img


def create_iconset(output_dir: Path):
    """Create all required icon sizes for macOS."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Required sizes for macOS iconset
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    # Create base high-res icon
    base_icon = create_rocket_icon(1024)

    for size in sizes:
        # Standard resolution
        icon = base_icon.resize((size, size), Image.Resampling.LANCZOS)
        icon.save(output_dir / f"icon_{size}x{size}.png")

        # Retina (@2x) for sizes up to 512
        if size <= 512:
            icon_2x = base_icon.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            icon_2x.save(output_dir / f"icon_{size}x{size}@2x.png")

    print(f"Created iconset in {output_dir}")


def create_icns(iconset_dir: Path, output_path: Path):
    """Convert iconset to .icns using macOS iconutil."""
    # Rename to .iconset format required by iconutil
    iconset_path = iconset_dir.parent / "MyLauncher.iconset"
    if iconset_path.exists():
        import shutil
        shutil.rmtree(iconset_path)

    iconset_dir.rename(iconset_path)

    # Use iconutil to create .icns
    subprocess.run([
        "iconutil", "-c", "icns", str(iconset_path), "-o", str(output_path)
    ], check=True)

    print(f"Created {output_path}")


if __name__ == "__main__":
    resources_dir = Path(__file__).parent.parent / "resources"
    iconset_dir = resources_dir / "iconset"

    create_iconset(iconset_dir)
    create_icns(iconset_dir, resources_dir / "MyLauncher.icns")

    # Also save a PNG for other uses
    icon = create_rocket_icon(512)
    icon.save(resources_dir / "icon.png")
    print(f"Created {resources_dir / 'icon.png'}")
