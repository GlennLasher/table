# Table

Abstract class to manage a database table

## What?

In handling database tables, I find this pattern repeating itself, so
I extracted it from another one of my projects and put it here.

## Why?

For easy importation and code reuse, of course!

## How?

### Background

First, you would generally not instantiate this class.  You can, but
it's not overly useful in and of itself.

So....

### Deriving a class from it

First, import it into a module where you're going to override some of
the properties.

    from table import Table

Next, there are some variables to override.

The simplest one is dataSize.  This is an int and is the number of
columns you're going to present when inserting a row into the table.

getId_select is a dict containing two str's, one keyed to "SQLite3"
and one keyed to "PG".  These are the SELECT statements to execute,
parameterized as appropriate to the sqlite3 and psycopg modules.

getId_insert is the same concept with the INSERT statement for getId.

getId_currval is only really used by PostgreSQL (because the relevant
mechanism differs from that of SQLite), however, it is still in her in
dict form, just in case I decided to add other database engines at a
later date.  It should contain a SQL statement that will retrieve the
current value of the sequence used to produce row IDs for this table.

createTable_list is a dict of lists, each list containing the commands
needed to create a given table and its accessories.

dropTable_list is a dict of lists, each list containing the commands
needed to drop a table and its accessories.

getById_select is a dict of str's, containing SELECT statements to
execute, parameterized as appropriate, to retrieve a record from the
table by its id.

For instance, here is the code for StatusTable taken out of my module
Bumddb, slightly updated to handle the multi-database capability:

    class StatusTable (Table):
        """Implements a table to hold the status of a backup.  This is based
        entirely on methods inherited from Table.
    
        """
    
        dataSize = 1
        getId_select = {
            "SQLite3" : "SELECT id FROM status_v1 WHERE status = ?",
            "PG"      : "SELECT id FROM status_v1 WHERE status = %s"
        }

        getId_insert = {
            "SQLite3" : "INSERT INTO status_v1 (status) VALUES (?)",
            "PG"      : "INSERT INTO status_v1 (status) VALUES (%s)",
        }

        createTable_list = {
            "SQLite3" : [
                "CREATE TABLE IF NOT EXISTS status_v1 (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT)",
                "CREATE INDEX IF NOT EXISTS status_v1_idx ON status_v1(status)"
            ],
            "PG" : [
                "CREATE SEQUENCE IF NOT EXISTS status_v1_seq",
                "CREATE TABLE IF NOT EXISTS status_v1 (id INTEGER PRIMARY KEY NOT NULL DEFAULT NEXTVAL(status_v1_seq), status TEXT)",
                "CREATE INDEX IF NOT EXISTS status_v1_idx ON status_v1(status)"
            ]
        }

    
        dropTable_list = {
            "SQLite3" : [
                "DROP INDEX IF EXISTS status_v1_idx",
                "DROP TABLE IF EXISTS status_v1"
            ],
            "PG" : [
                "DROP INDEX IF EXISTS status_v1_idx",
                "DROP TABLE IF EXISTS status_v1",
                "DROP SEQUENCE IF EXISTS status_v1_seq"
            ]
        }

       getById_select = {
           "SQLite3" : "SELECT status FROM status_v1 WHERE id = ?",
           "PG"      : "SELECT status FROM status_v1 WHERE id = %d"
       }

...and that's pretty much it.  You can also add more methods if you see fit.

### Then what?

Following the example of StatusTable above, you can do things like this:

    table = StatusTable(dbh, dbType = "SQLite3", readOnly = False, create  = False, reset = False, verbose = False)

This would instaniate a Table.  dbh is the database handle
(connection) generated by the connect() method of either sqlite3 or
psycopg.

Set dbType to either "SQLite3" or "PG".  It will default to "SQLite3".

readOnly defaults to False and if set to True will block any INSERT,
CREATE, UPDATE or DROP operations in the included methods.  If you add
your own methods, you should honour this in them.

create defaults to False.  If set to True, then \_\_init\_\_() will
automatically call createTable.  If the table is already there, then
this is non-destructive and can be helpful on the grounds that it will
automatically generate whatever objects are needed.  If you are aiming
to segregate administration from operation, however, you will want to
set this to False.

reset defaults to False.  If set to True, then \_\_init\_\_() will
automatically call dropTable.  **This is destructive!** \_\_init\_\_()
will also reset create to True if reset is True, so that the database
objects are automatically made ready after deleting them.

verbose defaults to False.  If set to True, then \_\_init\_\_() will
add this flag to the object.  As of this writing, the methods in this
module do not do anything with this, however, you can use it in any
way you like in your derived clases.  The intent is for it to cause
debug information to be sent to stdout.

    rowId = table.getId(datm [, datum [ . . . ]] )

This will attempt to look up a value or set of values in the table
that we are operating on.

If the row is found, then the row ID is returned.

If the row is not found and readOnly is False, a row will be
inserted, and the new row's ID will be returned.

If the row is not found and readOnly is True, getId will return None.

If the objective is to just make sure a record is present and you do
not care about where it is, you can simply not assign the return
value.

    table.getById(rowId)

This will attempt to look up a set of values for a (hopefully)
existing record by that record's rowId.  If it succeeds, it will
return the data as a tuple.  You can set up exactly how this works by
how you define the getById_select strings.

    table.createTable()

This will create the table and its associated database objects, such
as sequences and indices.  You probably don't need to call it directly
(just set create = True when you instantiate the object) but there is
no reason you can't.

    table.dropTable()

This will remove the table and its associated objects, such as
sequences and indices.  **This is destructive!**.  For most cases, you
won't need to do this, but this is the best way to remove a table from
a database permanently, as trying to do it by setting reset = True on
instantiation will just end up creating a new set of objects.

