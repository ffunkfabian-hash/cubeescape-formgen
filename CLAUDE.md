# Regeln für Claude in diesem Repository

Zuerst gelten die globalen Regeln aus `ffunkfabian-hash/cubeescape-nexogen` (lokal `~/.claude/CLAUDE.md` bzw.
`~/.codex/AGENTS.md`). Ergänzend für dieses Repo:

- Claude schreibt ausschließlich unter `claude/` (Pipeline, Modelle, Konzeptblätter, Prompts).
- **Eine Pipeline** (Nutzer, 23.10.2026): Neue Konzeptarbeit nur noch unter `claude/`. `codex/` (A „Parallax“, K „Flux Bloom“) ist
  eingefroren – lesbarer Bestand, nicht ändern, nicht löschen, keine neuen Codex-Varianten. Codex hilft nur noch als Unteragent einer
  Claude-Sitzung unter `claude/` (wie bei KC11–KJ25). Die Regeln unten zu `codex/` gelten für diesen Bestand.
- `codex/` gehört Codex: nicht ändern, nicht verschieben, keine Dateien daraus übernehmen oder per Symlink koppeln.
- **Gleiche Regeln für Codex** (Nutzer, 17.10.2026): Alles hier gilt für Codex sinngemäß mit `codex/`. Wer hier eine Regel
  ändert, zieht `AGENTS.md` im selben Zug nach. Codex-Varianten (A „Parallax“, K „Flux Bloom“) stehen in `variants.CODEX`.
- `docs/` ist gemeinsam (Masterprompt, Aufträge, Vorlagen): nur nach ausdrücklichem Wunsch des Nutzers ändern.
- Releases von Claude: Branch `release/claude-<version>` pushen; der Workflow legt Tag `claude-v<version>` und Release an.
- Wurzeldateien (`README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `.ce-repo.json`, `.github/`) pflegt Claude; Codex meldet
  Änderungswünsche (z. B. eigene CHANGELOG-Zeilen `codex-…`) im PR oder an den Nutzer.
- Codex arbeitet auf Branches `codex/…`; der Merge nach `main` erfolgt per Pull Request durch den Nutzer bzw. nach seiner Freigabe.
  Claude committet seine eigenen Ordner direkt auf `main`.
- **Variantennamen** (Regel des Nutzers, 17.10.2026): Jede neue Variante bekommt zum Kennbuchstaben einen kurzen, markanten
  **englischen Namen** (1–3 Wörter, z. B. J „Black Ice“; Codex: „Parallax“). Der Buchstabe bleibt die ID der Blätter (KJ01 …),
  der Name steht in Kopfzeile, Prompts, Spec (`sheet.variant_name`) und README. Namen nicht doppelt vergeben, I und O nicht als
  Buchstaben. Claude: Eintrag über `claude/generator/new_variant.py` (prüft die Regel), Register `claude/generator/variants.py`.
  C–H bleiben ohne Namen.
- **Viewer bei jeder Varianten-Sitzung aktualisieren** (Regel des Nutzers, 17. Oktober 2026; geändert am selben Tag: Blätter sind Release-Asset):
  Wer Konzeptblätter neu baut oder ändert (neue Variante, Korrekturen), bringt lokal alles auf Stand: Blätter `K??NN.dc.html`, Vorschauen
  `claude/output/previews/K??NN.webp` und zuletzt den Viewer mit `python3 claude/generator/make_viewer.py` (erzeugt `claude/output/index.html`;
  ruft `build_all.py` ihn auf, genügt dessen Lauf). Die Ausgabe nennt Blattzahl und Varianten: prüfen, dass die neue Variante samt
  Vorschauen drin ist. **Blätter, Vorschauen und `index.html` werden nicht committet** (gitignoriert); sie kommen mit
  `python3 claude/generator/release_assets.py` (Probelauf, `--upload` nur auf Wunsch) ins Release. Im Repo bleiben `KXnn.spec.json` und
  `claude/tests/golden.json` (nach Neubau `python3 claude/tests/test_golden.py --update`). Beim Abschluss **einmal** anbieten, den Viewer
  zu öffnen (`open claude/output/index.html`, Knopf in der Abschlussbox); nicht ungefragt öffnen, nicht wiederholt anbieten.
- Bildstufen (Rendern der Konzeptblätter) und Hash-Prüfungen (`test_golden --full`, libwebp-abhängig) laut globaler Regel auf dem Mac mit
  `heavy_lock`; Cloud-Sitzungen (auch Codex Cloud, nur auf freigegebenem Branch) dürfen umsetzen und alles ohne Bildstufe prüfen.
  Bekommt Codex einen Auftrag, dessen Ergebnis am Bild beurteilt wird (Visiere, Modelle), legt Claude vorher die Zielbild-Vorschauen
  lokal ab (`~/Library/Caches/CubeEscapeDesign/…`) und nennt den Pfad im Auftrag.
- **Erfahrungen** (Lehren aus Modell-, Raster- und Render-Pipeline, Prompts und Konzeptblättern) stehen in `docs/masterprompt.md` und
  `docs/prompt-vorlagen.md` (gemeinsam, Änderungen nur auf Wunsch des Nutzers), Claudes zusätzlich in `claude/docs/versions/`;
  dauerhafte Entscheidungen des Nutzers mit Grund in `claude/docs/ENTSCHEIDUNGEN.md` (Datum | Entscheidung | Grund, neue Zeilen unten,
  Quelle verlinken statt kopieren; vor Änderungen an Spec, Blättern oder Regeln lesen); vor dem
  Bauen, das ein Schwesterprojekt berührt (Toolgen, Cube Escape, Robogen, Cubegen), dessen Stelle lesen: `~/.claude/CLAUDE.md` ›
  Erfahrungen festhalten und querlesen.
- **Texturen gemeinsam hinterlegen** (Wunsch des Nutzers, 17.10.2026): Materialmuster und Skins sollen an einer gemeinsamen Stelle
  liegen, die Claude und Codex gleich nutzen: Katalog `docs/textures/` (Parameter und Musterbilder; Entscheidung 18.10.2026, angelegt mit
  claude-0.6.1, Beschreibung in `docs/textures/README.md`). Bis er auf `main` liegt, keine neuen Textur- oder Skin-Arten ohne Eintrag im Versionsbericht.

@docs/LESSONS.md
