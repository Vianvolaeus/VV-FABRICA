"""MATERIALS MODULE — TEXTURE RELOAD, UNUSED MATERIAL CLEANUP."""

MODULE_INFO = {
    "id": "materials",
    "name": "Materials",
    "description": "Texture reload, unused material cleanup",
    "default_enabled": True,
    "icon": "MATERIAL",
}


def get_classes():
    from . import operators, panels, menus
    return operators.classes + panels.classes + menus.classes


def get_scene_properties():
    return {}


def get_menu_class():
    from . import menus
    return menus.VV_FABRICA_MT_materials
