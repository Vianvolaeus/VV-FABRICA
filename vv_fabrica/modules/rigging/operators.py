import bpy
import bmesh
import math
from bpy.types import Operator
from mathutils import Vector, Matrix


# ¦ ¦ ¦ HELPERS

def normalize_weights(weights):
    total_weight = sum(weights.values())
    if total_weight == 0:
        return weights
    return {key: value / total_weight for key, value in weights.items()}


def merge_vertex_weights_and_remove_bones(context):
    obj = context.active_object
    if obj is None or obj.type != "ARMATURE":
        return {"ERROR"}, "[VV-FABRICA] Active object must be an armature"

    if context.mode != "POSE":
        return {"ERROR"}, "[VV-FABRICA] Must be in Pose mode to perform this operation"

    active_bone = context.active_pose_bone
    if active_bone is None:
        return {"ERROR"}, "[VV-FABRICA] No active bone selected"

    selected_bones = context.selected_pose_bones.copy()
    selected_bones.remove(active_bone)

    bpy.ops.object.mode_set(mode='OBJECT')

    mesh_objects = [ob for ob in context.scene.objects if ob.type == 'MESH' and ob.find_armature() == obj]

    if not mesh_objects:
        return {"ERROR"}, "[VV-FABRICA] No mesh objects found with the active armature as their modifier"

    for mesh_obj in mesh_objects:
        if active_bone.name not in mesh_obj.vertex_groups:
            mesh_obj.vertex_groups.new(name=active_bone.name)

        active_group = mesh_obj.vertex_groups[active_bone.name]

        vertex_weights = {}
        for bone in selected_bones:
            if bone.name in mesh_obj.vertex_groups:
                source_group = mesh_obj.vertex_groups[bone.name]
                for vertex in mesh_obj.data.vertices:
                    for group in vertex.groups:
                        if group.group == source_group.index:
                            if vertex.index not in vertex_weights:
                                vertex_weights[vertex.index] = {bone.name: group.weight}
                            else:
                                vertex_weights[vertex.index][bone.name] = max(group.weight, vertex_weights[vertex.index].get(bone.name, 0))

        for vertex_index, weights in vertex_weights.items():
            normalized_weights = normalize_weights(weights)
            total_weight = sum(normalized_weights.values())
            if total_weight > 0:
                active_group.add([vertex_index], total_weight, 'ADD')

        bpy.ops.object.mode_set(mode='EDIT')
        for bone in selected_bones:
            edit_bone = obj.data.edit_bones.get(bone.name)
            if edit_bone is not None:
                obj.data.edit_bones.remove(edit_bone)
            if bone.name in mesh_obj.vertex_groups:
                source_group = mesh_obj.vertex_groups[bone.name]
                mesh_obj.vertex_groups.remove(source_group)

    bpy.ops.object.mode_set(mode='POSE')

    for mesh_obj in mesh_objects:
        mesh_obj.data.update()

    return {"FINISHED"}, ""


# ¦ ¦ ¦ OPERATORS: BONE MERGE

class VVFabrica_OT_rigging_merge_to_active_bone(Operator):
    bl_idname = "vv_fabrica.rigging_merge_to_active_bone"
    bl_label = "Merge Bones to Active"
    bl_description = "Merge selected bones' vertex weights to the active bone and remove them"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        result, message = merge_vertex_weights_and_remove_bones(context)
        if result == "ERROR":
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, "[VV-FABRICA] Bones merged to active bone successfully")
        return {"FINISHED"}


# ¦ ¦ ¦ OPERATORS: WEIGHT TRANSFER

