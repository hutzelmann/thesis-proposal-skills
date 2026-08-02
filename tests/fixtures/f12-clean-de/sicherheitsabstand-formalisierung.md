# Einführung und Motivation

Automatisierte Fahrfunktionen entscheiden in nahezu jedem Regelschritt darüber, welcher Abstand zu vorausfahrenden und benachbarten Verkehrsteilnehmern noch vertretbar ist.
Verletzungen dieser Abstände bleiben in der Simulation oft unbemerkt, weil gängige Bewertungsverfahren nur Kollisionen zählen und Beinaheereignisse nicht sichtbar machen [@Berger21Responsibility].
Solche unbemerkten Verletzungen führen dazu, dass Freigabeentscheidungen auf einer unvollständigen Sicherheitsargumentation beruhen [@Vogel23Formal].
Die vorliegende Arbeit untersucht, wie ein formales Abstandsmodell Sicherheitsverletzungen bereits vor der Auswertung eines Fahrversuchs erkennbar macht.

# Problemstellung und Forschungsfragen

Der Forschungsfokus liegt auf der Frage, welchen Anteil realer Abstandsverletzungen ein unsicherheitsbehaftetes Abstandsmodell mit minimalen Annahmen formal ausschließen kann.

1. In welchem Maße lassen sich Sicherheitsabstände einschließlich verdeckter und lateral bewegter Verkehrsteilnehmer in einem unsicherheitsbehafteten Modell ausdrücken?
2. Unter welchen Bedingungen bleibt die Prüfung der Abstandsbedingungen entscheidbar und mit vertretbarem Aufwand durchführbar?
3. Zu welchem Grad deckt das formalisierte Modell die in der Literatur dokumentierten Klassen kritischer Fahrsituationen ab?

# Verwandte Arbeiten

Bestehende Ansätze formalisieren Sicherheitsabstände für einzelne Fahrmanöver, setzen dafür jedoch vollständige und fehlerfreie Umfeldwahrnehmung voraus [@Berger21Responsibility].
Laufzeitüberwachungen erkennen Verletzungen erst während der Fahrt und liefern keine Aussage über nicht befahrene Situationen [@Roth24Runtime].
Diese Arbeit formalisiert ein Abstandsmodell mit expliziter Wahrnehmungsunsicherheit, das nur an den Schnittstellen der Wahrnehmung Annahmen benötigt und den Regelkern unverändert lässt.
Gegenüber @Vogel23Formal erweitert die Formalisierung die abgedeckten Situationsklassen um Verdeckungen und laterale Manöver.
Formale Sicherheitsmodelle für automatisiertes Fahren werden inzwischen in Normungsgremien als Referenz herangezogen [@Ibarra23Standards].
@Sorensen24Uncertainty zeigen, dass die Vernachlässigung von Wahrnehmungsunsicherheit die berechneten Mindestabstände systematisch unterschätzt.
Entscheidbarkeitsresultate für hybride Systeme begrenzen, welche Klassen solcher Bedingungen überhaupt automatisch prüfbar sind [@Halbach22Decidable].
Für die Bewertung von Beinaheereignissen existieren Kritikalitätsmetriken, die jedoch ohne formale Garantie auskommen [@Weber24Criticality], und Verdeckungsmodelle für die Planung liegen ebenfalls vor [@Novak25Occlusion].
Maschinell geprüfte Beweise für Sicherheitsabstände sind bislang nur für unverdeckte Längsszenarien veröffentlicht [@Aranda23Proofs].

# Methodik: Theoretische Analyse

## Definition des Anwendungsfalls

Gegenstand der Untersuchung ist eine innerstädtische Kreuzung mit Sichtverdeckungen durch parkende Fahrzeuge, modelliert als Menge von Verkehrssituationen mit unsicherer Wahrnehmung.
Dieser Anwendungsfall eignet sich für die Forschungsfragen, weil Verdeckungen dort systematisch auftreten und die Abstandsbedingungen genau dann nicht mehr aus vollständiger Wahrnehmung ableitbar sind.
Die Situationsklassen stammen aus einer öffentlich dokumentierten Taxonomie; nicht betrachtet werden Autobahnszenarien und Situationen mit mehr als vier beteiligten Verkehrsteilnehmern.

## Formalisierung

Die Analyse definiert einen Kalkül, dessen Zustandsraum Position, Geschwindigkeit und Wahrnehmungsunsicherheit jedes Verkehrsteilnehmers umfasst und der etablierte Kalküle zur verantwortungssensitiven Sicherheit aufgreift [@Klein20Calculi].
Aufbauend darauf formalisiert die Arbeit Abstandsregeln samt Prüfalgorithmus und weist deren Ausdrucksmächtigkeit für Verdeckungen und laterale Manöver nach (RQ1).
Ein Entscheidbarkeitsbeweis grenzt ab, unter welchen Bedingungen der Prüfalgorithmus terminiert (RQ2).

## Anforderungen

Das Modell muss longitudinale, laterale und verdeckungsbedingte Abstandsbedingungen ausdrücken können.
Erwartet wird ferner ein Soundness-Beweis für den Kernkalkül.
Vernachlässigbar sind Fahrdynamik höherer Ordnung, Kommunikationslatenzen und die Performanz einer späteren Implementierung.

## Beispiel

Als durchgängiges Beispiel dient eine vereinfachte innerstädtische Kreuzung, in der ein verdeckter Radfahrer und ein einscherendes Fahrzeug zusammentreffen.
Eine Abbildung der in der Literatur dokumentierten Situationsklassen auf dieses Beispiel zeigt, welche Klassen das Modell formal ausschließt (RQ3).

