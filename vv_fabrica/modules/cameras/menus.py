import bpy


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_cameras(bpy.types.Menu):
    bl_label = "Cameras"
    bl_idname = "VV_FABRICA_MT_cameras"

    def draw(self, context):
        layout = self.layout
        layout.operator("vv_fabrica.cameras_add_viewport_camera", icon='CAMERA_DATA')
        layout.operator("vv_fabrica.cameras_switch_previous", text="Previous Camera", icon='TRIA_LEFT')
        layout.operator("vv_fabrica.cameras_switch_next", text="Next Camera >", icon='NONE')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_MT_cameras,
]
