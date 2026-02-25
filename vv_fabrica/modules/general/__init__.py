"""GENERAL MODULE — OBJECT RENAME, VIEWPORT WIREFRAME TOGGLE."""

MODULE_INFO = {
    "id": "general",
    "name": "General",
    "description": "Object rename, wireframe toggle",
    "default_enabled": True,
    "icon": "TOOL_SETTINGS",
}


def get_classes():
    from . import operators, panels, menus
    return operators.classes + panels.classes + menus.classes


def get_scene_properties():
    return {}


def get_menu_class():
    from . import menus
    return menus.VV_FABRICA_MT_general
