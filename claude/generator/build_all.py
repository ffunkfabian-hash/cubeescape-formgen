"""Baut alle Karten und Konzeptblätter neu.
   python generator/build_all.py            # alles (Karten + XL-Blätter + Prompts)
   python generator/build_all.py --nur-xl   # nur die großen Konzeptblätter aus den vorhandenen reg/*.pkl
   python generator/build_all.py C G J      # nur bestimmte Varianten (Buchstaben aus variants.py)
   python generator/build_all.py VS         # nur die Visier-Serie VS01–VS09 (mit Buchstaben: diese Varianten und VS)
   python generator/build_all.py --nur-xl --release   # Release (claude-0.19): Inhalts-Cache plus erzwungene Stichprobe, danach test_golden.py --full
   python generator/build_all.py --force    # ohne Inhalts-Cache (sheetcache.py): alle Blätter neu; volle Regression im Nachtlauf (ce_nightly)
--release (Entscheidung des Nutzers 24.10.2026): Cache-Treffer kommen aus dem Cache; frisch gebaut werden alle Cache-Fehltreffer, alle
Blätter, deren Golden-Hash sich seit dem letzten Tag claude-v* geändert hat, und RELEASE_SAMPLE zufällige Blätter (CE_RELEASE_SAMPLE=n,
--seed=n wiederholt eine Auswahl; der Seed steht im Log). Weicht ein frisch gebautes Blatt der Stichprobe von golden.json ab, endet der
Lauf mit Exit 1 (nicht nachbaubar oder golden.json nicht nachgezogen).
Ohne --force baut build_xl.py/build_vs.py nur Blätter, deren Schlüssel (Modell, Palette/Skin, Quelltext der schreibenden Funktionen) sich geändert hat.
Blätter (KXnn und VSnn) baut seit claude-0.19 ein Prozess-Pool je Blatt (vorher ein Prozess je Variante, VS seriell danach):
Prozesszahl = Kerne, begrenzt durch den Speicher (SHEET_GB je Prozess); CE_SHEET_JOBS=n setzt sie fest. Die WebP-Bilder eines
Blatts kodiert raster.deferred in Threads (CE_WEBP_THREADS).
"""
import subprocess,sys,os,shutil,time,traceback
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor,as_completed
import multiprocessing as mp
from cepaths import E3D,ROOT,OUT,PROMPTS
import variants,sheetcache
RELEASE_SAMPLE=int(os.environ.get('CE_RELEASE_SAMPLE') or 10)
SHEET_GB=3.5   # Spitzenspeicher eines Blattprozesses (Messung KG02: 2,95 GB, Isometrie 5400×3600 Bildpunkte) plus Reserve
# Bewusst am physischen RAM (feste Obergrenze, 16 GB → 4 Prozesse), nicht am freien: der schwankt mit anderen Sitzungen; bei knappem
# Speicher CE_SHEET_JOBS kleiner setzen. Gemessen 24.10.2026: 4 Prozesse, Swap blieb bei ~7–8 GB (vorher schon belegt).
def sheet_jobs():
    if os.environ.get('CE_SHEET_JOBS'):return max(1,int(os.environ['CE_SHEET_JOBS']))
    try:mem=os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')
    except (ValueError,OSError):mem=16<<30
    return max(1,min(os.cpu_count() or 4,int(mem/(SHEET_GB*(1<<30)))))
def _sheet_job(kind,sid,force):
    """Aufgabe im Prozess-Pool: ein Blatt bauen (build_xl.build bzw. build_vs.build); liefert Logzeile und Sekunden."""
    t=time.time()
    if kind=='vs':import build_vs as b
    else:import build_xl as b
    return b.build(sid,force),time.time()-t
