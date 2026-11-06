# adressbuecher-basel

Auswertung der Adressbücher der Stadt Basel 1841, 1850 und 1862 (Staatsarchiv
Basel-Stadt, STA H 43 17 / 20 / 22, gemeinfrei).

Nebengeleis zu [adressbuecher-aarau](https://github.com/thodel/adressbuecher-aarau) mit
derselben Methode und demselben CSV-Schema (`docs/schema.md`), damit beide Korpora
später in einen Graphen (CIDOC-CRM 7.1.3 + SDHSS) zusammengeführt werden können. Das
Tooling (ATR, Vokabular-Register, Graph-Bauer) kommt aus
[agentic_historian](https://github.com/thodel/agentic_historian).

Der Plan mit Befund, Pipeline und Abnahmekriterien steht in [PLAN.md](PLAN.md).

Kontrollseite der Datensätze (Flagging, Verortung): https://thodel.github.io/adressbuecher-basel/

## Betrieb

- ATR läuft über den Server `tei` (SSH-Alias in `~/.ssh/config`, oder `TEI_SSH=user@host`); die
  Läufe werden über den MCP-ATR-Server von agentic_historian gestartet (siehe PLAN.md, Welle 1).
- `make fullrun-fetch fullrun-lines fullrun-parse geo erstblick` holt fertige Läufe, parst alle
  Abschnitte, verortet die Gebäude über das HGB und baut die Kontrollseite `web/index.html`;
  GitHub Pages baut dieselbe Seite bei jedem Push, der `data/csv/` oder `data/review/` berührt.
- Flags von der Kontrollseite: CSV exportieren, `make flags-merge FILE=…`, committen.
- Abnahme des Parsers: `make abnahme` vergleicht die Parser-Ausgabe der GT-Seiten mit den
  handgeprüften Gold-Tabellen in `data/gt/entries_*.csv`, `buildings_*.csv`, `residents_*.csv`.
