import bpy
from bpy.types import Panel
from ... import ui_conventions as ui


# ¦ ¦ ¦ PANELS
class VV_FABRICA_PT_mesh_ops(Panel):
    bl_idname = "VV_FABRICA_PT_mesh_ops"
    bl_label = "Mesh Operators"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VV-FABRICA"

    def draw_header(self, context):
        self.layout.label(icon='MESH_DATA')

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        is_mesh = obj is not None and obj.type == 'MESH'
        has_selection = len(context.selected_objects) > 0

        group_box = ui.section_box(layout)

        actions_box = group_box.box()
        row = actions_box.row()
        row.enabled = is_mesh
        row.operator("vv_fabrica.mesh_ops_vis_geo_shape_key", icon='SHAPEKEY_DATA')

        row = actions_box.row()
        row.enabled = has_selection
        row.operator("vv_fabrica.mesh_ops_toggle_modifiers", icon='HIDE_OFF')

        if obj and obj.type == 'MESH':
            mod_count = len(obj.modifiers)
            data_box = group_box.box()
            data_box.label(text=f"Active: {obj.name} ({mod_count} modifier(s))", icon='OBJECT_DATA')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_PT_mesh_ops,
]
