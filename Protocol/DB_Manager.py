
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
        """x = self.users_col.delete_many({})
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
        x = self.users_col.find_one(query)
        if x:
            return False, NAME_TAKEN_MESSAGE
        ins_info = self.users_col.insert_one({"name": user_name, "password": password})
        return True, ins_info.inserted_id

    def new_project(self, name: str, owner_id: str, settings: dict, permission: list):
        query = {"name": name}
        x = self.users_col.find_one(query)
        if x:
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

        path_collection = {
            "projects": self.projects_col,
            "nodes": self.nodes_col,
            "veins": self.veins_col,
            "files": self.files_col
        }

        selected_collection = path_collection[item_collection]

        for k, v in selected_collection.find_one(query, {"_id": 1}):
            item = v

        if item:
            return True, item
        else:
            return False, None

    def push_to_dict(self, dict_id, collection: str, operation: str, change, change_type:str):
        query = {"_id": dict_id}
        items = None

        path_collection = {
            "projects": self.projects_col,
            "nodes": self.nodes_col,
            "veins": self.veins_col,
            "files": self.files_col
        }

        selected_collection = path_collection[collection]
        print(selected_collection)

        _idk = selected_collection.find_one(query, {"_id": 0, f"{change_type}": 1})
        print(_idk)
        if _idk is None:

        for k, v in _idk:
            items = v

        if items:
            items = set(items)
            path_operation = {
                "add": items.add,
                "remove": items.remove
            }

            selected_operation = path_operation[operation]
            selected_operation(change)
            items = list(items)
            x = selected_collection.update_one(query, {"$set": {f"{change_type}": items}})
            return x.acknowledged

        return False

    def new_node(self, project_id, permission: list, node_data: list, settings: dict):
        ins_info = self.nodes_col.insert_one({"permission": permission, "node_data": node_data, "settings": settings})
        node_id = ins_info.inserted_id
        self.push_to_dict(project_id, "projects", "add", node_id, "node")
        return node_id

    def new_vein(self, project_id, permission: list, vein_data: str, settings: dict):
        ins_info = self.veins_col.insert_one({"permission": permission, "vein_data": vein_data, "settings": settings})
        vein_id = ins_info.inserted_id
        self.push_to_dict(project_id, "projects", "add", vein_id, "vein")
        return vein_id

    def new_file(self, node_id, permission: list, file: bytes, settings: dict):
        ins_info = self.files_col.insert_one({"permission": permission, "file": file, "settings": settings})
        file_id = ins_info.inserted_id
        self.push_to_dict(node_id, )


if __name__ == "__main__":
    DB = DatabaseManager("mongodb://localhost:27017/")
    Success, user_id = DB.new_user("dish11111", "Roblox")
    id = DB.new_project("zov3333", user_id, {}, ["hello"])
    print(DB.push_to_dict(id, "projects", "add", user_id, "permission"))

