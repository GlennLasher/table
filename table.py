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
    getId_insert = None
    getId_currval = None

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

    insertRow_insert = {"SQLite3" : "INSERT INTO foo (foo) VALUES (?)",
                        "PG"      : "INSERT INTO foo (foo) VALUES (%s)"}

    currval = {
        "PG" : "SELECT CURRVAL('foo_seq')"
    }

    updateRow_update = {"SQLite3" : "UPDATE foo SET foo = ? WHERE id = ?",
                        "PG"      : "UPDATE foo SET foo = %s WHERE id = %d"}

    deleteRow_delete = {"SQLite3" : "DELETE FROM foo WHERE id = ?",
                        "PG"      : "DELETE FROM foo WHERE id = %d"}

    def __init__(self, dbh, dbType = "SQLite3", readOnly = False, create = False, reset = False, verbose = False):
        """Sets up a Table object.  Puts database handle and type, and
        readOnly/verbose properties onthe object.

        dbh is a connection to the database.

        dbType is either SQLite3 or PG to indicate SQLite3 or
        PostgreSQL, respectively

        readOnly, if True, will prevent any writes to the database via this object.

        create, if True, will cause the table and related objects to
        be created by calling createTable().  It is expected that the
        CREATE TABLE and CREATE INDEX statements, and any others
        called by createTable(), contain an IF NOT EXISTS clause so
        that they will silently abort if the objects already exist.

        reset, if True, will cause the table and related objects to be
        deleted by calling dropTable().  In complement to createTable,
        it is expected that the DROP TABLE and DROP INDEX statements,
        and any others called by dropTable(), contain an IF EXISTS
        clause so that they will silently abort if the objects do not
        exist.

        verbose, if True, will enable debugging messages to be written
        to stdout.  You can use this in your derived classes as you
        see fit.

        """

        #Plain object properties
        
        self.verbose = verbose
        self.dbh = dbh
        self.readOnly = readOnly

        #Manage legacy

        if self.getId_insert is not None:
            self.insertRow_insert = self.getId_insert

        if self.getId_currval is not None:
            self.currval = self.getId_currval
        
        #Manage bad DB types
        
        if (dbType not in ["SQLite3", "PG"]):
            raise NotImplementedError("dbType %s is not supported.")
        self.dbType = dbType

        #Optional automatic DB object creation
        
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
            rowId = self.insertRow(*data)
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

    def insertRow (self, *data):
        """Takes a data tuple and adds a row to the table containing that
        tuple, similar to getId.  Unlike getId, it does not first check to see
        if there is an existing row, so duplicate rows become possible."""

        if (self.readOnly):
            return None
        
        if (len(data) != self.dataSize):
            raise TypeError("insertRow is expecting %d arguments and got %d." %(self.dataSize, len(data)))

        cursor = self.dbh.cursor()
        rowId = None

        cursor.execute(self.insertRow_insert[self.dbType], data)
        if (self.dbType == SQLite3):
            rowId = cursor.lastrowid
        elif(self.dbType = "PG"):
            cursor.execute(self.currval[self.dbType], [])
            result = cursor.fetchone()
            rowId = result[0]
            
        return rowId

    def updateRow (self, rowId, *data):
        """Takes a rowId and a data tuple, updates all of the values in the
        row to those in the tuple"""

        if (self.readOnly):
            raise NotImplementedError("Writing to read-only tables is not yet (and probably won't be) implemented.")

        if (len(data) != self.dataSize):
            raise TypeError("getId is expecting %d arguments and got %d." %(self.dataSize, len(data)))

        cursor = self.dbh.cursor()
        cursor.execute (self.updateRow_update[self.dbType], data + [rowId])

    def deleteRow(self, rowId):
        """Takes a rowId and deletes the row"""

        if (self.readOnly):
            raise NotImplementedError("Writing to read-only tables is not yet (and probably won't be) implemented.")

        cursor = self.dbh.cursor()
        cursor.execute(self.deleteRow_delete[self.dbType], (rowId,))
        
