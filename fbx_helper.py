from io_scene_fbx import parse_fbx
from io_scene_fbx.fbx_utils import FBX_KTIME
from io_scene_fbx.import_fbx import elem_find_first

import bpy

def get_fbx_local_time(filepath):
    try:
        elem_root, version = parse_fbx.parse(filepath)
    except Exception as e:
        # can't read
        return

    takes = elem_find_first(elem_root, b'Takes')
    local_time = None
    for take in takes:
        for elem in take:
            try:
                local_time = elem_find_first(elem, b'ReferenceTime')
            except (KeyError, AttributeError):
                continue
            if local_time:
                break

    if local_time:
        return local_time.props


def convert_from_fbx_duration(start, end):
    return (end - start)/FBX_KTIME



def make_annotations(cls):
    """Add annotation attribute to fields to avoid Blender 2.8+ warnings"""
    if not hasattr(bpy.app, "version") or bpy.app.version < (2, 80):
        return cls
    if bpy.app.version < (2, 93, 0):
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, tuple)}
    else:
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, bpy.props._PropertyDeferred)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls