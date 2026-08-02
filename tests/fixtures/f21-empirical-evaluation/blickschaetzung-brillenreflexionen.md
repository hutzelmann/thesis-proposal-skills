# Einführung und Motivation

Kamerabasierte Fahrerbeobachtung schätzt die Blickrichtung aus Bildern der Augenpartie und meldet Ablenkung, sobald der Blick zu lange von der Straße abweicht.
Brillengläser erzeugen Reflexionen der Innenraumbeleuchtung, die genau diese Augenpartie überstrahlen [@Ahmadi22Gaze].
Berichtete Genauigkeiten stammen überwiegend aus Datensätzen, in denen Brillenträger unterrepräsentiert sind [@Baumgartner24Bias].
Ein Verfahren, das im Mittel gut abschneidet, kann für eine Teilgruppe der Fahrenden systematisch versagen, ohne dass dies in der Gesamtmetrik sichtbar wird.
Die vorliegende Arbeit vergleicht deshalb Blickschätzverfahren gezielt unter Brillenreflexionen.

# Problemstellung und Forschungsfragen

Der Forschungsfokus liegt auf der Genauigkeit kamerabasierter Blickschätzverfahren bei Brillenträgern unter variierender Reflexionsstärke.

1. In welchem Maße unterscheidet sich der Winkelfehler etablierter Blickschätzverfahren zwischen Aufnahmen mit und ohne Brillenreflexion?
2. Unter welchen Reflexionsstärken überschreitet der Winkelfehler die für eine Ablenkungserkennung nutzbare Schwelle?
3. Zu welchem Grad lässt sich der Genauigkeitsverlust der Vorverarbeitung zur Reflexionsunterdrückung zuordnen statt der Modellarchitektur?

# Verwandte Arbeiten

Veröffentlichte Vergleiche von Blickschätzverfahren berichten aggregierte Winkelfehler über den gesamten Testdatensatz [@Ahmadi22Gaze].
Arbeiten zu Verzerrungen in Fahrerbeobachtungsdaten dokumentieren die Unterrepräsentation von Brillenträgern, evaluieren aber keine Verfahren entlang dieses Merkmals [@Baumgartner24Bias].
@Feldkamp25Robust schlagen eine Vorverarbeitung zur Reflexionsunterdrückung vor und weisen deren Nutzen an einem einzelnen Verfahren nach.
Diese Arbeit ergänzt eine vergleichende Evaluation mehrerer Verfahren unter kontrolliert variierter Reflexionsstärke und trennt den Beitrag der Vorverarbeitung vom Beitrag der Modellarchitektur.
Damit wird sichtbar, ob Robustheit gegenüber Reflexionen eine Eigenschaft des Modells oder der Vorverarbeitung ist.
Standards für die Berichterstattung von Modellvergleichen fordern Varianzangaben und Ablationen, werden in der Praxis aber selten eingehalten [@Ferreira23Reporting].
@Kaur24Subgroup zeigen, dass aggregierte Genauigkeiten Teilgruppenfehler in Fahrerbeobachtungsdaten systematisch verdecken.
Bildmaße zur Quantifizierung spiegelnder Reflexionen sind etabliert [@Delgado22Specular], und die Auswirkung von Trainingsdatenzusammensetzung auf Teilgruppenfehler ist dokumentiert [@Lindqvist25Composition].
Für Blickschätzung existieren Schwellenwerte, ab denen ein Winkelfehler die Ablenkungserkennung unbrauchbar macht [@Aranda24Threshold].
Personendisjunkte Aufteilungen gelten in Fahrerbeobachtungs-Benchmarks als Mindestanforderung, werden aber nicht durchgängig eingehalten [@Beck23Splits].
Für die Zuordnung eines Effekts zur Vorverarbeitung statt zur Architektur liegen ausgearbeitete Ablationsdesigns vor [@Novak25Ablation].

# Methodik: Empirische Modellevaluation

