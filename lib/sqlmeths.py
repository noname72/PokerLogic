import sqlite3
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def connect(file):
    if isinstance(file, Path): file = str(file)
    try:
        con = sqlite3.connect(file)
        yield con
        con.commit()
        con.close()
    except sqlite3.Error as err:
        yield print(err)

def safetywrapper(fun):
    def retfun(dbfile, *args, **kwargs):
        try:
            with connect(dbfile) as con:
                ret = fun(con, *args, **kwargs)
                return ret if ret is not None else True
        except sqlite3.Error as e:
            print(e)
    return retfun

@safetywrapper
def executesql(con, *sqls):
    for sql in sqls: con.cursor().execute(sql)

@safetywrapper
def insert(con, table, **vals):
    strkeys = map(str, vals.keys())
    sql = f'''INSERT INTO {table}({', '.join(strkeys)})
              VALUES({', '.join(['?'] * len(vals))})'''
    con.cursor().execute(sql, tuple(vals.values()))

@safetywrapper
def update(con, table, valsdic, wheredic):
    vals = ', '.join([f'{key}=?' for key in valsdic])
    where = ', '.join([f'{key}=?' for key in wheredic])
    sql = f'''UPDATE {table}
              SET {vals}
              WHERE {where}'''
    con.cursor().execute(sql, tuple(valsdic.values()) +
                              tuple(wheredic.values()))

@safetywrapper
def deletefromtable(con, table, wheredic):
    where = ', '.join([f'{key}=?' for key in wheredic])
    sql = f'DELETE FROM {table} WHERE {where}'
    con.cursor().execute(sql, tuple(wheredic.values()))
@safetywrapper
def emptytable(con, table):
    con.cursor().execute(f'DELETE FROM {table}')

@safetywrapper
def getcol(con, table, colname):
    cur = con.cursor()
    cur.execute(f'SELECT {colname} FROM {table}')
    return cur.fetchall()

@safetywrapper
def getasdict(con, table, idname, idval):
    cur = con.cursor()
    cur.execute(f'PRAGMA table_info({table})')
    keys = map(lambda l: l[1], cur.fetchall())
    cur.execute(f'SELECT * FROM {table} WHERE {idname}=?', (idval,))
    vals = cur.fetchall()
    if len(vals) == 1: return dict(tuple(zip(keys, vals[0])))
    else: return {}

@safetywrapper
def getasdicts(con, table, key, value, wheredic):
    formatted = ', '.join([f'{wkey}=?' for wkey in wheredic])
    sql = f'SELECT {key}, {value} FROM {table} WHERE {formatted}'
    cur = con.cursor()
    cur.execute(sql, tuple(wheredic.values()))
    return dict(cur.fetchall())
