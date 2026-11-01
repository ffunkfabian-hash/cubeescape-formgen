# Regeln für Codex in diesem Repository

Zentraler Repo-Einstieg: [Nexogen](https://github.com/ffunkfabian-hash/cubeescape-nexogen) – Repo-Links, Zuständigkeiten, Abhängigkeiten und Live-Status über die Status-CLI im Nexogen-Repo. Globale Regeln dort, Fachwissen und Prüfbelege hier.

**Werkzeuge:** `./ce check` · `./ce search query "Begriff"` · `./ce session topics` · `./ce codex quota|judge` · `./ce evidence clip|sheet|still|diff` · `./ce lock unity|blender|gpu -- <Befehl>` · `./ce report --since 7d`.

**Keine Werkzeugkopie (seit claude-0.16.0):** `./ce` ist der Lader der gemeinsamen Werkzeuge (Plugin `ce-shared`, Repo ffunkfabian-hash/ce-agent-tools) und führt den Stand aus `.ce-repo.json` › `tools_version` aus (`./ce tools where|fetch`); neuer Stand nur per `./ce tools pin <Commit>`, nie von Hand. `./ce docs` prüft Längen/Gliederung, `./ce tidy` zeigt Reste (Probelauf), `.mcp.json` startet `ce_search` über `./ce search serve`; die `ce-*`-Profile unter `.claude/agents/` liefert das Plugin.

**Hooks (seit Agent Tools 0.12):** Der gemeinsame Wächter wird über Nexogen installiert – für Codex erst nach Vertrauen unter `/hooks`,
für Antigravity nur auf den gemessenen Oberflächen CLI `agy` 1.4.5 und IDE 2.5.5. Das reversible Git-Netz wirkt unabhängig davon für
alle Clients. Die Commit-Vorabprüfung ist begrenzt (nur einzelne, statisch eindeutige Aufrufe); Einbau und Grenzen stehen zentral in
[Werkzeuge und Durchsetzung](https://github.com/ffunkfabian-hash/cubeescape-nexogen/blob/main/templates/regeln-details.md#werkzeuge-und-durchsetzung). Postfach (seit ce-shared 0.15.1, nur Claude Code mit installiertem Plugin): Für eine reservierte Sitzung (`./ce session reserve|patch`) startet ein Stop-Hook den Wächter selbst und weckt sie bei Nachrichten; läuft keiner, hält ein zweiter Stop-Hook das Ende einmal an (höchstens alle 2 h). Versionen (ce-shared 0.16): Claude Code führt je Checkout und Worktree einen eigenen Plugin-Eintrag, den `claude plugin update` nicht sicher erreicht – nach einem Update `./ce plugins check`, bei Abweichung `./ce plugins fix --apply`; eine Sitzung mit älterem ce-shared warnt beim Start.

Zuerst gelten die globalen Regeln aus `ffunkfabian-hash/cubeescape-nexogen` (lokal `~/.claude/CLAUDE.md` bzw.
`~/.codex/AGENTS.md`). Ergänzend für dieses Repo:

- **Gleiche Regeln wie Claude** (Entscheidung des Nutzers, 17.10.2026): Jede Regel in `CLAUDE.md` gilt für Codex genauso, mit
  `codex/` statt `claude/`. Unterschiede gibt es nur bei der Zuständigkeit (unten). Kommt in `CLAUDE.md` eine Regel dazu, gilt sie
  ab dann auch hier; Claude zieht diese Datei im selben Zug nach.
- **`codex/` ist eingefroren** (Entscheidung des Nutzers, 23.10.2026): keine neue Arbeit in der Codex-Pipeline, keine neuen
  Codex-Varianten, nichts löschen. Codex arbeitet hier nur noch als Unteragent einer Claude-Sitzung unter `claude/` nach deren Auftrag
  (wie bei KC11–KJ25). Die folgenden Regeln zu `codex/` gelten für den Bestand.
- Codex schreibt ausschließlich unter `codex/` (eigene Pipeline, Modelle, Konzeptblätter, Prompts) – außer als Unteragent von Claude (oben).
- `claude/` gehört Claude: nicht ändern, nicht verschieben, keine Dateien daraus übernehmen oder per Symlink koppeln. Lesen ist
  erlaubt und für den gemeinsamen Maßstab nötig (`claude/docs/`).
- `docs/` ist gemeinsam (Masterprompt `docs/masterprompt.md`, Auftrag `docs/AUFTRAG.md`): nur nach ausdrücklichem Wunsch des Nutzers ändern.
- Verbindliche Gestaltungsregeln: `docs/masterprompt.md`.
- Wurzeldateien (`README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `.ce-repo.json`, `.github/`) pflegt Claude; Codex meldet
  Änderungswünsche (z. B. eigene CHANGELOG-Zeilen `codex-…`) im PR oder an den Nutzer.
- Codex arbeitet auf Branches `codex/…`; der Merge nach `main` erfolgt per Pull Request durch den Nutzer bzw. nach seiner Freigabe.
  Claude committet seine eigenen Ordner direkt auf `main`.
- **Variantennamen** (Regel des Nutzers, 17.10.2026): Jede neue Variante bekommt zum Kennbuchstaben einen kurzen, markanten
  **englischen Namen** (1–3 Wörter, z. B. J „Black Ice“; Codex: A „Parallax“, K „Flux Bloom“). Der Buchstabe bleibt die ID der
  Blätter (KJ01 …), der Name steht in Kopfzeile, Prompts, Spec (`sheet.variant_name`) und README. Namen und Buchstaben gelten für
  beide Pipelines zusammen und werden nicht doppelt vergeben; I und O nicht als Buchstaben. Register: Claude
  `claude/generator/variants.py` (`VARIANTS`, Codex-Einträge in `CODEX`). Codex prüft eine neue Variante vor dem Bau gegen dieses
  Register und meldet Buchstabe und Name im PR, damit Claude sie in `CODEX` einträgt. C–H bleiben ohne Namen.
- **Viewer bei jeder Varianten-Sitzung aktualisieren** (wie `CLAUDE.md`): Wer Blätter neu baut oder ändert, bringt Blätter,
  Vorschauen und den Codex-Viewer (`codex/index.html` bzw. die Galerie der Pipeline) lokal auf Stand und prüft, dass die neue
  Variante samt Vorschauen drin ist. Blätter, Vorschauen und erzeugte Galerien werden nicht committet; im Repo bleiben Specs und
  Prüfwerte (Hashes). Beim Abschluss einmal anbieten, den Viewer zu öffnen.
- Releases nur auf Wunsch des Nutzers. Der Release-Workflow kennt bisher nur `release/claude-<version>`; einen Codex-Weg
  (`release/codex-<version>`, Tag `codex-v<version>`) legt Claude an, sobald der Nutzer ihn möchte.
- Bildstufen (Rendern der Konzeptblätter) und Hash-Prüfungen (`test_golden --full`, libwebp-abhängig) laut globaler Regel auf dem Mac mit
  `heavy_lock`; Cloud-Sitzungen (auch Codex Cloud, nur auf freigegebenem Branch) dürfen umsetzen und alles ohne Bildstufe prüfen.
  Bekommt Codex einen Auftrag, dessen Ergebnis am Bild beurteilt wird (Visiere, Modelle), legt Claude vorher die Zielbild-Vorschauen
  lokal ab (`~/Library/Caches/CubeEscapeDesign/…`) und nennt den Pfad im Auftrag.
- **Erfahrungen** (Lehren aus Modell-, Raster- und Render-Pipeline, Prompts und Konzeptblättern) stehen in `docs/masterprompt.md` und
  `docs/prompt-vorlagen.md` (gemeinsam, Änderungen nur auf Wunsch des Nutzers), Codex' zusätzlich in `codex/docs/versions/`.
  Dauerhafte Entscheidungen des Nutzers: `claude/docs/ENTSCHEIDUNGEN.md` (gilt für beide Pipelines, vor Änderungen an Spec, Blättern
  oder Regeln lesen); Codex-eigene Entscheidungen in `codex/docs/ENTSCHEIDUNGEN.md` im selben Format (Datum | Entscheidung | Grund).
  Vor dem Bauen, das ein Schwesterprojekt berührt (Toolgen, Cube Escape, Robogen, Cubegen), dessen Stelle lesen: `~/.claude/CLAUDE.md` ›
  Erfahrungen festhalten und querlesen.
- **Texturen gemeinsam hinterlegen** (Wunsch des Nutzers, 17.10.2026): Materialmuster und Skins sollen an einer gemeinsamen Stelle
  liegen, die Claude und Codex gleich nutzen: Katalog `docs/textures/` (Parameter und Musterbilder; Entscheidung 18.10.2026, angelegt mit
  claude-0.6.1, Beschreibung in `docs/textures/README.md`). Bis er auf `main` liegt, keine neuen Textur- oder Skin-Arten ohne Eintrag im Versionsbericht; vorhandene Definitionen
  nicht umbauen. Danach lesen beide Pipelines Materialien, Oberflächen und Skins aus dem Katalog.

Werkzeug-Erfahrungen: [docs/LESSONS.md](docs/LESSONS.md); die verlinkte Systemdokumentation bleibt die Langform.
