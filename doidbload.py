import sqlite3
from sqlite3 import Error
import urllib.request

def loaddb():
    BASE_URL = 'http://dx.doi.org/'
    doifile = "MagBio.doi"
    try:
        conn = sqlite3.connect('doidb.db')
        bibfile = doifile.split(".")[0] + ".txt"
        with open(doifile) as dois:
            for line in dois:
                if "doi.org" in line:
                    line = line.split(".org/")[1]
                url = BASE_URL + line
                print(url, end=" JSON ")
                req = urllib.request.Request(url)
                req.add_header('Accept', 'application/json')
                try:
                    print("Connecting!")
                    with urllib.request.urlopen(req, timeout=15) as f:
                        jsonbruto=f.read()
                    sql ='insert into doi(url,json) values(?,?)'
                    cur =conn.cursor()
                    cur.execute(sql,((''.join(url.splitlines())),jsonbruto))
                    conn.commit()
                except Exception as e:
                    print(str(e))
    finally:
        if conn:
            conn.close()

def get_json(url):
    conn = sqlite3.connect('doidb.db')
    cursor=conn.execute('select json from doi where url=?',(url))
    for fila in cursor:
        print(fila)
    return fila

loaddb()