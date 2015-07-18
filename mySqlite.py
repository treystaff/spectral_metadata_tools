import sqlite3


class mySqlite:
    # Define what happens on class initialization
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

    def query(self, query, *args):
        if args and len(args) == 1:
            if isinstance(args[0], list) or isinstance(args[0], tuple):
                self.cursor.execute(query, list(args[0]))
            else:
                self.cursor.execute(query, [args[0]])
        elif args and len(args) > 1:
            # Treat the other args as the list of query values
            self.cursor.execute(query, list(args))
        else:
            # Just a raw query
            self.cursor.execute(query)

        # Return the result
        result = self.cursor.fetchall()
        return result  # a list of tuples

    def get_last_id(self):
        self.cursor.execute('SELECT last_insert_rowid()')
        id = self.cursor.fetchall()[0]
        return id

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
