"""Baut die Blätter der Visier-Serie: claude/output/sheets/VSnn.dc.html (Bildstufe: numpy/scipy, auf dem Mac mit heavy_lock).
   python3 claude/generator/build_vs.py            # alle neun
   python3 claude/generator/build_vs.py VS01 VS05  # nur diese
Die Specs schreibt export_sight.py (ohne Bildstufe); das Blatt liest dieselben Modelle (vsmodels.py)."""
from cepaths import E3D,OUT
import os,sys,time
sys.path.insert(0,E3D)
import sheetcache,vsmodels,export_sight
USE_CACHE=not sheetcache.disabled()   # CE_NO_CACHE=1: Cache ganz aus
FORCE=sheetcache.forced()             # --force: alles neu bauen, Einträge erneuern (Release, test_golden --full)
def write(vid,page):
    with open(os.path.join(OUT,f'{vid}.dc.html'),'w',encoding='utf-8') as f:f.write(page)
    with open(os.path.join(E3D,'final',f'{vid}.html'),'w',encoding='utf-8') as f:f.write(page.replace('<script src="./support.js"></script>',''))
def build(vid,force=False):
    """Baut ein Visier-Blatt; liefert die Logzeile. Auch Aufgabe des Prozess-Pools in build_all.py (claude-0.19)."""
    t=time.time();dest=os.path.join(OUT,f'{vid}.dc.html')
    # Eingaben: Modell und Sight-Spec (die auch die Waffen-Specs des Typs liest, export_sight.weapon_sheets)
    key=sheetcache.sheet_key('vs',vid,vsmodels.load(vid),export_sight.build(vid)) if USE_CACHE else None
    meta=sheetcache.lookup(key) if key and not force else None
    if meta:
        wrote=sheetcache.restore(key,meta,dest)
        with open(dest,encoding='utf-8') as f:page=f.read()
        sheetcache.write_if_changed(os.path.join(E3D,'final',f'{vid}.html'),page.replace('<script src="./support.js"></script>',''))
        return ' '.join(map(str,(f'{vid}.dc.html',meta['size']//1024,'KB','Cache-Treffer','geschrieben' if wrote else 'unverändert',sheetcache.golden_state('vs',vid,meta['sha256']))))
    import vsheet
    page=vsheet.sheet(vid);write(vid,page)
    if key:sheetcache.store(key,page,dict(sheet=vid))
    return ' '.join(map(str,(f'{vid}.dc.html',len(page)//1024,'KB',f'{time.time()-t:.1f} s','gebaut'+('' if key else ' (ohne Cache)'),sheetcache.golden_state('vs',vid,sheetcache.sha_bytes(page.encode('utf-8'))))))
def main(ids):
    for vid in ids or vsmodels.IDS:print(build(vid,FORCE),flush=True)
if __name__=='__main__':main([a for a in sys.argv[1:] if not a.startswith('--')])
