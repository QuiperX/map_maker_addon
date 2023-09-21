
import bpy

def change_base_path(new_path):
    # get the active scene
    scene = bpy.context.scene
    # get the compositing node tree
    node_tree = scene.node_tree
    # find the file output node
    file_output_node = node_tree.nodes.get("File Output")
    # check if the node exists
    if file_output_node is not None:
        # change the base path
        file_output_node.base_path = new_path
        # return True if successful
        return True
    else:
        # return False if the node is not found
        return False

def change_output_res(resolution):
    # get the scene
    scene = bpy.context.scene
    # get the render settings
    render = scene.render
    # change the resolution
    render.resolution_x = resolution
    render.resolution_y = resolution
    # return True if successful
    return True

def change_output_format(output_format):
    # get the scene
    scene = bpy.context.scene
    # get the compositing node tree
    node_tree = scene.node_tree
    # find the file output node
    file_output_node = node_tree.nodes.get("File Output")
    # check if the node exists
    if file_output_node is not None:
        # change the format
        file_output_node.format.file_format = output_format
        # return True if successful
        return True
    else:
        # return False if the node is not found
        return False