import bson
from bson import ObjectId
import pymongo
from bson.binary import Binary
NAME_TAKEN_MESSAGE = "Failed to add document, Name already taken"


class DatabaseManager:
    def __init__(self, server_address):
        self.client = pymongo.MongoClient(server_address)
        file_name = "test.MOV"
        self.db = self.client["database"]
        self.users_col = self.db["Users"]
        self.projects_col = self.db["Projects"]
        self.veins_col = self.db["Veins"]
        self.nodes_col = self.db["Nodes"]
        self.files_col = self.db["Files"]

        """print(self.db.list_collection_names())
        with open(file_name, "rb") as file:
            encoded = Binary(file.read())
        self.users_col.insert_one({"filename": file_name, "file": encoded, "description": "test" })

        y = 0
        for x in self.users_col.find({},{"_id": 0,"file": 1}):
            with open(f"file_name{y}.MOV", "wb") as file:
                file.write(x["file"])
                y += 1"""

    def create_collections(self):
        pass

    def new_user(self, user_name: str, password: str):
        query = {"name": user_name}
        item = None
        for x in self.users_col.find(query, {"_id": 1}):
            item = x
        if item is not None:
            return False, NAME_TAKEN_MESSAGE
        ins_info = self.users_col.insert_one({"name": user_name, "password": password})
        return True, ins_info.inserted_id

    def new_project(self, name: str, owner_id: str, settings: dict, permission: list):
        query = {"name": name}
        item = None
        for x in self.projects_col.find(query, {"_id": 1}):
            item = x
        if item is not None:
            return False, NAME_TAKEN_MESSAGE
        ins_info = self.projects_col.insert_one(
            {"name": name, "owner_id": owner_id, "settings": settings,
             "permission": permission, "veins": [], "nodes": []})
        return True, ins_info.inserted_id

    def fetch_id(self, item_name: str, item_collection: str):
        query = {"name": item_name}
        item = None
        try:
            path_collection = {
                "projects": self.projects_col,
                "nodes": self.nodes_col,
                "veins": self.veins_col,
                "files": self.files_col,
                "users": self.users_col
            }

            selected_collection = path_collection[item_collection]
        except Exception as e:
            return False, e
        for k in selected_collection.find(query, {"_id": 1}):
            item = k

        if item:
            return True, item["_id"]
        else:
            return False, "Failed to fetch id, No such item"

    def push_to_dict(self, dict_id: bson.objectid.ObjectId, collection: str, operation: str, change, change_type: str):
        query = {"_id": dict_id}
        items = None
        found_data = None

        path_collection = {
            "projects": self.projects_col,
            "nodes": self.nodes_col,
            "veins": self.veins_col,
            "files": self.files_col
        }

        selected_collection = path_collection[collection]
        result = selected_collection.find_one(query, {})
        if result:
            found_data = result.get(change_type)

        if found_data is None or operation == "replace":
            items = change
            x = selected_collection.update_one(query, {"$set": {f"{change_type}": items}})
            return x.acknowledged

        if type(found_data) is not list:
            if found_data != change:
                items = [found_data, change]
            else:
                return True
        else:
            items = set(found_data)
            path_operation = {
                "add": items.add,
                "discard": items.discard
            }
            if operation not in path_operation:
                return False
            selected_operation = path_operation[operation]
            selected_operation(change)
            items = list(items)
        x = selected_collection.update_one(query, {"$set": {f"{change_type}": items}})
        return x.acknowledged

    def new_node(self, project_id, permission: list, node_data: list, settings: dict):
        ins_info = self.nodes_col.insert_one({"permission": permission, "node_data": node_data, "settings": settings,
                                              "files": []})
        node_id = ins_info.inserted_id
        success = self.push_to_dict(project_id, "projects", "add", node_id, "nodes")
        return node_id, success

    def new_vein(self, project_id, permission: list, vein_data: str, settings: dict):
        ins_info = self.veins_col.insert_one({"permission": permission, "vein_data": vein_data, "settings": settings})
        vein_id = ins_info.inserted_id
        success = self.push_to_dict(project_id, "projects", "add", vein_id, "veins")
        return vein_id, success

    def new_file(self, node_id, permission: list, file: bytes, settings: dict):
        ins_info = self.files_col.insert_one({"permission": permission, "file": file, "settings": settings})
        file_id = ins_info.inserted_id
        success = self.push_to_dict(node_id, "nodes", "add", file_id, "files")
        return file_id, success

    def remove_entry(self, entry_id, collection):
        path_collection = {
            "projects": self.projects_col,
            "nodes": self.nodes_col,
            "veins": self.veins_col,
            "files": self.files_col,
            "users": self.users_col
        }

        selected_collection = path_collection[collection]
        query = {"_id": entry_id}
        result = selected_collection.delete_one(query)
        return result

    def print_all_in_collection(self, collection: str):
        path_collection = {
            "projects": self.projects_col,
            "nodes": self.nodes_col,
            "veins": self.veins_col,
            "files": self.files_col,
            "users": self.users_col
        }

        selected_collection = path_collection[collection]
        for x in selected_collection.find({}, {}):
            print(x)

    def clear_all_in_collection(self, collection: str):
        path_collection = {
            "projects": self.projects_col,
            "nodes": self.nodes_col,
            "veins": self.veins_col,
            "files": self.files_col,
            "users": self.users_col
        }

        selected_collection = path_collection[collection]
        selected_collection.delete_many({}, {})

    def fetch_projects(self, user_id) -> list:
        projects = []

        for x in self.projects_col.find({}, {}):
            perms = x.get("permission")
            if type(perms) is list:
                if user_id in perms:
                    projects.append(x)
            else:
                if user_id == perms:
                    projects.append(x)

        return projects

    def fetch_veins_and_nodes(self, user_id, project_id):
        query = {"_id": project_id}

        veins_id = []
        nodes_id = []
        veins = []
        nodes = []

        for x in self.projects_col.find(query, {}):
            perms = x.get("permission")
            if type(perms) is list:
                if user_id in perms:
                    veins_id = x.get("veins")
                    nodes_id = x.get("nodes")
            else:
                if user_id == perms:
                    veins_id = x.get("veins")
                    nodes_id = x.get("nodes")

        if type(veins_id) is list:
            for x in veins_id:
                query = {"_id": x}
                z = self.veins_col.find_one(query)
                perms = z.get("permission")
                if type(perms) is list:
                    if user_id in perms:
                        veins.append(z)
                else:
                    if user_id == perms:
                        veins.append(z)
        else:
            query = {"_id": veins_id}
            z = self.veins_col.find_one(query)
            perms = z.get("permission")
            if type(perms) is list:
                if user_id in perms:
                    veins.append(z)
            else:
                if user_id == perms:
                    veins.append(z)

        if type(nodes_id) is list:
            for x in nodes_id:
                query = {"_id": x}
                z = self.nodes_col.find_one(query)
                perms = z.get("permission")
                if type(perms) is list:
                    if user_id in perms:
                        nodes.append(z)
                else:
                    if user_id == perms:
                        nodes.append(z)
        else:
            query = {"_id": nodes_id}
            z = self.nodes_col.find_one(query)
            perms = z.get("permission")
            if type(perms) is list:
                if user_id in perms:
                    nodes.append(z)
            else:
                if user_id == perms:
                    nodes.append(z)

        return veins, nodes

    def fetch_files(self, user_id, node_id):
        query = {"_id": node_id}
        files_id = []
        files = []

        for x in self.nodes_col.find(query, {}):
            perms = x.get("permission")
            if type(perms) is list:
                if user_id in perms:
                    files_id = x.get("files")
            else:
                if user_id == perms:
                    files_id = x.get("files")

        if type(files_id) is list:
            for x in files_id:
                query = {"_id": x}
                z = self.files_col.find_one(query)
                perms = z.get("permission")
                if type(perms) is list:
                    if user_id in perms:
                        files.append(z)
                else:
                    if user_id == perms:
                        files.append(z)

        else:
            query = {"_id": files_id}
            z = self.files_col.find_one(query)
            perms = z.get("permission")
            if type(perms) is list:
                if user_id in perms:
                    files.append(z)
            else:
                if user_id == perms:
                    files.append(z)

        return files


if __name__ == "__main__":
    pass

    #DB = DatabaseManager("mongodb://localhost:27017/")
    #DB.clear_all_in_collection("files")
    #bool, proj_id = DB.fetch_id("GitSheet", "projects")
    #print(DB.fetch_veins_and_nodes("123", proj_id))
    #DB.new_project("GitSheet", "123", {"hi": "hello"}, ["123"])
    #bool, proj_id = DB.fetch_id("GitSheet", "projects")
    #node_idd, Success1 = DB.new_node(proj_id, ["123"], ["Important info"], {"hi": "bye"})
    #print(DB.fetch_veins_and_nodes("123", ObjectId("67a8ee274a8273e4c778beb2")))
    #file_idd, Success2 = DB.new_file(node_idd, ["123"], b"1001", {"default": "settings"})
    #print(Success)
    #DB.push_to_dict(proj_id, "projects", "add", "4321", "permission")
    #DB.print_all_in_collection("nodes")
    #print(DB.fetch_files("123", node_idd))
    #print(DB.remove_entry(proj_id, "projects"))
