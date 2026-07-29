# Motivation

Statische Analysewerkzeuge prüfen Quelltext auf Fehlermuster, ohne das Programm auszuführen.
In JavaScript-Projekten ist ihr Einsatz besonders verbreitet, da die dynamische Typisierung viele Fehlerklassen erst zur Laufzeit sichtbar macht.
Die Auswahl eines geeigneten Werkzeugs fällt Entwicklungsteams jedoch schwer, weil sich die verfügbaren Werkzeuge in Regelumfang, Konfigurierbarkeit und Meldungsqualität deutlich unterscheiden [@Lintfox25Rules].
Eine fundierte Entscheidungsgrundlage für kleine und mittlere Projekte fehlt bislang.

# Zielsetzung

Ziel der Bachelorarbeit ist ein systematischer Vergleich von drei verbreiteten statischen Analysewerkzeugen für JavaScript.
Der Vergleich soll zeigen, welches Werkzeug für kleine bis mittlere Projekte am besten geeignet ist.
Als Grundlage dienen die offiziellen Regelkataloge und Handbücher der Hersteller [@Codegull25Handbuch].
Bewertet werden unter anderem die Anzahl der gefundenen Probleme, die Rate falsch positiver Meldungen und der Aufwand für die Konfiguration.
Das Ergebnis der Arbeit ist eine begründete Empfehlung, die Entwicklungsteams bei der Werkzeugauswahl unterstützt.

# Arbeitsschritte

Zunächst wird eine Auswahl von Open-Source-Projekten als Testkorpus zusammengestellt.
Anschließend werden die drei Werkzeuge mit ihrer Standardkonfiguration auf den Korpus angewendet.
Die gemeldeten Befunde werden manuell klassifiziert und den Kategorien echter Fehler, Stilfrage und Fehlalarm zugeordnet.
Abschließend werden die Ergebnisse tabellarisch gegenübergestellt und im Hinblick auf die Projektgröße diskutiert.

# Zeitplan

| Phase | Monat 1 | Monat 2 | Monat 3 | Monat 4 |
|---|---|---|---|---|
| Einarbeitung und Werkzeugauswahl | X | | | |
| Aufbau des Testkorpus | X | X | | |
| Durchführung der Analyse | | X | X | |
| Klassifikation und Auswertung | | | X | X |
| Ausarbeitung | | | | X |

---
title: Vergleich statischer Analysewerkzeuge für JavaScript
author: Erika Musterfrau
subtitle: "Exposé zur Bachelorarbeit"
lang: de
references:
- id: Lintfox25Rules
  type: webpage
  author:
  - literal: Lintfox Project
  issued:
    year: 2025
  title: "Lintfox Documentation: Rule Reference"
  URL: https://docs.lintfox.example.org/rules
- id: Codegull25Handbuch
  type: webpage
  author:
  - literal: Codegull GmbH
  issued:
    year: 2025
  title: "Codegull Handbuch: Regelkatalog und Konfiguration"
  URL: https://www.codegull.example.com/handbuch/regeln
---
