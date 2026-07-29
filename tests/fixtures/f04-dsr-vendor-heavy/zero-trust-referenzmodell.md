Erika Musterfrau
Matrikelnummer: 00000000
E-Mail: erika@example.org
Studiengang: Informatik (M. Sc.)

## Betreuer

Prof. Dr. Hans Beispiel, Institut für Softwaretechnik
Dr. Petra Platzhalter, NetSentio GmbH

**Vertraulich** — enthält Angaben zum Praxispartner und ist nicht zur Weitergabe bestimmt.

# Inhaltsverzeichnis

1. Einführung in das Thema
2. Beitrag zum Stand der Technik
3. Forschungsfokus und Forschungsfragen
4. Gliederung der Arbeit
5. Forschungsmethodik: Prototypimplementierung

# Abkürzungsverzeichnis

- IAM: Identity and Access Management
- KMU: kleine und mittlere Unternehmen
- ZTA: Zero-Trust-Architektur

# Einführung in das Thema

Klassische Perimetersicherheit verliert in verteilten Unternehmensnetzen zunehmend an Wirksamkeit.
Zero-Trust-Architektur (ZTA) bezeichnet laut der Produktdokumentation von NetSentio ein Sicherheitsmodell, das keiner Identität und keinem Gerät implizit vertraut [@NetSentio25Zero].
Gerade kleine und mittlere Unternehmen (KMU) verfügen selten über die personellen Ressourcen, um eine solche Umstellung systematisch zu planen [@Schmidt23Zero].
Die vorliegende Arbeit entwickelt deshalb ein Referenzmodell, das die Einführung einer ZTA in KMU strukturiert.

# Beitrag zum Stand der Technik

Bestehende Reifegradmodelle für ZTA adressieren überwiegend Großunternehmen mit eigenen Sicherheitsabteilungen [@Schmidt23Zero].
Herstellerleitfäden wie das Zonenmodell von CloudArc beschreiben zwar konkrete Migrationsschritte, bleiben jedoch an das jeweilige Produktportfolio gebunden [@CloudArc24Zone].
Wissenschaftliche Arbeiten zur Migration von Identitätsinfrastrukturen betrachten bislang vor allem technische Einzelaspekte [@Krause22Identity].
Diese Arbeit verbindet beide Perspektiven zu einem herstellerneutralen Referenzmodell und ergänzt einen Kriterienkatalog zur Priorisierung einzelner Migrationsschritte [@Weber24Migration].

# Forschungsfokus und Forschungsfragen

Der Fokus der Arbeit liegt auf der Frage, wie KMU eine ZTA schrittweise und ressourcenschonend einführen können.
Die übergeordnete Forschungsfrage lautet: Wie kann ein Referenzmodell für die Einführung von Zero-Trust-Architekturen in KMU gestaltet werden?
Daraus leiten sich vier Teilfragen ab:

1. Wie kann ein Reifegradmodell für den Zero-Trust-Ausbaugrad eines KMU aufgebaut werden?
2. Wie kann die Migration bestehender IAM-Systeme in das Referenzmodell integriert werden?
3. Wie kann eine Priorisierung der Migrationsschritte nach Risiko und Aufwand entworfen werden?
4. Wie kann das Referenzmodell in einem realen KMU-Umfeld umgesetzt werden?

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

Der Prototyp setzt auf der Policy-Engine von NetSentio auf und nutzt deren Schnittstellen zur Durchsetzung von Zugriffsregeln [@NetSentio25Zero].
Für die Modellierung der Migrationsschritte kommt eine leichtgewichtige Beschreibungssprache zum Einsatz, die auf etablierten Notationen für Unternehmensarchitekturen aufbaut [@Weber24Migration].

## Anforderungen

Das Referenzmodell muss die Reifegradstufen eines KMU abbilden und daraus konkrete Migrationsschritte ableiten.
Der Prototyp muss die Priorisierung der Schritte nach Risiko und Aufwand nachvollziehbar dokumentieren.
Performanz und Mehrmandantenfähigkeit sind für den Prototyp vernachlässigbar.

## Evaluation

Eine Abbildung des Referenzmodells auf drei anonymisierte KMU-Szenarien prüft die Tragfähigkeit des Reifegradmodells (RQ1).
Die prototypische Anbindung eines bestehenden IAM-Testsystems zeigt, wie sich Identitätsinfrastrukturen in das Modell integrieren lassen (RQ2).
Ein Vergleich der berechneten Priorisierung mit Einschätzungen erfahrener Administratoren bewertet den Kriterienkatalog (RQ3).
Eine Fallstudie im Umfeld des Praxispartners untersucht die Umsetzbarkeit des Gesamtmodells (RQ4).

---
title: Ein Referenzmodell für die Einführung von Zero-Trust-Architekturen in KMU
author: Erika Musterfrau
subtitle: "Exposé zur Masterarbeit"
lang: de
references:
- id: NetSentio25Zero
  type: webpage
  author:
  - literal: NetSentio GmbH
  issued:
    year: 2025
  title: Zero Trust Platform — Produktdokumentation
  URL: https://docs.example.com/netsentio/zero-trust
- id: NetSentio25Zero
  type: webpage
  author:
  - literal: NetSentio GmbH
  issued:
    year: 2025
  title: Zero Trust Platform — Produktdokumentation
  URL: https://docs.example.com/netsentio/zero-trust
- id: CloudArc24Zone
  type: webpage
  author:
  - literal: CloudArc Inc.
  issued:
    year: 2024
  title: Zone-Based Zero Trust Adoption Guide
  URL: https://www.example.com/cloudarc/zone-guide
- id: Schmidt23Zero
  type: paper-conference
  author:
  - family: Schmidt
    given: A.
  issued:
    year: 2023
  title: Zero Trust Maturity in Large Enterprises
  container-title: Proceedings of the Example Conference on Enterprise Security
  DOI: 10.xxxx/xxxx4
- id: Krause22Identity
  type: article-journal
  author:
  - family: Krause
    given: M.
  issued:
    year: 2022
  title: Identity Infrastructure Migration Patterns
  container-title: Journal of Example Security Engineering
  DOI: 10.xxxx/xxxx5
- id: Weber24Migration
  type: article-journal
  author:
  - family: Weber
    given: S.
  issued:
    year: 2024
  title: Migration Planning for Security Architectures
  container-title: Example Journal of Systems Architecture
  DOI: 10.xxxx/xxxx6
---
