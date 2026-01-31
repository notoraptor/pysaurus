"""
Entry point for PySide6 interface.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from pysaurus.core.informer import Information
from pysaurus.interface.pyside6.main_window import MainWindow

logger = logging.getLogger(__name__)

# Minimum font size in points for comfortable reading on high-res screens
MIN_FONT_SIZE_PT = 11

# Additional scale factor per unit of devicePixelRatio above 1.0
# e.g., at ratio 1.75, extra scale = 0.75 * 0.15 = 0.1125 (11% extra)
DPR_SCALE_FACTOR = 0.20


def _calculate_font_scale(app: QApplication) -> float:
    """
    Calculate font scale factor based on screen properties.

    On high DPI screens (like 4K), even with OS scaling, fonts may appear
    too small due to the high pixel density. This function calculates
    a scale factor considering:
    - Device pixel ratio (OS scaling factor)
    - Minimum comfortable font size
    - Physical screen properties

    Returns a scale factor >= 1.0
    """
    screen = app.primaryScreen()
    if not screen:
        return 1.0

    # Get screen properties
    device_pixel_ratio = screen.devicePixelRatio()
    physical_dpi_x = screen.physicalDotsPerInchX()
    physical_dpi_y = screen.physicalDotsPerInchY()
    physical_dpi = (physical_dpi_x + physical_dpi_y) / 2

    # Get default font size
    default_font = app.font()
    font_size_pt = default_font.pointSize()
    if font_size_pt <= 0:
        font_size_pt = 9  # Windows default

    # Calculate scale to reach minimum font size
    min_size_scale = MIN_FONT_SIZE_PT / font_size_pt if font_size_pt > 0 else 1.0

    # Add extra scaling for high devicePixelRatio
    # When DPR > 1, the OS is scaling but fonts may still feel small on large screens
    dpr_extra = (
        (device_pixel_ratio - 1.0) * DPR_SCALE_FACTOR
        if device_pixel_ratio > 1.0
        else 0.0
    )

    # Combine scales
    final_scale = max(min_size_scale, 1.0) + dpr_extra

    # Clamp to reasonable range
    final_scale = max(1.0, min(final_scale, 2.5))

    logger.debug(
        f"Screen: DPR={device_pixel_ratio:.2f}, Physical DPI={physical_dpi:.1f}, "
        f"Font={font_size_pt}pt, Min={MIN_FONT_SIZE_PT}pt, "
        f"DPR extra={dpr_extra:.2f}, Final scale={final_scale:.2f}"
    )

    return final_scale


def _setup_scaled_font(app: QApplication) -> None:
    """Set up application font with DPI-based scaling."""
    scale = _calculate_font_scale(app)

    if scale > 1.0:
        font = app.font()
        current_size = font.pointSize()
        if current_size <= 0:
            current_size = 10  # Default fallback

        new_size = int(current_size * scale)
        font.setPointSize(new_size)
        app.setFont(font)

        logger.info(
            f"Font scaled from {current_size}pt to {new_size}pt (scale: {scale:.2f})"
        )


def _run():
    """Run the Qt application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Pysaurus")
    app.setOrganizationName("Pysaurus")

    # Apply DPI-based font scaling for high resolution screens
    _setup_scaled_font(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def main():
    """Launch the PySide6 interface with Information context."""
    with Information():
        _run()


if __name__ == "__main__":
    main()
