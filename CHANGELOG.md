# CHANGELOG

Einträge je Erzeuger: `claude-…` (Ordner `claude/`), `codex-…` (Ordner `codex/`).

## claude-0.19.0 „Afterburner“ – 2026-10-24

- Release-Vollbau schneller, Ausgabe bytegleich (`golden.json` unverändert): WebP-Kodierung der Blattbilder (71 % der Blattzeit) läuft in Threads parallel zur numpy-Arbeit (`raster.deferred`), `build_all.py` baut alle 159 Blätter (Waffen + VS) in einem Prozess-Pool je Blatt (Prozesszahl nach RAM), Ankersuche im Bauteilrahmen, Determinismus-Seeds in `test_golden --full` parallel.
- Gemessen (`--nur-xl --force`): vorher ≈ 45 min (92 von 150 Waffenblättern in 23,6 min), nachher 27:37 min; `test_golden --full` 34 s. Bericht [claude/docs/versions/0.19.md](claude/docs/versions/0.19.md).
- Release über den Inhalts-Cache plus erzwungene Stichprobe (Entscheidung des Nutzers 24.10.2026): `build_all.py --nur-xl --release` baut Cache-Fehltreffer, seit dem letzten `claude-v*` geänderte und 10 zufällige Blätter frisch und bricht bei Abweichung von `golden.json` ab; gemessen 2:05 min + `test_golden --full` 28 s. Volle Regression (`--force`) bleibt im Nachtlauf.

## claude-0.17.2 – 2026-10-24

- Golden-Blatt-Hashes KG02 und KG06 nach frischem Bau (`build_all.py --nur-xl --force`) neu; alle übrigen Blätter, Specs, Geo- und Visier-Hashes unverändert. KG02 ist bytegleich zum Blatt aus claude-v0.15.1 (der Schienenkanal `MT_Metal` aus 0.15.2 steht nur in Spec/Geo; der Wert von 0.15.2 ließ sich auf 3d23912 selbst nicht nachbauen).
- KG06 am Bild geprüft: Beschriftung „Vordergriff“, dadurch Material `rubber` (Gummi-Muster creme, Vordergriff im Hauptskin creme statt orange wie die übrigen Griffe), Prompt-Teileliste mit Vordergriff – genau die Änderung aus 0.16.2.
- `claude/prompts/Waffen-Prompts.md` von `mkdoc.py` nachgezogen: KG01 mit Kimme und Korn statt VS01 (Stand 0.17.1).

## claude-0.17.1 – 2026-10-24

