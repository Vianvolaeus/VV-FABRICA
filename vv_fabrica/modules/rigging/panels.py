import bpy
from bpy.types import Panel
from ... import ui_conventions as ui


# ¦ ¦ ¦ PANELS
class VV_FABRICA_PT_rigging(Panel):
    bl_idname = "VV_FABRICA_PT_rigging"
    bl_label = "Rigging"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VV-FABRICA"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'EDIT_ARMATURE', 'POSE', 'EDIT_MESH'}

    def draw_header(self, context):
        self.layout.label(icon='BONE_DATA')

    def draw(self, context):
        layout = self.layout

        group_box = ui.section_box(layout)

        actions_box = group_box.box()
        actions_box.operator("vv_fabrica.rigging_merge_to_active_bone", icon='BONE_DATA')
        actions_box.operator("vv_fabrica.rigging_button_attach", icon='PINNED')

        weight_section = ui.section_box(group_box, title="Weight Transfer", icon='MOD_VERTEX_WEIGHT')

        prop_box = weight_section.box()
        prop_box.use_property_split = True
        prop_box.prop(context.scene, "vv_fabrica_source_object", icon='OBJECT_DATA')

        ui.draw_primary_operator(
            weight_section,
            "vv_fabrica.rigging_smooth_rig_xfer",
            icon='MOD_VERTEX_WEIGHT'
        )


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_PT_rigging,
]
