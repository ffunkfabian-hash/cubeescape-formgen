"""Inhalts-Cache der Blätter (claude/generator/sheetcache.py): Funktionsliste vollständig, Schlüssel stabil und empfindlich, Cache atomar.
   python3 claude/tests/test_sheetcache.py       # ohne Bildstufe (kein numpy/scipy nötig)
Fehlt eine Funktion, die ein Blatt schreibt, in sheetcache.CODE_PARTS, schlägt test_every_function_is_listed an.
"""
import ast,copy,json,os,subprocess,sys,tempfile,unittest
HERE=os.path.dirname(os.path.abspath(__file__))
GEN=os.path.join(HERE,'..','generator');sys.path.insert(0,GEN)
tmp_cache=tempfile.mkdtemp(prefix='ce-sheet-cache-test-')
os.environ['CE_SHEET_CACHE']=tmp_cache   # nie den echten Cache berühren
import sheetcache as SC,sheetmodels,vsmodels,export_sight

def local_imports(mod):
    """Module aus generator/, die mod importiert (auch innerhalb von Funktionen)."""
    with open(os.path.join(GEN,mod+'.py'),encoding='utf-8') as f:t=ast.parse(f.read())
    out=set()
    for n in ast.walk(t):
        names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module] if isinstance(n,ast.ImportFrom) and n.module else []
        out|={x.split('.')[0] for x in names if os.path.exists(os.path.join(GEN,x.split('.')[0]+'.py'))}
    return out

class CodeParts(unittest.TestCase):
    def test_every_function_is_listed(self):
        for mod,names in SC.CODE_PARTS.items():
            with self.subTest(module=mod):
                defined={n.name for n in SC._defs(SC._tree(mod))}
                if names=='*':continue
                skipped={n for (m,n) in SC.NOT_HASHED if m==mod}
                self.assertEqual(sorted(defined-set(names)-skipped),[],f'{mod}: Funktion fehlt in sheetcache.CODE_PARTS (oder NOT_HASHED mit Grund)')
                self.assertEqual(sorted(set(names)-defined),[],f'{mod}: CODE_PARTS nennt Funktionen, die es nicht gibt')
    def test_import_closure_is_covered(self):
        """Jedes Modul, das ein schreibendes Modul importiert, steht in CODE_PARTS oder ist Datenquelle (Modell/Sight-Spec im Schlüssel)."""
        for kind,mods in SC.CODE_MODULES.items():
            known=set(mods)|SC.DATA_MODULES
            for m in mods:
                for i in local_imports(m):
                    with self.subTest(kind=kind,module=m,imports=i):
                        self.assertIn(i,known,f'{m} importiert {i}: in CODE_MODULES aufnehmen (CODE_PARTS) oder als DATA_MODULES begründen')
    def test_kinds_use_listed_modules(self):
        for mods in SC.CODE_MODULES.values():self.assertTrue(set(mods)<=set(SC.CODE_PARTS))

class CodeDigest(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.mkdtemp();self.old=SC.E3D;SC.E3D=self.dir
    def tearDown(self):SC.E3D=self.old
    def put(self,src):
        with open(os.path.join(self.dir,'m.py'),'w',encoding='utf-8') as f:f.write(src)
    def test_sensitivity(self):
        self.put('K=1\ndef a(x):\n    return x+1\ndef b():\n    return 2\n')
        base=SC.code_digest('m',['a'])
        self.put('K=1\n# Kommentar\ndef a(x):\n    return x+1   # noch einer\ndef b():\n    return 3\n')   # b nicht gelistet
        self.assertEqual(SC.code_digest('m',['a']),base,'Kommentar/ungelistete Funktion ändern den Schlüssel nicht')
        self.assertNotEqual(SC.code_digest('m',['a','b']),base)
        self.put('K=1\ndef a(x):\n    return x+2\ndef b():\n    return 2\n');self.assertNotEqual(SC.code_digest('m',['a']),base,'Funktionskörper')
        self.put('K=2\ndef a(x):\n    return x+1\ndef b():\n    return 2\n');self.assertNotEqual(SC.code_digest('m',['a']),base,'Konstante auf Modulebene')
        with self.assertRaises(KeyError):SC.code_digest('m',['fehlt'])

class Keys(unittest.TestCase):
    def key(self,sheet):
        d=sheetmodels.load(sheet);return SC.sheet_key('weapon',sheet,d,d['V'])
    def test_stable_across_processes(self):
        code='import sys;sys.path.insert(0,%r);import sheetcache as S,sheetmodels as M,vsmodels as V,export_sight as E\nd=M.load("KC01");print(S.sheet_key("weapon","KC01",d,d["V"]),S.sheet_key("vs","VS01",V.load("VS01"),E.build("VS01")))'%GEN
        outs=[subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,env={**os.environ,'PYTHONHASHSEED':s}) for s in ('1','2')]
        for r in outs:self.assertEqual(r.returncode,0,r.stderr[-800:])
        self.assertEqual(outs[0].stdout,outs[1].stdout)
        self.assertEqual(len(outs[0].stdout.split()),2)
    def test_model_change_changes_key(self):
        d=sheetmodels.load('KC01');k=SC.sheet_key('weapon','KC01',d,d['V'])
        e=copy.deepcopy(d);v=e['m'].parts[0]['F'][0]['v'];v[0]=(v[0][0]+0.5,)+tuple(v[0][1:])
        self.assertNotEqual(SC.sheet_key('weapon','KC01',e,e['V']),k)
        e=copy.deepcopy(d);e['palette']=list(e['palette'])+['#123456'] if isinstance(e['palette'],(list,tuple)) else e['palette']
        if e['palette']!=d['palette']:self.assertNotEqual(SC.sheet_key('weapon','KC01',e,e['V']),k,'Palette')
    def test_all_sheet_keys_unique(self):
        keys={s:self.key(s) for s in sheetmodels.SHEETS}
        self.assertEqual(len(set(keys.values())),len(sheetmodels.SHEETS))
        vs={v:SC.sheet_key('vs',v,vsmodels.load(v),export_sight.build(v)) for v in vsmodels.IDS}
        self.assertEqual(len(set(vs.values())),len(vsmodels.IDS))
        self.assertFalse(set(keys.values())&set(vs.values()))
    def test_vs_model_change_rebuilds_weapon_sheets(self):
        """Ein geändertes Visier-Modell (vsmodels.load) ändert das Waffenblatt, das es verwendet (vsmount.apply)."""
        import vsmount
        sheet=next(s for s in sheetmodels.SHEETS if vsmount.VS_OF.get(sheetmodels.load(s)['name'])=='VS01')
        before=self.key(sheet);orig=vsmodels.load
        def patched(vid):
            L=orig(vid)
            if vid=='VS01':
                v=L['S'].m.parts[0]['F'][0]['v'];v[0]=(v[0][0]+0.25,)+tuple(v[0][1:])
            return L
        vsmodels.load=patched
        try:after=self.key(sheet)
        finally:vsmodels.load=orig
        self.assertNotEqual(before,after)
        other=next(s for s in sheetmodels.SHEETS if vsmount.VS_OF.get(sheetmodels.load(s)['name'])=='VS05')
        ref=self.key(other)   # vor dem Patch
        vsmodels.load=patched
        try:self.assertEqual(self.key(other),ref,'Waffenblatt mit anderem Visier bleibt gleich')
        finally:vsmodels.load=orig
    def test_canon_rejects_unknown(self):
        with self.assertRaises(TypeError):SC.canon(object())
        with self.assertRaises(TypeError):SC.canon(lambda:0)
        with self.assertRaises(TypeError):SC.canon([].append)
        self.assertNotEqual(SC.canon(1.0),SC.canon(1))

