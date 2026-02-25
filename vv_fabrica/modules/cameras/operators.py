import bpy
from mathutils import Vector
from bpy.types import Operator
from ... import preferences as addon_preferences


# ¦ ¦ ¦ HELPERS

def _next_viewport_camera_index():
    pattern_prefix = "Viewport Camera #"
    max_index = 0

    for obj in bpy.data.objects:
        name = obj.name
        if not name.startswith(pattern_prefix):
            continue
        suffix = name[len(pattern_prefix):]
        if suffix.isdigit():
            max_index = max(max_index, int(suffix))

    candidate = max_index + 1
    while True:
        camera_name = f"Viewport Camera #{candidate:03d}"
        dof_empty_name = f"DoF Empty #{candidate:03d}"
        if camera_name not in bpy.data.objects and dof_empty_name not in bpy.data.objects:
            return candidate
        candidate += 1


def _scene_cameras():
    return [obj for obj in bpy.data.objects if obj.type == 'CAMERA']


def _get_configured_dof_fstop(context):
    prefs = addon_preferences.get_addon_preferences(context)
    configured_fstop = getattr(prefs, "cameras_dof_aperture_fstop", 1.2) if prefs else 1.2
    try:
        configured_fstop = float(configured_fstop)
    except Exception:
        configured_fstop = 1.2
    if configured_fstop <= 0:
        configured_fstop = 1.2
    return configured_fstop


# ¦ ¦ ¦ OPERATORS: VIEWPORT CAMERAS

class VVFabrica_OT_cameras_add_viewport_camera(Operator):
    bl_idname = "vv_fabrica.cameras_add_viewport_camera"
    bl_label = "Add Viewport Camera"
    bl_description = (
        "Add a new camera named 'Viewport Camera', set it as active, "
        "align it to the current viewport view, and set up an Empty "
        "as its Depth of Field object."
    )
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' and context.mode == 'OBJECT'

    def execute(self, context):
        camera_index = _next_viewport_camera_index()
        camera_name = f"Viewport Camera #{camera_index:03d}"
        dof_empty_name = f"DoF Empty #{camera_index:03d}"

        bpy.ops.object.select_all(action='DESELECT')

        for space in context.area.spaces:
            if space.type == 'VIEW_3D':
                space.region_3d.view_perspective = 'PERSP'

        bpy.ops.object.camera_add()
        camera = bpy.context.active_object
        camera.name = camera_name
        camera.data.name = camera_name
        bpy.context.scene.camera = camera
        camera.data.passepartout_alpha = 1
        bpy.ops.view3d.camera_to_view()

        rv3d = context.space_data.region_3d
        is_persp = rv3d.window_matrix[3][3] == 0
        if is_persp:
            camera.data.type = 'PERSP'
            camera.data.dof.use_dof = True
        else:
            camera.data.type = 'ORTHO'
            camera.data.dof.use_dof = False

        if camera.data.type == 'ORTHO':
            camera.data.ortho_scale = context.space_data.region_3d.view_distance

        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = bpy.context.active_object
        empty.name = dof_empty_name
        configured_fstop = _get_configured_dof_fstop(context)
        camera.data.dof.aperture_fstop = configured_fstop
        camera.data.dof.focus_object = empty

        bpy.ops.object.select_all(action='DESELECT')
        empty.select_set(True)
        camera.select_set(True)
        context.view_layer.objects.active = camera
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        ctx = bpy.context
        depsgraph = ctx.evaluated_depsgraph_get()
        origin = camera.location
        direction = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        result, location, normal, index, obj, matrix = ctx.scene.ray_cast(
            depsgraph, origin, direction
        )
        if result:
            empty.location = location
            dof_target_name = obj.name
            print(f"[VV-FABRICA:cameras] DoF target placed on '{dof_target_name}'")
        else:
            dof_target_name = None
            print("[VV-FABRICA:cameras] No raycast hit, DoF empty at camera origin")

        coll_name = "Viewport Camera"
        if coll_name not in bpy.data.collections:
            viewport_camera_collection = bpy.data.collections.new(coll_name)
            bpy.context.scene.collection.children.link(viewport_camera_collection)
        else:
            viewport_camera_collection = bpy.data.collections[coll_name]

        current_collection = camera.users_collection[0]
        current_collection.objects.unlink(camera)
        current_collection.objects.unlink(empty)
        viewport_camera_collection.objects.link(camera)
        viewport_camera_collection.objects.link(empty)

        for area in ctx.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].shading.use_dof = True

        if dof_target_name:
            self.report(
                {"INFO"},
                f"[VV-FABRICA] Camera '{camera.name}' added (f/{configured_fstop:.2f}), DoF target on '{dof_target_name}'",
            )
        else:
            self.report(
                {"WARNING"},
                f"[VV-FABRICA] Camera '{camera.name}' added (f/{configured_fstop:.2f}), DoF empty at world origin (no object in front of camera)",
            )
        return {"FINISHED"}


# ¦ ¦ ¦ OPERATORS: CAMERA NAVIGATION

class VVFabrica_OT_cameras_switch_previous(Operator):
    bl_idname = "vv_fabrica.cameras_switch_previous"
    bl_label = "Previous Camera"
    bl_description = "Switch to the previous camera in the scene."
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return len(_scene_cameras()) > 0

    def execute(self, context):
        cameras = _scene_cameras()
        if not cameras:
            self.report({"WARNING"}, "[VV-FABRICA] No cameras in the scene")
            return {"CANCELLED"}

        current = context.scene.camera
        if current and current in cameras:
            idx = cameras.index(current)
            prev_idx = (idx - 1) % len(cameras)
        else:
            prev_idx = 0

        context.scene.camera = cameras[prev_idx]
        self.report({"INFO"}, f"[VV-FABRICA] Active camera: {cameras[prev_idx].name}")
        return {"FINISHED"}


class VVFabrica_OT_cameras_switch_next(Operator):
    bl_idname = "vv_fabrica.cameras_switch_next"
    bl_label = "Next Camera"
    bl_description = "Switch to the next camera in the scene."
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return len(_scene_cameras()) > 0

    def execute(self, context):
        cameras = _scene_cameras()
        if not cameras:
            self.report({"WARNING"}, "[VV-FABRICA] No cameras in the scene")
            return {"CANCELLED"}

        current = context.scene.camera
        if current and current in cameras:
            idx = cameras.index(current)
            next_idx = (idx + 1) % len(cameras)
        else:
            next_idx = 0

        context.scene.camera = cameras[next_idx]
        self.report({"INFO"}, f"[VV-FABRICA] Active camera: {cameras[next_idx].name}")
        return {"FINISHED"}


# ¦ ¦ ¦ REGISTRATION

classes = [
    VVFabrica_OT_cameras_add_viewport_camera,
    VVFabrica_OT_cameras_switch_previous,
    VVFabrica_OT_cameras_switch_next,
]