# Zielsetzung

Primäres Ziel ist die Formalisierung eines Abstandsmodells, das Wahrnehmungsunsicherheit explizit führt und dessen Prüfung entscheidbar bleibt.

Weitere Ziele:

- Einen Kalkül für Position, Geschwindigkeit und Unsicherheit der Verkehrsteilnehmer definieren.
- Abstandsregeln samt Prüfalgorithmus formulieren und deren Korrektheit beweisen.
- Die Entscheidbarkeitsgrenzen des Prüfalgorithmus bestimmen.
- Die abgedeckten Situationsklassen an einem durchgängigen Beispiel nachweisen.

# Erwartete Beiträge und Ergebnisse

Der wissenschaftliche Beitrag besteht in einem bewiesen korrekten Abstandsmodell, das Verdeckungen und laterale Manöver unter expliziter Unsicherheit abdeckt.
Praktisch entsteht daraus eine Prüfvorschrift, die sich auf aufgezeichnete Fahrdaten anwenden lässt, ohne den Regelkern einer Fahrfunktion zu verändern.
Erwartet wird, dass die Entscheidbarkeit an unbeschränkte Unsicherheitsintervalle gebunden ist und dass verdeckungsbedingte Situationsklassen nur teilweise formal ausschließbar sind.
Absehbare Grenzen sind die Beschränkung auf einen Kernkalkül, die Vernachlässigung von Fahrdynamik höherer Ordnung und die Abhängigkeit von einer Taxonomie, die selbst unvollständig ist.

# Arbeitsplan und Zeitplan

| Aufgabe | Wochen |
|---|---|
| Literatur und Kalkülauswahl | 1-4 |
| Definition des Kernkalküls | 3-8 |
| Abstandsregeln und Prüfalgorithmus | 7-13 |
| Korrektheits- und Entscheidbarkeitsbeweise | 12-18 |
| Durchgängiges Beispiel und Abdeckungsanalyse | 17-21 |
| Ausarbeitung und Überarbeitung | 18-24 |

Die Beweise hängen vollständig vom fertigen Kalkül ab und bilden damit den kritischen Pfad.
Das durchgängige Beispiel wird bewusst erst nach den Beweisen ausgearbeitet, weil es deren Voraussetzungen illustrieren soll.
Vier Wochen Überlappung zwischen Analyse und Ausarbeitung fangen Rückmeldungen ab.

---
title: Ein formales Abstandsmodell zur Bewertung automatisierter Fahrfunktionen unter Wahrnehmungsunsicherheit
author: Erika Musterfrau
subtitle: "Exposé zur Bachelorarbeit"
lang: de
references:
- id: Berger21Responsibility
  type: article-journal
  author:
  - family: Berger
    given: T.
  issued:
    year: 2021
  title: Responsibility-Sensitive Safety Models for Urban Driving
  container-title: Example Journal of Vehicle Safety
  DOI: 10.xxxx/zzzz1
- id: Vogel23Formal
  type: paper-conference
  author:
  - family: Vogel
    given: N.
  issued:
    year: 2023
  title: Formal Detection of Safety Envelope Violations in Driving Logs
  container-title: Proceedings of the Example Conference on Formal Methods
  DOI: 10.xxxx/zzzz2
- id: Roth24Runtime
  type: article-journal
  author:
  - family: Roth
    given: C.
  issued:
    year: 2024
  title: Runtime Monitoring of Safety Envelopes and Its Overhead
  container-title: Example Journal of Empirical Systems Engineering
  DOI: 10.xxxx/zzzz3
- id: Klein20Calculi
  type: paper-conference
  author:
  - family: Klein
    given: D.
  issued:
    year: 2020
  title: Calculi for Safety Distance Reasoning under Uncertainty
  container-title: Proceedings of the Example Symposium on Hybrid Systems
  DOI: 10.xxxx/zzzz4
- id: Ibarra23Standards
  type: article-journal
  author:
  - family: Ibarra
    given: L.
  issued:
    year: 2023
  title: Formal Safety Models in Automated Driving Standardisation
  container-title: Example Journal of Vehicle Safety
  DOI: 10.xxxx/zz11
- id: Sorensen24Uncertainty
  type: paper-conference
  author:
  - family: Sorensen
    given: M.
  issued:
    year: 2024
  title: Perception Uncertainty and Minimum Safe Distance
  container-title: Proceedings of the Example Conference on Intelligent Vehicles
  DOI: 10.xxxx/zz12
- id: Halbach22Decidable
  type: article-journal
  author:
  - family: Halbach
    given: T.
  issued:
    year: 2022
  title: Decidability Boundaries for Hybrid System Verification
  container-title: Example Journal of Formal Methods
  DOI: 10.xxxx/zz13
- id: Weber24Criticality
  type: article-journal
  author:
  - family: Weber
    given: S.
  issued:
    year: 2024
  title: Criticality Metrics for Near-Miss Assessment
  container-title: Journal of Example Traffic Safety Research
  DOI: 10.xxxx/zz14
- id: Novak25Occlusion
  type: paper-conference
  author:
  - family: Novak
    given: T.
  issued:
    year: 2025
  title: Occlusion Models for Urban Motion Planning
  container-title: Proceedings of the Example Conference on Robotics
  DOI: 10.xxxx/zz15
- id: Aranda23Proofs
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2023
  title: Mechanised Proofs for Safety Envelopes
  container-title: Example Journal of Automated Reasoning
  DOI: 10.xxxx/zz16
---
