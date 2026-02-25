"""VRC ANALYSIS MODULE — AVATAR PERFORMANCE ANALYSIS."""

MODULE_INFO = {
    "id": "vrc_analysis",
    "name": "VRC Analysis",
    "description": "Avatar performance analysis",
    "default_enabled": True,
    "icon": "GRAPH",
}

def get_classes():
    from . import operators, panels, menus
    return operators.classes + panels.classes + menus.classes

def get_scene_properties():
    return {}

def get_menu_class():
    from . import menus
    return menus.VV_FABRICA_MT_vrc_analysis
