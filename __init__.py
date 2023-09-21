bl_info = {
    "name": "Map Maker",
    "author": "quiper",
    "version": (1, 2),
    "blender": (3, 5, 0),
    "location": "View3D > Sidebar > Map Maker",
    "description": "Create height maps from selected objects",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import os
import mathutils
from mathutils import Vector
from . import map_functions as dmf
from . import scene_functions as dsf
from bpy.props import FloatVectorProperty
import time


def change_file_format(self, context):

    scene = bpy.context.scene

    node_tree = scene.node_tree

    file_output_nodes = [node for node in node_tree.nodes if node.type == "OUTPUT_FILE"]

    for node in file_output_nodes:

        node.format.file_format = self.file_format

def append_elements_from_helper_blend():

    script_file = os.path.realpath(__file__)

    directory = os.path.dirname(script_file)

    filepath = os.path.join(directory, "Height Map Maker Helper.blend")
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.scenes = [scene for scene in data_from.scenes if scene == "heightMapCreator"]
        data_to.materials = [mat for mat in data_from.materials if mat == "Height Map"]
        data_to.texts = [text for text in data_from.texts if text == "heightMapper"]


def get_height_map_creator_scene():
    for scene in bpy.data.scenes:
        if scene.name == "heightMapCreator":
            return scene
    return None


def generate_height_maps(self, context):
    
    #first lets check previous import and delete:

    if "Height Map World" in bpy.data.worlds:
        bpy.data.worlds.remove(bpy.data.worlds["Height Map World"])


    if "Height Map" in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials["Height Map"])


    if "heightMapper" in bpy.data.texts:
        bpy.data.texts.remove(bpy.data.texts["heightMapper"])
        

    if "heightMapCreator" in bpy.data.scenes:
        bpy.data.scenes.remove(bpy.data.scenes["heightMapCreator"])
        

    if "Height Map Camera" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Height Map Camera"])


    try:

        main_scene = context.scene
        append_elements_from_helper_blend()
        height_map_creator_scene = get_height_map_creator_scene()

        
        # Transfer selected objects to the heightMapCreator scene

        for obj in context.selected_objects:
            obj_copy = obj.copy()
            obj_copy.data = obj.data.copy()
            height_map_creator_scene.collection.objects.link(obj_copy)

            # Ensure the copied object is in the active view layer before selecting it
            height_map_creator_scene.view_layers[0].active_layer_collection.collection.objects.unlink(obj_copy)
            height_map_creator_scene.view_layers[0].active_layer_collection.collection.objects.link(obj_copy)
            try:
                obj_copy.select_set(True)
            except:
                pass
        
        # Set the active scene to heightMapCreator and run the heightMapper script


        bpy.context.window.scene = height_map_creator_scene
        dsf.change_base_path(main_scene.map_maker_props.output_path)
        print("output path is: " + main_scene.map_maker_props.output_path)
        res = int(main_scene.map_maker_props.output_resolution)
        dsf.change_output_res(res)
        output_format = main_scene.map_maker_props.output_format
        dsf.change_output_format(output_format)

        #fix objects:
        dmf.convert_to_meshes()
        
        #exec(height_map_Script.as_string())

        tree = bpy.context.scene.node_tree

        temp_loc = [1.0,1.0,1.0]
        object_counter = 0
        mat = bpy.data.materials.get("Height Map")
        divider = 1
        timestampstr = str(int(time.time()))
        biggest_object = None

        if main_scene.map_maker_props.combine_meshes:
            main_scene.map_maker_props.use_relative_scale = False
            #if there is a mesh object then go, but if there is a curve, text object, we will convert it to mesh
            dmf.combine_meshes(bpy.context.selected_objects)

        #FIND BIGGEST OBJECT
        biggest_object = dmf.find_biggest_object()
        
        #get biggest object location

        dmf.clean_camera_area()
        
        if main_scene.map_maker_props.use_relative_scale:
            print("we are using relative scale, biggest object is: " + biggest_object.name)
            
            relative_divider = dmf.fix_scale(biggest_object)
            for obj in bpy.context.selected_objects:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                if obj.type == 'CAMERA':
                    print("Current object type: ", obj.type)
                    pass
                bpy.context.view_layer.objects.active = obj
                bpy.ops.transform.resize(value=(relative_divider, relative_divider, relative_divider))
                temp_loc = dmf.get_loc_and_apply_list(temp_loc,obj)
                
                bpy.context.active_object.location = (0.0,0.0,0.0)
                obj.location.z = obj.location.z + (obj.dimensions.z / 2)
                #delete material slots
                obj.active_material_index = 0
                print("MATERIAL SLOT COUNT: ", len(obj.material_slots))
                for i in range(len(obj.material_slots)):
                    bpy.ops.object.material_slot_remove({'object': obj})
                
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
                try:
                    mat.node_tree.nodes['DEGER'].inputs[1].default_value = 1 / obj.dimensions.z
                    
                except:
                    print("possible division By 0 so transfer the object")
                    obj.location.z = 1
                tree.nodes['File Output'].file_slots[0].path = obj.name + "_" + timestampstr + "_" + str(object_counter) + "_" + "height_map"
                object_counter = object_counter+1
                bpy.ops.render.render(use_viewport=True)
                obj = dmf.set_loc(temp_loc,obj)
                bpy.ops.transform.resize(value=(1/relative_divider, 1/relative_divider, 1/relative_divider))

        else:
            for obj in bpy.context.selected_objects:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                
                if obj.type == 'CAMERA':
                    continue;
                divider = dmf.fix_scale(obj)
                bpy.ops.transform.resize(value=(divider, divider, divider))
                
                temp_loc = dmf.get_loc_and_apply_list(temp_loc,obj)
                timestampstr = str(int(time.time()))
                
                
                
                bpy.context.active_object.location = (0.0,0.0,0.0)
                obj.location.z = obj.location.z + (obj.dimensions.z / 2)
                
                #delete material slots
                obj.active_material_index = 0
                #print("MATERIAL SLOT COUNT: ", len(obj.material_slots))
                for i in range(len(obj.material_slots)):
                    bpy.ops.object.material_slot_remove({'object': obj})
                
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
                try:
                    mat.node_tree.nodes['DEGER'].inputs[1].default_value = 1 / obj.dimensions.z
                except:
                    print("possible division By 0 so transfer the object")
                    obj.location.z = 1
                tree.nodes['File Output'].file_slots[0].path = obj.name + "_" + timestampstr + "_" + str(object_counter) + "_" + "height_map"
                object_counter = object_counter+1
                bpy.ops.render.render(use_viewport=True)
                obj = dmf.set_loc(temp_loc,obj)
                bpy.ops.transform.resize(value=(1/divider, 1/divider, 1/divider))
        

        #we will delete all objects in the height map scene
        bpy.context.window.scene = main_scene

        try:
            bpy.context.window.scene = height_map_creator_scene
            bpy.context.window.scene = height_map_creator_scene
            # Select all objects in the scene
            bpy.ops.object.select_all(action='SELECT')
            for obj in bpy.context.selected_objects:
                # Get the mesh data of the object
                mesh = obj.data
                # Remove the object from the file
                bpy.data.objects.remove(obj)
                # Remove the mesh data from the file
                try:
                    bpy.data.meshes.remove(mesh)
                except:
                    pass
            bpy.ops.object.delete()
        except:
            pass
        
        bpy.context.window.scene = main_scene
        
        try:
            bpy.data.texts.remove(bpy.data.texts["heightMapper"])
            bpy.data.materials.remove(bpy.data.materials["Height Map"])
            bpy.data.cameras.remove(bpy.data.cameras["Height Map Camera"])
            bpy.data.worlds.remove(bpy.data.worlds["Height Map World"])
            bpy.data.scenes.remove(bpy.data.scenes["heightMapCreator"])
        except:
            pass
    #Except part will print the error message if something goes wrong
    except Exception as e:
        print("ERROR IS HTERE", e)
        #we will delete all objects in the height map scene if created
        try:
            bpy.data.texts.remove(bpy.data.texts["heightMapper"])
            bpy.data.materials.remove(bpy.data.materials["Height Map"])
            bpy.data.cameras.remove(bpy.data.cameras["Height Map Camera"])
            bpy.data.worlds.remove(bpy.data.worlds["Height Map World"])
            bpy.data.scenes.remove(bpy.data.scenes["heightMapCreator"])
        except:
            pass



