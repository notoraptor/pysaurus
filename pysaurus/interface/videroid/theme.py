"""Shared visual constants for videroid pages and widgets.

Single source of truth for the few background colors reused across pages and
cards, so a tweak lands in one place. They had drifted before being centralized
here: ``BADGE_BG`` was ``(240, 240, 240)`` on the card but ``(230, 230, 230)`` in
the videos page, and ``SELECTED_BG`` existed both as a tuple and as the string
``"#e3f2fd"``.
"""

import videre

# Table header row.
HEADER_BG = videre.parse_color((225, 225, 225))
# Zebra-striped even rows.
EVEN_BG = videre.parse_color((245, 245, 245))
# Selected / expanded item highlight (== "#e3f2fd").
SELECTED_BG = videre.parse_color((227, 242, 253))
# Small inline badges (property / classifier chips).
BADGE_BG = videre.parse_color((240, 240, 240))
# Sidebar filter sections — alternating backgrounds (kyuti color_light/lighter,
# videos_page.py:389-390 = "#f0f0f0"/"#ffffff").
SECTION_BG_A = videre.parse_color((240, 240, 240))
SECTION_BG_B = videre.parse_color((255, 255, 255))
