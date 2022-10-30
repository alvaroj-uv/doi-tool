import difflib as dl
import sys
import urllib.request
from json import loads

import numpy as np
import pandas as pd
import re

BASE_URL = 'http://dx.doi.org/'
JOURNALS = pd.read_csv("TodasUnique.csv")
JOURNALS["Journal name"] = JOURNALS["Journal name"].str.upper()

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
    def __init__(self, name, lastname):
        self.name = name
        self.lastname = lastname

class publicacion:
    def __init__(self, title,doi):
        def clean(vtitle):
            vtitle = re.compile(r'<[^>]+>').sub('', vtitle)
            return ' '.join(str(vtitle).replace('\n', ' ').replace('\r', '').split())
        self.authors=[]
        self.doi=clean(doi)
        self.title=clean(title)
        self.vol=''
        self.issn=''
        self.journal=''
        self.anno=''
    def add_authors(self,authorlist):
        for nn in authorlist:
            try:
                autor = author(nn['given'], nn['family'])
            except:
                autor = author(nn['given'], '')
            self.authors.append(autor)
    def get_autorlist(self):
        autlista=[]
        for a in self.authors:
            aut = a.lastname+' '+''.join([x[0] for x in a.name.split(' ')])
            autlista.append(aut)
        return ', '.join(autlista)

    def getstrtoprint(self):
        return self.get_autorlist()+'|'+self.anno+'|'+self.title+'|'+self.journal+'|'+self.vol+'|'+self.doi+'|'+"publicado"


def journalsearch(journalname):
    match = dl.get_close_matches(journalname, JOURNALS["Journal name"],n=1,cutoff=0.75)
    print("Matching", journalname, end=" ")
    if match:
        candidateRow = JOURNALS[JOURNALS["Journal name"] == match[0]]
        print("->", candidateRow["Journal name"].values[0])
        if candidateRow['ISSN'].values[0] is np.NAN:
            return candidateRow["eISSN"].values[0], round(candidateRow["2021 JIF"].values[0], 3),candidateRow['JIF Quartile'].values[0]
        else:
            return candidateRow["ISSN"].values[0], round(candidateRow["2021 JIF"].values[0], 3), candidateRow['JIF Quartile'].values[0]
    print("no match")
    return "X-X", 0.0, 'n/a'


# script

if len(sys.argv) > 1:
    doifile = sys.argv[1]
else:
    doifile = "PatricioOrio.doi"
bibfile = doifile.split(".")[0] + ".txt"
outpubz = []

with open(doifile) as dois:
    for line in dois:
        if "doi.org" in line:
            line = line.split(".org/")[1]
        url = BASE_URL + line
        print(url, end=" JSON ")
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=5) as f:
                json = loads(f.read().decode("utf-8"))
            pub=publicacion(json["title"],url)
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
                pub.year= json['published']['date-parts'][0][0]
                pub.journal=json["container-title"]
                print(" - OK!")
            except:
                print(" - Error!")
            if pub:
                issn, impact, Q = journalsearch(pub.journal.upper())
                #str(issn), f'{impact:.3f} ({Q})'
                outpubz.append(pub)
                print(pub.get_autorlist())
            else:
                print(pub.title, "No encontrado")
            print(pub.title)
        except:
            print('Help')
with open('./t-' + bibfile, "w", encoding="utf-8") as wbib:
    for b in outpubz:
        wbib.write(b.getstrtoprint()+'\n')