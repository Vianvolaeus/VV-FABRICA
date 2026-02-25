import bpy


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_materials(bpy.types.Menu):
    bl_label = "Materials"
    bl_idname = "VV_FABRICA_MT_materials"

    def draw(self, context):
        layout = self.layout
        layout.operator("vv_fabrica.materials_remove_unused", icon='TRASH')
        layout.operator("vv_fabrica.materials_reload_textures", icon='FILE_REFRESH')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_MT_materials,
]
