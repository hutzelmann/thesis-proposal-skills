# Einführung in das Thema

Gewachsene Fahrzeug-Softwarearchitekturen bilden in vielen Baureihen den funktionalen Kern, sind jedoch häufig als schwer wartbare Steuergeräte-Monolithen umgesetzt [@Hoffmann23Migration].
Eine Zerlegung in Dienste einer softwaredefinierten Fahrzeugplattform verspricht kürzere Release-Zyklen und eine unabhängige Aktualisierung einzelner Fahrfunktionen [@Lang24Decomposition].
Der Umbau eines seriennahen Systems birgt allerdings erhebliche Risiken, da sicherheitsrelevante Signalpfade unterbrechungsfrei weiterlaufen müssen.
Die vorliegende Arbeit untersucht deshalb, unter welchen Bedingungen eine schrittweise Migration eines monolithischen Komfortsteuergeräts gelingt.

# Beitrag zum Stand der Technik

Verwandte Arbeiten beschreiben Migrationsmuster wie die Strangler-Fig-Strategie und bewerten sie anhand einzelner Industriefallstudien [@Neumann22Strangler].
Offen bleibt, wie sich diese Muster auf Steuergeräte mit harten Latenzanforderungen und stark gekoppelten Signalflüssen übertragen lassen [@Hoffmann23Migration].
Diese Arbeit schließt die Lücke, indem sie ein Bestandssteuergerät mustergeleitet zerlegt und die Auswirkungen auf Signallatenzen, Zustandskonsistenz und Ausfallzeiten quantifiziert.
Damit entsteht eine nachvollziehbare Bewertung der Muster für latenzkritische Fahrzeugsysteme mittlerer Größe.

# Abgrenzung

Die Arbeit betrachtet ausschließlich die Softwarearchitektur des Komfortsteuergeräts.
Bedienoberflächen im Cockpit, Freigabeprozesse und organisatorische Aspekte der Umstellung bleiben außerhalb des Untersuchungsrahmens.

# Forschungsfokus und Forschungsfragen

Der Forschungsfokus liegt auf der mustergeleiteten Zerlegung eines seriennahen Steuergeräts und deren messbaren Auswirkungen auf zentrale Qualitätsmerkmale.

1. Zu welchem Grad lassen sich die Funktionsdomänen des Steuergeräts anhand statischer und dynamischer Kopplungsanalysen voneinander abgrenzen?
2. Lässt sich der Bestandsmonolith mit der Strangler-Fig-Strategie ohne messbare Ausfallzeit schrittweise ablösen?
3. Unter welchen Bedingungen bleibt die Zustandskonsistenz zwischen extrahierten Diensten und verbleibendem Monolithen gewährleistet?

# Forschungsmethodik: Prototypimplementierung

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
---
