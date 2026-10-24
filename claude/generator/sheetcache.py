"""Inhalts-Cache der Konzeptblätter (claude-0.8; Muster: Robogen EXPORT_CODE_PARTS, Toolgen STAGE_CACHE_FUNCTIONS, Cubegen cache.py).

Ein Blatt (KXnn oder VSnn) hängt an einem Schlüssel (sha256) aus
  1. dem Modell nach sheetmodels.load / vsmount.apply (bzw. vsmodels.load samt Sight-Spec): kanonisch serialisiert, also
     Teile, Flächen, Aufkleber, Palette, Beschriftungen, Skin-Eingaben und das montierte Visier;
  2. dem Quelltext der Funktionen, die das Blatt schreiben (CODE_PARTS: je Modul die Funktionsnamen; dazu immer alle
     Anweisungen auf Modulebene, also Konstanten, Fonts, Tabellen). Verglichen wird der AST: Kommentare und Leerzeichen
     ändern den Schlüssel nicht;
  3. der Umgebung (Python-Minor, numpy, scipy, Pillow) – die Bildstufe rechnet mit ihnen.
Der Cache liegt außerhalb des Repos (~/Library/Caches/CubeEscape/concept-sheets/sheet-cache/, mit CE_SHEET_CACHE
umlegbar). Einträge werden atomar geschrieben (temporäre Datei, dann os.replace; das Blatt zuletzt). Trifft der Schlüssel und
stimmen Größe und sha256 der Cache- und der Ausgabedatei, wird nichts geschrieben.

Nie über den Cache: Release, `test_golden.py --full` (Cube-Escape-Entscheidung 15.10.2026: volle Regression nicht über den
Cache), `build_all.py --force`, `CE_NO_CACHE=1`. test_sheetcache.py prüft, dass keine schreibende Funktion in CODE_PARTS fehlt.
"""
import ast,hashlib,json,os,sys,types

from cepaths import E3D,OUT

CACHE_DIR=os.environ.get('CE_SHEET_CACHE') or os.path.expanduser('~/Library/Caches/CubeEscape/concept-sheets/sheet-cache')
KEY_VERSION=1   # bei Änderungen an Schlüsselbildung oder Eintragsformat erhöhen

# Funktionen/Klassen, die Blätter schreiben, je Modul (Modulebene-Anweisungen sind immer dabei).
# Eine neue Funktion in einem dieser Module muss hier stehen oder in NOT_HASHED (mit Grund) – sonst schlägt der Test an.
CODE_PARTS={
 'xl':['make_texture','swatch_svg','_bbox','detail_view','_callouts','DEFS','panel','prompts','pick_labels','_shift_part',
       'compact_sight','_sight_view','sight_panel','_chip','skin_row','sheet','_sheet','_profile_swatch','profile_strip','prompt_font','op_strip'],
 'xlroles':['_rgb','_hex','_lum','_sat','_mix','all_colors','color_roles','recolor','material_of','preferred_channel',
            'assign_channels','area3','area2','part_area','_hexu','channel_palettes'],
 'eng':['hx','lum','roundpoly','rect','circ','area','Model','tf','shadef','render','hull','svgview','svgview_vec','extent',
        'label','channel','copy_channels','model_origin','sight','split_sight'],
 'raster':['_hex','_glass_pass','rasterview','_webp_b64','_image_b64','deferred'],
 'skins':['pick','_seg','_bar','_slant','_shrink','emblem','glyph_items','layout','_verts','bbox','side_face','inside',
          '_rect_hit','top_at','Frame','_unit','_blockers','place_rect','area_poly','resolve','_dist','base_slots','_resolve',
          '_trim','slot_colors','slots_used','apply','summary'],
 'skinraster':['_rgb','tones','_inpoly','_hsh','skin_texture'],
 'fontcss':[],
 'variants':['name','lib','title'],
 'vsheet':['split','center_of','view','proj','recolor','T','reticle_svg','scene_svg','sheet','_sheet'],
 # vsmodels: ganzes Modul ('*'). Es liefert nicht nur das Modell (load), sondern auch Rahmen, Module, Tönungen, Farben, die
 # vsheet.sheet für alle Varianten zeichnet und xl._sight_view (TINTS) liest.
 'vsmodels':'*',
 # texcat: ganzes Modul; der Inhalt des Texturkatalogs steht über texcat.fingerprint() im Schlüssel (code_key)
 'texcat':'*',
 # texprofile: ganzes Modul (Datentabelle PROFILES, seit claude-0.9 auf dem Blatt im Feld TEXTURPROFIL)
 'texprofile':'*',
 # wtypes: ganzes Modul (Typenkatalog claude-0.10: Typnamen, Nahkampf, Kurznamen der beweglichen Teile im Feld BEDIENUNG)
 'wtypes':'*',
}
NOT_HASHED={('variants','name_problems'):'prüft nur Namen beim Anlegen einer Variante (new_variant.py), schreibt nichts'}
# Module, deren Ausgabe als Daten im Schlüssel steht (Modell, Sight-Spec) – ihr Quelltext zählt nur über diese Daten
DATA_MODULES={'cepaths','vsmount','export_sight','export_spec'}
# Module je Blattart. xl und vsheet rufen sich gegenseitig auf (xl._sight_view nutzt vsheet.DRAW_ALPHA und vsmodels.TINTS,
# vsheet nutzt xl.panel/_callouts/ISO), darum haben beide Arten dieselbe Liste.
COMMON=['xl','xlroles','eng','raster','skins','skinraster','fontcss','variants','vsheet','vsmodels','texcat','texprofile','wtypes']
CODE_MODULES={'weapon':COMMON,'vs':COMMON}
ENTRY_MODULES={'weapon':'xl','vs':'vsheet'}

