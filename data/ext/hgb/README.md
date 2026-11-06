# Externe Daten: Historisches Grundbuch Basel (HGB), Projekt «Ökonomien des Raums»

Quelle: Universität Basel, Departement Geschichte, Projekt «Ökonomien des Raums»
(Jonas Aeby, Benjamin Hitz, Ismail Prada Ziegler), Repositorien
<https://github.com/history-unibas/economies-of-space-database> (MIT, Stand 06.11.2026,
Ordner `data/project_database_update/`) und
<https://github.com/history-unibas/economies-of-space-metadata> (= Zenodo
<https://doi.org/10.5281/zenodo.22112366>, CC BY 4.0). Der vollständige Datenbank-Dump
liegt unter <https://doi.org/10.5281/zenodo.22025829> (CC BY 4.0, 1,6 GB).

| Datei | Inhalt |
|---|---|
| `stabs_serie.csv` | 231 HGB-Serien = Strassen (`stabsId`, `title`, `link`, `serieId`) — Metadaten des Staatsarchivs Basel-Stadt (LOD, <https://ld.bs.ch/>) |
| `stabs_dossier.csv` | 6 057 HGB-Dossiers = Liegenschaften: `title` ist die Adresse nach dem Adressbuch 1862 (Strasse + neue Hausnummer), `oldHousenumber` die alte stadtweite Nummer (vor 1862), `houseName`, `owner1862` (Eigentümer laut Adressbuch 1862), `link` (Archivkatalog) |
| `dossiergeomshifted_202607151617.csv` | 4 353 Dossier-Standorte als Punkt in LV95 (EPSG:2056), `locationshifted`; Herkunft: Georeferenzierung durch das Grundbuch- und Vermessungsamt Basel-Stadt, im Projekt ergänzt und am Löffelplan 1862 geprüft (Dokumentation Kap. 4.3/4.4 in `documentation.md` des Datenbank-Repos) |
| `oldHousenumberCorrections.csv` | 200 handkorrigierte Lesarten der alten Hausnummern (Zenodo 22112366) |

Nutzung hier: `scripts/10_geo_hgb.py` bildet die Gebäude aus `05_buildings.csv` über
Strasse + neue Nummer (1862) beziehungsweise alte Nummer (1841/1850) auf Dossiers und
damit auf Koordinaten ab. Für die Standortdaten (Shapefile des Vermessungsamts) nennt
das Repo keine eigene Datenlizenz; vor einer Veröffentlichung der Karte klären.
