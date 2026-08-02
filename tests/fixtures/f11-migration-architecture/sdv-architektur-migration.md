# Einführung und Motivation

Gewachsene Fahrzeug-Softwarearchitekturen bilden in vielen Baureihen den funktionalen Kern, sind jedoch häufig als schwer wartbare Steuergeräte-Monolithen umgesetzt [@Hoffmann23Migration].
Eine Zerlegung in Dienste einer softwaredefinierten Fahrzeugplattform verspricht kürzere Release-Zyklen und eine unabhängige Aktualisierung einzelner Fahrfunktionen [@Lang24Decomposition].
Der Umbau eines seriennahen Systems birgt allerdings erhebliche Risiken, da sicherheitsrelevante Signalpfade unterbrechungsfrei weiterlaufen müssen.
Die vorliegende Arbeit untersucht deshalb, unter welchen Bedingungen eine schrittweise Migration eines monolithischen Komfortsteuergeräts gelingt.

# Abgrenzung

Die Arbeit betrachtet ausschließlich die Softwarearchitektur des Komfortsteuergeräts.
Bedienoberflächen im Cockpit, Freigabeprozesse und organisatorische Aspekte der Umstellung bleiben außerhalb des Untersuchungsrahmens.

# Problemstellung und Forschungsfragen

Der Forschungsfokus liegt auf der mustergeleiteten Zerlegung eines seriennahen Steuergeräts und deren messbaren Auswirkungen auf zentrale Qualitätsmerkmale.

1. Zu welchem Grad lassen sich die Funktionsdomänen des Steuergeräts anhand statischer und dynamischer Kopplungsanalysen voneinander abgrenzen?
2. Lässt sich der Bestandsmonolith mit der Strangler-Fig-Strategie ohne messbare Ausfallzeit schrittweise ablösen?
3. Unter welchen Bedingungen bleibt die Zustandskonsistenz zwischen extrahierten Diensten und verbleibendem Monolithen gewährleistet?

# Verwandte Arbeiten

Verwandte Arbeiten beschreiben Migrationsmuster wie die Strangler-Fig-Strategie und bewerten sie anhand einzelner Industriefallstudien [@Neumann22Strangler].
Offen bleibt, wie sich diese Muster auf Steuergeräte mit harten Latenzanforderungen und stark gekoppelten Signalflüssen übertragen lassen [@Hoffmann23Migration].
Diese Arbeit schließt die Lücke, indem sie ein Bestandssteuergerät mustergeleitet zerlegt und die Auswirkungen auf Signallatenzen, Zustandskonsistenz und Ausfallzeiten quantifiziert.
Damit entsteht eine nachvollziehbare Bewertung der Muster für latenzkritische Fahrzeugsysteme mittlerer Größe.
Serviceorientierte Fahrzeugarchitekturen werden inzwischen als Referenzarchitektur beschrieben, ohne den Migrationsweg dorthin zu behandeln [@Ferreira23SDV].
@Kaur24Latency zeigen, dass die Dienstvermittlung den größten Einzelbeitrag zur zusätzlichen Signallatenz nach einer Zerlegung liefert.
Kopplungsmaße für die Domänenabgrenzung sind etabliert [@Delgado22Coupling], und für die Zustandssynchronisation während einer Migration liegen Konsistenzmodelle vor [@Lindqvist25Consistency].
Übertragungen der Strangler-Fig-Strategie außerhalb von Informationssystemen sind bislang Einzelfallberichte ohne Messdaten [@Aranda24Strangler].

# Methodik: Prototypimplementierung

## Definition des Anwendungsfalls

Gegenstand der Untersuchung ist ein anonymisiertes Abbild eines seriennahen Komfortsteuergeräts mit rund vierzig Funktionen und harten Latenzanforderungen an zwei Signalpfaden.
Dieser Anwendungsfall eignet sich für die Forschungsfragen, weil das Steuergerät produktiv eingesetzt wird und die Kopplung zwischen Funktionsdomänen dort real gewachsen und nicht konstruiert ist.
Das Abbild steht über den Praxispartner zur Verfügung; sicherheitsrelevante Fahrfunktionen sind darin nicht enthalten.

## Vorarbeiten

Der Prototyp baut auf einem anonymisierten Abbild der bestehenden Steuergerätesoftware auf.
Für die Kopplungsanalyse kommen etablierte Werkzeuge zur statischen Codeanalyse zum Einsatz [@Lang24Decomposition].
Die Laufzeitinfrastruktur folgt dem Betriebsleitfaden der Fahrzeugplattform AdaptiveCore [@AdaptiveCore25Guide] sowie der Referenzdokumentation der Dienstvermittlung ServiceLink [@ServiceLink24Manual].

## Anforderungen

- Der Prototyp muss zwei Funktionsdomänen als eigenständige Dienste extrahieren.
- Der Prototyp muss eingehende Signale transparent zwischen Monolith und Diensten vermitteln.
- Der Prototyp muss Zustandsdaten während der Migration synchron halten.
- Der Prototyp soll Signallatenzen und Fehlerraten fortlaufend protokollieren.

Optimierte Ressourcennutzung und eine vollständige Zerlegung aller Funktionsdomänen sind vernachlässigbar.

## Evaluation

