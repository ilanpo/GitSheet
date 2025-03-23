# from ClientBL import ClientBl as CBL

import dearpygui.dearpygui as ui

VIEWPORT_WIDTH: int = 1280
VIEWPORT_HEIGHT: int = 1000


class Node:
    
    _parent:    int # Parent DearPyGui ID
    _tag:       str # Custom tag
    _id:        int # DearPyGui ID
    _callback:  any

    _input_id:  int
    _output_id: int

    def __init__(self, parent: int, tag: str, title: str, position: list):
        self._parent = parent
        self._tag = tag

        self._callback = None

        self.__init_node_widget(title, position)

    def __init_node_widget(self, title: str, position: list):
        
        self._id = ui.add_node(parent=self._parent, label=title, pos=[position[0], position[1]])

        self._input_id = ui.add_node_attribute(parent=self._id, attribute_type=ui.mvNode_Attr_Input)
        ui.add_text(parent=self._input_id, label="Hello")
        self._output_id = ui.add_node_attribute(parent=self._id, attribute_type=ui.mvNode_Attr_Output)
        ui.add_text(parent=self._output_id, label="Hello2")

        with ui.node_attribute(parent=self._id):
            ui.add_button(label=f"Press to add another Node", callback=self.__callback_wrap)
        
    def __callback_wrap(self, *args):
        
        if self._callback is None:
            return
        
        self._callback()

    def get_id(self):
        return self._id
    
    def get_tag(self):
        return self._tag
    
    def get_input(self):
        return self._input_id

    def get_output(self):
        return self._output_id
    
    def attach_callback(self, new_callback):
        self._callback = new_callback


class Vein:
    
    _parent:        int
    _tag:           str
    _id:            int

    _start_node:    Node
    _end_node:      Node

    _callback:      any

    def __init__(self, parent: int, tag: str):
        self._parent = parent
        self._tag = tag

        self._callback = None

    def attach_nodes(self, start_node: Node, end_node: Node):
        
        self._start_node = start_node
        self._end_node = end_node

        self._id = ui.add_node_link( start_node.get_input(), end_node.get_output(), parent=self._parent )

    def on_press(self):
        if self._callback is None:
            return
        
        self._callback()

    def get_id(self):
        return self._id
    
    def get_tag(self):
        return self._tag

    def attach_callback(self, new_callback):
        self._callback = new_callback


class NodeEditor:
    
    _parent:    int
    _id:        int
    _tags:      dict

    _nodes:     dict
    _veins:     dict

    _did_press: bool

    def __init__(self, parent: int):
        
        self._parent = parent

        self._id = -1
        self._tags = { }

        self._veins = { }
        self._nodes = { }

        self._did_press = False

        self.__setup_editor( )

    def __setup_editor(self):
        self._id = ui.add_node_editor(parent=self._parent, minimap=True, minimap_location=ui.mvNodeMiniMap_Location_BottomRight)

    def add_vein(self, vein_tag, start_node: str, end_node: str):
        if vein_tag in self._veins:
            raise Exception("Why you want to add the same vein tag?!??!!. U F&#@^#$ N$@@3&")
        
        new_vein = Vein(self._id, vein_tag)

        new_vein.attach_nodes(start_node, end_node)

        self._tags[new_vein.get_id()] = vein_tag
        self._veins[vein_tag] = new_vein

        return new_vein

    def add_node(self, node_tag, name, position: list) -> Node:
        if node_tag in self._nodes:
            raise Exception("Why you want to add the same node tag?!??!!. U F&#@^#$ N$@@3&")
        
        new_node = Node(self._id, node_tag, name, position)

        #self._tags[new_node.get_id()] = node_tag
        self._nodes[node_tag] = new_node

        return new_node

    def update(self):
        
        selected_links: list = ui.get_selected_links(self._id)
        length: int = len(selected_links)

        if length == 0:
            self._did_press = False
            return

        if length > 1:
            self._did_press = False

            # Clear the selection
            return ui.clear_selected_links(self._id)
        
        if length == 1:
            # Run the callback
            self.__callback_on_press(selected_links[0])

            # Clear selection
            return ui.clear_selected_links(self._id)
        
    def __callback_on_press(self, id_value: int):
        if self._did_press:
            return

        tag: str = self._tags[id_value]
        self._did_press = True

        self._veins[tag].on_press()



class ClientGUI:

    _window_tag:    str
    _node_editor:   NodeEditor

    def __init__(self):
        
        # Create application window
        self.__create_window()

        # Create window instance of dearpygui
        self.__load_window()

        # Create the node editor instance
        self.__create_node_editor()

    def __create_window(self):
        
        # Create dearpygui context
        ui.create_context()

        # Create viewport
        ui.create_viewport(title="Client", width=VIEWPORT_WIDTH, height=VIEWPORT_HEIGHT)

        # Setup dear py gui
        ui.setup_dearpygui()

    def __load_window(self):
        
        # Create a window instance
        self._window_tag = ui.add_window(no_title_bar=True, no_move=True, no_resize=True, no_collapse=True, no_close=True)

        # Load menu bar
        self.__load_menu_bar()

        # Set this window as primary window
        ui.set_primary_window( self._window_tag, True )

    def __load_menu_bar(self):

        menu_bar_id = ui.add_menu_bar(parent=self._window_tag)

        with ui.menu(parent=menu_bar_id, label="File"):
            ui.add_menu_item(label="Test1")
            ui.add_menu_item(label="Test2")
            ui.add_menu_item(label="Test3")
            ui.add_separator()
            ui.add_menu_item(label="Test4")

        with ui.menu(parent=menu_bar_id, label="Help"):
            ui.add_menu_item(label="IDK")
            ui.add_menu_item(label="ITEM")
        

    def __create_node_editor(self):
        
        self._node_editor = NodeEditor(self._window_tag)

        # TODO ! Remove
        node1 = self._node_editor.add_node( "Node1", "Project1", [100, 400] )
        node2 = self._node_editor.add_node( "Node2", "Project2", [300, 100] )
        node3 = self._node_editor.add_node( "Node3", "Project3", [500, 230] )

        node3.attach_callback( self.__test_callback )

        v = self._node_editor.add_vein("Vein1", node1, node2)

        v.attach_callback(lambda: print("IDK"))

    def __test_callback(self):
        self._node_editor.add_node( "Node4", "Project4", [100, 100] )

    def __show_window(self):

        ui.show_viewport()
        
        while ui.is_dearpygui_running():
            
            # Execute the .update of the node editor
            self._node_editor.update( )

            # Render the frame
            ui.render_dearpygui_frame( )

        ui.start_dearpygui()

    def __unload(self):

        # Destroy context
        ui.destroy_context()

        # TODO !!! Clear things you havent on unload

    def execute(self):

        # Actually renders the application
        self.__show_window()

        # Unload application
        self.__unload()