class MapMakerPanel(bpy.types.Panel):
    bl_label = "Map Maker"
    bl_idname = "HEIGHT_MAP_MAKER_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Map Maker"

    def draw(self, context):
        layout = self.layout
        props = context.scene.map_maker_props

        layout.prop(props, "output_path")
        layout.prop(props, "output_resolution")
        layout.prop(props, "output_format")
        layout.operator("height_map_maker.generate_height_maps")
        if props.combine_meshes == False:
            layout.prop(props, "use_relative_scale")
        layout.prop(props, "combine_meshes")
       


class MapMakerProperties(bpy.types.PropertyGroup):
    output_path: bpy.props.StringProperty(
        name="Output Path",
        description="Select a file path for the height map outputs",
        default="",
        maxlen=1024,
        subtype="DIR_PATH",
    )
    output_resolution: bpy.props.EnumProperty(
        name="Resolution",
        description="Set the resolution for the height maps",
        items=[
            ("512", "512x512", ""),
            ("1024", "1024x1024", ""),
            ("2048", "2048x2048", ""),
            ("4096", "4096x4096", ""),
            ("8192", "8192x8192", ""),
        ],
        default="2048",
        
    )
    output_format: bpy.props.EnumProperty(
        name="Output Format",
        description="Select a file format for the height map outputs",
        items=[
            ("PNG", "PNG", ""),
            ("JPEG", "JPEG", ""),
            ("TIFF", "TIFF", ""),
            ("OPEN_EXR", "OPEN_EXR", ""),
            ("HDR", "HDR", ""),
            ("TARGA", "TARGA", ""),
            ("BMP", "BMP", ""),
            ("IRIS", "IRIS", ""),
        ],
        default="PNG",
    )
    use_relative_scale: bpy.props.BoolProperty(
        name="Use Relative Scale",
        description="Use relative scale for map generation, if you activate this option, objects scale will not change but locations will be setted to 0,0,0",
        default=False,
    )
    combine_meshes: bpy.props.BoolProperty(
        name="Combine Meshes",
        description="Combine all meshes into one mesh, if you activate this option, the relative scale option will be ignored",
        default=False,
    )
    keep_relative_location: bpy.props.BoolProperty(
        name="Keep Relative Location",
        description="Keep relative location of objects",
        default=False,
    )


class HEIGHT_MAP_MAKER_OT_generate_height_maps(bpy.types.Operator):
    bl_idname = "height_map_maker.generate_height_maps"
    bl_label = "Generate Height Maps"
    

    def execute(self, context):
        if context.scene.map_maker_props.output_path == "":
            self.report({"ERROR"}, "SET OUTPUT PATH FIRST")
            return {"CANCELLED"}
        else:
            generate_height_maps(self, context)
            return {"FINISHED"}


def register():
    bpy.utils.register_class(MapMakerPanel)
    bpy.utils.register_class(MapMakerProperties)
    bpy.types.Scene.map_maker_props = bpy.props.PointerProperty(type=MapMakerProperties)
    bpy.utils.register_class(HEIGHT_MAP_MAKER_OT_generate_height_maps)


def unregister():
    bpy.utils.unregister_class(MapMakerPanel)
    bpy.utils.unregister_class(HEIGHT_MAP_MAKER_OT_generate_height_maps)
    del bpy.types.Scene.map_maker_props
    bpy.utils.unregister_class(MapMakerProperties)



if __name__ == "__main__":
    register()