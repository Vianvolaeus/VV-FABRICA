import bpy


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_general(bpy.types.Menu):
    bl_label = "General"
    bl_idname = "VV_FABRICA_MT_general"

    def draw(self, context):
        layout = self.layout
        layout.operator("vv_fabrica.general_rename_data_blocks", icon='SORTALPHA')
        layout.operator("vv_fabrica.general_vp_wireframe", icon='SHADING_WIRE')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_MT_general,
]
