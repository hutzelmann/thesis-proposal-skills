# Motivation

Werkzeuge zur Blickerfassung bestimmen aus Kamerabildern, wohin eine Person im Fahrzeug schaut, ohne dass zusätzliche Hardware am Kopf getragen werden muss.
In Fahrerbeobachtungssystemen ist ihr Einsatz besonders verbreitet, da Ablenkung und Müdigkeit sich vor allem im Blickverhalten zeigen.
Die Auswahl eines geeigneten Werkzeugs fällt Entwicklungsteams jedoch schwer, weil sich die verfügbaren Werkzeuge in Kalibrieraufwand, Robustheit gegenüber Brillen und Genauigkeit deutlich unterscheiden [@Gazelytics25Rules].
Eine fundierte Entscheidungsgrundlage für kleine Fahrsimulatorstudien fehlt bislang.

# Zielsetzung

Ziel der Bachelorarbeit ist ein systematischer Vergleich von drei verbreiteten Werkzeugen zur kamerabasierten Blickerfassung im Fahrzeuginnenraum.
Der Vergleich soll zeigen, welches Werkzeug für kleine bis mittlere Simulatorstudien am besten geeignet ist.
Als Grundlage dienen die offiziellen Genauigkeitsangaben und Handbücher der Hersteller [@Cabinsense25Handbuch].
Bewertet werden unter anderem der Winkelfehler der Blickschätzung, die Ausfallrate bei Brillenträgern und der Aufwand für die Kalibrierung.
Das Ergebnis der Arbeit ist eine begründete Empfehlung, die Forschungsteams bei der Werkzeugauswahl unterstützt.

# Arbeitsschritte

Zunächst wird eine Auswahl von Aufnahmen aus einem Fahrsimulator als Testkorpus zusammengestellt.
Anschließend werden die drei Werkzeuge mit ihrer Standardkonfiguration auf den Korpus angewendet.
Die geschätzten Blickziele werden manuell klassifiziert und den Kategorien Straße, Cockpitdisplay und Nebenaufgabe zugeordnet.
Abschließend werden die Ergebnisse tabellarisch gegenübergestellt und im Hinblick auf die Studiengröße diskutiert.

# Zeitplan

| Phase | Monat 1 | Monat 2 | Monat 3 | Monat 4 |
|---|---|---|---|---|
| Einarbeitung und Werkzeugauswahl | X | | | |
| Aufbau des Testkorpus | X | X | | |
| Durchführung der Analyse | | X | X | |
| Klassifikation und Auswertung | | | X | X |
| Ausarbeitung | | | | X |

---
title: Vergleich von Werkzeugen zur kamerabasierten Blickerfassung im Fahrzeug
author: Erika Musterfrau
subtitle: "Exposé zur Bachelorarbeit"
lang: de
references:
- id: Gazelytics25Rules
  type: webpage
  author:
  - literal: Gazelytics Project
  issued:
    year: 2025
  title: "Gazelytics Documentation: Accuracy Reference"
  URL: https://docs.gazelytics.example.org/accuracy
- id: Cabinsense25Handbuch
  type: webpage
  author:
  - literal: Cabinsense GmbH
  issued:
    year: 2025
  title: "Cabinsense Handbuch: Kalibrierung und Konfiguration"
  URL: https://www.cabinsense.example.com/handbuch/kalibrierung
---
