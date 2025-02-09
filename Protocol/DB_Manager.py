import bson
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

        # TEMPORARY AUTOMATIC CLEAR
        """x = self.projects_col.delete_many({})
        print(x.deleted_count, " documents deleted.")"""

        """print(self.db.list_collection_names())
        with open(file_name, "rb") as file:
            encoded = Binary(file.read())
        self.users_col.insert_one({"filename": file_name, "file": encoded, "description": "test" })

        y = 0
        for x in self.users_col.find({},{"_id": 0,"file": 1}):
            with open(f"file_name{y}.MOV", "wb") as file:
                file.write(x["file"])
                y += 1"""

        """for x in self.projects_col.find({}, {"file": 0}):
            print(x)"""

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
            {"name": name, "owner_id": owner_id, "settings": settings, "permission": permission, "veins": [], "nodes": []})
        return True, ins_info.inserted_id

    # OBSOLETE use push to dict with collection as "projects" and operation as "add" instead.
    """def add_to_permission(self, project_id, userid):
        query = {"_id": project_id}
        perms = None
        for in self.projects_col.find_one(query, {"_id": 0, "permission": 1}):
            perms = x
        if perms:
            perms = set(perms)
            perms.add(userid)
            perms = list(perms)
            x = self.projects_col.update_one(query, {"$set": {"permission": perms}})
            return x.acknowledged
        return False"""

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
        except:
            return False, "Failed to fetch id, No such collection"
        for k in selected_collection.find(query, {"_id": 1}):
            item = k

        if item:
            return True, item
        else:
            return False, "Failed to fetch id, No such item"

    def push_to_dict(self, dict_id: bson.objectid.ObjectId, collection: str, operation: str, change, change_type:str):
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
        result = selected_collection.find_one(query,{"_id": 0, f"{change_type}": 1})
        if result:
            found_data = result.get(change_type)

        if found_data is None:
            items = change
            x = selected_collection.update_one(query, {"$set": {f"{change_type}": items}})
            return x.acknowledged

        if type(found_data) is not list:
            items = [found_data, change]
        else:
            items = set(found_data)
            path_operation = {
                "add": items.add,
                "remove": items.discard
            }
            selected_operation = path_operation[operation]
            selected_operation(change)
            items = list(items)
        x = selected_collection.update_one(query, {"$set": {f"{change_type}": items}})
        return x.acknowledged

    def new_node(self, project_id, permission: list, node_data: list, settings: dict):
        ins_info = self.nodes_col.insert_one({"permission": permission, "node_data": node_data, "settings": settings})
        node_id = ins_info.inserted_id
        self.push_to_dict(project_id, "projects", "add", node_id, "nodes")
        return node_id

    def new_vein(self, project_id, permission: list, vein_data: str, settings: dict):
        ins_info = self.veins_col.insert_one({"permission": permission, "vein_data": vein_data, "settings": settings})
        vein_id = ins_info.inserted_id
        self.push_to_dict(project_id, "projects", "add", vein_id, "veins")
        return vein_id

    def new_file(self, node_id, permission: list, file: bytes, settings: dict):
        ins_info = self.files_col.insert_one({"permission": permission, "file": file, "settings": settings})
        file_id = ins_info.inserted_id
        self.push_to_dict(node_id, "nodes", "add", file_id, "file")


if __name__ == "__main__":
    DB = DatabaseManager("mongodb://localhost:27017/")
    #DB.new_project("GitSheet", "123", {"hi": "hello"}, ["123"])
    bool, proj_id = DB.fetch_id("GitSheet", "projects")
    print(proj_id["_id"])
    node_id = DB.new_node(proj_id["_id"], ["stuff"], ["python", "other stuff"], {"hi": "bye"})





