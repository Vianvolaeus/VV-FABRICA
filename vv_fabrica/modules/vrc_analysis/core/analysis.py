"""PURE ANALYSIS FUNCTIONS FOR VRC AVATAR PERFORMANCE RANKING.

NO BLENDER (`bpy`) IMPORTS — THESE ARE TESTABLE OUTSIDE BLENDER.
"""


def performance_rank(statistics):
    """DETERMINE VRC PERFORMANCE RANK FROM `statistics` DICT."""
    ranks = [
        ('Excellent', {'triangles': 32000, 'texture_memory': 40 * 1024 * 1024, 'skinned_meshes': 1, 'meshes': 4, 'material_slots': 4, 'bones': 75}),
        ('Good', {'triangles': 70000, 'texture_memory': 75 * 1024 * 1024, 'skinned_meshes': 2, 'meshes': 8, 'material_slots': 8, 'bones': 150}),
        ('Medium', {'triangles': 70000, 'texture_memory': 110 * 1024 * 1024, 'skinned_meshes': 8, 'meshes': 16, 'material_slots': 16, 'bones': 256}),
        ('Poor', {'triangles': 70000, 'texture_memory': 150 * 1024 * 1024, 'skinned_meshes': 16, 'meshes': 24, 'material_slots': 32, 'bones': 400}),
        ('Very Poor', {}),
    ]

    rank_index = 0
    for key, value in statistics.items():
        for i, (rank, limits) in enumerate(ranks[:-1]):
            if value > limits[key]:
                rank_index = max(rank_index, i + 1)

    return ranks[rank_index][0]


def performance_warning(statistics):
    """GENERATE WARNING MESSAGES FOR STATISTICS THAT EXCEED THRESHOLDS."""
    warnings = []

    if statistics['triangles'] > 70000:
        warnings.append("Polygon count is high. Consider dissolving unnecessary geometry, decimation, or removing unnecessary geometry entirely.")

    if statistics['texture_memory'] > 150 * 1024 * 1024:
        warnings.append("Detected VRAM is high! Consider reducing texture resolution, or using VRAM reduction techniques in Unity. If you are using high resolution source textures, remember Unity will downres these to 2K on import.")

    if statistics['skinned_meshes'] > 16:
        warnings.append("Skinned Mesh count is high. Consider merging skinned meshes as appropriate, or offloading things like outfit changes to a different avatar entirely.")

    if statistics['meshes'] > 24:
        warnings.append("Meshes count is high. It is questionable why you need so many meshes, and you should consider merging them as appropriate, or removing them as appropriate.")

    if statistics['material_slots'] > 32:
        warnings.append("Material Count is very high. Check for duplicate entries, unused material slots, and atlas textures if required. If you can merge two meshes that share the exact same material, this stat will effectively be lowered.")

    if statistics['bones'] > 400:
        warnings.append("Bones count is very high. Check for duplicate or unused armatures, _end bones (leaf bones), zero weight bones and remove them as needed.")

    return warnings
