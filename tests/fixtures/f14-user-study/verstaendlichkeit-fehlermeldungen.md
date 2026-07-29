# Einführung in das Thema

Programmieranfänger verbringen einen erheblichen Teil ihrer Übungszeit mit der Deutung von Compiler-Fehlermeldungen [@Weber23Kryptische].
Viele dieser Meldungen richten sich an erfahrene Entwickler und setzen Wissen über Interna des Compilers voraus.
Empirische Untersuchungen zeigen, dass unverständliche Meldungen den Lernfortschritt bremsen und Frustration erzeugen [@Nowak22Novice].
Gestaltungsrichtlinien für verständlichere Meldungen existieren, ihre Wirkung auf Anfänger ist jedoch kaum direkt gemessen.
Diese Arbeit untersucht die Wirkung umformulierter Fehlermeldungen in einer kontrollierten Nutzerstudie.

# Beitrag zum Stand der Technik

Bisherige Studien bewerten umformulierte Fehlermeldungen überwiegend indirekt, etwa über Kennzahlen aus Übungsplattformen [@Nowak22Novice] oder über Einschätzungen von Lehrenden [@Keller24Messages].
Direkte Messungen, ob Anfänger mit umformulierten Meldungen Fehler schneller und korrekter beheben, fehlen weitgehend.
Diese Arbeit schließt die Lücke durch eine kontrollierte Nutzerstudie mit Studierenden des ersten Studienjahres.
Der Beitrag liegt in belastbaren Messdaten zu Verständnis, Korrekturzeit und wahrgenommener Verständlichkeit, die bestehende Gestaltungsrichtlinien empirisch fundieren.

# Forschungsfokus und Forschungsfragen

Der Forschungsfokus liegt auf der messbaren Wirkung umformulierter Compiler-Fehlermeldungen auf Programmieranfänger im ersten Studienjahr, abgegrenzt auf typische Fehlerbilder in Java.
Die Studie erfasst sowohl objektive Größen als auch die subjektive Einschätzung der Teilnehmenden.

1. In welchem Maße erhöhen umformulierte Compiler-Fehlermeldungen die Korrektheit, mit der Programmieranfänger die Ursache eines Fehlers benennen?
2. Unter welchen Bedingungen verkürzen umformulierte Compiler-Fehlermeldungen die Zeit bis zur erfolgreichen Korrektur eines Fehlers?
3. In welchem Maße unterscheidet sich die wahrgenommene Verständlichkeit zwischen originalen und umformulierten Meldungen?

# Forschungsmethodik: Nutzerstudie

## Vorbereitung

Die Studie folgt einem Within-Subject-Design mit den Bedingungen originale und umformulierte Meldungen.
Als Material dienen zwölf kurze Java-Programme mit je einem typischen Anfängerfehler aus einer dokumentierten Fehlerklassifikation [@Weber23Kryptische].
Die umformulierten Meldungen entstehen nach publizierten Gestaltungsrichtlinien [@Keller24Messages].
Rekrutiert wird über Erstsemesterveranstaltungen; die Teilnahme ist freiwillig und anonym.

## Durchführung

Jede teilnehmende Person bearbeitet alle zwölf Programme in randomisierter Reihenfolge, je sechs pro Bedingung.
Zu jedem Programm benennt sie zunächst die vermutete Fehlerursache und korrigiert anschließend den Code im Editor.
Die Studienumgebung protokolliert die benannte Ursache, die Korrekturzeit und den Erfolg der Korrektur; ein abschließender Fragebogen erhebt die wahrgenommene Verständlichkeit auf einer Likert-Skala.

## Analyse

Ein gepaarter statistischer Test vergleicht die Korrektheit der Ursachenbenennung zwischen beiden Bedingungen (RQ1).
Eine nach Fehlerklassen getrennte Auswertung der Korrekturzeiten zeigt, unter welchen Bedingungen die Umformulierung Zeit einspart (RQ2).
Die Auswertung der Fragebogendaten stellt die wahrgenommene Verständlichkeit beider Bedingungen gegenüber (RQ3).

---
title: Verständlichkeit von Compiler-Fehlermeldungen für Programmieranfänger
author: Erika Musterfrau
subtitle: "Exposé zur Bachelorarbeit"
lang: de
references:
- id: Weber23Kryptische
  type: paper-conference
  author:
  - family: Weber
    given: A.
  issued:
    year: 2023
  title: Kryptische Fehlermeldungen im Programmierunterricht
  container-title: Tagungsband der Beispielkonferenz für Informatikdidaktik
  DOI: 10.xxxx/xxx20
- id: Nowak22Novice
  type: article-journal
  author:
  - family: Nowak
    given: P.
  issued:
    year: 2022
  title: Novice Programmers and Compiler Error Messages
  container-title: Journal of Example Computing Education
  DOI: 10.xxxx/xxx21
- id: Keller24Messages
  type: paper-conference
  author:
  - family: Keller
    given: B.
  issued:
    year: 2024
  title: Messages that Teach — Design Guidelines for Compiler Diagnostics
  container-title: Proceedings of the Example Conference on Programming Education
  DOI: 10.xxxx/xxx22
---
