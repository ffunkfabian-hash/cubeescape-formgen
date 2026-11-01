# cubeescape-design

Zentraler Repo-Einstieg: [Nexogen](https://github.com/ffunkfabian-hash/cubeescape-nexogen) – Repo-Links, Zuständigkeiten, Abhängigkeiten und Live-Status über die Status-CLI im Nexogen-Repo. Globale Regeln dort, Fachwissen und Prüfbelege hier.

Gemeinsame Werkzeuge: Agent Tools (gepinnter Stand: `.ce-repo.json` › `tools_version`, derzeit 0.22.0), ohne eingebettete Kopie (seit claude-0.16.0): `./ce` ist der Lader; `./ce tools where` zeigt den Stand. Der Modellstand bleibt claude-0.15. [Bericht](claude/docs/versions/0.16.md).

**Status:** ruht – Formgen v2 entsteht nach dem Ausbau auf Basis von Critic und BALLON (Entscheidung des Nutzers 30.10.2026, Nexogen `repos.json`); der Bestand bleibt lesbar und baubar.

Waffen-Konzeptblätter für **Cube Escape**: Low-Poly-Sci-Fi, technisch konsistent, als Vorlage für 3D-Modellierung
(Mensch oder KI-Agent). Jede Waffe ist als kleines 3D-Modell in Python beschrieben. Alle Ansichten werden aus genau
diesem Modell gerendert und sind damit garantiert deckungsgleich.

Verbindliche Gestaltungsregeln: [`docs/masterprompt.md`](docs/masterprompt.md) (Concept-Art-Qualitäts-Masterprompt).

## Inhalt eines Konzeptblatts (4800 × 4432)

- Isometrische Hauptansicht **ohne Visier**, mit höchstens 8 deutschen Bauteil-Beschriftungen
- Sechs orthografische Ansichten (links, rechts, vorne, hinten, oben, unten) im gleichen Maßstab mit Bezugslinien
- Detail Abzugsbereich von schräg unten
- **Visier separat**: Optik ist ein modulares Anbauteil; auf der Waffe bleibt nur die Visierschiene
  (bei Raketenwerfern seitlich links am Rohr)
- Material & Texturen im Objektraum (lackiert, gebürstet, gummiert, matt, beleuchtet) mit Musterfeldern
- Texturprofil des Waffentyps (claude-0.9, Waffen 1–9): Gehäuse, Metall, Gummi, Energie, Kantenabnutzung, Toolgen-Decals
- Vier Farbvarianten derselben Geometrie (Basis, Cube Escape Standard, Arktis, Nacht)
- Prompt auf Deutsch und Englisch

## Visier-Serie VS01–VS09 (claude-0.6)

Zielbild der Visiere der Waffen 1–9 (Entscheidung des Nutzers 17.10.2026): je Waffe ein Blatt `VSnn.dc.html` im XL-Stil und ein
Sight-Spec `VSnn.spec.json` (Format `cubeescape-design/sight-spec`, [claude/docs/sight-spec.md](claude/docs/sight-spec.md)), beide aus
einem Modell (`claude/generator/vsmodels.py`). Blatt: Isometrie, Seite/Oben/Rück mit Visierlinie und Ankern, Durchsicht im Spiel,
vier Varianten, Fadenkreuz-Varianten (nur Bild), Bausteine (Glas-Tönungen, Rahmen, Tech-Module). Alle Fenster sind frei durchsichtig
(geprüft an der Geometrie). Bauen: `python3 claude/generator/export_sight.py` (Specs), `python3 claude/generator/build_vs.py` (Blätter).
Seit claude-0.7 tragen die Waffenblätter 1–9 dieses Visier (dasselbe Modell über `claude/generator/vsmount.py`, Farben der Waffe);
der Weapon-Spec verweist mit `sight.sight_spec` auf den Sight-Spec.

## Geometrie-Spec für Toolgen (claude-0.13)

Je Blatt ein `KXnn.geo.json` bzw. `VSnn.geo.json` (Format `cubeescape-design/geometry-spec` 1, [claude/docs/geometry-spec.md](claude/docs/geometry-spec.md)):
das Netz jedes Teils in Metern im Toolgen-Rahmen, Primitiv-Hinweise, Aufkleber als Polygone, Griff, Stützhand, Visier (`Socket_Eye`, `Socket_Reticle`)
und Anker – die Bauquelle, mit der Toolgen seine Waffen aus den Konzeptmodellen baut (Umsetzungsplan, Etappe DS-1). Erzeugen
`python3 claude/generator/export_geo.py`, prüfen `test_geo_spec.py`; die Dateien sind Release-Asset (`geo/`), im Repo stehen nur ihre Hashes.
Sichtprüfung in Blender: `geo_blender.py` (ein Modell), `geo_blender_skins.py` (claude-0.14: alle Farbvarianten und Skins eines Blatts als Szene,
Aufruf im Kopf der Datei; Ausgabe im Cache, nicht im Repo).

## Varianten

| Variante | Name | Idee |
|---|---|---|
| C | – | Neue Formen der Originalwaffen, je eigene Palette |
| D | – | Originalformen, konstruktiv überarbeitet, Farbvarianten |
| F | – | Neue Formen, mutige Paletten |
| G | – | Neue Formen in der Cube-Escape-Farbwelt (Creme, Anthrazit, Orange, Cyan) |
| H | – | „Werkstatt-Serie“: modulare Prototypen mit Klemm-/Schraubverbindungen |
| J | **Black Ice** | Stealth-Serie: wenige große, scharfe Facetten wie bei Tarnkappenjets, matte dunkle Grundtöne, eisblaue Leuchtkanten |

Neue Varianten bekommen einen englischen Namen (Regel in `CLAUDE.md`/`AGENTS.md`) und werden mit
`python claude/generator/new_variant.py <Buchstabe> "<Name>" "<Idee>"` angelegt; Register: `claude/generator/variants.py`.

Waffen je Variante: Pistole, Sturmgewehr, Impulsgewehr, Schrotflinte, Scharfschützengewehr, Maschinenpistole,
Fusionsgewehr, Spurgewehr, Raketenwerfer, Bogen.

**Neue Waffentypen (claude-0.10, Abgleich mit Destiny 2, [claude/docs/waffentypen.md](claude/docs/waffentypen.md)):** in Variante G die Blätter
KG11 Scout-Gewehr, KG12 Handfeuerwaffe, KG13 Lineares Fusionsgewehr, KG14 Spezial-Granatwerfer, KG15 Schwerer Granatwerfer, KG16 Maschinengewehr,
KG17 Schwert, KG18 Glefe, KG19 Schwere Armbrust, KG20 Raketenpistole, KG21 Raketen-Impulsgewehr, KG22 Slug-Schrotflinte, dazu seit claude-0.10.1
KG23 Hitze-Blaster, KG24 Mikroraketen-Granatwerfer, KG25 Streuschuss-Handfeuerwaffe (Modelle `g11.py`–`g25.py`,
Bauhelfer `tlib.py`, Typenkatalog `wtypes.py`). Seit claude-0.11 gibt es die 15 neuen Typen in allen Claude-Varianten
(KC11–KC25, KD11–KD25, KF11–KF25, KH11–KH25, KJ11–KJ25; Modelle `c11.py` … `j25.py`, gebaut von Codex als Unteragent), und alle 150 Waffenblätter
haben das Feld **BEDIENUNG** (Bestandsblätter: `ops.py`). Die neuen Typen sind in Toolgen/Cube Escape noch nicht angebunden
(`toolgen_id` null). Das Spurgewehr (KX08) heißt bei Toolgen seit 0.17 `trace_rifle` (bis claude-0.11 `scout_rifle`, Weapon-Spec seit claude-0.12 `format_version` 2; ältere Fassung = Release `claude-v0.11`); das echte Scout-Gewehr ist KG11 (`toolgen_id` null).

## Struktur

Die Stände sind **nach Erzeuger getrennt**: `claude/` enthält ausschließlich Claudes Pipeline und Konzepte,
`codex/` ausschließlich die von Codex. Gemeinsam ist nur `docs/` (Regeln und Aufträge). Siehe `CLAUDE.md` und `AGENTS.md`.

```
docs/                    gemeinsam: Regeln und Aufträge
  masterprompt.md        verbindliche Qualitätsregeln
  AUFTRAG.md             vollständiger Auftrag für Codex (inkl. Masterprompt)
  prompt-vorlagen.md     Vorlagen für ChatGPT-Bildgenerator und Codex
claude/                  nur Claude
  docs/                  weapon-spec.md, sight-spec.md (Formate), ENTSCHEIDUNGEN.md (Entscheidungen des Nutzers), versions/ (Berichte)
  prompts/               fertige Prompts je Waffe (DE/EN)
  generator/
    eng.py raster.py     Modell-API und Z-Buffer-Toon-Renderer
    views.py xl.py       Karte (2400×1560) und Konzeptblatt XL (4800×4432)
    v01m.py c02–c10.py   Modelle Variante C
    dmods.py dmodels.py  Modelle Variante D
    f01–f10.py g01–g10.py h01–h10.py
    jlib.py j01–j10.py   Facetten-Bausteine und Modelle Variante J „Black Ice“
    wtypes.py tlib.py    Typenkatalog (Destiny-Abgleich) und Bauhelfer der neuen Typen; g11–g25.py ihre Modelle (claude-0.10, 0.10.1),
                         c11–c25, d11–d25, f11–f25, h11–h25, j11–j25.py (claude-0.11)
    ops.py sketch.py     Bedienung der Blätter KX01–KX10; Schnellskizze eines Modells ohne Blatt (claude-0.11)
    variants.py          Varianten-Register (Buchstabe, Name, Idee); new_variant.py legt neue Varianten an
    build_*.py           Bauskripte je Variante, build_all.py baut alles; preview.py nimmt die Vorschauen auf
    export_spec.py       Spec je Blatt (KXnn.spec.json); test_spec.py, spec_checks.py (Richtung, Visier gegen CE-Zielbild)
    vsmodels.py vsheet.py  Visier-Serie: Modelle VS01–VS09 und Blatt; build_vs.py, export_sight.py (VSnn.spec.json), test_sight_spec.py
    vsmount.py           setzt das VS-Visier auf die Waffenblätter 1–9 (Schiene, Erhöhung, Kanalfarben)
    export_geo.py        Geo-Spec je Blatt (KXnn.geo.json, VSnn.geo.json, Bauquelle Toolgen); test_geo_spec.py, geo_blender.py (Sichtprüfung)
    geo_blender_skins.py Blender-Szene je Blatt: Farbvarianten und Skins wie auf dem Blatt (geo_textures.py: Katalog-Muster)
  output/
    sheets/              KXnn.spec.json und VSnn.spec.json (im Repo), fonts/ (Schriften, SIL OFL); Konzeptblätter KXnn.dc.html (KC01 … KJ10) nur lokal/Release
    previews/            WebP-Vorschauen (nur lokal/Release, werden auf dem Mac erzeugt)
  tests/                 golden.json (sha256 je Blatt und Spec), test_golden.py
  reference/crops/       Original-Seitenansichten (Referenz für Variante D)
codex/                   nur Codex (eigene Pipeline, eigene Konzepte; eingefroren seit 23.10.2026)
```

## Einrichten und bauen

```bash
pip install -r requirements.txt
playwright install chromium        # nur für Screenshots / Vorschauen
python claude/generator/build_all.py      # alles neu bauen (dauert, die XL-Blätter sind groß)
python claude/generator/build_all.py G J  # nur bestimmte Varianten
```

**Viewer:** `claude/output/index.html` zeigt alle Blätter mit Vorschau, Filter und Großansicht (`python claude/generator/make_viewer.py`,
läuft auch am Ende von `build_all.py`). Im normalen Browser per Doppelklick öffnen. Im Browser-Bereich der Claude-App lokale
Dateien nicht direkt öffnen, dort laden die Bilder nicht (statischer Schnappschuss). Stattdessen die Vorschau „viewer“ aus
`.claude/launch.json` starten (`python3 -m http.server 8765 --directory claude/output`, dann http://localhost:8765).

**Wo liegen die Blätter?** Seit claude-0.4.1 nicht mehr im Repo (waren 46 MB), sondern als Release-Asset (je Variante ein zip mit
Blättern, Specs und `fonts/`, ein zip Visier-Serie, dazu ein zip Vorschauen) oder per `build_all.py --nur-xl` lokal gebaut. Im Repo bleiben Generator, Specs und
`claude/tests/golden.json` (sha256, Prüfung: `python3 claude/tests/test_golden.py --full`).
Release-Weg: Blätter lokal bauen, dann `python3 claude/generator/release_assets.py` (Probelauf, packt nach `dist/`) und nach Freigabe des Nutzers
`--upload` (`gh release upload` an `claude-v<Version>`); der Workflow legt nur Tag und Release an.
Die Schriften (Chakra Petch, Barlow, JetBrains Mono, SIL OFL 1.1) liegen als Dateien neben den Blättern in `claude/output/sheets/fonts/`.
`claude/output/sheets/*.dc.html` sind Canvas-Artboards; zum Ansehen im Browser die Zeile
`<script src="./support.js"></script>` ignorieren bzw. entfernen.

## Modell-API (Kurzfassung)

Koordinaten: x = Längsachse (Mündung +x), y nach unten, z = Breite (z+ = linke Waffenseite).

```python
from eng import *
m = Model()
m.prism(profil_xy, farbe, z0, z1, r=8); label(m, 'Gehäuse')   # extrudiertes Seitenprofil, gerundete Ecken
m.cyl(x0, x1, y, z, radius, farbe);     label(m, 'Lauf')      # Zylinder entlang x
m.decal('z+', z, punkte, farbe, emit=True)                     # Detail auf einer Fläche (beidseitig)
m.prism(...); sight(m)                                          # Visierteil -> wird separat gezeichnet
```

Regeln (aus dem Masterprompt): Abzug mit Bügel auch in der Isometrie sichtbar, Magazin im Schacht, sichtbarer Lauf,
keine schwebenden Teile, keine ungewollten Durchdringungen (koplanare Teile ≥ 1 Einheit versetzen), max. 8 Labels.

## Mit Codex weiterarbeiten

Seit 23.10.2026 gibt es nur noch die Claude-Pipeline (Entscheidung des Nutzers): `codex/` ist eingefroren und bleibt als
Bestand lesbar; Codex hilft nur noch als Unteragent einer Claude-Sitzung unter `claude/`. `docs/AUFTRAG.md` (kompletter Auftrag
inklusive Masterprompt) bleibt die Grundlage dafür.

## Bekannte Grenzen

- Texturen sind prozedurale Muster für Konzeptblätter, keine UV-Texturen.
- Farbvarianten werden automatisch nach Bauteil-Rollen umgefärbt; einzelne Akzente können an ungewohnter Stelle landen.
- Gestalterische Referenz, keine bemaßte Fertigungszeichnung.