# ---------- Kanonische Serialisierung
def canon(o):
    """JSON-fähige, eindeutige Form von o. Reihenfolge von Listen und Wörterbüchern bleibt (sie bestimmt die Zeichenreihenfolge);
    unbekannte Typen sind ein Fehler, nie ein stilles repr() (Adressen im repr würden den Schlüssel je Lauf ändern)."""
    if o is None or isinstance(o,(bool,str)):return o
    if isinstance(o,int):return o
    if isinstance(o,float):return ['f',repr(o)]
    if isinstance(o,(list,tuple)):return ['t' if isinstance(o,tuple) else 'l',[canon(x) for x in o]]
    if isinstance(o,dict):return ['d',[[canon(k),canon(v)] for k,v in o.items()]]
    if isinstance(o,(set,frozenset)):return ['s',sorted(json.dumps(canon(x)) for x in o)]
    if isinstance(o,types.FunctionType) and o.__name__!='<lambda>' and not o.__closure__:
        return ['fn',o.__module__,o.__qualname__]   # Bauprozedur im Serien-Eintrag: Quelltext zählt über CODE_PARTS, Ergebnis steht als Modell im Schlüssel
    if hasattr(o,'__dict__') and type(o).__module__!='builtins':
        return ['o',type(o).__name__,[[k,canon(v)] for k,v in vars(o).items()]]
    raise TypeError(f'sheetcache.canon: Typ {type(o).__name__} nicht serialisierbar')

