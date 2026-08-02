Erika Musterfrau
Matrikelnummer: 00000000
E-Mail: erika@example.org
Studiengang: Informatik (M. Sc.)

## Betreuer

Prof. Dr. Hans Beispiel, Institut für Fahrzeugtechnik
Dr. Petra Platzhalter, TelemaOne GmbH

**Vertraulich** — enthält Angaben zum Praxispartner und ist nicht zur Weitergabe bestimmt.

# Inhaltsverzeichnis

1. Einführung in das Thema
2. Beitrag zum Stand der Technik
3. Forschungsfokus und Forschungsfragen
4. Gliederung der Arbeit
5. Forschungsmethodik: Prototypimplementierung

# Abkürzungsverzeichnis

- DMS: Driver Monitoring System
- DSGVO: Datenschutz-Grundverordnung
- KMU: kleine und mittlere Unternehmen

# Einführung in das Thema

Ablenkung und Müdigkeit am Steuer bleiben in gewerblichen Fuhrparks eine der häufigsten Unfallursachen.
Ein Driver Monitoring System (DMS) bezeichnet laut der Produktdokumentation von TelemaOne ein kamerabasiertes System, das Blickrichtung und Lidschlussverhalten kontinuierlich auswertet [@TelemaOne25Zero].
Gerade kleine und mittlere Unternehmen (KMU) verfügen selten über die personellen Ressourcen, um eine solche Einführung systematisch zu planen [@Schmidt23Fatigue].
Die vorliegende Arbeit entwickelt deshalb ein Referenzmodell, das die Einführung eines DMS in KMU-Fuhrparks strukturiert.

# Beitrag zum Stand der Technik

Bestehende Reifegradmodelle für Fahrerbeobachtung adressieren überwiegend Großflotten mit eigenen Sicherheitsabteilungen [@Schmidt23Fatigue].
Herstellerleitfäden wie das Stufenmodell von CabinArc beschreiben zwar konkrete Einführungsschritte, bleiben jedoch an das jeweilige Produktportfolio gebunden [@CabinArc24Zone].
Wissenschaftliche Arbeiten zur Akzeptanz von Fahrerüberwachung betrachten bislang vor allem einzelne Messgrößen [@Krause22Acceptance].
Diese Arbeit verbindet beide Perspektiven zu einem herstellerneutralen Referenzmodell und ergänzt einen Kriterienkatalog zur Priorisierung einzelner Einführungsschritte [@Weber24Rollout].

# Forschungsfokus und Forschungsfragen

Der Fokus der Arbeit liegt auf der Frage, wie KMU ein DMS schrittweise und DSGVO-konform einführen können.
Die übergeordnete Forschungsfrage lautet: Wie kann ein Referenzmodell für die Einführung von Fahrerbeobachtungssystemen in KMU-Fuhrparks gestaltet werden?
Daraus leiten sich vier Teilfragen ab:

1. Wie kann ein Reifegradmodell für den Ausbaugrad der Fahrerbeobachtung in einem KMU aufgebaut werden?
2. Wie kann die Anbindung bestehender Telematiksysteme in das Referenzmodell integriert werden?
3. Wie kann eine Priorisierung der Einführungsschritte nach Risiko und Aufwand entworfen werden?
4. Wie kann das Referenzmodell in einem realen Fuhrparkumfeld umgesetzt werden?

# Gliederung der Arbeit

1. Einleitung
2. Grundlagen und verwandte Arbeiten
3. Anforderungsanalyse
4. Konstruktion des Referenzmodells
5. Prototypische Umsetzung
6. Evaluation
7. Fazit und Ausblick

# Forschungsmethodik: Prototypimplementierung

## Vorarbeiten

Der Prototyp setzt auf der Auswertungsplattform von TelemaOne auf und nutzt deren Schnittstellen zur Übernahme von Ereignismeldungen [@TelemaOne25Zero].
Für die Modellierung der Einführungsschritte kommt eine leichtgewichtige Beschreibungssprache zum Einsatz, die auf etablierten Notationen für Unternehmensarchitekturen aufbaut [@Weber24Rollout].

## Anforderungen

Das Referenzmodell muss die Reifegradstufen eines KMU abbilden und daraus konkrete Einführungsschritte ableiten.
Der Prototyp muss die Priorisierung der Schritte nach Risiko und Aufwand nachvollziehbar dokumentieren.
Performanz und Mehrmandantenfähigkeit sind für den Prototyp vernachlässigbar.

## Evaluation

Eine Abbildung des Referenzmodells auf drei anonymisierte Fuhrparkszenarien prüft die Tragfähigkeit des Reifegradmodells (RQ1).
Die prototypische Anbindung eines bestehenden Telematik-Testsystems zeigt, wie sich vorhandene Datenquellen in das Modell integrieren lassen (RQ2).
Ein Vergleich der berechneten Priorisierung mit Einschätzungen erfahrener Fuhrparkleitungen bewertet den Kriterienkatalog (RQ3).
Eine Fallstudie im Umfeld des Praxispartners untersucht die Umsetzbarkeit des Gesamtmodells (RQ4).

---
title: Ein Referenzmodell für die Einführung von Fahrerbeobachtungssystemen in KMU-Fuhrparks
author: Erika Musterfrau
subtitle: "Exposé zur Masterarbeit"
lang: de
references:
- id: TelemaOne25Zero
  type: webpage
  author:
  - literal: TelemaOne GmbH
  issued:
    year: 2025
  title: Zero-Distraction Driver Monitoring Platform — Produktdokumentation
  URL: https://docs.example.com/telemaone/driver-monitoring
- id: TelemaOne25Zero
  type: webpage
  author:
  - literal: TelemaOne GmbH
  issued:
    year: 2025
  title: Zero-Distraction Driver Monitoring Platform — Produktdokumentation
  URL: https://docs.example.com/telemaone/driver-monitoring
- id: CabinArc24Zone
  type: webpage
  author:
  - literal: CabinArc Inc.
  issued:
    year: 2024
  title: Zone-Based Driver Monitoring Adoption Guide
  URL: https://www.example.com/cabinarc/zone-guide
- id: Schmidt23Fatigue
  type: paper-conference
  author:
  - family: Schmidt
    given: A.
  issued:
    year: 2023
  title: Fatigue Monitoring Maturity in Large Commercial Fleets
  container-title: Proceedings of the Example Conference on Vehicle Safety
  DOI: 10.xxxx/xxxx4
- id: Krause22Acceptance
  type: article-journal
  author:
  - family: Krause
    given: M.
  issued:
    year: 2022
  title: Acceptance Patterns for In-Cabin Driver Monitoring
  container-title: Journal of Example Human Factors Engineering
  DOI: 10.xxxx/xxxx5
- id: Weber24Rollout
  type: article-journal
  author:
  - family: Weber
    given: S.
  issued:
    year: 2024
  title: Rollout Planning for Safety Technology in Commercial Fleets
  container-title: Example Journal of Systems Architecture
  DOI: 10.xxxx/xxxx6
---