class VVFabrica_OT_rigging_smooth_rig_xfer(Operator):
    bl_idname = "vv_fabrica.rigging_smooth_rig_xfer"
    bl_label = "Smooth Rig Transfer"
    bl_description = "Transfer vertex weights from active object to selected objects with smoothing"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "vv_fabrica_source_object")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        source_object = context.scene.vv_fabrica_source_object
        if source_object is None:
            self.report({'ERROR'}, "[VV-FABRICA] No source object set. Select a source mesh in the operator dialog.")
            return {'CANCELLED'}

        selected_objects = context.selected_objects
        source_armature = source_object.find_armature()

        if source_armature is None:
            self.report({'ERROR'}, "[VV-FABRICA] Source object has no armature")
            return {'CANCELLED'}

        for obj in selected_objects:
            if obj == source_object:
                continue
            if obj.type != 'MESH':
                continue

            obj.select_set(True)
            context.view_layer.objects.active = obj

            for vertex_group in source_object.vertex_groups:
                obj.vertex_groups.new(name=vertex_group.name)

            dt_modifier = obj.modifiers.new(name="DataTransfer", type='DATA_TRANSFER')
            dt_modifier.object = source_object
            dt_modifier.use_vert_data = True
            dt_modifier.data_types_verts = {'VGROUP_WEIGHTS'}
            dt_modifier.vert_mapping = 'POLYINTERP_NEAREST'

            # FIXED: Use temp_override instead of deprecated context override dict
            with bpy.context.temp_override(object=obj):
                bpy.ops.object.modifier_apply(modifier=dt_modifier.name)

            bpy.ops.object.select_all(action='DESELECT')
            source_armature.select_set(True)
            obj.select_set(True)
            context.view_layer.objects.active = source_armature
            bpy.ops.object.parent_set(type='ARMATURE')

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            bpy.ops.object.vertex_group_smooth(
                group_select_mode='ALL',
                factor=0.5,
                repeat=3,
                expand=-0.25
            )
            bpy.ops.object.mode_set(mode='OBJECT')

        transferred = [obj.name for obj in selected_objects if obj != source_object and obj.type == 'MESH']
        self.report({'INFO'}, f"[VV-FABRICA] Rig transferred from '{source_object.name}' (armature: '{source_armature.name}') to {len(transferred)} object(s)")
        return {'FINISHED'}


# ¦ ¦ ¦ OPERATORS: ATTACHMENT

