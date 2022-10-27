from fileinput import filename
import sys
import difflib as dl
import pandas as pd
from json import loads
import urllib.request
from urllib.error import HTTPError
import numpy as np

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

def bibparser(bibtext):
    bibdict = {}
    bibtext = bibtext.replace("{","").replace("}","").strip().split(",")
    bibdict = dict(list(map(lambda x:x.strip().split(" = "),bibtext))[1:])
    return bibdict

def journalsearch(journalname):
    match = dl.get_close_matches(journalname,JOURNALS["Journal name"])
    print("Matching",journalname,end=" ")
    if match:
        candidateRow = JOURNALS[JOURNALS["Journal name"]==match[0]]
        print("->",candidateRow["Journal name"].values[0])
        if candidateRow['ISSN'].values[0] is np.NAN:
            return candidateRow["eISSN"].values[0],round(candidateRow["2021 JIF"].values[0],3), candidateRow['JIF Quartile'].values[0]
        else:
            return candidateRow["ISSN"].values[0],round(candidateRow["2021 JIF"].values[0],3), candidateRow['JIF Quartile'].values[0]
    print("no match")
    return "X-X",0.0, 'n/a'

def doitobib(doi="10.1126/science.169.3946.635"):
    if "doi.org" in doi:
        doi = doi.split(".org/")[1]
    url = BASE_URL + doi
    print(url,end="")
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/x-bibtex')
    try:
        with urllib.request.urlopen(req, timeout = 1) as f:
            bibtex = urllib.parse.unquote_plus(f.read().decode("utf-8"), encoding='utf-8', errors='replace')
        print(" - OK!")
        return bibtex
    except:
        print(" - Error!")
        return ""

def doitotxt(doi="10.1126/science.169.3946.635"):
    if "doi.org" in doi:
        doi = doi.split(".org/")[1]
    url = BASE_URL + doi
    print(url,end=" TXT ")
    req = urllib.request.Request(url)
    req.add_header('Accept', 'text/x-bibliography')
    try:
        with urllib.request.urlopen(req, timeout = 1) as f:
            txt = f.read()#.decode("utf-8")#urllib.parse.unquote_plus(, encoding='utf-8', errors='replace')
        print(" - OK!")
        return txt
    except:
        print(" - Error!")
        return ""

def doitojson(doi="10.3389/fncel.2017.00174"):
    if "doi.org" in doi:
        doi = doi.split(".org/")[1]
    url = BASE_URL + doi
    print(url,end=" JSON ")
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout = 1) as f:
            json = loads(f.read().decode("utf-8"))#urllib.parse.unquote_plus(f.read().decode("utf-8"), encoding='utf-8', errors='replace'))
            newjson={"authors":json["author"],"title":json["title"],"volume":json["volume"],"issn":json["ISSN"],"year":json["indexed"]["date-parts"],"journal":json["container-title"],}
        print(" - OK!")
        return newjson
    except:
        print(" - Error!")
        return {}

#script

if len(sys.argv)>1:
    doifile = sys.argv[1]
else:
    doifile = "KarenCastillo.doi"
bibfile = doifile.split(".")[0]+".txt"
outbibs = []
with open(doifile) as dois:
    for line in dois:
        #print(doitojson(line.strip()),doitotxt(line.strip()))
        # bib = doitojson(line.strip())
        if "doi.org" in line:
            line = line.split(".org/")[1]
        url = BASE_URL + line
        print(url,end=" JSON ")
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout = 5) as f:
                json = loads(f.read().decode("utf-8"))#urllib.parse.unquote_plus(f.read().decode("utf-8"), encoding='utf-8', errors='replace'))
            authlist = []
            for nn in json['author']:
                try:
                    authlist.append(f"{nn['family']} " + ''.join([x[0] for x in nn['given'].split(' ')]))
                except:
                    authlist.append(f"{nn['family']}")
            authorsF = ', '.join(authlist)
            vol=""
            if 'volume' in json.keys():
                vol = json["volume"]
            if 'page' in json.keys():
                vol = vol+':'+json["page"]
            elif 'issue' in json.keys():
                vol = vol+'('+json["issue"]+')'
            newjson={"authors":authorsF,"title":json["title"],"volume":vol,"issn":json["ISSN"],"year":json['published']['date-parts'],"journal":json["container-title"],}
            while '  ' in newjson['title']:
                newjson['title'] = newjson['title'].replace('  ',' ')
            newjson['title'] = newjson['title'].replace('\n ','')
            newjson['title'] = newjson['title'].replace('<sup>','')
            newjson['title'] = newjson['title'].replace('</sup>','')
            newjson['title'] = newjson['title'].replace('<sub>','')
            newjson['title'] = newjson['title'].replace('</sub>','')

            print(" - OK!")
            bib =  newjson
        except:
            print(" - Error!")
            bib= {}
        
        
        if bib:
            #print(bib)
            #bibdict = bibparser(bib)
            # autores = ", ".join([a["given"]+" "+a["family"] for a in bib["authors"]])
            issn,impact, Q = journalsearch(bib["journal"].upper())
            out="\t".join([bib['authors'],str(bib["year"][0][0]),bib['title'],bib["journal"]+", "+bib["volume"]+" "+BASE_URL+line.strip(),"Publicada",str(issn),f'{impact:.3f} ({Q})'])+"\n"
            out=out.replace('\u2010','-')
            
            outbibs.append(out)
        else:
            print(bib, "No encontrado")
        print()
    

with open('../' + bibfile,"w", encoding="utf-8") as wbib:
    for b in outbibs:
        wbib.write(b)