class Store(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.mkdtemp();SC.CACHE_DIR=self.dir
    def test_roundtrip_and_integrity(self):
        key='ab'*32;dest=os.path.join(self.dir,'out.html')
        self.assertIsNone(SC.lookup(key))
        meta=SC.store(key,'<html>Blatt ä</html>',dict(prompt=dict(de='a',en='b')))
        got=SC.lookup(key);self.assertEqual(got['sha256'],meta['sha256']);self.assertEqual(got['prompt']['de'],'a')
        self.assertTrue(SC.restore(key,got,dest));self.assertFalse(SC.restore(key,got,dest),'gleiche Datei: nichts schreiben')
        mt=os.path.getmtime(dest);SC.restore(key,got,dest);self.assertEqual(os.path.getmtime(dest),mt)
        with open(dest,'w') as f:f.write('verändert')
        self.assertTrue(SC.restore(key,got,dest));self.assertEqual(SC.sha_file(dest),meta['sha256'])
        with open(SC._entry(key)+'.html','ab') as f:f.write(b'x')   # Blatt im Cache beschädigt
        self.assertIsNone(SC.lookup(key))
    def test_incomplete_entry_is_a_miss(self):
        key='cd'*32;SC.store(key,'x');os.remove(SC._entry(key)+'.json');self.assertIsNone(SC.lookup(key))
    def test_disabled(self):
        self.assertTrue(SC.forced(['--force']));self.assertFalse(SC.forced([]));self.assertFalse(SC.disabled(['--force']))
        os.environ['CE_NO_CACHE']='1'
        try:self.assertTrue(SC.disabled([]))
        finally:del os.environ['CE_NO_CACHE']

class ReleasePlan(unittest.TestCase):
    """build_all.py --release (Entscheidung 24.10.2026): seit dem letzten Release geänderte Blätter immer frisch, dazu RELEASE_SAMPLE
    zufällige; gleicher Seed = gleiche Auswahl; ohne Release-Tag alles frisch."""
    def setUp(self):
        import build_all;self.B=build_all;self.orig=build_all.changed_since_release
        self.jobs=[('xl',f'g{n:02d}') for n in range(1,26)]+[('xl','v01'),('vs','VS01'),('vs','VS02')]
    def tearDown(self):self.B.changed_since_release=self.orig
    def test_changed_plus_sample(self):
        self.B.changed_since_release=lambda:({'KG02','KX99'},'claude-v0.0')
        a=self.B.release_plan(self.jobs,7);b=self.B.release_plan(self.jobs,7)
        self.assertEqual(a,b);self.assertIn('KG02',a);self.assertNotIn('KX99',a)
        self.assertEqual(len(a),1+self.B.RELEASE_SAMPLE)
        self.assertTrue(a<={self.B.sheet_id(k,i) for k,i in self.jobs});self.assertEqual(self.B.sheet_id('xl','v01'),'KC01')
    def test_without_tag_everything(self):
        self.B.changed_since_release=lambda:(None,'')
        self.assertEqual(len(self.B.release_plan(self.jobs,7)),len(self.jobs))

if __name__=='__main__':unittest.main()
