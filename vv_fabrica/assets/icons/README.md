# Runtime Icons

This directory stores icon image files used at runtime by VV-FABRICA UI drawing code.

Usage intent:
- Place exported PNG icon files here (or subfolders).
- Load icons using addon-relative paths in preview collections.
- Keep filenames stable once referenced in code.

Recommended export guidelines:
- Transparent PNG
- Square aspect ratio
- Designed for small display sizes (test at 100% and HiDPI UI scale)

Do not place editable source project files here. Use `/assets/source/` for that.