- Patch KG01 (Pistole): Reflexvisier VS01 (p13–p26) und die angefügte Visierschiene (p12) entfallen; Kimme (Sockel, Kerbe zwischen zwei Pfosten) und Korn (Keil) sitzen fest auf dem Schlitten p06 und laufen im Bewegungsteil `slide` mit (Entscheidung des Nutzers 24.10.2026, Toolgen Sidearm 0.27). p00–p11 bleiben, p12–p15 sind Kimme/Korn.
- Spec additiv (`format_version` 2): Anker `Socket_Sight` = Oberkante der Kimmenkerbe, neu `Socket_FrontSight` = Kornspitze (gleiche Höhe, Visierlinie parallel zur Mündungsachse), `sight.iron` (Kimmenbreite 0,0133 m, Kerbe 0,0039 m, Korn 0,0028 m), `moving_parts.items[].riding_parts`; Schema und `weapon-spec.md` › Kimme und Korn. Nur KG01-Spec, -Geo und -Blatt ändern sich; `golden.json` nur KG01. Bericht [claude/docs/versions/0.17.md](claude/docs/versions/0.17.md#patch-0171--kg01-kimme-und-korn).

## claude-0.17.0 „Tethered“ – unveröffentlicht

- Scout-Gewehr (KC11, KD11, KF11, KG11, KH11, KJ11) an Toolgens Werkzeug `scout_rifle` (Toolgen 0.24) angebunden: Spec `toolgen_id` `scout_rifle`, `element` `energy`, `toolgen_status` `tool`, Use-Clip nicht mehr `proposed`; `wtypes` mit `retro`/`has_tool` (Blatt bleibt Nachrüst-Typ). Weapon-Spec `format_version` bleibt 2. [Versionsbericht](claude/docs/versions/0.17.md).

## claude-0.16.2 – 2026-10-24

- Patch KG06: Vordergriff (p09) trug keine Bezeichnung; `Socket_SupportHand` fiel auf den Laufmantel zurück. `g06.py` beschriftet ihn „Vordergriff“ (Spec: Anker p09, Material `rubber`, `support_forward_m` 0.1996); Tests `test_support_hand_is_foregrip`, `test_kg06_foregrip_labelled`; Golden Spec/Geo neu. Blatt-Hash KG06 ändert sich (Beschriftung), neu beim nächsten `--full`-Lauf auf dem Mac.
- KG11 (`toolgen_id`/`element` null) ist laut claude-0.12 Sollzustand; Toolgen führt `scout_rifle` (element `energy`) seit 0.24 – Anbindung offen, eigener Auftrag.

## claude-0.16.1 – 2026-10-24

- Werkzeug-Pin auf ce-agent-tools 0.22.0 „Tollgate“ (`9f1ed12`, vorher 0.20.0 `6e9e823`): `./ce session say/mail` mit Courier-Verbesserungen (Modellzeile, Kopie an Sightline bei PR/Merge, `ce-freigabe`-Erkennung, `--follow`), Merge-Sperre im Plugin; `.ce-repo.json`, `./ce`, PR-Check-Schritt. Kein Verhalten des Generators geändert.

## claude-0.16.0 „Ungrafted“ – unveröffentlicht

Nur Werkzeuge; Blätter, Specs und Golden unverändert.

- Keine eingebettete Werkzeugkopie mehr: `tools/ce_tools/` entfällt, `./ce` ist der Lader aus Agent Tools 0.20 „Lodestar“, `.ce-repo.json` › `tools_version` pinnt Commit `6e9e8235dd04` (statt `tools_dir`). Wie Motiongen 0.13, Robogen 1.23 und Cubegen 0.33.
- `.mcp.json` (`ce-search` über `./ce search serve`), `check.nightly` (`./ce lock gpu`) und `check.yml` (Aktion `ce-tools@6e9e823`) nutzen den Lader; die Links `.claude/agents/ce-*.md` entfallen (Profile kommen mit dem Plugin).
- Neu `.ce-repo.json` › `tidy` für die Generator-Zwischenstände `claude/generator/reg` und `final`. [Versionsbericht](claude/docs/versions/0.16.md).

## claude-0.15.3 – 2026-10-23

- Eine Pipeline (Entscheidung des Nutzers): neue Konzeptarbeit nur noch unter `claude/`, `codex/` (Parallax, Flux Bloom) eingefroren als lesbarer Bestand; Codex nur noch als Unteragent einer Claude-Sitzung. Regeln in `CLAUDE.md`, `AGENTS.md`, README und `claude/docs/ENTSCHEIDUNGEN.md`; keine Änderung an Blättern, Specs oder Golden.

## claude-0.15.2 – 2026-10-22

- Holo-Familie: Typregel `vsmount.VS_TYPE` – alle Impulsgewehr-Blätter tragen das Holo-Visier VS02 (KC03, KD03, KF03, KH03, KJ03 neu, KG03 schon seit 0.15.1); `spec_checks.CE_SIGHTS` Zeile 3 folgt CE 0.111.1 (Holo, offenes Fenster).
- KG02-Schiene p10: 30 Quadrate `#33343A` auf `MT_Metal` statt `MT_Secondary` (unter `base` beige, Befund Toolgen 0.23); ausdrücklicher Aufkleber-Kanal `dch` je Bau-Eintrag.
- Altfehler: `fgen.board` übergibt `FONT_CSS` (2D-Karten F/G/H 01–05 bauen wieder), KG08-Text nennt das Zielverfolgungs-Visier VS08 statt „Zielfernrohr auf zwei Ringen“. Bericht [claude/docs/versions/0.15.md](claude/docs/versions/0.15.md#patch-0152--holo-familie).

## claude-0.15.1 – 2026-10-22

- Stützgriff: KG03 und KG08 bekommen einen „Vordergriff“ (`late=True`, KG03 `p40` vor der Energiezelle, KG08 `p43`); `Socket_SupportHand` jetzt ableitbar: KG03 y −0,272 / z 0,024 m, KG08 y −0,250 / z 0,057 m (vorher „nicht ableitbar“).
- KG03: Holo-Visier VS02 statt Präzisions-Röhre VS03 (Ausnahme je Blatt `vsmount.VS_SHEET`, Entscheidung des Nutzers 22.10.2026) und Salve aus drei statt vier Impulsen.
- Golden nur KG03/KG08 (Spec, Blatt, Geo); alle übrigen 148 Waffen- und 9 Visier-Blätter bytegleich. Bericht [claude/docs/versions/0.15.md](claude/docs/versions/0.15.md#patch-0151--stützgriff).

## tools-0.16 „Tidemark“ – 2026-10-22

- Gemeinsame Werkzeuge über `ce_sync.py` aus Agent Tools 0.16 (ce-agent-tools#15): `./ce plugins check|fix` hält die Claude-Code-Installationen von ce-shared auf einer Version (je Worktree ein Eintrag, Update erreicht sie nicht sicher); der SessionStart-Hook des Plugins warnt bei älterem ce-shared.
- Hinweis in `AGENTS.md` › Plugins und Hooks; fachliche Versionen und Ausgaben unverändert.

## tools-0.15.1 „Wakeline“ – 2026-10-22

- Gemeinsame Werkzeuge über `ce_sync.py` aus Agent Tools 0.15.1 (ce-agent-tools#13, #14): `./ce session mail` braucht keinen Namen mehr und teilt den Stand mit dem neuen Stop-Hook des Plugins, der den Postfach-Wächter für reservierte Sitzungen selbst startet (am Mac live geprüft); `say` nimmt den Absender aus der Reservierung des Worktrees.
- Hook-Beschreibung in `AGENTS.md` › Plugins und Hooks ergänzt; fachliche Versionen und Ausgaben unverändert.

## tools-0.14.0 „Crosstalk“ – 2026-10-22

- Gemeinsame Werkzeuge über `ce_sync.py` aus Agent Tools 0.14 synchronisiert: `--reserve`/`./ce session patch` melden die Sitzung im Postfach (cubeescape-nexogen#16) an, `./ce session say|who` schreiben Sitzungen einander bzw. listen die angemeldeten.
- Eigenständiger Werkzeugpaket-Stand; fachliche Versionen und Ausgaben unverändert.
- Abnahme über [Tools #12](https://github.com/ffunkfabian-hash/ce-agent-tools/pull/12) (401 Tests, Opus-Richter), `ce_sync --check` und Repo-Quick.

## tools-0.13.0 „Glasshouse“ – 2026-10-22

- Gemeinsame Werkzeuge über `ce_sync.py` aus dem geprüften Agent-Tools-Quellstand 0.13 synchronisiert: Dashboard, Belegvergleich, Vorprüfung, Durchlaufmessung und strengere Cloud-/Vertragsprüfungen.
- Eigenständiger Werkzeugpaket-Stand; fachliche Versionen und Ausgaben unverändert, bestehende Gatehouse-Hooks werden nicht neu installiert.
- Abnahme über [Tools #11](https://github.com/ffunkfabian-hash/ce-agent-tools/pull/11), Quellhash-Abgleich, Repo-Quick und Doku-Prüfung.

## tools-0.12.0 „Gatehouse“ – 2026-10-22

- Gemeinsame Werkzeuge über `ce_sync.py` aus der freigegebenen Quelle Agent Tools 0.12 synchronisiert, einschließlich der Korrektur für ältere Toolgen-Prüfschnittstellen aus 0.11.1.
- Hook-Beschreibung in `AGENTS.md` ergänzt: gemeinsame Client-Vorabprüfung und unabhängiges Git-Netz werden separat über Nexogen installiert; Einbau und Grenzen bleiben zentral dokumentiert. Modellstand claude-0.15 und Codex-Varianten unverändert.
- Eigenständiger Werkzeugpaket-Stand; Abnahme durch Quellfreigabe [Tools #10](https://github.com/ffunkfabian-hash/ce-agent-tools/pull/10), Hash-Abgleich, Repo-Quick und Doku-Prüfung.

## tools-0.11.0 „Wayfinder“ – 2026-10-22

- Gemeinsame Werkzeuge über `ce_sync.py` auf die geprüfte Agent-Tools-Quelle 0.11.0 aktualisiert: korrigierte inkrementelle FTS-Schreibzugriffe, öffentliche Such-Aliase und gemeinsame Prüf-/API-Werkzeuge.
- Reiner Werkzeug-Rollout; Modellstand claude-0.15 und Codex-Varianten unverändert. Die offene Ladehebel-Ergänzung in `claude/prompts/Waffen-Prompts.md` bleibt separat im Haupt-Checkout erhalten.
- [Werkzeug-Abnahme](docs/versions/tools-0.11.md).

## claude-0.15 „Rackshot“
- KG02 (Sturmgewehr, Variante G) bekommt den Ladehebel `p32` (Bezeichnung „Ladehebel“, Material `painted`, Schwarz) an der linken Gehäuseseite (Toolgen +X):
  `moving_parts.items[0]` = `bolt`/`Anim_Bolt`, `parts` `["p32"]`, `match` `label` (vorher `null`); Verfahrweg 50 mm nach hinten (+Y) frei. Anlass: Rückfrage Toolgen 0.18 „Bedrock“.
- Neu: Anbauteile mit `late=True` stehen hinter dem Visier in der Teileliste, so bleiben p00–p31 unverändert (`vsmount`, `skins.Frame` ohne diese Teile). Format, Schema, Skins
  und alle anderen Blätter unverändert; Weapon-Spec 2 und Geo-Spec 1 nur für KG02 neu, Golden nur die drei KG02-Zeilen. Bericht [claude/docs/versions/0.15.md](claude/docs/versions/0.15.md).

## claude-0.14 „Livery“
- Alle 150 Waffenblätter als Blender-Szenen wie auf dem Blatt: vier Farbvarianten mit Hauptskin, dazu die übrigen vier Skins; Skin-Lagen des Weapon-Specs
  (Flächen, Streifen, Verläufe, Ringe, Glyphen, Schmuckteile, Kantenabnutzung) im Shader, Katalog-Texturen, Chrom/Gold/Neon (`geo_blender_skins.py`).
- `geo_textures.build` mit optionalem Skin-Haken; Specs, Blätter und Golden unverändert. Bericht [claude/docs/versions/0.14.md](claude/docs/versions/0.14.md).

## codex-0.1.6 / codex-0.2.6 „Switchcraft“ (PR #14, gemerged)
- Parallax (0.1.6) und Flux Bloom (0.2.6): alle Specs auf Weapon-Spec `format_version` 2, Spurgewehr KA08/KK08 mit `toolgen_id` `trace_rifle`
  (Mindestabnehmer Toolgen 0.17.0 / Cube Escape 0.98; ältere Fassung `git show 5a5615d:codex/parallax/output/KA08.spec.json`, analog KK08).
- Feld BEDIENUNG und Spec `operation` auf den 20 Bestandsblättern (unten 400 px ergänzt, bisherige Bildflächen pixelgleich).
- Je 15 neue Konzepte Nr. 11–25 in A und K (30 neue, 50 Blätter gesamt): `toolgen_id` null, Status `not_connected`, Bewegungen und Texturprofile als Vorschlag.
- Mac-Abnahme unter `heavy_lock`: 105 Tests grün, 50 Specs gegen beide Format-2-Schemas ohne Befund, 50 Chromium-Blätter ohne Überlauf.
  Berichte [Parallax 0.1.6](codex/docs/versions/0.1.md#patch-016-switchcraft-19102026), [Flux Bloom 0.2.6](codex/docs/versions/0.2.md#patch-026-switchcraft-19102026).

## claude-0.13
- Geometrie-Spec `KXnn.geo.json`/`VSnn.geo.json` (neues Format `cubeescape-design/geometry-spec` 1, Etappe DS-1 des Umsetzungsplans Modelle): Netz je Teil in Metern
  im Toolgen-Rahmen, Primitiv-Hinweise, Aufkleber als Polygone, Griff (Achse, Neigung, Abzug), Stützhand-Querschnitt, Visier mit `Socket_Eye`/`Socket_Reticle`, Anker;
  `surface` mit dem eigenen Texturprofil je Waffentyp und der Kantenabnutzung in m; `string`-Block für Bogen und Armbrust (Sehnenspitzen, Nockpunkt, Pfeilachse, Auflage; Entscheidung 19.10.2026: Bogen sofort in TG-A).
- 159 Dateien aus `export_geo.py`, Test `test_geo_spec.py`, Golden-Gruppe `geo`, Release-Asset `geo/`; Blätter, Weapon-Spec 2 und Sight-Spec 2 unverändert.
- Befunde als Daten für Toolgen: 916 koplanare Teilpaare (Z-Fighting-Gefahr), 28 Aufkleber über ihr Teil hinaus, KC10-Wurfarme mit Innen-Normalen (im Export gerichtet).
  Bericht [claude/docs/versions/0.13.md](claude/docs/versions/0.13.md).

## claude-0.12
- Namenskonflikt `scout_rifle` gelöst (Toolgen 0.17.0 „Retrace“, Cube Escape 0.98 „Recast“): Spurgewehr KC/KD/KF/KG/KH/KJ08 und VS08 tragen `toolgen_id` `trace_rifle`;
  KG11 bleibt `toolgen_id` null. Weapon-Spec und Sight-Spec `format_version` 2 (Bedeutungswechsel); ältere Fassung für Abnehmer mit Toolgen < 0.17: Release `claude-v0.11`.
- Blätter und Bilder unverändert, nur Specs und `golden.json`. Bericht [claude/docs/versions/0.12.md](claude/docs/versions/0.12.md).

## claude-0.11
- Die 15 neuen Typen Nr. 11–25 in allen Claude-Varianten: 75 neue Konzepte KC/KD/KF/KH/KJ11–25 im Stil der Variante, gleiche Mechanik wie G,
  eigene Silhouette; Modelle von Codex (`gpt-6.1-sol`) als Unteragent, Probeblatt je Variante vom Nutzer freigegeben, von Claude geprüft.
- Feld BEDIENUNG und Spec `operation` auf allen 60 Bestandsblättern (`ops.py`, Texte je Blatt nach Bauweise); sonst bleiben die Blätter gleich.
- Hohle Grundrisse quer zur Waffe (`tlib.B.Y`) richtig schattiert; Schnellskizze `sketch.py`. 150 Waffenblätter, 159 mit Visierserie.
  Bericht [claude/docs/versions/0.11.md](claude/docs/versions/0.11.md).

## claude-0.10.1
- Drei Lücken aus 0.10 als eigene Konzepte in Variante G: KG23 Hitze-Blaster (Impulsgewehr ohne Magazin, Hitzespeicher, Entlüftungsklappen),
  KG24 Mikroraketen-Granatwerfer (einschüssig, Abschussrohr, Raketenvorrat), KG25 Streuschuss-Handfeuerwaffe (Kipprahmen-Revolver, Streumündung).
- Spec additiv: Untertypen `dynamic_heat`, `micro_missile`, `spread_shot`; Bewegungsarten `vent`, `top_break` (Vorschlag); bestehende 72 Blätter bytegleich.
  Bericht [claude/docs/versions/0.10.md › 0.10.1](claude/docs/versions/0.10.md#patch-0101--lücken-kg23kg25).

## claude-0.10
- Abgleich mit dem Destiny-2-Katalog (17 Typen, schwere Armbrust seit 2025, Untertypen): Bestands- und Maßnahmenübersicht
  [claude/docs/waffentypen.md](claude/docs/waffentypen.md); `weapon.design_type` u. a. in allen Specs (additiv), Spurgewehr = `trace_rifle`.
- Zwölf neue Konzepte in Variante G (KG11–KG22): Scout-Gewehr, Handfeuerwaffe, lineares Fusionsgewehr, Spezial- und schwerer Granatwerfer,
  Maschinengewehr, Schwert, Glefe, schwere Armbrust, Raketenpistole, Raketen-Impulsgewehr, Slug-Schrotflinte; neues Blattfeld BEDIENUNG, Spec `operation`.
- Neue Typen nicht angebunden: `toolgen_id` null, Bewegungen als Vorschlag (`proposed`), Texturprofile abgeleitet; bestehende 60 Blätter bytegleich.
  Bericht [claude/docs/versions/0.10.md](claude/docs/versions/0.10.md).

## codex-0.1.5 / codex-0.2.5 (PR #7, gemerged)
- Parallax (0.1.5) und Flux Bloom (0.2.5): Texturprofil auf den neun Waffenblättern KA01–KA09/KK01–KK09 (Feld TEXTURPROFIL, Material-IDs des
  Katalogs, Kantenabnutzung, Toolgen-Decals) und additiver Block `texture_profile` im Weapon-Spec v1 (`format_version` 1); Bögen KA10/KK10 unverändert.
- Chromium-QA und Specs auf dem Mac geprüft (97 Tests grün, `spec_checks` 0 Befunde auf 20 Specs); Stilmedian-Prüfung mit Toleranz eines Rundungsschritts.
  Berichte [Parallax](codex/docs/versions/0.1.md), [Flux Bloom](codex/docs/versions/0.2.md).

## claude-0.9
- Texturprofil auf den Blättern (Entscheidung des Nutzers 18.10.2026): neues Feld **TEXTURPROFIL** unter der Materialansicht mit sechs Kacheln
  (Gehäuse, Metall, Gummi, Energie mit Material-ID des Katalogs und Kurztext, Kantenabnutzung mit Stufe, Toolgen-Decals) auf allen 54 Blättern der Waffen 1–9;
  Bögen ohne Profil und unverändert. Materialansicht dafür niedriger, Blattgröße gleich.
- Prompts (de/en, Blatt und `claude/prompts/Waffen-Prompts.md`) nennen das Texturprofil (Kurztexte bzw. Materialien, Abnutzung, Toolgen-Decals); Bögen unverändert.
  Schrift im Prompt-Feld nur bei Bedarf kleiner (`xl.prompt_font`, 18 → 14 px), Feld gleich groß.
- `texprofile` im Cache-Schlüssel (`sheetcache.COMMON`/`CODE_PARTS`); Spec unverändert (kein Vertragswechsel). Bericht [claude/docs/versions/0.9.md](claude/docs/versions/0.9.md).

## claude-0.8
- Pipeline liest den gemeinsamen Texturkatalog `docs/textures/catalog.json` (`texcat.py`): Muster der Materialansicht in mm am Objekt (mit der Modelleinheit
  des Blatts umgerechnet, gleiche Rändelung auf jeder Waffe gleich fein), Skins, Tonleitern und Kantenabnutzung aus dem Katalog; Katalog-Inhalt im Cache-Schlüssel.
- Spec (additiv, format_version 1): `parts[].texture`, `skin.catalog_id`/`items[].catalog_id`, `textures.catalog`; `texture_profile` je Waffentyp (Textur-Blatt:
  Material-IDs, Abnutzungsstufe, Toolgen-Decals; Waffen 1–9) – damit ist die Decal-Zuordnung zu Toolgen erledigt.
- Black Ice (J) bevorzugt bei Gleichstand dunkle Hauptskins; andere Varianten unverändert.
- Inhalts-Cache für Blätter (`claude/generator/sheetcache.py`): `build_all.py`/`build_xl.py`/`build_vs.py` bauen nur Blätter neu, deren Schlüssel
  (Modell, Palette/Skin, Quelltext der schreibenden Funktionen `CODE_PARTS`) sich geändert hat; Cache außerhalb des Repos. `--force` (alles neu, Einträge
  erneuert) und `CE_NO_CACHE=1` (Cache ganz aus) umgehen den Cache; `full`-Check (`test_golden --full`) und Release immer ohne Cache. Test `claude/tests/test_sheetcache.py`.
- Alle 60 Waffenblätter und Specs neu (Musterfeinheit; KJ: Skin-Auswahl), Visier-Serie unverändert. Bericht [claude/docs/versions/0.8.md](claude/docs/versions/0.8.md).

## codex-0.1.4 / codex-0.2.4 (PR #5, gemerged)
- Parallax und Flux Bloom: Die Augenmuschel von VS03/VS05 öffnet mit dem Okularradius statt mit dem Bohrungsradius (Öffnung ≥ Okularglas, Außenmaße ±0,5 mm);
  betroffen KA03/KA05/KK03/KK05. Claudes `spec_checks`: 0 Befunde; Stilwerte unverändert. (Befund der Zweitprüfung von PR #4.)

## codex-0.1.3 / codex-0.2.3 (PR #4, gemerged)
- Parallax (0.1.3) und Flux Bloom (0.2.3): KA01–KA09 und KK01–KK09 tragen das Standardvisier VS01–VS09 (nachgebaut nach `VSnn.spec.json`, ±0,5 mm,
  Montage auf der Schiene, Glas, Strahlprüfung über die ganze Öffnung; KK03 mit Erhöhung 33 mm); Bögen behalten den Pin (Pin/Leuchtpunkt entlang −Y,
  `Socket_Sight` Unterkante-Mitte). Das Visier sitzt auf den Blättern nicht auf der Waffe (Hauptansicht „ohne Optik“, Feld „Visier · separat“; Entscheidung 18.10.2026).
- Claudes `spec_checks` auf allen 20 Specs: 58 → 0 Befunde; Berichte [Parallax](codex/docs/versions/0.1.md), [Flux Bloom](codex/docs/versions/0.2.md).

## codex-0.1.2 / codex-0.2.2 (PR #3, gemerged)
- Stilvertrag (Konturen, kameragebundenes Licht, große Orthos langer Waffen), Weapon-Spec v1 (`KAnn.spec.json`/`KKnn.spec.json`) und gemeinsamer Texturkatalog
  `docs/textures/` (physische Mustergrößen, Katalog-IDs); 20 Blätter neu gebaut, Modelle und Paletten unverändert.

## claude-0.7
- Waffenblätter 1–9 (C, D, F, G, H, J) tragen das Standardvisier ihres Typs aus der Visier-Serie VS01–VS09 (`vsmount.py`, Modell aus
  `vsmodels.py`, Farben über die MT_-Kanäle der Waffe, Sitz auf der Visierschiene; 15 Blätter mit neuer Schiene, 5 mit Erhöhung).
- Spec (additiv, format_version 1): `sight.sight_spec` (Verweis `VSnn.spec.json`, Lage, Erhöhung, Anker), `material: glass`; Typ/Rahmen aus der Serie.
- Die 23 Querfenster sind behoben (`KNOWN_CROSS_WINDOWS` leer), Bogen-Pins fluchten entlang −Y, Visier-Hinweise 0; Test `VisierSerie`.
- Glas ohne Schraffur (Wunsch des Nutzers): getönte Fläche mit weichem Glanz; VS01–VS09 neu gebaut.
- Bericht [claude/docs/versions/0.7.md](claude/docs/versions/0.7.md).

## claude-0.6.1
- Gemeinsamer Texturkatalog [docs/textures/](docs/textures/README.md) (`cubeescape-design/texture-catalog` v1): Materialien nach Toolgen-Namen, Muster in mm
  (Median-Maßstab der 60 Specs als Startwert), Oberflächen mit Tonleitern und Kantenabnutzung, 14 Skins (9 Claude, 5 Codex), Kanäle; 24 Musterbilder.
- `make_swatches.py` (nur aus `catalog.json`), `check_catalog.py` (Schema, sha256, Abgleich mit Toolgen `surface_recipes.json`); Teil von `./check`.
  Claudes Pipeline liest den Katalog noch nicht (eigener Schritt mit Bildstufe); Bericht [claude/docs/versions/0.6.md](claude/docs/versions/0.6.md).

## claude-0.6
- Visier-Serie VS01–VS09: je Waffe 1–9 ein Blatt im XL-Stil aus einem Modell (`vsmodels.py`, `vsheet.py`, `build_vs.py`): Isometrie,
  Seite/Oben/Rück mit Visierlinie und Ankern, Durchsicht im Spiel, vier Varianten, Fadenkreuze (nur Bild), Bausteine.
- Neues Format `cubeescape-design/sight-spec` v1 (`VSnn.spec.json`, [claude/docs/sight-spec.md](claude/docs/sight-spec.md), Schema, Test):
  Fenster, Rahmen, Glas-Tönung (RGBA linear), Röhre, Modul, Anker `Socket_Mount`/`Socket_Sight`/`Socket_Reticle`/`Socket_Eye`, Verweis
  auf die Waffen-Specs. Freie Durchsicht an der Geometrie geprüft (Visierlinie, ganze Öffnung, Funktionsfläche); 60 Waffenblätter unverändert.
- Raster: Glas durchscheinend (nur mit `glass=`, Waffenblätter bytegleich); Viewer-Gruppe „VS“; Bericht [claude/docs/versions/0.6.md](claude/docs/versions/0.6.md).

## claude-0.5.2
- Spec (additiv, format_version 1): `sight.type` (neun Typen des Visiertypen-Blatts plus `iron`/`pin`, `kind` folgt daraus),
  `sight.frame` (Rahmen-Variante), `parts[].toolgen_material` (Toolgen-Materialien); Visier-Hinweise vergleichen jetzt den Zieltyp.
- Richtungstest an der Funktionsfläche (`spec_checks.window_problems`, wiederverwendbar für VS01–VS09): Seitenscheiben, Öffnungen
  und Ringe zählen als Fenster; 23 bekannte Querfenster datiert im Test (Fix mit der Umstellung auf VS01–VS09), Gegenbeweis je Fall.
- Entscheidungen: Visier-Serie VS01–VS09 wird Zielbild, Waffenblätter werden danach umgestellt; Vokabular wie vorgeschlagen; Querfenster
  „Test jetzt, Fix mit Umstellung“.

## claude-0.5.1
- Spec (additiv, format_version 1): `robot_fit` – Größe in der Roboterhand (CE 0.82): Zielzahlen mit Quelle, Blatt auf Ziellänge
  gemessen; Pistole und Bogen ausgenommen; keine Roboter-Konzeptblätter.
- Visier-Abgleich aller 60 Blätter gegen die Visier-Blätter des Nutzers ([claude/docs/visier-abgleich.md](claude/docs/visier-abgleich.md)):
  6 passen, 46 weichen als Blatt ab, 19 mit Fenster quer zur Laufachse; Vorschlag `sight.type`/`frame`; Abgleich mit Toolgen-Mustern/Decals.
- ENTSCHEIDUNGEN.md: MP4 nur auf Anfrage, keine Roboter-Blätter, `robot_fit`, Visier-Zielbild.

## claude-0.5
- Spec (additiv, format_version 1): `moving_parts` und `parts[].moving` (bewegliche Teile wie Toolgens Use-Clip, Wurzel fest, Zuordnung
  über Bezeichnungen, sonst `null` mit Grund), `sight.window_geometry` (Fenster mit Durchsichtachse aus der Geometrie), `anchors.*.part`.
- `Socket_Muzzle` am vorderen Ende der Mündungsachse (17 Blätter: Mündungskappe/Pfeilspitze mitgezählt, Rakete im Rohr nicht).
- Richtungstest mit Gegenbeweis (gespiegelte Achsen), Visier gegen CE-Zielbild als Hinweisliste (`spec_checks.py`); `claude/docs/ENTSCHEIDUNGEN.md`.
- Bericht: [claude/docs/versions/0.5.md](claude/docs/versions/0.5.md), Format: [claude/docs/weapon-spec.md](claude/docs/weapon-spec.md)

## claude-0.4.1
- Golden nur als sha256 (`claude/tests/golden.json`, Blätter und Specs), Test `claude/tests/test_golden.py` (quick: Specs, Determinismus,
  Gegenbeweis; `--full`: Blätter, Determinismus eines Blatts). Blätter waren nicht reproduzierbar: `hash()` in `xl.swatch_svg` (je Prozess
  anderes IDs) → `zlib.crc32`; alle 60 Blätter neu gebaut, nur diese IDs ändern sich.
- `shot.py`: PNG ohne date/time-Chunks, 8 Bit (ImageMagick 6 und 7); `report.md` ungetrackt.
- Repo-Größe: Blätter (`*.dc.html`) und Vorschauen nicht mehr im Repo, sondern Release-Asset (je Variante ein zip, dazu Vorschauen;
  `claude/generator/release_assets.py`, Upload per `gh release upload` vom Mac, `release.yml` legt nur Release an); WebP-Qualität 92 → 60. Historie unverändert.
- Schriften als Dateien mit echten Gewichten (Chakra Petch 400–700, Barlow 400–600, JetBrains Mono variabel, SIL OFL 1.1) in `claude/output/sheets/fonts/`, relative `@font-face` statt Google Fonts.

## claude-0.4
- Neue Variante **J „Black Ice“**: zehn Stealth-Waffen (KJ01–KJ10) aus Facettenkörpern (`jlib.py`: abgeschrägte Prismen,
  Sechs-/Achtkant-Läufe, eisige Leuchtkanten), Blätter, Vorschauen, Specs und Prompts.
- Regel: neue Varianten bekommen einen englischen Namen; Register `variants.py`, Anlage mit `new_variant.py` (prüft die Regel).
- Spec: `sheet.variant_name` (additiv); `preview.py` nimmt die WebP-Vorschauen auf; `mkdoc.py` behält Abschnitte bei Teilbau.
- Bericht: [claude/docs/versions/0.4.md](claude/docs/versions/0.4.md)

## claude-0.3
- Skins: Katalog mit 9 gestalteten Skins (Farbflächen, eigene Glyphen/Zahlen/Embleme, Streifen/Verläufe/Ringe, Gold/Chrom mit
  Kantenabnutzung, Rippen/Finnen), je Waffe fünf; Farben aus den MT_-Kanälen plus zwei feste Skin-Akzente, Kontrastregel.
- Konzeptblätter: Hauptskin in Isometrie, Orthos und Farbvarianten, neue Reihe SKIN/MUSTER (Blatt 4800×4432), Prompts nennen den Skin.
- Spec: Feld `skin` (additiv, format_version 1) mit Lagen im Toolgen-Rahmen und neuen Mustertypen; Test 12 Fälle.
- Bericht: [claude/docs/versions/0.3.md](claude/docs/versions/0.3.md), Format: [claude/docs/weapon-spec.md › Skins](claude/docs/weapon-spec.md#skins)

## claude-0.2
- Weapon-Spec je Konzeptblatt (`claude/output/sheets/KXnn.spec.json`, 50 Dateien): Element, Kanal-Paletten der vier
  Farbvarianten, Bauteile, Visier, Aufkleber, Maße, Anker, Texturmuster – für Toolgen ohne Bildlesen.
- Exporter, Schema und Test ohne numpy (quick-Check); ausdrückliche Kanalzuordnung `channel()`/`ch`.
- Bericht: [claude/docs/versions/0.2.md](claude/docs/versions/0.2.md), Format: [claude/docs/weapon-spec.md](claude/docs/weapon-spec.md)

## claude-0.1.2
- Detailfeld „Abzugsbereich“: Griff, Abzug und Bügel mittig unter der Feldüberschrift (Rahmen aus der sichtbaren Box, Magazin im
  Griff zählt mit, beim Bogen die Pfeilauflage); alle 50 Blätter neu aufgenommen, nur das Detailbild geändert.
- `build_all.py` überspringt Schritte, deren gitignorierte Vorlagen fehlen (`render_dx05.py`, `make_v2d.py`).
- Bericht: [claude/docs/versions/0.1.md](claude/docs/versions/0.1.md) (Abschnitt 0.1.2)

## claude-0.1.1
- Mac-Prüfung aller 50 Konzeptblätter (4800×3400, Vorschauen unter `claude/output/previews/`); Vorprüfung in der Cloud.
- KD01, KD04, KD10 mit Visierschiene bzw. -aufnahme und separatem Visier; Abzug von KD01/KD07 sichtbar gemacht.
- Visier-Ansicht: getrennte Kimme/Korn rücken zusammen (11 Blätter); Prompts KD01/04/10 und `.gitignore` korrigiert.
- Bericht: [claude/docs/versions/0.1.md](claude/docs/versions/0.1.md) (Abschnitt 0.1.1)

## claude-0.1
- Pipeline, 50 Waffenmodelle (Varianten C, D, F, G, H) und Konzeptblätter XL mit separatem Visier, Material- und Farbvarianten.
- Trennung `claude/` · `codex/` · gemeinsames `docs/`; Release-Workflow für Tags `claude-v*`.
- Bericht: [claude/docs/versions/0.1.md](claude/docs/versions/0.1.md)

## codex-0.1
- Parallax: eigenständige Pipeline unter `codex/parallax/` mit zehn Waffenmodellen und konsistenten Konzeptblättern.
- CPU-Toon-Renderer, getrennte Optiken, Materialmuster, vier Farbpaletten und deutsche/englische Referenzprompts.
- 22 Unit-Tests und zehn auf dem Mac visuell geprüfte Blätter; [Versionsbericht](codex/docs/versions/0.1.md).
