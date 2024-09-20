"""
Utils for storage related activitie - MySQLManager
"""

import warnings
import mysql.connector

WARNING_MESSAGE = 'cursor object not found'


def _handle_bytes(results):
    for index in results:
        for result in results[index]:
            for key in result.keys():
                if isinstance(key, bytes):
                    decoded_key = key.decode('utf-8')
                    result[decoded_key] = result[key]
                    if decoded_key != key:
                        del result[key]
    return results


def mysqlcursor(method):
    """Decorator function to maintain mysql connections.

    Instance of MySqlConnection / cursor object is passed in keyword arguments
    """
    required_kws = ['host', 'user', 'password', 'database']

    def inner(*args, **kw):
        """Wrapper method for creating connection objects."""
        if not kw:
            raise ValueError('no keyword arguments passed')
        for kwarg in required_kws:
            if kwarg not in kw:
                raise ValueError('%s is missing in keyword arguments' % kwarg)
        cnx = None
        try:
            cnx = mysql.connector.connect(**kw)
            cursor = cnx.cursor()
            kw['cursor'] = cursor
            result = method(*args, **kw)
            cursor.close()
            cnx.commit()

            return result
        finally:
            if cnx:
                cnx.close()

    return inner


class MySQLManager(object):

    @staticmethod
    @mysqlcursor
    def call_proc(proc_name, args, **kw):
        """Calls stored procedure and returns a dictionary of results.

        :param proc_name:
            the name of stored procedure to execute
        :type proc_name:
            str
        :param args: arguments of the stored procedure. args should be in tuple
                     Example: ('arg1', 'arg2', ...)
        :type args:
            tuple|list|enumerator
        :returns: a dictionary of results with each result containing a list of
                  dictionaries <column_name> vs <column_value> of that row
                  Example: [{
                      'col1': 'row1col1val',
                      'col2': 'row1col2val',
                      ...
                    }, {
                      'col1': 'row2col1val',
                      'col2': 'row2col2val',
                      ...
                    }, ...]
        """
        cursor = kw.get('cursor')
        if not cursor:
            raise UserWarning(WARNING_MESSAGE)
        results = {}
        cursor.callproc(proc_name, args)
        stored_results = cursor.stored_results()
        for index, result in enumerate(stored_results):
            rows = result.fetchall()
            results[index] = []
            for row in rows:
                results[index].append(dict(zip(result.column_names, row)))
        return _handle_bytes(results)

    @staticmethod
    @mysqlcursor
    def execute_query(query, args, **kw):
        """Executes query and returns a dictionary of results.

        :param query:
            the query to execute
        :type query:
            str
        :param args: arguments for the query. args should be in tuple
                     Example: ('arg1', 'arg2', ...)
        :type args:
            tuple|list|enumerator
        :returns: a list of dictionaries <column_name> vs <column_value> of that row
                  Example: [{
                      'col1': 'row1col1val',
                      'col2': 'row1col2val',
                      ...
                    }, {
                      'col1': 'row2col1val',
                      'col2': 'row2col2val',
                      ...
                    }, ...]
        """
        cursor = kw.get('cursor')
        if not cursor:
            raise UserWarning(WARNING_MESSAGE)
        cursor.execute(query, args)
        results = []
        rows = cursor.fetchall()
        for row in rows:
            results.append(dict(zip(cursor.column_names, row)))
        for result in results:
            for key in result.keys():
                if isinstance(key, bytes):
                    decoded_key = key.decode('utf-8')
                    result[decoded_key] = result[key]
                    if decoded_key != key:
                        del result[key]
        return results

    @staticmethod
    @mysqlcursor
    def execute_multi(query, args, **kw):
        """Executes multi query and returns a dictionary of results if any.

        :param query:
            the query to execute
        :type query:
            str
        :param args: arguments for the query. args should be in tuple
                     Example: ('arg1', 'arg2', ...)
        :type args:
            tuple|list|enumerator
        :returns: a list of dictionaries <column_name> vs <column_value> of that row
                  Example: [{
                      'col1': 'row1col1val',
                      'col2': 'row1col2val',
                      ...
                    }, {
                      'col1': 'row2col1val',
                      'col2': 'row2col2val',
                      ...
                    }, ...]
        """
        cursor = kw.get('cursor')
        if not cursor:
            raise UserWarning(WARNING_MESSAGE)
        results = []
        for result in cursor.execute(query, args, multi=True):
            if result.with_rows:
                query_results = []
                rows = result.fetchall()
                for row in rows:
                    query_results.append(dict(zip(result.column_names, row)))
                results.append(query_results)
            else:
                results.append(result.rowcount)
        return results

    @staticmethod
    @mysqlcursor
    def insert(table, data, **kw):
        """Executes insert query and returns the lastrow id if id is AUTO_INCREMENT and not passed in the data.

        :param table:
            name of the table for insert
        :type table:
            str
        :param data: data to be inserted in the table. arg should be a dict
                     Example: {'id': 1, 'val': '1'}
        :type data:
            dict
        :returns: last row id
        """
        cursor = kw.get('cursor')
        if not cursor:
            raise UserWarning(WARNING_MESSAGE)
        if not data:
            return None
        query = ('INSERT INTO ' + table + '(' + ','.join(data.keys()) + ') ' 'values(')
        for key in data:
            query += '%(' + key + ')s,'
        query = query.rstrip(',') + ')'
        cursor.execute(query, data)
        return cursor.lastrowid

    @staticmethod
    @mysqlcursor
    def bulk_insert(table, cols, data, **kw):
        """Executes query and returns a dictionary of results.

        :param table:
            name of the table for bulk insert
        :type table:
            str
        :param cols: column names. arg should be in list
                        Example: ['col1', 'col2']
        :type cols:
            tuple|list|enumerator
        :param data: data to be inserted in the table. arg should be a dict
                    Example: {
                        data = []
                        data.append({'id': 1, 'val': '1'})
                        data.append({'id': 2, 'val': '2'})
                        data.append({'id': 3, 'val': '3'})
                    }
        :type data:
            `list` of `dict`s
        :returns: number of rows inserted
        """
        cursor = kw.get('cursor')
        if not cursor:
            raise UserWarning(WARNING_MESSAGE)
        insert_query = ("INSERT INTO " + table + " (" + ",".join(cols) + ") "
                        "VALUES(" + ",".join(["%s"] * len(cols)) + ")")
        values = [tuple(row.get(col) for col in cols) for row in data]
        cursor.executemany(insert_query, values)
        return cursor.rowcount

    @staticmethod
    @mysqlcursor
    def update(table, data, conditional_data, **kw):
        """Executes update query and returns the no of rows affected

        :param table:
            name of the table for update
        :type table:
            str
        :param data: data to be updated in the table. arg should be a dict
                     Example: {'id': 1, 'val': '1'}
        :type data:
            dict
        :param conditional_data: on which condition should the update statement to be executed
                    Example: {'id': 0}
        :type conditional_data:
            dict
        :returns: no of rows updated
        """
        cursor = kw.get('cursor')
        if not cursor:
            raise UserWarning(WARNING_MESSAGE)
        if not data:
            return None
        query = 'UPDATE ' + table + ' SET '
        for key in data.keys():
            query += key + ' = (%(' + key + ')s),'
        query = query.rstrip(',') + ' WHERE '
        conditional_keys = list(conditional_data.keys())
        for key in conditional_keys:
            query += key + ' = (%(' + key + '1)s) AND '
            conditional_data[key + '1'] = conditional_data[key]
            del conditional_data[key]
        query = query.rstrip('AND ')
        data.update(conditional_data)
        cursor.execute(query, data)
        return cursor.rowcount