## Definition des Anwendungsfalls

Gegenstand der Untersuchung sind zwei öffentlich verfügbare Datensätze zur Blickschätzung im Fahrzeuginnenraum, die Aufnahmen von Brillenträgern in unterschiedlicher Beleuchtung enthalten.
Dieser Anwendungsfall eignet sich für die Forschungsfragen, weil nur dort Reflexionsstärke und Blickwahrheit gemeinsam vorliegen und damit ein Fehler entlang der Reflexionsstärke aufgelöst werden kann.
Beide Datensätze sind für Forschungszwecke frei nutzbar; Nachtaufnahmen und Sonnenbrillen sind darin unterrepräsentiert und begrenzen die Reichweite der Aussagen.

## Daten und Baselines

Die Evaluation nutzt zwei öffentlich verfügbare Datensätze zur Blickschätzung im Fahrzeuginnenraum, die Aufnahmen mit und ohne Brille enthalten und deren Aufteilung in Trainings-, Validierungs- und Testmenge personendisjunkt erfolgt.
Als Baselines dienen drei veröffentlichte Verfahren mit frei verfügbaren Gewichten, die unterschiedliche Architekturfamilien vertreten [@Ahmadi22Gaze].
Ein viertes Verfahren mit vorgeschalteter Reflexionsunterdrückung ergänzt die Vergleichsmenge [@Feldkamp25Robust].
Die Reflexionsstärke jeder Testaufnahme wird über ein publiziertes Bildmaß quantifiziert und in vier Stufen eingeteilt.

## Versuchsaufbau

Alle Verfahren laufen unverändert in ihrer veröffentlichten Konfiguration auf derselben Hardware, sodass Unterschiede nicht auf abweichende Laufzeitumgebungen zurückgehen.
Jeder Durchlauf wird mit fünf verschiedenen Zufallsinitialisierungen wiederholt, soweit das Verfahren nachtrainiert wird; rein inferenzbasierte Verfahren laufen einmal, da ihr Ergebnis deterministisch ist.
Hyperparameter werden ausschließlich auf der Validierungsmenge gewählt, die Testmenge bleibt bis zur Endauswertung ungenutzt.

## Analyse

Der mittlere Winkelfehler wird getrennt nach Aufnahmen mit und ohne Brille berichtet, jeweils mit Konfidenzintervall über die Wiederholungen (RQ1).
Eine Auswertung entlang der vier Reflexionsstufen bestimmt, ab welcher Stufe der Fehler die Nutzbarkeitsschwelle überschreitet (RQ2).
Eine Ablation, die die Reflexionsunterdrückung einzeln zu- und abschaltet, trennt deren Beitrag von dem der Architektur (RQ3).

# Zielsetzung

Primäres Ziel ist eine vergleichende Evaluation von Blickschätzverfahren, die den Genauigkeitsverlust unter Brillenreflexionen quantifiziert und seiner Ursache zuordnet.

Weitere Ziele:

- Die Reflexionsstärke jeder Testaufnahme über ein publiziertes Bildmaß quantifizieren und stufen.
- Drei Baseline-Verfahren und ein Verfahren mit Reflexionsunterdrückung unter identischen Bedingungen ausführen.
- Den Winkelfehler getrennt nach Brillenträgern und Reflexionsstufe mit Varianzangabe berichten.
- Den Beitrag der Vorverarbeitung durch eine Ablation von dem der Architektur trennen.

# Erwartete Beiträge und Ergebnisse

Der wissenschaftliche Beitrag besteht in einer nach Reflexionsstärke aufgelösten Fehleranalyse, die aggregierte Benchmarkwerte durch eine teilgruppenspezifische Aussage ersetzt.
Praktisch entsteht daraus eine Entscheidungsgrundlage dafür, ob in einem Serienprojekt die Vorverarbeitung oder die Modellarchitektur gewechselt werden sollte.
Erwartet wird, dass der Winkelfehler ab der dritten Reflexionsstufe die Nutzbarkeitsschwelle überschreitet und dass die Vorverarbeitung einen größeren Anteil des Verlusts erklärt als die Architektur.
Absehbare Grenzen sind zwei Datensätze, die Unterrepräsentation von Nachtaufnahmen und Sonnenbrillen sowie der Verzicht auf ein Nachtraining der Baselines.

