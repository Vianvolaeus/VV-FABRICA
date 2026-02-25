import bpy
from bpy.types import Panel
from ... import ui_conventions as ui


# ¦ ¦ ¦ PANELS
class VV_FABRICA_PT_general(Panel):
    bl_idname = "VV_FABRICA_PT_general"
    bl_label = "General"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VV-FABRICA"

    def draw_header(self, context):
        self.layout.label(icon='TOOL_SETTINGS')

    def draw(self, context):
        layout = self.layout
        selected = context.selected_objects

        group_box = ui.section_box(layout)

        actions_box = group_box.box()
        actions_box.operator("vv_fabrica.general_rename_data_blocks", icon='SORTALPHA')
        actions_box.operator("vv_fabrica.general_vp_wireframe", icon='SHADING_WIRE')

        if selected:
            data_box = group_box.box()
            data_box.label(text=f"{len(selected)} object(s) selected", icon='OBJECT_DATA')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_PT_general,
]
