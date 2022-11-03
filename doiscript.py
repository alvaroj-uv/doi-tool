import sys
import urllib.request
from json import loads
import sqlite3
import re
import html
def get_json(url):
    conn = sqlite3.connect('doidb.db')
    vurl=''.join(url.splitlines())
    cursor=conn.execute('select json from doi where url=?',(vurl,))
    for fila in cursor:
        return fila[0]

BASE_URL = 'http://dx.doi.org/'

samplebib = """
@article{Frank_1970,
	doi = {10.1126/science.169.3946.635},
	url = {https://doi.org/10.1126%2Fscience.169.3946.635},
	year = 1970,
	month = {aug},
	publisher = {American Association for the Advancement of Science ({AAAS})},
	volume = {169},
	number = {3946},
	pages = {635--641},
	author = {Henry S. Frank},
	title = {The Structure of Ordinary Water},
	journal = {Science}
}
"""


class author:
    def __init__(self, name, lastname,first):
        self.name = name
        self.lastname = lastname
        self.first = first


class publicacion:
    def __init__(self, title, doi):
        def clean(vtitle):
            if len(vtitle)>0:
                vtitle = html.unescape(vtitle)
                vtitle = re.compile(r'<[^>]+>').sub('', vtitle)
                return ' '.join(str(vtitle).replace('\n', ' ').replace('\r', '').split())
            return ''
        self.authors = []
        self.doi = clean(doi)
        self.title = clean(title)
        self.vol = ''
        self.issn = ''
        self.journal = ''
        self.anno = ''
        self.impact=''
        self.found=False

    def add_authors(self, authorlist):
        for nn in authorlist:
            firstauthor=False
            try:
                if (nn.get('given')!=None) or (nn.get('family')!=None):
                    if (nn.get('sequence') != None):
                        if (nn['sequence'] == 'first'):
                            firstauthor = True
                    if (nn.get('given')!=None) and (nn.get('family')!=None):
                        autor = author(nn['given'], nn['family'],firstauthor)
                    elif nn.get('family')!=None:
                        autor = author('',nn['family'],firstauthor)
                    elif nn.get('given')!=None:
                        autor = author(nn['given'], '',firstauthor)
                    else:
                        autor = 'Unresolved'
            except Exception as e:
                print(str(e) + " - Error en author!")
            self.authors.append(autor)

    def get_autorlist(self):
        autlista = []
        for a in self.authors:
            aut = a.lastname
            if len(a.lastname)>0 and len(a.name)>0:
                aut = a.lastname + ' ' + ''.join([x[0] for x in a.name.split(' ')])
            autlista.append(aut)
        return ', '.join(autlista)

    def getstrtoprint(self):
        return self.get_autorlist() + '|' + self.anno + '|' + self.title + '|' + self.journal + '|' + self.vol + '|' + self.doi + '|' + "Publicada"+'|'+self.issn+'|'+self.impact

def journal_issn_search(journalissn):
    conn = sqlite3.connect('doidb.db')
    if len(journalissn)==1:
        cursor=conn.execute('select w.ISSN,ifnull(w.IF_2022,0) if_2022,w.JIF_Quartile from WOS w where w.EISSN=? or w.ISSN=? or w.EISSN=? or w.ISSN=?',(json["ISSN"][0],json["ISSN"][0],json["ISSN"][0],json["ISSN"][0]))
    else:
        cursor = conn.execute('select w.ISSN,ifnull(w.IF_2022,0) if_2022,w.JIF_Quartile from WOS w where w.EISSN=? or w.ISSN=? or w.EISSN=? or w.ISSN=?',(json["ISSN"][1],json["ISSN"][1],json["ISSN"][0],json["ISSN"][0]))
    for fila in cursor:
        return fila[0],fila[1],fila[2]
    print("ISSN Not in DB")
    return "X-X", 0.0, 'n/a'


# script

if len(sys.argv) > 1:
    doifile = sys.argv[1]
else:
    doifile = "MagBio.doi"
bibfile = doifile.split(".")[0] + ".txt"
outpubz = []

with open(doifile) as dois:
    for line in dois:
        if "doi.org" in line:
            line = line.split(".org/")[1]
        url = BASE_URL + line
        print(url)
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        try:
            print("Connecting!")
            try:
                json = loads(get_json(url).decode("utf-8"))
                print("Response from db")
            except Exception as e:
                print(str(e))
                try:
                    with urllib.request.urlopen(req, timeout=15) as f:
                        json = loads(f.read().decode("utf-8"))
                    print("Response from  web")
                except Exception as e:
                    print(str(e))
            pub = publicacion(json["title"], url)
            pub.add_authors(json['author'])
            try:
                vol = ""
                if 'volume' in json.keys():
                    vol = json["volume"]
                if 'page' in json.keys():
                    vol = vol + ':' + json["page"]
                elif 'issue' in json.keys():
                    vol = vol + '(' + json["issue"] + ')'
                pub.vol = vol
                pub.issn = json["ISSN"]
                pub.anno = str(json['published']['date-parts'][0][0])
                pub.journal = json["container-title"]
                print("Publication - OK!")
            except Exception as e:
                print(str(e)+" - Error!")
            if pub:
                issn, impact, Q = journal_issn_search(pub.issn)
                pub.issn=str(issn)
                pub.impact=f'{impact:.3f} ({Q})'
                pub.found=True
                outpubz.append(pub)
                print(pub.get_autorlist())
            else:
                print(pub.title, "No encontrado")
            print(pub.title)
        except Exception as e:
            print(str(e))
with open('./t-' + bibfile, "w", encoding="utf-8") as wbib:
    for b in outpubz:
        if b.found:
            wbib.write(b.getstrtoprint() + '\n')