def sheet_id(kind,i):return i if kind=='vs' else 'K'+('C' if i[0]=='v' else i[0].upper())+i[1:]   # 'g02' -> 'KG02'
def changed_since_release():
    """Blatt-IDs, deren Golden-Hash (sheets, vs_sheets) sich seit dem letzten Tag claude-v* geändert hat; ohne Tag: None (alle)."""
    import json
    git=lambda *a:subprocess.run(['git','-C',ROOT,*a],capture_output=True,text=True)
    tag=git('describe','--tags','--match','claude-v*','--abbrev=0').stdout.strip()
    old=git('show',f'{tag}:claude/tests/golden.json') if tag else None
    if not tag or old.returncode:return None,tag
    o=json.loads(old.stdout)
    with open(os.path.join(E3D,'..','tests','golden.json'),encoding='utf-8') as f:g=json.load(f)
    return {s for k in ('sheets','vs_sheets') for s,h in g.get(k,{}).items() if o.get(k,{}).get(s)!=h},tag
def release_plan(jobs,seed=None):
    """--release: welche Blätter frisch bauen (force) – geänderte seit dem letzten Release plus RELEASE_SAMPLE zufällige."""
    import random
    ch,tag=changed_since_release()
    if seed is None:seed=int.from_bytes(os.urandom(4),'big')
    ids=[sheet_id(k,i) for k,i in jobs]
    rest=[s for s in ids if ch is None or s not in ch]
    sample=set(random.Random(seed).sample(rest,min(RELEASE_SAMPLE,len(rest))))
    forced=set(ids) if ch is None else (ch&set(ids))|sample
    print(f'Release-Stichprobe (seed={seed}): {len(sample)} zufällig {sorted(sample)}; seit {tag or "– (kein Tag)"} geändert: '
          f'{"alle" if ch is None else sorted(ch&set(ids)) or "keine"}; frisch gebaut zusammen {len(forced)}, dazu alle Cache-Fehltreffer',flush=True)
    return forced
def run_sheets(jobs,force,forced=()):
    """Baut alle Blätter (kind, id) im Prozess-Pool; Ausgabe je Blatt, sobald es fertig ist. forced = IDs, die trotz Cache frisch
    gebaut werden (Release-Stichprobe) und golden.json treffen müssen. Liefert die Zahl der Fehler."""
    n=min(sheet_jobs(),len(jobs));t0=time.time();bad=0;fresh=0;miss=[]
    print(f'Blätter: {len(jobs)} in {n} Prozessen',flush=True)
    with ProcessPoolExecutor(n,mp_context=mp.get_context('spawn')) as ex:
        fs={ex.submit(_sheet_job,k,i,force or sheet_id(k,i) in forced):sheet_id(k,i) for k,i in jobs}
        for f in as_completed(fs):
            try:
                line,dt=f.result();print(f'OK  {line}  {dt:.1f} s',flush=True)
                if fs[f] in forced:
                    fresh+=1
                    if 'golden ok' not in line:miss.append(fs[f])
            except Exception as e:
                bad+=1;print(f'FEHLER {fs[f]}: {e!r}',flush=True);traceback.print_exception(e)
    print(f'Blätter fertig in {time.time()-t0:.0f} s',flush=True)
    if forced:
        print(f'Stichprobe: {fresh} frisch gebaut, '+(f'ABWEICHEND von golden.json: {sorted(miss)}' if miss else 'alle golden ok'),flush=True)
        bad+=len(miss)
    return bad
