# Einführung in das Thema

Gewachsene Warenwirtschaftssysteme bilden in vielen Handelsunternehmen den betrieblichen Kern, sind jedoch häufig als schwer wartbare Monolithen umgesetzt [@Hoffmann23Migration].
Eine Zerlegung in Microservices verspricht kürzere Release-Zyklen und eine unabhängige Skalierung einzelner Fachdomänen [@Lang24Decomposition].
Der Umbau eines produktiven Systems birgt allerdings erhebliche Risiken, da Bestandsprozesse unterbrechungsfrei weiterlaufen müssen.
Die vorliegende Arbeit untersucht deshalb, unter welchen Bedingungen eine schrittweise Migration einer monolithischen Lagerverwaltung gelingt.

# Beitrag zum Stand der Technik

Verwandte Arbeiten beschreiben Migrationsmuster wie die Strangler-Fig-Strategie und bewerten sie anhand einzelner Industriefallstudien [@Neumann22Strangler].
Offen bleibt, wie sich diese Muster auf Lagerverwaltungssysteme mit stark gekoppelten Datenbeständen übertragen lassen [@Hoffmann23Migration].
Diese Arbeit schließt die Lücke, indem sie ein Bestandssystem mustergeleitet zerlegt und die Auswirkungen auf Antwortzeiten, Datenkonsistenz und Ausfallzeiten quantifiziert.
Damit entsteht eine nachvollziehbare Bewertung der Muster für datenintensive Bestandssysteme mittlerer Größe.

# Abgrenzung

Die Arbeit betrachtet ausschließlich die serverseitige Architektur der Lagerverwaltung.
Benutzeroberflächen, Betriebsprozesse und organisatorische Aspekte der Umstellung bleiben außerhalb des Untersuchungsrahmens.

# Forschungsfokus und Forschungsfragen

Der Forschungsfokus liegt auf der mustergeleiteten Zerlegung einer produktiven Lagerverwaltung und deren messbaren Auswirkungen auf zentrale Qualitätsmerkmale.

1. Zu welchem Grad lassen sich die Fachdomänen der Lagerverwaltung anhand statischer und dynamischer Kopplungsanalysen voneinander abgrenzen?
2. Lässt sich der Bestandsmonolith mit der Strangler-Fig-Strategie ohne messbare Ausfallzeit schrittweise ablösen?
3. Unter welchen Bedingungen bleibt die Datenkonsistenz zwischen extrahierten Services und verbleibendem Monolithen gewährleistet?

# Forschungsmethodik: Prototypimplementierung

## Vorarbeiten

Der Prototyp baut auf einem anonymisierten Abbild der bestehenden Lagerverwaltung auf.
Für die Kopplungsanalyse kommen etablierte Werkzeuge zur statischen Codeanalyse zum Einsatz [@Lang24Decomposition].
Die Migrationsinfrastruktur folgt dem Betriebsleitfaden der Container-Plattform StratoMesh [@StratoMesh25Guide] sowie der Referenzdokumentation des API-Gateways KubeFlex [@KubeFlex24Manual].

## Anforderungen

- Der Prototyp muss zwei Fachdomänen als eigenständige Services extrahieren.
- Der Prototyp muss eingehende Aufrufe transparent zwischen Monolith und Services routen.
- Der Prototyp muss Bestandsdaten während der Migration synchron halten.
- Der Prototyp soll Antwortzeiten und Fehlerraten fortlaufend protokollieren.

Optimierte Betriebskosten und eine vollständige Zerlegung aller Fachdomänen sind vernachlässigbar.

## Evaluation

Eine Kopplungsanalyse des Bestandssystems mit anschließender Experteneinschätzung bewertet die Abgrenzbarkeit der Fachdomänen (RQ1).
Ein Lasttest der schrittweisen Ablösung misst Ausfallzeiten während der Umschaltung zwischen Monolith und extrahierten Services (RQ2).
Konsistenzprüfungen auf replizierten Bestandsdaten unter parallelen Schreibzugriffen untersuchen die Grenzen der Datensynchronisation (RQ3).

# Zusammenfassung

Die Arbeit zerlegt eine produktive Lagerverwaltung mustergeleitet in Microservices und quantifiziert die Auswirkungen auf Ausfallzeiten und Datenkonsistenz.
Das Vorgehen liefert Handelsunternehmen eine belastbare Entscheidungsgrundlage für vergleichbare Migrationen.

# Zeitplan

Die Arbeit beginnt im Oktober 2026 und wird im März 2027 eingereicht.

---
title: Architekturgetriebene Migration einer monolithischen Lagerverwaltung zu Microservices
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
  title: Migration Strategies for Legacy Enterprise Systems
  container-title: Example Journal of Software Evolution
  DOI: 10.xxxx/yyyy1
- id: Lang24Decomposition
  type: paper-conference
  author:
  - family: Lang
    given: B.
  issued:
    year: 2024
  title: Decomposition of Monolithic Systems via Coupling Analysis
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
- id: StratoMesh25Guide
  type: webpage
  author:
  - literal: StratoMesh Ltd.
  issued:
    year: 2025
  title: StratoMesh Operations Guide
  URL: https://docs.example.com/stratomesh/operations
- id: KubeFlex24Manual
  type: webpage
  author:
  - literal: KubeFlex Project
  issued:
    year: 2024
  title: KubeFlex Gateway Reference Manual
  URL: https://docs.example.com/kubeflex/reference
---
