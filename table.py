#!/usr/bin/python3



class Table (object):
    """Implements a generic table and some methods to operate on one.
    These will be inherited by other classes.

    The basic concept is that you create a subclass of this class,
    then define the actual SQL statements in place of the ones defined
    below.  The dataSize variable defines the number of variables that
    should be expected by the getId method

    """

    dataSize = 1
    getId_select = {"SQLite3" : "SELECT id FROM foo WHERE foo = ?",
                    "PG"      : "SELECT id FROM foo WHERE foo = %s"}
    getId_insert = {"SQLite3" : "INSERT INTO foo (foo) VALUES (?)",
                    "PG"      : "INSERT INTO foo (foo) VALUES (%s)"}

    getId_currval = {
        "PG" : "SELECT CURRVAL('foo_seq')"
    }

    createTable_list = {
        "SQLite3" : [
            "CREATE TABLE IF NOT EXISTS foo (id INTEGER PRIMARY KEY AUTOINCREMENT, foo TEXT)",
            "CREATE INDEX IF NOT EXISTS foo_idx ON foo(foo)"
        ],
        "PG" : [
            "CREATE SEQUENCE IF NOT EXISTS foo_seq",
            "CREATE TABLE IF NOT EXISTS foo (id INTEGER PRIMARY KEY NOT NULL DEFAULT NEXTVAL('foo_seq'), foo TEXT)",
            "CREATE INDEX IF NOT EXISTS foo_idx ON foo(foo)"
        ]
    }

    dropTable_list = {
        "SQLite3" : [
            "DROP INDEX IF EXISTS foo_idx",
            "DROP TABLE IF EXISTS foo"
        ],
        "PG" : [
            "DROP INDEX IF EXISTS foo_idx",
            "DROP TABLE IF EXISTS foo",
            "DROP SEQUENCE IF EXISTS foo_seq"
        ]
    }

    getById_select = {
        "SQLite3 " : "SELECT foo FROM foo WHERE id = ?",
        "PG"       : "SELECT foo FROM foo WHERE id = %d"
    }
    
    def __init__(self, dbh, dbType = "SQLite3", readOnly = False, create = False, reset = False, verbose = False):
        """Sets up a Table object.  Put a reference to the database handle and
        the read-only flag on the object as parameters.  If warranted,
        drop and/or create the table by calling the relevant methods.

        """
        self.verbose = verbose
        
        self.dbh = dbh
        self.readOnly = readOnly

        if (dbType not in ["SQLite3", "PG"]):
            raise NotImplementedError("dbType %s is not supported.")
        self.dbType = dbType

        if (reset):
            create = True
            self.dropTable()

        if (create):
            self.createTable()

    def getId (self, *data):
        """Gets an ID for a value, come hell or high water.  If there is a
        record that matches the data, the ID of that record is
        returned.  If not, and readOnly is False, then it will insert
        a new record with the given data and then return the ID of the
        new record.  If readOnly is True and the record is not found,
        returns None.
        """
        
        if (len(data) != self.dataSize):
            raise TypeError("getId is expecting %d arguments and got %d." %(self.dataSize, len(data)))

        cursor = self.dbh.cursor()
        rowId = None

        cursor.execute(self.getId_select[self.dbType], data)
        result = cursor.fetchone()

        if (self.readOnly and (result is None)):
            return None
        elif (result is None):
            cursor.execute(self.getId_insert[self.dbType], data)
            if (self.dbType == "SQLite3"):
                rowId = cursor.lastrowid
            elif (self.dbType == "PG"):
                cursor.execute (self.getId_currval[self.dbType], [])
                result = cursor.fetchone()
                rowid = result[0]
        else:
            rowId = result[0]

        return rowId

    def getById(self, rowId):
        """Retrieves a row from the database by its ID.  Returned row does not
        ideally contain the ID field, but can do just by changing the
        getByID_select variable above.

        """
        
        cursor = self.dbh.cursor()
        cursor.execute(self.getById_select[self.dbType], (rowId,))
        return cursor.fetchone()
        
    def createTable (self):
        """Creates the table and anything that needs to go with it by stepping
        through the commands stored in the createTable_list variable
        above or in a class that inherits this method.

        """
        cursor = self.dbh.cursor()
        for command in self.createTable_list[self.dbType]:
            cursor.execute(command)

    def dropTable (self):
        """Drops the table and anything that goes with it by stepping through
        the commands stored in the dropTable_list variable above or in
        a class that inherits this method.

        """
        cursor = self.dbh.cursor()
        for command in self.dropTable_list[self.dbType]:
            cursor.execute(command)

