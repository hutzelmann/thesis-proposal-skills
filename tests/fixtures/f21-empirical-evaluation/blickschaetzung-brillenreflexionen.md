# Einführung in das Thema

Kamerabasierte Fahrerbeobachtung schätzt die Blickrichtung aus Bildern der Augenpartie und meldet Ablenkung, sobald der Blick zu lange von der Straße abweicht.
Brillengläser erzeugen Reflexionen der Innenraumbeleuchtung, die genau diese Augenpartie überstrahlen [@Ahmadi22Gaze].
Berichtete Genauigkeiten stammen überwiegend aus Datensätzen, in denen Brillenträger unterrepräsentiert sind [@Baumgartner24Bias].
Ein Verfahren, das im Mittel gut abschneidet, kann für eine Teilgruppe der Fahrenden systematisch versagen, ohne dass dies in der Gesamtmetrik sichtbar wird.
Die vorliegende Arbeit vergleicht deshalb Blickschätzverfahren gezielt unter Brillenreflexionen.

# Beitrag zum Stand der Technik

Veröffentlichte Vergleiche von Blickschätzverfahren berichten aggregierte Winkelfehler über den gesamten Testdatensatz [@Ahmadi22Gaze].
Arbeiten zu Verzerrungen in Fahrerbeobachtungsdaten dokumentieren die Unterrepräsentation von Brillenträgern, evaluieren aber keine Verfahren entlang dieses Merkmals [@Baumgartner24Bias].
@Feldkamp25Robust schlagen eine Vorverarbeitung zur Reflexionsunterdrückung vor und weisen deren Nutzen an einem einzelnen Verfahren nach.
Diese Arbeit ergänzt eine vergleichende Evaluation mehrerer Verfahren unter kontrolliert variierter Reflexionsstärke und trennt den Beitrag der Vorverarbeitung vom Beitrag der Modellarchitektur.
Damit wird sichtbar, ob Robustheit gegenüber Reflexionen eine Eigenschaft des Modells oder der Vorverarbeitung ist.

# Forschungsfokus und Forschungsfragen

Der Forschungsfokus liegt auf der Genauigkeit kamerabasierter Blickschätzverfahren bei Brillenträgern unter variierender Reflexionsstärke.

1. In welchem Maße unterscheidet sich der Winkelfehler etablierter Blickschätzverfahren zwischen Aufnahmen mit und ohne Brillenreflexion?
2. Unter welchen Reflexionsstärken überschreitet der Winkelfehler die für eine Ablenkungserkennung nutzbare Schwelle?
3. Zu welchem Grad lässt sich der Genauigkeitsverlust der Vorverarbeitung zur Reflexionsunterdrückung zuordnen statt der Modellarchitektur?

# Forschungsmethodik: Empirische Modellevaluation

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
---
