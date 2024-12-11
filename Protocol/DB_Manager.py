import sqlite3


class DatabaseManager:
    def __init__(self, db_name):
        self.db_name: str = db_name
        self.varbinary_max_len = 100000

    def create_tables(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS Users (
                            id INTEGER PRIMARY KEY,
                            user_name TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            );
                        """)

        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS Permissions (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            );
                        """)

        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS Projects (
                            id INTEGER PRIMARY KEY,
                            owner_id INTEGER UNIQUE NOT NULL,
                            nodes INTEGER NOT NULL,
                            veins INTEGER NOT NULL,
                            permission INTEGER UNIQUE NOT NULL,
                            settings VARBINARY({self.varbinary_max_len}) NOT NULL,
                            );
                        """)

        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS Veins (
                            id INTEGER PRIMARY KEY,
                            permission INTEGER UNIQUE NOT NULL,
                            vein_data VARBINARY({self.varbinary_max_len}) NOT NULL,
                            settings VARBINARY({self.varbinary_max_len}) NOT NULL,
                            );
                        """)

        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS Nodes (
                            id INTEGER PRIMARY KEY,
                            permission INTEGER UNIQUE NOT NULL,
                            settings VARBINARY({self.varbinary_max_len}) NOT NULL,
                            );
                        """)

        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS Files (
                            id INTEGER PRIMARY KEY,
                            node_id INTEGER NOT NULL,
                            permission INTEGER UNIQUE NOT NULL,
                            file VARBINARY({self.varbinary_max_len}) NOT NULL,
                            settings VARBINARY({self.varbinary_max_len}) NOT NULL,
                            );
                        """)

        connection.commit()
        connection.close()

    def add_user(self, user_name, password):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute('''
                    INSERT INTO Users (user_name, password) VALUES (?,?)
                    ''', (user_name, password))

        connection.commit()
        connection.close()


if __name__ == "__main__":
    pass
