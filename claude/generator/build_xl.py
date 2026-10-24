from cepaths import E3D,OUT
import sys,pickle,re,glob,json,os
sys.path.insert(0,E3D+'')
import sheetcache
PROJ=OUT+'/'
USE_CACHE=not sheetcache.disabled()   # CE_NO_CACHE=1: Cache ganz aus
def build(fid,force=False):
    """Baut ein Blatt (fid z. B. 'g02'); force = --force: alles neu bauen, Einträge erneuern (Release, test_golden --full).
    Liefert die Logzeile. Auch Aufgabe des Prozess-Pools in build_all.py (claude-0.19)."""
    pk=f'{E3D}/reg/{fid}.pkl'
    if os.path.exists(pk):
        import vsmount
        import ops
        d=pickle.load(open(pk,'rb'))
        ops.attach(d,'K'+('C' if fid[0]=='v' else fid[0].upper())+fid[1:])   # Bedienung (claude-0.11) wie in sheetmodels.load
        d=vsmount.apply(d)   # Kartenweg: Visier der Visier-Serie wie in sheetmodels.load (claude-0.7)
    else:   # ohne Kartenlauf: Modell direkt aus dem Bauskript (sheetmodels, wie der Spec-Export)
        import sheetmodels
        d=sheetmodels.load('K'+('C' if fid[0]=='v' else fid[0].upper())+fid[1:])
    mm=re.search(r'VARIANTE\s+([A-Z])\s*·\s*„([^“]+)“',d['sub'])
    V,nick=mm.group(1),mm.group(2).title()
    d['nick']=nick
    fn=f'K{V}{d["num"]}.dc.html';sid=fn[:-8]
    key=sheetcache.sheet_key('weapon',sid,d,V) if USE_CACHE else None
    meta=sheetcache.lookup(key) if key and not force else None
    if meta and not isinstance(meta.get('prompt'),dict):meta=None   # Eintrag ohne Prompts: neu bauen
    if meta:
        wrote=sheetcache.restore(key,meta,PROJ+fn)
        with open(PROJ+fn,encoding='utf-8') as f:page=f.read()
        sheetcache.write_if_changed(f'{E3D}/final/{sid}.html',page.replace('<script src="./support.js"></script>',''))
        pr=meta['prompt']
        sheetcache.write_if_changed(f'{E3D}/reg/{fid}.prompt.json',json.dumps(dict(V=V,num=d['num'],name=d['name'],nick=nick,de=pr['de'],en=pr['en']),ensure_ascii=False))
        return ' '.join(map(str,(fn,meta['size']//1024,'KB','Cache-Treffer',('geschrieben' if wrote else 'unverändert'),sheetcache.golden_state('weapon',sid,meta['sha256']))))
    import xl
    page,de,en=xl.sheet(d,V)
    open(PROJ+fn,'w').write(page)
    open(f'{E3D}/final/{fn[:-8]}.html','w').write(page.replace('<script src="./support.js"></script>',''))
    json.dump(dict(V=V,num=d['num'],name=d['name'],nick=nick,de=de,en=en),open(f'{E3D}/reg/{fid}.prompt.json','w'),ensure_ascii=False)
    if key:sheetcache.store(key,page,dict(sheet=sid,prompt=dict(de=de,en=en)))
    return ' '.join(map(str,(fn,len(page)//1024,'KB','gebaut'+('' if key else ' (ohne Cache)'),sheetcache.golden_state('weapon',sid,sheetcache.sha_bytes(page.encode('utf-8'))))))
if __name__=='__main__':
    for fid in [a for a in sys.argv[1:] if not a.startswith('--')]:print(build(fid,sheetcache.forced()),flush=True)
