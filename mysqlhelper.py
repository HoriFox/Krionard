import pymysql

class DBConnection:
    def __init__(self, **kwargs):
        self.connect = pymysql.connect(**kwargs)

    def __del__(self):
        self.connect.close()

    def insert(self, table, is_replace = False, timestamp = None, **kwargs):
        try:
            cursor = self.connect.cursor()
            placeholders = ', '.join(['%s'] * len(kwargs))
            columns = ', '.join(kwargs.keys())
            query = "INSERT INTO %s (%s) VALUES (%s)" % (table, columns, placeholders)
            if is_replace:
                placeholders_update = ', '.join('`{}`=VALUES(`{}`)'.format(key, key)
                                                 for key in list(kwargs.keys())[1:])
                if timestamp:
                    placeholders_update += ', `' + timestamp + '`=NOW()'
                query += "ON DUPLICATE KEY UPDATE %s" % (placeholders_update)
            cursor.execute(query, list(kwargs.values()))
        except pymysql.Error as err:
            print('Error', err)
        else:
            self.connect.commit()

    def select(self, table, where = None):
        try:
            cursor = self.connect.cursor()
            query = "SELECT * FROM %s" % (table)
            if where:
                where_part = ', '.join("`{}`='{}'".format(key, value) for (key, value) in list(where.items()))
                query += " WHERE %s" % (where_part)
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except pymysql.Error as err:
            print('Error', err)