class VVFabrica_OT_rigging_button_attach(Operator):
    bl_idname = "vv_fabrica.rigging_button_attach"
    bl_label = "Button Attach"
    bl_description = "Attach object to an Edit Mode selection, transferring weights."
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    normal_offset: bpy.props.FloatProperty(
        name="Normal Offset",
        description="Offset the target object along the normal direction",
        default=0.0,
        soft_min=-10.0,
        soft_max=10.0,
    )

    rotation_offset: bpy.props.FloatVectorProperty(
        name="Rotation Offset",
        description="Offset the target object rotation",
        default=(0.0, 0.0),
        soft_min=-math.pi,
        soft_max=math.pi,
        step=1.0,
        size=2,
        subtype='EULER',
        unit='ROTATION',
    )

    weight_transfer_method: bpy.props.EnumProperty(
        name="Weight Method",
        description="Choose the method for transferring vertex weights",
        items=[
            ("EXACT", "Exact", "Transfer exact vertex or poke face vertex weight"),
            ("DATA_TRANSFER", "Data Transfer", "Transfer weights using Nearest Face Interpolated data transfer"),
        ],
        default="EXACT",
    )

    confirm: bpy.props.BoolProperty(
        name="Confirm",
        description="Confirm the position before attaching",
        default=False,
    )

    def invoke(self, context, event):
        self.normal_offset = 0.0
        self.confirm = False
        return self.execute(context)

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def snap_to_vertex(self, source_obj, target_obj, vertex):
        target_obj.location = source_obj.matrix_world @ (vertex.co + vertex.normal * self.normal_offset)
        normal_world = source_obj.matrix_world.to_3x3() @ vertex.normal
        target_obj.rotation_euler = normal_world.to_track_quat('Z', 'Y').to_euler()
        target_obj.rotation_euler.rotate_axis('X', self.rotation_offset[0])
        target_obj.rotation_euler.rotate_axis('Y', self.rotation_offset[1])

    def snap_to_face(self, source_obj, target_obj, center_vert, normal):
        center = source_obj.matrix_world @ (center_vert.co + normal * self.normal_offset)
        target_obj.location = center
        normal_world = source_obj.matrix_world.to_3x3() @ normal
        target_obj.rotation_euler = normal_world.to_track_quat('Z', 'Y').to_euler()
        target_obj.rotation_euler.rotate_axis('X', self.rotation_offset[0])
        target_obj.rotation_euler.rotate_axis('Y', self.rotation_offset[1])

    def parent_to_armature(self, source_obj, target_obj):
        armature_obj = None
        for modifier in source_obj.modifiers:
            if modifier.type == 'ARMATURE':
                armature_obj = modifier.object
                break

        if armature_obj is not None:
            target_obj.parent = armature_obj
            existing_mod = next((mod for mod in target_obj.modifiers if mod.type == 'ARMATURE' and mod.object == armature_obj), None)
            if not existing_mod:
                armature_mod = target_obj.modifiers.new("Armature", 'ARMATURE')
                armature_mod.object = armature_obj
        else:
            self.report({"WARNING"}, "[VV-FABRICA] No Armature modifier found in source object")

    def transfer_weights(self, source_obj, target_obj, temp_bm, center_vert_index):
        if self.weight_transfer_method == "EXACT":
            target_obj.vertex_groups.clear()
            deform_layer = temp_bm.verts.layers.deform.active
            if deform_layer is None:
                return
            vert_groups = {}
            for v in temp_bm.verts:
                vert_groups[v.index] = {source_obj.vertex_groups[group].name: v[deform_layer][group] for group in v[deform_layer].keys()}
            center_vert_groups = vert_groups[center_vert_index]
            for group_name, weight in center_vert_groups.items():
                target_group = target_obj.vertex_groups.get(group_name)
                if target_group is None:
                    target_group = target_obj.vertex_groups.new(name=group_name)
                if target_obj.mode == 'EDIT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                target_group.add([v.index for v in target_obj.data.vertices], weight, 'REPLACE')
                if target_obj.mode == 'OBJECT':
                    bpy.ops.object.mode_set(mode='EDIT')

        elif self.weight_transfer_method == "DATA_TRANSFER":
            if target_obj.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
            for group in source_obj.vertex_groups:
                if group.name not in target_obj.vertex_groups:
                    target_obj.vertex_groups.new(name=group.name)
            data_transfer_mod = target_obj.modifiers.new("Data Transfer", 'DATA_TRANSFER')
            data_transfer_mod.object = source_obj
            data_transfer_mod.use_vert_data = True
            data_transfer_mod.data_types_verts = {'VGROUP_WEIGHTS'}
            data_transfer_mod.vert_mapping = 'POLYINTERP_NEAREST'
            bpy.ops.object.datalayout_transfer()
            # FIXED: Use temp_override instead of deprecated context override dict
            with bpy.context.temp_override(object=target_obj):
                bpy.ops.object.modifier_apply(modifier=data_transfer_mod.name)
            if target_obj.mode == 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')

    def execute(self, context):
        source_obj = context.active_object
        other_objs = [obj for obj in context.selected_objects if obj != source_obj]
        if not other_objs:
            self.report({"ERROR"}, "[VV-FABRICA] No target object found")
            return {"CANCELLED"}

        target_obj = other_objs[0]

        bm = bmesh.from_edit_mesh(source_obj.data)
        selected_elems = [e for e in bm.select_history if isinstance(e, (bmesh.types.BMVert, bmesh.types.BMFace))]

        if not selected_elems:
            self.report({"ERROR"}, "[VV-FABRICA] No vertex or face selection found")
            return {"CANCELLED"}

        if len(selected_elems) > 1:
            self.report({"ERROR"}, "[VV-FABRICA] Please select only one vertex or one face")
            return {"CANCELLED"}

        elem = selected_elems[0]

        if isinstance(elem, bmesh.types.BMVert):
            self.snap_to_vertex(source_obj, target_obj, elem)
        elif isinstance(elem, bmesh.types.BMFace):
            temp_bm = bmesh.new()
            temp_bm.from_mesh(source_obj.data)
            temp_bm.faces.ensure_lookup_table()
            temp_face = temp_bm.faces[elem.index]
            res = bmesh.ops.poke(temp_bm, faces=[temp_face])
            center_vert = res["verts"][0]
            self.snap_to_face(source_obj, target_obj, center_vert, elem.normal)
            temp_bm.free()

        if self.confirm:
            if isinstance(elem, bmesh.types.BMVert):
                self.transfer_weights(source_obj, target_obj, bm, elem.index)
            elif isinstance(elem, bmesh.types.BMFace):
                temp_bm = bmesh.new()
                temp_bm.from_mesh(source_obj.data)
                temp_bm.faces.ensure_lookup_table()
                temp_face = temp_bm.faces[elem.index]
                res = bmesh.ops.poke(temp_bm, faces=[temp_face])
                center_vert = res["verts"][0]
                self.transfer_weights(source_obj, target_obj, temp_bm, center_vert.index)
                temp_bm.free()

            self.parent_to_armature(source_obj, target_obj)
            print(f"[VV-FABRICA:rigging] Button Attach confirmed: '{target_obj.name}' attached to '{source_obj.name}' with {self.weight_transfer_method} weights")
            self.report({"INFO"}, f"[VV-FABRICA] '{target_obj.name}' attached to '{source_obj.name}'")
        else:
            print(f"[VV-FABRICA:rigging] Button Attach preview: '{target_obj.name}' snapped to '{source_obj.name}' (not yet confirmed)")
        return {"FINISHED"}


# ¦ ¦ ¦ REGISTRATION

classes = [
    VVFabrica_OT_rigging_merge_to_active_bone,
    VVFabrica_OT_rigging_smooth_rig_xfer,
    VVFabrica_OT_rigging_button_attach,
]