Eine Kopplungsanalyse des Bestandssystems mit anschließender Experteneinschätzung bewertet die Abgrenzbarkeit der Funktionsdomänen (RQ1).
Ein Lasttest der schrittweisen Ablösung misst Ausfallzeiten während der Umschaltung zwischen Monolith und extrahierten Diensten (RQ2).
Konsistenzprüfungen auf replizierten Zustandsdaten unter parallelen Schreibzugriffen untersuchen die Grenzen der Zustandssynchronisation (RQ3).

# Zusammenfassung

Die Arbeit zerlegt ein seriennahes Komfortsteuergerät mustergeleitet in Dienste und quantifiziert die Auswirkungen auf Ausfallzeiten und Zustandskonsistenz.
Das Vorgehen liefert Fahrzeugherstellern eine belastbare Entscheidungsgrundlage für vergleichbare Migrationen.

# Zielsetzung

Primäres Ziel ist eine mustergeleitete Zerlegung eines seriennahen Steuergeräts mit quantifizierter Auswirkung auf Ausfallzeit und Zustandskonsistenz.

Weitere Ziele:

- Die Funktionsdomänen über statische und dynamische Kopplungsanalyse abgrenzen.
- Zwei Domänen als eigenständige Dienste extrahieren.
- Die schrittweise Umschaltung mit Lasttest vermessen.
- Die Grenzen der Zustandssynchronisation unter parallelen Schreibzugriffen bestimmen.

# Erwartete Beiträge und Ergebnisse

Der wissenschaftliche Beitrag besteht in einer messbasierten Bewertung der Strangler-Fig-Strategie für latenzkritische Steuergeräte, die bislang nur für Informationssysteme belegt ist.
Praktisch entsteht daraus eine Entscheidungsgrundlage für Fahrzeughersteller, die vergleichbare Steuergeräte migrieren wollen.
Erwartet wird, dass die Umschaltung ohne messbare Ausfallzeit gelingt und dass die Zustandskonsistenz erst unter hoher paralleler Schreiblast bricht.
Absehbare Grenzen sind ein einzelnes Steuergerät, der Ausschluss sicherheitsrelevanter Funktionen und eine Laborumgebung ohne reale Fahrzeugvernetzung.

# Arbeitsplan und Zeitplan

| Aufgabe | Wochen |
|---|---|
| Literatur und Werkzeugauswahl | 1-4 |
| Kopplungsanalyse des Bestandssystems | 3-8 |
| Extraktion der ersten Domäne | 7-12 |
| Extraktion der zweiten Domäne | 11-15 |
| Lasttest und Konsistenzprüfungen | 14-19 |
| Ausarbeitung und Überarbeitung | 17-24 |

Die Extraktion setzt die abgeschlossene Kopplungsanalyse voraus, die damit den kritischen Pfad bestimmt.
Bewusst wird die zweite Domäne erst nach der ersten begonnen, weil deren Vermittlungsschicht wiederverwendet wird.
Als Streichposten ist die zweite Extraktion vorgesehen, falls frühere Phasen überziehen.

---
title: Architekturgetriebene Migration eines monolithischen Steuergeräts zu einer SDV-Plattform
author: Erika Musterfrau
subtitle: "Exposé zur Bachelorarbeit"
lang: de
references:
- id: Hoffmann23Migration
  type: article-journal
  author:
  - family: Hoffmann
    given: K.
  issued:
    year: 2023
  title: Migration Strategies for Legacy Automotive Software
  container-title: Example Journal of Software Evolution
  DOI: 10.xxxx/yyyy1
- id: Lang24Decomposition
  type: paper-conference
  author:
  - family: Lang
    given: B.
  issued:
    year: 2024
  title: Decomposition of Monolithic Control Units via Coupling Analysis
  container-title: Proceedings of the Example Conference on Software Architecture
  DOI: 10.xxxx/yyyy2
- id: Neumann22Strangler
  type: paper-conference
  author:
  - family: Neumann
    given: F.
  issued:
    year: 2022
  title: Strangler-Based Migration in Industrial Case Studies
  container-title: Proceedings of the Example Symposium on Software Maintenance
  DOI: 10.xxxx/yyyy3
- id: AdaptiveCore25Guide
  type: webpage
  author:
  - literal: AdaptiveCore Ltd.
  issued:
    year: 2025
  title: AdaptiveCore Operations Guide
  URL: https://docs.example.com/adaptivecore/operations
- id: ServiceLink24Manual
  type: webpage
  author:
  - literal: ServiceLink Project
  issued:
    year: 2024
  title: ServiceLink Discovery Reference Manual
  URL: https://docs.example.com/servicelink/reference
- id: Ferreira23SDV
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2023
  title: Reference Architectures for Software-Defined Vehicles
  container-title: Example Journal of Vehicle Engineering
  DOI: 10.xxxx/xc11
- id: Kaur24Latency
  type: paper-conference
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2024
  title: Service Discovery Overhead After Control Unit Decomposition
  container-title: Proceedings of the Example Conference on Embedded Systems
  DOI: 10.xxxx/xc12
- id: Delgado22Coupling
  type: article-journal
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2022
  title: Coupling Measures for Domain Boundary Identification
  container-title: Journal of Example Software Architecture
  DOI: 10.xxxx/xc13
- id: Lindqvist25Consistency
  type: article-journal
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2025
  title: Consistency Models for Incremental State Migration
  container-title: Example Journal of Distributed Systems
  DOI: 10.xxxx/xc14
- id: Aranda24Strangler
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2024
  title: Strangler Migrations Outside Information Systems
  container-title: Journal of Empirical Software Engineering Examples
  DOI: 10.xxxx/xc15
---
