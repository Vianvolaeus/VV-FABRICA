import bpy


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_rigging(bpy.types.Menu):
    bl_label = "Rigging"
    bl_idname = "VV_FABRICA_MT_rigging"

    def draw(self, context):
        layout = self.layout
        layout.operator("vv_fabrica.rigging_merge_to_active_bone", icon='BONE_DATA')
        layout.operator("vv_fabrica.rigging_smooth_rig_xfer", icon='MOD_VERTEX_WEIGHT')
        layout.operator("vv_fabrica.rigging_button_attach", icon='PINNED')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_MT_rigging,
]
