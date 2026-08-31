# Ein Typsystem zur statischen Erkennung von Einheitenfehlern in Simulationssoftware

*Exposé zur Bachelorarbeit*

## Einführung in das Thema

Wissenschaftliche Simulationssoftware verarbeitet physikalische Größen wie Kräfte, Zeiten und Temperaturen in nahezu jeder Berechnung.
Verwechslungen von Einheiten bleiben dabei oft unbemerkt, weil gängige Programmiersprachen Zahlenwerte ohne Einheiteninformation darstellen [@Berger21Dimensional].
Solche Fehler haben in der Vergangenheit zu erheblichen Schäden in Forschung und Technik geführt [@Vogel23Static].
Die vorliegende Arbeit untersucht, wie ein statisches Typsystem Einheitenfehler bereits vor der Ausführung erkennbar macht.

## Beitrag zum Stand der Technik

Bestehende Ansätze erweitern einzelne Sprachen um Einheitenannotationen, verlangen dafür jedoch Angaben an nahezu jeder Deklaration [@Berger21Dimensional].
Dynamische Prüfverfahren erkennen Einheitenfehler erst zur Laufzeit und verursachen messbaren Mehraufwand [@Roth24Runtime].
Diese Arbeit formalisiert ein Typsystem mit Einheiteninferenz, das Annotationen nur an Modulschnittstellen benötigt und den Programmkern unverändert lässt.
Gegenüber @Vogel23Static erweitert die Formalisierung die abgedeckten Fehlerklassen um zusammengesetzte und skalierte Einheiten.

## Forschungsfokus und Forschungsfragen

Der Forschungsfokus liegt auf der Frage, welchen Anteil realer Einheitenfehler ein inferenzbasiertes Typsystem mit minimalen Annotationen statisch ausschließen kann.

1. In welchem Maße lassen sich physikalische Einheiten einschließlich zusammengesetzter und skalierter Formen in einem inferenzbasierten Typsystem ausdrücken?
2. Unter welchen Bedingungen bleibt die Typprüfung für einheitenbehaftete Programme entscheidbar und mit vertretbarem Aufwand durchführbar?
3. Zu welchem Grad deckt das formalisierte Typsystem die in der Literatur dokumentierten Klassen von Einheitenfehlern ab?

## Forschungsmethodik: Theoretische Analyse

### Formalisierung

Die Analyse definiert einen Termkalkül, dessen Einheitentypen eine Abelsche Gruppe über Basiseinheiten bilden und der etablierte Kalküle zur Dimensionsanalyse aufgreift [@Klein20Calculi].
Aufbauend darauf formalisiert die Arbeit Typregeln samt Inferenzalgorithmus und weist deren Ausdrucksmächtigkeit für zusammengesetzte und skalierte Einheiten nach (RQ1).
Ein Entscheidbarkeitsbeweis grenzt ab, unter welchen Bedingungen der Inferenzalgorithmus terminiert (RQ2).

### Anforderungen

Das Typsystem muss zusammengesetzte, skalierte und dimensionslose Einheiten ausdrücken können.
Erwartet wird ferner ein Soundness-Beweis für den Kernkalkül.
Vernachlässigbar sind Nebenläufigkeit, Effekte höherer Ordnung und die Performanz einer späteren Implementierung.

### Beispiel

Als durchgängiges Beispiel dient ein vereinfachtes Modul zur Bahnberechnung, das Kräfte, Massen und Beschleunigungen kombiniert.
Eine Abbildung der in der Literatur dokumentierten Fehlerklassen auf dieses Beispiel zeigt, welche Klassen das Typsystem statisch ausschließt (RQ3).

## Zeitplan

Die Arbeit beginnt im April 2027 und wird im September 2027 eingereicht.

## Literatur

---
references:
- id: Berger21Dimensional
  type: article-journal
  author:
  - family: Berger
    given: T.
  issued:
    year: 2021
  title: Dimensional Types for Scientific Computing
  container-title: Example Journal of Programming Languages
  DOI: 10.xxxx/zzzz1
- id: Vogel23Static
  type: paper-conference
  author:
  - family: Vogel
    given: N.
  issued:
    year: 2023
  title: Static Detection of Unit Errors in Numerical Code
  container-title: Proceedings of the Example Conference on Static Analysis
  DOI: 10.xxxx/zzzz2
- id: Roth24Runtime
  type: article-journal
  author:
  - family: Roth
    given: C.
  issued:
    year: 2024
  title: Runtime Unit Checking and Its Overhead
  container-title: Example Journal of Empirical Software Engineering
  DOI: 10.xxxx/zzzz3
- id: Klein20Calculi
  type: paper-conference
  author:
  - family: Klein
    given: D.
  issued:
    year: 2020
  title: Calculi for Dimensional Analysis in Typed Languages
  container-title: Proceedings of the Example Symposium on Types
  DOI: 10.xxxx/zzzz4
---
