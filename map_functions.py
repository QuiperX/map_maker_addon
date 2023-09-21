import bpy
import os
import time
import mathutils
from mathutils import Vector

#FUNCTIONS
def get_loc_and_apply_list(liste, obj):
    liste[0] =  obj.location.x
    liste[1] =  obj.location.y
    liste[2] =  obj.location.z
    return liste

def set_loc(liste, obj):
    obj.location.x = liste[0]
    obj.location.y = liste[1]
    obj.location.z = liste[2]  
    return obj

def fix_scale(obj):
    divider_x = 1
    divider_y = 1
    multp_x = 1
    multp_y = 1
    if obj.dimensions.x > 2:    
        divider_x = 2 / obj.dimensions.x
    if obj.dimensions.y > 2:
        divider_y = 2 / obj.dimensions.y
        
    if obj.dimensions.x < 2:   
        multp_x = 2 / obj.dimensions.x
        print("mutiple x = ", multp_x)
    if obj.dimensions.y < 2:

        multp_y = 2 / obj.dimensions.y
        print("mutiple y = ", multp_y)
    if divider_x < 1 or divider_y < 1:

        if divider_x < divider_y:

            return divider_x
        else:

            return divider_y
    elif multp_x > multp_y:

        return multp_y
    else:

        print("mutiple y = ", multp_y)
        return multp_x

def is_inside_area(obj):
    # assume the center area is a square with side length 2
    x_min = -4
    x_max = 4
    y_min = -4
    y_max = 4
    # get the object's location and dimensions
    x = obj.location.x
    y = obj.location.y
    dx = obj.dimensions.x / 2
    dy = obj.dimensions.y / 2
    # check if any part of the object overlaps with the center area
    if x + dx > x_min and x - dx < x_max and y + dy > y_min and y - dy < y_max:
        return True
    else:
        return False

def move_outside_area(obj):
    # assume the outside area is a square with side length 4
    x_min = -4
    x_max = 4
    y_min = -4
    y_max = 4
    # get the bounding box coordinates of the object in global space
    bbox = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    # get the minimum and maximum values along each axis
    x_vals = [v.x for v in bbox]
    y_vals = [v.y for v in bbox]
    x_min_bbox = min(x_vals)
    x_max_bbox = max(x_vals)
    y_min_bbox = min(y_vals)
    y_max_bbox = max(y_vals)
    # calculate the distance to move the bounding box along each axis
    dx_min = x_min - x_max_bbox
    dx_max = x_max - x_min_bbox
    dy_min = y_min - y_max_bbox
    dy_max = y_max - y_min_bbox
    # choose the smallest distance that will move the bounding box outside the area
    dx_move = min(abs(dx_min), abs(dx_max))
    dy_move = min(abs(dy_min), abs(dy_max))
    # create a vector with the direction and magnitude of the translation
    vec = Vector((dx_move, dy_move, 0))
    # get the inverse of the object's world matrix
    inv = obj.matrix_world.copy()
    inv.invert()
    # align the vector to the object's local axis
    vec_rot = vec @ inv
    # move the object by adding the vector to its location
    obj.location += vec_rot

def findBiggestObject(objList):
    biggestObject = objList[0]
    for obj in objList:
        if obj.dimensions.x > biggestObject.dimensions.x:
            biggestObject = obj
    return biggestObject


def clean_camera_area():
    for obj in bpy.context.selected_objects:
        if obj.type == 'CAMERA':
            continue;
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        # check if the object is inside the area 
        if is_inside_area(obj): 
            # print the object's name and location 
            print(f"Area occupation: {obj.name} at {obj.location}") 
            # move the object outside the area by calling the function 
            move_outside_area(obj)


def find_biggest_object():
    biggest_object = None
    biggest_object_area = 0
    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        if obj.type == 'MESH':
            if obj.dimensions[0] * obj.dimensions[1] > biggest_object_area:
                biggest_object = obj
                biggest_object_area = obj.dimensions[0] * obj.dimensions[1]
    print("biggest object is: " + biggest_object.name)
    return biggest_object


def convert_to_meshes():
    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        #CURVE,FONT, SURFACE, META
        if obj.type == 'CURVE' or obj.type == 'FONT' or obj.type == 'SURFACE' or obj.type == 'META':
            print("converting", obj.type, "to mesh")
            bpy.ops.object.convert(target='MESH')
        elif obj.type == 'MESH':
            continue
        else:
            bpy.data.objects.remove(obj)


def combine_meshes(selected_objects):
    for obj in selected_objects:
        #apply modifiers if any
        print("for this object:" + obj.name)
        bpy.context.view_layer.objects.active = obj

        for modifier in obj.modifiers:
            print("applying modifier:", modifier.name)
            #fix possible subsurf modifier error
            if modifier.type == 'SUBSURF':
                print("viewport subdivisions:", modifier.levels)
                print("render subdivisions:", modifier.render_levels)
                if modifier.render_levels > modifier.levels:
                    modifier.levels = modifier.render_levels
            #fix possible multires modifier error
            if modifier.type == 'MULTIRES':
                print("viewport subdivisions:", modifier.levels)
                print("render subdivisions:", modifier.render_levels)
                if modifier.render_levels > modifier.levels:
                    modifier.levels = modifier.render_levels
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        if obj.type == 'CURVE' or obj.type == 'FONT':
            print("converting", obj.type, "to mesh")
            bpy.ops.object.convert(target='MESH')
        elif obj.type == 'MESH':
            continue
        else:
            #delete this object
            bpy.data.objects.remove(obj)
    #now combine meshes
    bpy.ops.object.join()