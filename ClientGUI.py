from ClientBL import ClientBl as CBL

import dearpygui.dearpygui as ui

VIEWPORT_WIDTH: int = 1280
VIEWPORT_HEIGHT: int = 1000


class Node:
    
    _parent:    int  # Parent DearPyGui ID
    _tag:       str  # Custom tag
    _id:        int  # DearPyGui ID
    _title:     str
    _info:      str
    _callback:  any
    _callback_download_file: any
    _callback_open_file: any
    _callback_delete_node: any

    _input_id:  int
    _output_id: int

    def __init__(self, parent: int, tag: str, title: str, position: list, information: str):
        self._parent = parent
        self._tag = tag
        self._title = ""
        self._info = information
        self._callback = None

        self.__init_node_widget(title, position)

    def __init_node_widget(self, title: str, position: list):
        
        self._id = ui.add_node(parent=self._parent, label=title, pos=[position[0], position[1]])

        self._title = title

        self._input_id = ui.add_node_attribute(parent=self._id, attribute_type=ui.mvNode_Attr_Input)
        ui.add_text(parent=self._input_id)
        self._output_id = ui.add_node_attribute(parent=self._id, attribute_type=ui.mvNode_Attr_Output)
        ui.add_text(parent=self._output_id)

        with ui.node_attribute(parent=self._id):
            #ui.add_button(label=f"Press to add another Node", callback=self.__callback_wrap)
            ui.add_text( self._info )
            ui.add_button(label="Download File", callback=self.__callback_download_file)
            ui.add_button(label="Open File", callback=self.__callback_open_file)
            ui.add_button(label="Delete File", callback=self.__callback_delete_node) # TODO
            ui.add_button(label="Delete Node", callback=self.__callback_delete_node)
        
    def __callback_wrap(self, *args):
        
        if self._callback is None:
            return
        
        self._callback()

    def __callback_delete_node(self):

        if self._callback_delete_node is None:
            return

        self._callback_delete_node(self._tag)

    def __callback_download_file(self, *args):
        if self._callback_download_file is None:
            return

        self._callback_download_file(self._tag)

    def __callback_open_file(self, *args):
        if self.__callback_open_file is None:
            return

        self.__callback_open_file(self._tag)

    def get_id(self):
        return self._id
    
    def get_tag(self):
        return self._tag
    
    def get_name(self):
        return self._title
    
    def get_input(self):
        return self._input_id

    def get_output(self):
        return self._output_id
    
    def attach_callback(self, new_callback, callback_type: int = 1):

        if callback_type == 1:
            self._callback = new_callback
            return

        if callback_type == 2:
            self._callback_download_file = new_callback
            return

        if callback_type == 3:
            self._callback_open_file = new_callback
            return

        if callback_type == 4:
            self._callback_delete_node = new_callback
            return


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

        self._id = ui.add_node_link( start_node.get_output(), end_node.get_input(), parent=self._parent )

    def on_press(self):
        if self._callback is None:
            return
        
        self._callback(self._start_node.get_name(), self._end_node.get_name())

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

    def add_vein(self, vein_tag, start_node: Node, end_node: Node):
        if vein_tag in self._veins:
            raise Exception("Why you want to add the same vein tag?!??!!. U F&#@^#$ N$@@3&")
        
        new_vein = Vein(self._id, vein_tag)

        new_vein.attach_nodes(start_node, end_node)

        self._tags[new_vein.get_id()] = vein_tag
        self._veins[vein_tag] = new_vein

        return new_vein

    def add_node(self, node_tag, name, position: list, information: str) -> Node:
        if node_tag in self._nodes:
            raise Exception("Why you want to add the same node tag?!??!!. U F&#@^#$ N$@@3&")
        
        new_node = Node(self._id, node_tag, name, position, information)

        self._tags[new_node.get_id()] = node_tag
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

    def find_node(self, node_tag) -> any:

        if node_tag in self._nodes:
            return self._nodes[node_tag]

        return None

    def return_positions(self):
        positions = {}
        for item in self._tags:
            if self._tags[item] in self._nodes:
                pos = ui.get_item_pos(item)
                positions[self._tags[item]] = pos
        return positions

    def get_nodes(self):
        nodes = {}
        for item in self._tags:
            if self._tags[item] in self._nodes:
                name = self._nodes[self._tags[item]].get_name()
                nodes[name] = self._tags[item]
        return nodes

    def clear_editor(self):
        ui.delete_item(self._id, children_only=True)
        self._veins.clear()
        self._nodes.clear()
        self._tags.clear()


