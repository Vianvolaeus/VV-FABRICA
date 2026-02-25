import bpy
from bpy.types import Panel
from ... import ui_conventions as ui


# ¦ ¦ ¦ PANELS
class VV_FABRICA_PT_materials(Panel):
    bl_idname = "VV_FABRICA_PT_materials"
    bl_label = "Materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VV-FABRICA"

    def draw_header(self, context):
        self.layout.label(icon='MATERIAL')

    def draw(self, context):
        layout = self.layout
        has_mesh = any(obj.type == 'MESH' for obj in context.selected_objects)

        group_box = ui.section_box(layout)

        actions_box = group_box.box()
        actions_box.enabled = has_mesh
        actions_box.operator("vv_fabrica.materials_remove_unused", icon='TRASH')
        actions_box.operator("vv_fabrica.materials_reload_textures", icon='FILE_REFRESH')

        if not has_mesh:
            alert_box = ui.section_box(group_box, alert=True)
            alert_box.label(text="No mesh objects selected", icon='ERROR')
        else:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                data_box = group_box.box()
                data_box.label(text=f"{len(obj.material_slots)} material slot(s) on active", icon='MATERIAL')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_PT_materials,
]
