# Einführung in das Thema

Automatisierte Fahrfunktionen entscheiden in nahezu jedem Regelschritt darüber, welcher Abstand zu vorausfahrenden und benachbarten Verkehrsteilnehmern noch vertretbar ist.
Verletzungen dieser Abstände bleiben in der Simulation oft unbemerkt, weil gängige Bewertungsverfahren nur Kollisionen zählen und Beinaheereignisse nicht sichtbar machen [@Berger21Responsibility].
Solche unbemerkten Verletzungen führen dazu, dass Freigabeentscheidungen auf einer unvollständigen Sicherheitsargumentation beruhen [@Vogel23Formal].
Die vorliegende Arbeit untersucht, wie ein formales Abstandsmodell Sicherheitsverletzungen bereits vor der Auswertung eines Fahrversuchs erkennbar macht.

# Beitrag zum Stand der Technik

Bestehende Ansätze formalisieren Sicherheitsabstände für einzelne Fahrmanöver, setzen dafür jedoch vollständige und fehlerfreie Umfeldwahrnehmung voraus [@Berger21Responsibility].
Laufzeitüberwachungen erkennen Verletzungen erst während der Fahrt und liefern keine Aussage über nicht befahrene Situationen [@Roth24Runtime].
Diese Arbeit formalisiert ein Abstandsmodell mit expliziter Wahrnehmungsunsicherheit, das nur an den Schnittstellen der Wahrnehmung Annahmen benötigt und den Regelkern unverändert lässt.
Gegenüber @Vogel23Formal erweitert die Formalisierung die abgedeckten Situationsklassen um Verdeckungen und laterale Manöver.

# Forschungsfokus und Forschungsfragen

Der Forschungsfokus liegt auf der Frage, welchen Anteil realer Abstandsverletzungen ein unsicherheitsbehaftetes Abstandsmodell mit minimalen Annahmen formal ausschließen kann.

1. In welchem Maße lassen sich Sicherheitsabstände einschließlich verdeckter und lateral bewegter Verkehrsteilnehmer in einem unsicherheitsbehafteten Modell ausdrücken?
2. Unter welchen Bedingungen bleibt die Prüfung der Abstandsbedingungen entscheidbar und mit vertretbarem Aufwand durchführbar?
3. Zu welchem Grad deckt das formalisierte Modell die in der Literatur dokumentierten Klassen kritischer Fahrsituationen ab?

# Forschungsmethodik: Theoretische Analyse

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
---