class ClientGUI:

    _window:      str

    _node_editor:   NodeEditor

    def __init__(self):
        
        # Create application window
        self.__create_window()

        # Create window instance of dearpygui
        self.__load_windows()

        self.last_error = "no error registered"
        self.userid = "123"
        self.all_project_names = []
        self.all_project_ids = {}
        self.project_id = None

    def __create_window(self):
        
        # Create dearpygui context
        ui.create_context()

        # Create viewport
        ui.create_viewport(title="Client", width=VIEWPORT_WIDTH, height=VIEWPORT_HEIGHT)

        # Setup dear py gui
        ui.setup_dearpygui()

    def __load_windows(self):
        
        # Create a window instance
        self._window = ui.add_window(no_title_bar=True, no_move=True, no_resize=True, no_collapse=True, no_close=True)

        # First set the login window to be prim
        ui.set_primary_window(self._window, True)

        self.__init_login_window()

        self.__load_menu_bar()

        self.__create_node_editor()

    def __init_login_window(self):
        with ui.window(label="Login / Register", no_close=True, no_collapse=True, pos=[200, 200], modal=True, tag="LoginWindow"):
            ui.add_text("GitSheet")
            ui.add_separator()
            
            with ui.group(horizontal=True):
                ui.add_text("Ip:")
                ui.add_input_text(width=200, tag="IpInput", default_value="127.0.0.1")

            with ui.group(horizontal=True):
                ui.add_text("Port:")
                ui.add_input_text(width=200, tag="PortInput", default_value="7007")

            ui.add_separator()

            with ui.group(horizontal=True):
                ui.add_text("Username:")
                ui.add_input_text(width=200, tag="UsernameEntry")

            with ui.group(horizontal=True):
                ui.add_text("Password:")
                ui.add_input_text(width=200, password=True, tag="PasswordEntry")

            with ui.group(horizontal=True):
                ui.add_button(label="Register", callback=self.__press_register )
                ui.add_button(label="Login", callback=self.__press_login )

            ui.add_text(default_value="Welcome to GitSheet!", tag="ErrorLogin")

    def __press_register(self):
        try:
            ip, port = self.__get_connection_details()
            self.start_client(ip, port)
            username = ui.get_value("UsernameEntry")
            result = self.clientbl.register(username, ui.get_value("PasswordEntry"))
            print(f"{result}")
            self.stop_client()
            self.__failed_login(f"Successfully registered user {username}")
        except Exception as e:
            self.__failed_login(f"Encountered error on login: {e}")

    def __press_login(self, *args):
        try:
            ip, port = self.__get_connection_details()
            self.start_client(ip, port)
            result = self.clientbl.login(ui.get_value("UsernameEntry"), ui.get_value("PasswordEntry"))
            print(result)
            if result != "FA1L3D":
                self.__load_project_screen()
            else:
                self.__failed_login("Login failed, wrong password or username")
                self.stop_client()
        except Exception as e:
            self.__failed_login(f"Encountered error on login: {e}")

    def __load_project_screen(self):
        try:
            projects = self.clientbl.request_projects()
            if type(projects) != list:
                return print("Failed to fetch projects")
            for project in projects:
                self.all_project_names.append(project["name"])
                self.all_project_ids[project["name"]] = project["_id"]

            for item in ui.get_item_children("LoginWindow", slot=1): # Slot 1 is for regular content
                ui.hide_item(item)

            # Change the window title
            ui.set_item_label("LoginWindow", "Project")
            ui.set_item_height("LoginWindow", 400)
            ui.set_item_width("LoginWindow", 600)

            with ui.group(parent="LoginWindow", horizontal=True):

                ui.add_listbox(items=self.all_project_names, callback=self.__on_list_press, width=200 )

                with ui.group():
                    ui.add_text("Select Project")
                    ui.add_text(f"Project : None", tag="ProjectName")
                    ui.add_button(label="Load Project None", tag="ProjectLoadButton")
        except Exception as e:
            self.__failed_login(f"Encountered error on login: {e}")
    
    def __on_list_press(self, sender, app_data):
        
        ui.set_value( "ProjectName", f"{app_data}")
        ui.configure_item("ProjectLoadButton", label=f"Load {app_data}")

        # TODO ! Update the callback based on Project name
        ui.configure_item("ProjectLoadButton", callback=lambda: self.__load_project(app_data))

    def __load_project(self, project_name: str):
        self.project_id = self.all_project_ids[project_name]
        self.load_nodes()
        self.load_veins()

        print(f"Loaded {project_name}")

        ui.delete_item("LoginWindow")

        #node1 = self._node_editor.add_node( "Node1", "Project1", [100, 400], "Some first Node" )
        #node2 = self._node_editor.add_node( "Node2", "Project2", [300, 100], "Extremly aggresive. not recommanded to talk to" )
        #node3 = self._node_editor.add_node( "Node3", "Project3", [500, 230], "Toxic but cute :P" )

        #node3.attach_callback( self.__test_callback )

        #v = self._node_editor.add_vein("Vein1", node1, node2)
        #v2 = self._node_editor.add_vein("Vein2", node1, node3)

        #v.attach_callback(self.__add_vein_window)
        #v2.attach_callback(self.__add_vein_window)

    def __add_vein_window(self, start_name, end_name):
        with ui.window(label="Vein Info", pos=[200, 200]):
            ui.add_input_text(multiline=True, default_value=f"Linked {start_name} - {end_name}", tag="VeinValue")
            ui.add_button(label="Save changes", callback=self.__callback_save_vein)

    def __callback_save_vein(self, *args):
        value = ui.get_value("VeinValue")
        print(value)

        # TODO: Send this value
        
    def __failed_login( self, reason):
        ui.configure_item("ErrorLogin", default_value=f"{reason}!")
        print(f"{reason}!")

    def __get_connection_details(self) -> tuple:
        return ui.get_value("IpInput"), int(ui.get_value("PortInput"))

    def __show_window(self):

        ui.show_viewport()
        
        while ui.is_dearpygui_running():
            
            # Execute the .update of the node editor
            self._node_editor.update( )

            # Render the frame
            ui.render_dearpygui_frame( )

        # ui.start_dearpygui()

    def __unload(self):

        # Destroy context
        ui.destroy_context()

        self.stop_client()

        # TODO !!! Clear things you havent on unload

    def execute(self):
        # Initialize protocols
        self.init_protocols()

        # Actually renders the application
        self.__show_window()

        # Unload application
        self.__unload()

    def __load_menu_bar(self):

        menu_bar_id = ui.add_menu_bar(parent=self._window)

        with ui.menu(parent=menu_bar_id, label="Project"):
            ui.add_menu_item(label="Refresh", callback=self.__callback_refresh_button)
            ui.add_menu_item(label="Add Node", callback=self.__callback_add_node)
            ui.add_menu_item(label="Add Vein", callback=self.__callback_add_vein)
            ui.add_menu_item(label="Save new position", callback=self.__callback_save_position)

    def __callback_refresh_button(self):
        self._node_editor.clear_editor()
        self.load_nodes()
        self.load_veins()
        print("Refreshed editor")

    def __callback_save_position(self):
        positions = self._node_editor.return_positions()
        print(positions)
        for item in positions:
            settings = {"x": positions[item][0], "y": positions[item][1]}
            self.clientbl.update_position("nodes", item, settings)
        self.__callback_refresh_button()

    def __callback_add_node(self):
        if ui.does_item_exist("NodeWindow"):
            ui.delete_item("NodeWindow")
        try:
            with ui.window(label="Add Node", pos=[200, 200], tag="NodeWindow"):
                ui.add_input_text(default_value=f"Node name", tag="NodeData")
                ui.add_button(label="Create Node", callback=self.add_node)
        except Exception as e:
            self.error_popup(f"Encountered error on node create: {e}")

    def add_node(self):
        self.clientbl.create_node(str(self.project_id), [self.userid],
                                  [ui.get_value("NodeData")], {"x": 0, "y": 0})
        self.__callback_refresh_button()

    def __callback_add_vein(self):
        if ui.does_item_exist("VeinWindow"):
            ui.delete_item("VeinWindow")
        try:
            nodes = self._node_editor.get_nodes()
            node_names = []
            for node in nodes:
                node_names.append(node)

            with ui.window(label="Add Vein", pos=[200, 200], tag="VeinWindow"):
                with ui.group():
                    ui.add_input_text(default_value=f"Description displayed in vein", tag="VeinData")
                    ui.add_text("Origin:")
                    ui.add_listbox(items=node_names, width=200, tag="VeinStartNode")
                    ui.add_text("Destination:")
                    ui.add_listbox(items=node_names, width=200, tag="VeinEndNode")
                    ui.add_button(label="Create Vein", callback=self.add_vein)
        except Exception as e:
            self.error_popup(f"Encountered error on vein create: {e}")

    def add_vein(self):
        nodes = self._node_editor.get_nodes()
        self.clientbl.create_vein(str(self.project_id), [self.userid],
                                      ui.get_value("VeinData"), {"origin": nodes[ui.get_value("VeinStartNode")],
                                      "destination": nodes[ui.get_value("VeinEndNode")]})
        self.__callback_refresh_button()

    def error_popup(self, error):
        with ui.window(label="Error", pos=[200, 200]):
            ui.add_text(f"{error}")

    def __create_node_editor(self):
        self._node_editor = NodeEditor(self._window)

    def __test_callback(self):
        self._node_editor.add_node("Node4", "Project4", [100, 100],  "im test")

    def init_protocols(self):
        self.clientbl = CBL()
        self.clientbl.init_protocols()

    def start_client(self, ip, port):
        self.clientbl.start_client(ip, port)

    def stop_client(self):
        self.clientbl.disconnect()
    
    def load_nodes(self):
        nodes: any = self.clientbl.request_data("nodes", self.project_id)

        if type(nodes) == str:
            return print("Ops")

        for item in nodes:
            item: dict = item

            current_node = self._node_editor.add_node(item['_id'], item['node_data'][0],
                                                      [item['settings']["x"], item['settings']["y"]], "Info")
            current_node.attach_callback(self.__download_file, 2)
            current_node.attach_callback(self.__open_file, 3)
            current_node.attach_callback(self.__delete_node, 4)

    def __download_file(self, node_tag):
        print(f"Need to download file from node {node_tag}")

        # TODO ! Download file based on node tag

    def __open_file(self, node_tag):
        print(f"Need to open from node {node_tag}")

        # TODO ! Perform open file based on node tag

    def __delete_node(self, node_id):
        print("got to delete")
        self.clientbl.delete_node(node_id, self.project_id)
        print("deleted node")
        self.__callback_refresh_button()

    def load_veins(self):
            veins: any = self.clientbl.request_data("veins", self.project_id)

            if type(veins) == str:
                return print("type(veins) == str")

            for item in veins:
                item: dict = item

                settings: dict = item["settings"]

                start_node: Node = self._node_editor.find_node(settings["origin"])
                end_node: Node = self._node_editor.find_node(settings["destination"])

                if start_node is None or end_node is None:
                    print(f"INVALID IDS : {settings}")
                    continue

                vein = self._node_editor.add_vein(item["_id"], start_node, end_node)
                vein.attach_callback(self.__add_vein_window)