def model_digest(d):
    return hashlib.sha256(json.dumps(canon(d),ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()

# ---------- Quelltext der schreibenden Funktionen
_code_cache={}
def _tree(mod):
    with open(os.path.join(E3D,mod+'.py'),encoding='utf-8') as f:return ast.parse(f.read())
def _defs(tree):return [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
def code_digest(mod,names=None):
    """sha256 über die Modulebene (ohne Funktionen/Klassen) und die genannten Funktionen eines Moduls (AST-Form)."""
    names=CODE_PARTS[mod] if names is None else names
    tree=_tree(mod);want={n.name for n in _defs(tree)} if names=='*' else set(names)
    missing=want-{n.name for n in _defs(tree)}
    if missing:raise KeyError(f'{mod}: Funktion(en) fehlen: {sorted(missing)}')
    h=hashlib.sha256()
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            if n.name not in want:continue
            h.update(b'def:'+n.name.encode())
        else:
            # Docstring des Moduls zählt nicht
            if isinstance(n,ast.Expr) and isinstance(getattr(n,'value',None),ast.Constant) and isinstance(n.value.value,str):continue
            h.update(b'top:')
        h.update(ast.dump(n,include_attributes=False).encode())
    return h.hexdigest()

def env_fingerprint():
    v=[f'py{sys.version_info[0]}.{sys.version_info[1]}']
    for m in ('numpy','scipy','PIL'):
        try:v.append(f'{m}{__import__(m).__version__}')
        except Exception:v.append(f'{m}-')
    try:
        from PIL import features;v.append('webp'+str(features.version('webp')))   # eingebettete WebP-Bilder hängen am libwebp-Encoder
    except Exception:v.append('webp-')
    return ' '.join(v)

def code_key(kind):
    if kind not in _code_cache:
        h=hashlib.sha256()
        for mod in CODE_MODULES[kind]:h.update(f'{mod}:{code_digest(mod)};'.encode())
        import texcat
        h.update(('catalog:'+texcat.fingerprint()+';').encode())   # Muster, Oberflächen, Abnutzung, Claude-Skins des Katalogs
        h.update(env_fingerprint().encode())
        _code_cache[kind]=h.hexdigest()
    return _code_cache[kind]

def sheet_key(kind,sheet_id,*data):
    """Schlüssel eines Blatts. data = alle Eingaben außer dem Code: bei Waffenblättern (d,), bei Visieren (d, sight_spec)."""
    h=hashlib.sha256(f'v{KEY_VERSION}|{kind}|{sheet_id}|{code_key(kind)}|'.encode())
    for x in data:h.update(model_digest(x).encode())
    return h.hexdigest()

# ---------- Cache
def forced(argv=None):
    """--force: nichts aus dem Cache nehmen, alles neu bauen (die frisch gebauten Blätter erneuern die Einträge)."""
    return '--force' in (argv if argv is not None else sys.argv[1:])
def disabled(argv=None):
    """Cache ganz aus (CE_NO_CACHE=1): weder lesen noch schreiben."""
    return os.environ.get('CE_NO_CACHE')=='1'
def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def _entry(key):return os.path.join(CACHE_DIR,key[:2],key)
def _atomic(path,data):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    tmp=f'{path}.tmp{os.getpid()}'
    with open(tmp,'wb') as f:f.write(data)
    os.replace(tmp,path)

def lookup(key):
    """Meta (Wörterbuch) des Eintrags, wenn Meta und Blatt vorliegen und das Blatt zur Meta passt; sonst None."""
    e=_entry(key)
    try:
        with open(e+'.json',encoding='utf-8') as f:meta=json.load(f)
        if not isinstance(meta,dict):return None
        if meta.get('key')!=key or os.path.getsize(e+'.html')!=meta['size']:return None
        if sha_file(e+'.html')!=meta['sha256']:return None
        return meta
    except (OSError,ValueError,KeyError,TypeError):return None

def store(key,page,extra=None):
    """Legt das Blatt (str) ab: erst das Blatt, dann die Meta zuletzt (ohne Meta gilt der Eintrag als nicht vorhanden)."""
    data=page.encode('utf-8');e=_entry(key)
    meta=dict(key=key,size=len(data),sha256=sha_bytes(data),env=env_fingerprint(),**(extra or {}))
    _atomic(e+'.html',data)
    _atomic(e+'.json',json.dumps(meta,ensure_ascii=False,sort_keys=True).encode('utf-8'))
    return meta

def restore(key,meta,dest):
    """Schreibt das Blatt aus dem Cache nach dest, wenn dest fehlt oder abweicht. True = geschrieben, False = war schon gleich."""
    try:
        if os.path.getsize(dest)==meta['size'] and sha_file(dest)==meta['sha256']:return False
    except OSError:pass
    with open(_entry(key)+'.html','rb') as f:_atomic(dest,f.read())
    return True

def write_if_changed(path,text):
    """Schreibt text (utf-8) nur, wenn die Datei fehlt oder abweicht; True = geschrieben."""
    data=text.encode('utf-8')
    try:
        with open(path,'rb') as f:
            if f.read()==data:return False
    except OSError:pass
    _atomic(path,data);return True

def golden_state(kind,sheet_id,sha):
    """'golden ok' / 'golden abweicht' / 'nicht in golden' (Hinweis im Log; die Prüfung bleibt test_golden.py)."""
    try:
        with open(os.path.join(E3D,'..','tests','golden.json'),encoding='utf-8') as f:g=json.load(f)
        ref=g.get('sheets' if kind=='weapon' else 'vs_sheets',{}).get(sheet_id)
    except (OSError,ValueError):ref=None
    return 'nicht in golden' if ref is None else 'golden ok' if ref==sha else 'golden abweicht'