# Arbeitsplan und Zeitplan

| Aufgabe | Wochen |
|---|---|
| Literatur und Datensatzsichtung | 1-4 |
| Aufbau der Evaluationsumgebung | 3-8 |
| Quantifizierung der Reflexionsstärke | 6-10 |
| Durchführung der Vergleichsläufe | 10-15 |
| Ablation und Auswertung | 14-19 |
| Ausarbeitung und Überarbeitung | 17-24 |

Die Vergleichsläufe setzen die abgeschlossene Stufeneinteilung voraus, die damit auf dem kritischen Pfad liegt.
Die Evaluationsumgebung wird parallel zur Datensatzsichtung aufgebaut, weil beide voneinander unabhängig sind.
Fünf Wochen Überlappung zwischen Auswertung und Ausarbeitung fangen einen Wiederholungslauf ab.

---
title: Empirische Evaluation von Blickschätzverfahren unter Brillenreflexionen
author: Erika Musterfrau
subtitle: "Exposé zur Masterarbeit"
lang: de
references:
- id: Ahmadi22Gaze
  type: article-journal
  author:
  - family: Ahmadi
    given: N.
  issued:
    year: 2022
  title: Gaze Estimation Benchmarks for In-Vehicle Camera Systems
  container-title: Journal of Example Vehicular Intelligence
  DOI: 10.xxxx/xxx70
- id: Baumgartner24Bias
  type: paper-conference
  author:
  - family: Baumgartner
    given: S.
  issued:
    year: 2024
  title: Bias in Driver Monitoring Datasets
  container-title: Proceedings of the Example Conference on Human Factors
  DOI: 10.xxxx/xxx71
- id: Feldkamp25Robust
  type: article-journal
  author:
  - family: Feldkamp
    given: J.
  issued:
    year: 2025
  title: Robust Gaze Estimation under Specular Reflections
  container-title: Journal of Example Computer Vision Applications
  DOI: 10.xxxx/xxx72
- id: Ferreira23Reporting
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2023
  title: Reporting Practice in Model Comparison Studies
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xa11
- id: Kaur24Subgroup
  type: paper-conference
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2024
  title: Aggregate Accuracy Hides Subgroup Failure in Driver Monitoring
  container-title: Proceedings of the Example Conference on Human Factors
  DOI: 10.xxxx/xa12
- id: Delgado22Specular
  type: article-journal
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2022
  title: Quantifying Specular Reflection in Facial Imagery
  container-title: Journal of Example Computer Vision Applications
  DOI: 10.xxxx/xa13
- id: Lindqvist25Composition
  type: article-journal
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2025
  title: Training Set Composition and Subgroup Error
  container-title: Journal of Example Machine Learning Research Examples
  DOI: 10.xxxx/xa14
- id: Aranda24Threshold
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2024
  title: Angular Error Thresholds for Distraction Detection
  container-title: Journal of Example Vehicular Intelligence
  DOI: 10.xxxx/xa15
- id: Beck23Splits
  type: article-journal
  author:
  - family: Beck
    given: A.
  issued:
    year: 2023
  title: Person-Disjoint Splits in Driver Monitoring Benchmarks
  container-title: Journal of Example Traffic Safety Research
  DOI: 10.xxxx/xa16
- id: Novak25Ablation
  type: paper-conference
  author:
  - family: Novak
    given: T.
  issued:
    year: 2025
  title: Ablation Design for Preprocessing Pipelines
  container-title: Proceedings of the Example Conference on Computer Vision
  DOI: 10.xxxx/xa17
---
