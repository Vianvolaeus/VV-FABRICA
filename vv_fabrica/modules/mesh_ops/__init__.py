"""MESH OPERATORS MODULE — VISUAL GEOMETRY TO SHAPE, MODIFIER TOGGLES."""

MODULE_INFO = {
    "id": "mesh_ops",
    "name": "Mesh Operators",
    "description": "Visual geometry to shape, modifier toggles",
    "default_enabled": True,
    "icon": "MESH_DATA",
}


def get_classes():
    from . import operators, panels, menus
    return operators.classes + panels.classes + menus.classes


def get_scene_properties():
    return {}


def get_menu_class():
    from . import menus
    return menus.VV_FABRICA_MT_mesh_ops
