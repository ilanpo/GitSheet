
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

    def add_to_permission(self, project_name, user_id):
        query = {"name": project_name}
        perms = None
        for x in self.projects_col.find_one(query, {"_id": 0, "permission": 1}):
            print(x)
        if perms:
            perms = set(perms)
            perms.add(user_id)
            perms = list(perms)
            x = self.projects_col.update_one(query, {"$set": {"permission": perms}})
            return x.acknowledged
        return False

    """def new_vein(self, project_id, permission: list, vein_data: str, settings: dict):
        ins_info = self.veins_col.insert_one({"permission": permission, "vein_data": vein_data, "settings": settings})
        vein_id = ins_info.inserted_id
        project_update_info = """



if __name__ == "__main__":
    DB = DatabaseManager("mongodb://localhost:27017/")
    Success, user_id = DB.new_user("dish11111", "Roblox")
    print(DB.new_project("zov3333", user_id, {}, ["hello"]))
    print(DB.add_to_permission("zov3333", user_id))