os.chdir(E3D)
args=sys.argv[1:]
nur_xl='--nur-xl' in args
FORCE=['--force'] if sheetcache.forced(args) else []   # an build_xl/build_vs durchreichen
RELEASE='--release' in args and not FORCE
SEED=next((int(a.split('=',1)[1]) for a in args if a.startswith('--seed=')),None)
letters=[a for a in args if len(a)==1 and a in variants.LETTERS]
vs='VS' in args or not letters   # Visier-Serie VS01–VS09: bei allen oder mit Argument VS
V=letters or ([] if 'VS' in args else list(variants.LETTERS))
P=lambda *c:[sys.executable,*c]
N=[f'{i:02d}' for i in range(1,11)]
jobs={
 'C':[P('build_v01.py')]+[P('build_c25.py',n) for n in N[1:5]]+[P('build_c.py',n) for n in N[5:]]+[P('make_v2d.py',*N)],
 'D':[P('build_d15.py','1','2','3','4','5'),P('build_d.py',*N[5:]),P('render_dx05.py')],
 'F':[P('build_f15.py',*N[:5],'noshot'),P('build_f610.py',*N[5:],'noshot')],
 'G':[P('build_g15.py',n,'noshot') for n in N[:5]]+[P('build_g610.py',n,'noshot') for n in N[5:]],
 'H':[P('build_h15.py',n,'noshot') for n in N[:5]]+[P('build_h610.py',n,'noshot') for n in N[5:]],
}
for v in variants.LETTERS:   # jlib-Varianten (ab J): keine Karten, build_xl lädt die Modelle direkt (sheetmodels)
    if variants.lib(v)=='jlib':jobs[v]=[]
fid={'C':['v01']+[f'c{n}' for n in N[1:]],'D':[f'd{n}' for n in N],'F':[f'f{n}' for n in N],'G':[f'g{n}' for n in N],'H':[f'h{n}' for n in N]}
for v in variants.LETTERS:
    fid.setdefault(v,[f'{v.lower()}{n}' for n in N])
import wtypes
for v,nums in wtypes.NEW_SHEETS.items():fid[v]+=[f'{v.lower()}{n}' for n in nums]   # neue Waffentypen (claude-0.10): nur XL-Blatt, keine Karten
# Schritte, die gitignorierte alte Karten als Vorlage lesen: fehlt die Vorlage, wird der Schritt übersprungen (XL-Blätter brauchen sie nicht)
NEEDS={'render_dx05.py':['D05.dc.html','X05.dc.html'],'make_v2d.py':[f'V{n}.dc.html' for n in N]}
def run_seq(cmds):
    for c in cmds:
        miss=[f for f in NEEDS.get(c[1],[]) if not os.path.exists(os.path.join(OUT,f))]
        if miss:print('ÜBERSPRUNGEN '+' '.join(c[1:])+' (Vorlage fehlt: '+', '.join(miss[:3])+(' …' if len(miss)>3 else '')+')',flush=True);continue
        r=subprocess.run(c,capture_output=True,text=True)
        print(('OK  ' if r.returncode==0 else 'FEHLER ')+' '.join(c[1:]),flush=True)
        for ln in r.stdout.splitlines():
            if 'Cache' in ln or 'gebaut' in ln:print('    '+ln,flush=True)   # Treffer/Neubau je Blatt (sheetcache)
        if r.returncode:print(r.stderr[-2000:])
def main():   # Pool-Prozesse (spawn) laden dieses Skript als __mp_main__: dort nur Definitionen, kein Lauf
    if not nur_xl and V:
        with ThreadPoolExecutor(len(V)) as ex:list(ex.map(run_seq,[jobs[v] for v in V]))
    import vsmodels
    # Waffenblätter und Visier-Serie VS01–VS09 (claude-0.6, eigene Modelle vsmodels.py) in einem Pool
    sj=[('xl',f) for v in V for f in fid[v]]+([('vs',i) for i in vsmodels.IDS] if vs else [])
    bad=run_sheets(sj,bool(FORCE),release_plan(sj,SEED) if RELEASE else ()) if sj else 0
    run_seq([P('mkdoc.py')])
    if os.path.exists('Waffen-Prompts.md'):shutil.copy('Waffen-Prompts.md',os.path.join(PROMPTS,'Waffen-Prompts.md'))
    run_seq([P('make_viewer.py')])   # Viewer claude/output/index.html (Regel in CLAUDE.md)
    print('fertig' if not bad else f'fertig mit {bad} Fehler(n)')
    sys.exit(1 if bad else 0)
if __name__=='__main__':main()
