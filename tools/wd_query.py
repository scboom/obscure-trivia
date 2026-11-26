"""Run a SPARQL query against the Wikidata Query Service. Usage: wd_query.py QUERY.rq OUT.json"""
import sys, json, urllib.request, urllib.parse, time
q = open(sys.argv[1]).read()
req = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}),
                             headers={"User-Agent": "obscure-trivia-builder/1.0 (quiz data)", "Accept": "application/sparql-results+json"})
data = None
for attempt in range(8):
    try:
        data = json.load(urllib.request.urlopen(req, timeout=180)); break
    except Exception as e:
        print("retry", e, flush=True); time.sleep(70)
if data is None:
    sys.exit("gave up on " + sys.argv[1])
rows = [{k: v["value"] for k, v in b.items()} for b in data["results"]["bindings"]]
json.dump(rows, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)
print(len(rows), "rows ->", sys.argv[2])
