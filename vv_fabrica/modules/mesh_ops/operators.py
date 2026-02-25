import bpy
from bpy.types import Operator
from bpy.props import BoolProperty


# ¦ ¦ ¦ HELPERS

def _next_visgeo_name(obj):
    """GENERATE THE NEXT UNIQUE VISGEO SHAPE KEY NAME FOR `obj`.

    FIRST CALL PRODUCES "VISGEO SHAPE". SUBSEQUENT CALLS PRODUCE
    "VISGEO SHAPE #001", "VISGEO SHAPE #002", ETC.
    """
    base = "Visgeo Shape"
    if obj.data.shape_keys is None:
        return base

    existing = {kb.name for kb in obj.data.shape_keys.key_blocks}
    if base not in existing:
        return base

    n = 1
    while True:
        candidate = f"{base} #{n:03d}"
        if candidate not in existing:
            return candidate
        n += 1


def add_visgeo_shape_key(obj):
    """CAPTURE EVALUATED GEOMETRY AS A NEW SHAPE KEY ON `obj`.

    RETURNS THE NAME OF THE CREATED SHAPE KEY.
    RAISES `ValueError` IF THE EVALUATED MESH HAS A DIFFERENT VERTEX COUNT
    (TOPOLOGY-CHANGING MODIFIERS LIKE SUBDIVISION SURFACE, REMESH, BOOLEAN).
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = obj.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)

    base_vert_count = len(obj.data.vertices)
    eval_vert_count = len(mesh_from_eval.vertices)

    if base_vert_count != eval_vert_count:
        bpy.data.meshes.remove(mesh_from_eval)
        raise ValueError(
            f"Modifier stack changes vertex count "
            f"(base: {base_vert_count}, evaluated: {eval_vert_count}). "
            f"Shape keys require matching topology. "
            f"Disable topology-changing modifiers "
            f"(Subdivision Surface, Remesh, Boolean, etc.) first."
        )

    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis")

    key_name = _next_visgeo_name(obj)
    shape_key = obj.shape_key_add(name=key_name, from_mix=True)
    shape_key.slider_min = 0
    shape_key.slider_max = 1

    for i, vert in enumerate(mesh_from_eval.vertices):
        shape_key.data[i].co = vert.co

    bpy.data.meshes.remove(mesh_from_eval)
    return shape_key.name


# ¦ ¦ ¦ OPERATORS: SHAPE KEYS

class VVFabrica_OT_mesh_ops_vis_geo_shape_key(Operator):
    bl_idname = "vv_fabrica.mesh_ops_vis_geo_shape_key"
    bl_label = "Visgeo Shape"
    bl_description = (
        "Captures the visual (evaluated) geometry as a Shape Key. "
        "Requires that modifiers do not change vertex count."
    )
    bl_icon = "SHAPEKEY_DATA"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        if not context.active_object:
            self.report({"ERROR"}, "[VV-FABRICA] No active object selected")
            return {"CANCELLED"}
        if context.active_object.type != 'MESH':
            self.report({"ERROR"}, "[VV-FABRICA] Active object must be a mesh")
            return {"CANCELLED"}

        try:
            key_name = add_visgeo_shape_key(context.active_object)
        except ValueError as e:
            self.report({"ERROR"}, f"[VV-FABRICA] {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"[VV-FABRICA] Visgeo shape key '{key_name}' created")
        return {"FINISHED"}


# ¦ ¦ ¦ OPERATORS: MODIFIERS

class VVFabrica_OT_mesh_ops_toggle_modifiers(Operator):
    bl_idname = "vv_fabrica.mesh_ops_toggle_modifiers"
    bl_label = "Toggle Modifiers Visibility"
    bl_description = (
        "Toggles Viewport and Render visibility for all modifiers "
        "on the currently selected objects."
    )
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    on_off: BoolProperty(default=True)

    def execute(self, context):
        if not context.selected_objects:
            self.report({"WARNING"}, "[VV-FABRICA] No objects selected")
            return {"CANCELLED"}

        for obj in context.selected_objects:
            for modifier in obj.modifiers:
                modifier.show_viewport = self.on_off
                modifier.show_render = self.on_off

        state = "on" if self.on_off else "off"
        self.report({"INFO"}, f"[VV-FABRICA] Modifiers toggled {state} on {len(context.selected_objects)} object(s)")
        self.on_off = not self.on_off
        return {"FINISHED"}


# ¦ ¦ ¦ REGISTRATION

classes = [
    VVFabrica_OT_mesh_ops_vis_geo_shape_key,
    VVFabrica_OT_mesh_ops_toggle_modifiers,
]
