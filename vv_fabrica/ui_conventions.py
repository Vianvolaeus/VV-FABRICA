"""SHARED UI CONVENTIONS HELPERS FOR VV-FABRICA PANELS.

KEEP THIS MODULE INTENTIONALLY SMALL: HELPER FUNCTIONS SHOULD REMOVE
REPETITION WITHOUT HIDING BLENDER UI LAYOUT BEHAVIOR.
"""


def section_box(layout, title=None, icon='NONE', alert=False):
    """CREATE A BOXED CONTAINER WITH OPTIONAL HEADING AND ALERT STYLING."""
    box = layout.box()
    box.alert = alert
    if title:
        if icon and icon != 'NONE':
            box.label(text=title, icon=icon)
        else:
            box.label(text=title)
    return box


def draw_primary_operator(layout, operator_idname, text=None, icon='NONE', enabled=True, scale_y=1.3):
    """DRAW A SLIGHTLY-EMPHASIZED OPERATOR ROW FOR PRIMARY ACTIONS."""
    row = layout.row()
    row.enabled = enabled
    row.scale_y = scale_y
    if text is None:
        row.operator(operator_idname, icon=icon)
    else:
        row.operator(operator_idname, text=text, icon=icon)
    return row
