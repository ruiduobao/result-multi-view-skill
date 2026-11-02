"""
tile_extractor.py
Windowed raster and thumbnail extraction engine for result-multi-view-skill.
Adheres strictly to AGENTS.md rule 4 (windowed read only, peak RAM < 10-15 GB)
and rule 10 / dataviz rules (standard land cover palette, no sensitive terms).
"""

import os
import io
import base64
from typing import Optional, Tuple, Dict, Any
import numpy as np
from PIL import Image

# Land-cover Palette according to AGENTS.md and dataviz standard
# 0=NoData, 1=种植园 (PF), 2=自然林 (NF), 3=非林 (OT)
LC_PALETTE = {
    "colors_hex": {
        "nodata": "#f4f3ef",
        "PF": "#1f77b4",  # 种植园: 蓝
        "NF": "#2ca02c",  # 自然林: 绿
        "OT": "#b0b0b0"   # 非林: 灰
    },
    "rgb_array": np.array([
        [244, 243, 239],  # 0: nodata
        [31, 119, 180],   # 1: 种植园 PF (蓝)
        [44, 160, 44],    # 2: 自然林 NF (绿)
        [176, 176, 176],  # 3: 非林 OT (灰)
    ], dtype=np.uint8)
}


class WindowedTileExtractor:
    """Extracts memory-safe windowed thumbnails and cross-hair zooms from GeoTIFF rasters."""

    def __init__(self, rgb_array: Optional[np.ndarray] = None):
        self.rgb_array = rgb_array if rgb_array is not None else LC_PALETTE["rgb_array"]

    def extract_zoom_b64(
        self,
        raster_path: str,
        band: int = 1,
        col_mid: int = 300,
        row_mid: int = 300,
        half_size: int = 300,
        draw_crosshair: bool = True,
        crosshair_rgb: Tuple[int, int, int] = (235, 104, 52)
    ) -> str:
        """
        Extracts a (2*half_size, 2*half_size) window around (col_mid, row_mid)
        without reading the full raster into memory. Returns base64 PNG data URI.
        """
        try:
            import rasterio
            from rasterio.windows import Window

            if not os.path.exists(raster_path):
                return self._generate_fallback_patch(half_size * 2, f"File not found:\n{os.path.basename(raster_path)}")

            with rasterio.open(raster_path) as src:
                # Clamp window within raster bounds
                c_start = max(0, col_mid - half_size)
                r_start = max(0, row_mid - half_size)
                w = min(2 * half_size, src.width - c_start)
                h = min(2 * half_size, src.height - r_start)

                if w <= 0 or h <= 0:
                    return self._generate_fallback_patch(half_size * 2, "Window out of bounds")

                win = Window(c_start, r_start, w, h)
                arr = src.read(band, window=win)

            # Map class indices 0..3 to RGB
            clipped = np.clip(arr, 0, len(self.rgb_array) - 1)
            rgb = self.rgb_array[clipped].copy()

            # Optional crosshair
            if draw_crosshair and w > 20 and h > 20:
                mid_x = min(half_size, w - 1)
                mid_y = min(half_size, h - 1)
                for i in range(0, w, 8):
                    rgb[max(0, mid_y - 1) : min(h, mid_y + 1), i : min(i + 4, w)] = crosshair_rgb
                for i in range(0, h, 8):
                    rgb[i : min(i + 4, h), max(0, mid_x - 1) : min(w, mid_x + 1)] = crosshair_rgb

            img = Image.fromarray(rgb)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64_str = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64_str}"

        except Exception as e:
            return self._generate_fallback_patch(half_size * 2, f"Extraction error: {str(e)[:40]}")

    def extract_overview_b64(
        self,
        raster_path: str,
        band: int = 1,
        target_size: Tuple[int, int] = (300, 300)
    ) -> str:
        """
        Reads a decimated overview of a GeoTIFF using out_shape to avoid memory spike.
        """
        try:
            import rasterio
            from rasterio.enums import Resampling

            if not os.path.exists(raster_path):
                return self._generate_fallback_patch(target_size[0], "Raster missing")

            with rasterio.open(raster_path) as src:
                arr = src.read(
                    band,
                    out_shape=(target_size[1], target_size[0]),
                    resampling=Resampling.nearest
                )

            clipped = np.clip(arr, 0, len(self.rgb_array) - 1)
            rgb = self.rgb_array[clipped].copy()
            img = Image.fromarray(rgb)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64_str = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64_str}"
        except Exception as e:
            return self._generate_fallback_patch(target_size[0], f"Overview err: {str(e)[:40]}")

    @staticmethod
    def file_to_b64(image_path: str) -> str:
        """Reads a local PNG/JPG file and returns a base64 data URI."""
        if not os.path.exists(image_path):
            return ""
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/png" if ext == ".png" else ("image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png")
        with open(image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64_data}"

    def _generate_fallback_patch(self, size: int, label: str) -> str:
        """Creates an informative placeholder PNG when raster is missing or errored."""
        img = Image.new("RGB", (size, size), color=(26, 38, 64))
        # Draw some subtle grid lines
        arr = np.array(img)
        arr[::20, :, :] = [35, 49, 79]
        arr[:, ::20, :] = [35, 49, 79]
        img = Image.fromarray(arr)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64_str}"
