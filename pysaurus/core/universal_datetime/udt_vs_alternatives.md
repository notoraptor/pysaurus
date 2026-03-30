# UDT vs alternatives : cftime et astropy.time

Rapport de comparaison réalisé le 2026-03-29.

Objectif : évaluer si `cftime` ou `astropy.time` peuvent remplacer `UDT`
(Universal DateTime), dont l'avantage principal est la gestion de toutes les
années (y compris négatives et au-delà de 9999) avec support complet des
fuseaux horaires, en arithmétique entière pure.

---

## Résumé

| Critère | UDT | cftime 1.6.5 | astropy.time 7.2.0 |
|---|---|---|---|
| Années négatives (ISO) | Oui (`fromisoformat`) | Oui (constructeur) | **Non** (ValueError, JD requis) |
| Année 0 | Oui | Oui (`has_year_zero`) | Oui (mais affiché `0`, pas `0000`) |
| Plage d'années | Illimitée (entiers Python) | ±2 147 483 647 (C `long`) | ~-4800 à ~+1 465 000 (limite ERFA) |
| Fuseaux horaires | Complet | **Aucun** | **Aucun natif** |
| Précision | Microseconde exacte (entiers) | Microseconde (flottants) | Sub-nanoseconde (flottants) |
| Erreurs d'arrondi | Aucune | Constatées (~32 µs) | Constatées (~39.5 ns accumulés) |
| Format ISO conforme | Oui (années étendues, offsets) | Partiel (pas de parsing ISO) | **Non** (pas de zero-padding, pas d'offsets) |
| Calendriers | Proleptic Gregorian | 6 calendriers | Proleptic Gregorian |
| Dépendances | Zéro (pur Python) | Extension C | ~55 Mo (numpy, pyerfa, ERFA) |
| Temps d'import | Instantané | Rapide | ~284 ms |
| Domaine cible | Datetime universel | Climatologie (netCDF) | Astronomie |

**Verdict : ni cftime ni astropy.time ne remplacent UDT.**

---

## 1. UDT vs cftime

### 1.1 Présentation de cftime

`cftime` est une bibliothèque Python pour manipuler des dates selon les
conventions CF (Climate and Forecasting), principalement utilisée pour les
fichiers netCDF en climatologie. Version testée : 1.6.5.

### 1.2 Points forts de cftime

- **Années négatives** : supportées nativement via le constructeur
  (`cftime.datetime(-1000, 6, 15, calendar='proleptic_gregorian')`).
- **Année 0** : supportée avec `has_year_zero=True` (défaut en
  `proleptic_gregorian`).
- **6 calendriers** : `proleptic_gregorian`, `standard`/`gregorian` (mixte
  Julian/Gregorian), `julian`, `noleap`/`365_day`, `all_leap`/`366_day`,
  `360_day`.
- **Arithmétique** : `+`, `-` avec `timedelta`, comparaisons complètes,
  tri fonctionnel.
- **Années bissextiles** : correctes pour les années négatives selon le
  calendrier choisi.
- **Utilitaires** : `date2num()`, `num2date()`, `is_leap_year()`,
  `change_calendar()`.
- **Hashable et picklable**.

### 1.3 Limitations de cftime

#### Pas de fuseaux horaires

C'est la limitation la plus critique. `cftime.datetime` n'a aucun concept de
timezone : pas d'offset UTC, pas de `astimezone()`, pas de conversion entre
fuseaux. Les dates sont des dates "naïves" sans localisation temporelle.

Pour un datetime à usage général (horodatage de fichiers, logs, conversion
entre fuseaux), c'est rédhibitoire.

#### Plage d'années limitée au C `long`

La plage est ±2 147 483 647 (INT32_MAX sur Windows, où le C `long` est 32
bits). Au-delà, `OverflowError: Python int too large to convert to C long`.

UDT utilise des entiers Python arbitraires : aucune limite.

#### Pas de parsing ISO 8601

Pas de méthode `fromisoformat()` ou équivalent. Il faut construire les dates
via le constructeur avec des arguments numériques ou via `num2date()` avec une
chaîne d'unités CF.

#### Erreurs d'arrondi en virgule flottante

`change_calendar()` entre `proleptic_gregorian` et `julian` introduit une
erreur de ~32 µs (123456 → 123488 microsecondes). Artefact des Julian Day
Numbers en flottant.

UDT utilise exclusivement l'arithmétique entière (JDN + microsecondes) :
zéro erreur d'arrondi.

#### Format de sortie non standard pour les années

- Les années négatives s'affichent `-1000-06-15` (correct).
- L'année 0 s'affiche `0000-06-15` (correct).
- Les grandes années s'affichent `100000-01-01` (pas de préfixe `+` comme
  ISO 8601 l'exige pour les années étendues).
- Pas de méthode `isoformat()` avec format étendu.

#### Comportement surprenant avec `has_year_zero`

Créer l'année 0 sur un calendrier avec `has_year_zero=False` (défaut pour
`standard`/`julian`) émet un `CFWarning` mais **ne lève pas d'erreur** :
`has_year_zero` est silencieusement forcé à `True`. Piège potentiel.

#### Extension C requise

`cftime` est une extension C compilée, pas du pur Python. Moins portable
qu'une solution pure Python.

#### Conversion vers `datetime` limitée

Pas de méthode `.to_pydatetime()`. La conversion manuelle échoue pour les
années hors de la plage 1-9999 de Python `datetime`.

### 1.4 Tableau détaillé

| Fonctionnalité | UDT | cftime |
|---|---|---|
| Années négatives | Oui | Oui |
| Année 0 | Oui | Oui (avec `has_year_zero`) |
| Plage d'années | Illimitée | ±2 147 483 647 |
| Fuseaux horaires | `Timezone`, `astimezone()`, conversion UTC | **Aucun** |
| Parsing ISO 8601 | `fromisoformat()` complet | **Aucun** |
| Formatage ISO 8601 | `isoformat()` avec années étendues | `str()` partiel |
| Timestamps Unix | `timestamp()`, `from_timestamp()` | Via `date2num()` indirect |
| Arithmétique entière | Oui (JDN + µs) | Non (flottants internes) |
| Calendriers | Proleptic Gregorian | 6 calendriers |
| Dépendances | Zéro | Extension C |
| `strftime()` | Non | Oui |
| `timetuple()` | Non | Oui |

### 1.5 Conclusion

cftime gère correctement les années négatives, mais c'est une bibliothèque
spécialisée pour la climatologie. L'absence totale de fuseaux horaires, le
recours aux flottants, et l'absence de parsing ISO la rendent inadaptée comme
remplacement de UDT pour un usage datetime universel.

Le seul avantage réel de cftime sur UDT est la diversité des calendriers
(Julian, noleap, 360-day, etc.), qui n'est pas un besoin de UDT.

---

## 2. UDT vs astropy.time

### 2.1 Présentation d'astropy.time

`astropy.time` fait partie d'Astropy, la bibliothèque de référence en
astronomie Python. Elle fournit une classe `Time` haute précision basée sur le
Julian Date en deux parties (`jd1 + jd2`, deux `float64`). Version testée :
7.2.0.

### 2.2 Points forts d'astropy.time

- **Précision théorique** : sub-nanoseconde (~0.01 ns) grâce à la
  représentation en deux `float64` (technique SOFA/ERFA).
- **Échelles de temps astronomiques** : UTC, TAI, TT, TDB, TCG, TCB, UT1.
  Conversions automatiques entre échelles.
- **Arithmétique** : `Time + TimeDelta`, `Time - Time`, comparaisons
  complètes.
- **Timestamps Unix** : `t.unix`, `Time(val, format='unix')`.
- **Calendrier** : proleptic Gregorian (identique à UDT).
- **Formats multiples** : ISO, Julian Date, Julian Year, MJD, GPS, Unix,
  décimal, etc.

### 2.3 Limitations d'astropy.time

#### Impossible de parser les années négatives en ISO

C'est le problème le plus fondamental. Toutes ces tentatives échouent avec
`ValueError` :

```python
Time('-1000-06-15', format='isot')          # ValueError
Time('-0050-03-15T00:00:00', format='isot') # ValueError
Time('-001000-06-15', format='isot')        # ValueError (étendu aussi)
```

Il faut contourner via le Julian Day Number :

```python
Time(1356182.5, format='jd')  # -999-01-01 (convention astronomique)
```

Cela élimine l'intérêt principal pour un usage avec des dates historiques
ou BCE.

#### Plage d'années sévèrement limitée pour la sortie ISO

- Minimum : ~-4800 (année calendaire). En dessous, la fonction ERFA `d2dtf`
  lève "unacceptable date".
- Maximum : ~+1 465 000. Au-delà, `ErfaError`.
- La valeur JD interne peut stocker des dates plus extrêmes, mais elles ne
  sont pas convertibles en chaîne ISO.

UDT n'a aucune limite dans les deux sens.

#### Pas de fuseau horaire natif

`Time` n'a pas de concept de timezone. Les objets sont dans une "échelle"
(utc, tai, tt...), pas dans un fuseau civil.

```python
Time('2024-06-15T10:30:00+05:00', format='isot')  # ValueError
```

La conversion timezone passe obligatoirement par Python `datetime` :

```python
t.to_datetime(timezone=tz)  # conversion de sortie uniquement
```

Pas de `astimezone()`, pas d'offset UTC porté par l'objet.

#### Erreurs d'arrondi en virgule flottante

Malgré la technique deux-parties, les erreurs s'accumulent :

- **Opération unitaire** : 1 µs mesuré comme `1.000000082740371e-06` s
  (erreur de 82 ps).
- **Accumulation** : 86400 additions de 1 seconde dérivent de **~39.5 ns**
  par rapport au résultat attendu.
- **Aller-retour** : `t + 1µs - 1µs` revient à zéro (annulation favorable).

UDT : arithmétique entière, zéro dérive par construction.

#### Format ISO non standard en sortie

- Pas de zero-padding des années : année 1 → `1-01-01T00:00:00.000` au lieu
  de `0001-01-01T00:00:00.000`.
- Année 0 → `0-01-01T00:00:00.000` au lieu de `0000-01-01T00:00:00.000`.
- Pas de format étendu ISO 8601 (`+YYYYYY` / `-YYYYYY`).
- Pas d'offset UTC dans la sortie ISO.

#### Impossible de parser les offsets UTC

```python
Time('2024-06-15T10:30:00+05:00', format='isot')  # ValueError
```

Le parser ISO d'astropy n'accepte que les dates sans offset.

#### Dépendances massives (~55 Mo)

| Paquet | Taille |
|---|---|
| astropy | 25.5 Mo |
| numpy | 21.3 Mo |
| astropy-iers-data | 8.5 Mo |
| pyerfa | Extension C |
| packaging | 0.3 Mo |
| **Total** | **~55 Mo** |

On tire toute la bibliothèque d'astronomie (cosmologie, coordonnées,
convolution, modélisation, I/O FITS, tables...) pour un datetime.

#### Temps d'import élevé

~284 ms pour `from astropy.time import Time`, contre un import instantané
pour UDT.

#### Conversion vers `datetime` limitée

`t.datetime` et `t.to_datetime()` échouent pour les années hors de 1-9999
(`ValueError: year -999 is out of range`).

### 2.4 Tableau détaillé

| Fonctionnalité | UDT | astropy.time |
|---|---|---|
| Années négatives (ISO) | Oui | **Non** (JD requis) |
| Année 0 | Oui | Oui (affichage non standard) |
| Plage d'années (ISO) | Illimitée | ~-4800 à ~+1 465 000 |
| Fuseaux horaires | `Timezone`, `astimezone()` | **Aucun natif** |
| Parsing ISO avec offset | Oui (`+05:00`, `Z`) | **Non** |
| Formatage ISO conforme | Oui (zero-padding, étendu) | **Non** (pas de padding) |
| Timestamps Unix | Oui | Oui |
| Arithmétique entière | Oui | Non (deux `float64`) |
| Erreurs d'arrondi | Aucune | ~82 ps/op, ~39.5 ns/86400 ops |
| Échelles astronomiques | Non | UTC, TAI, TT, TDB, UT1... |
| Précision théorique | Microseconde | Sub-nanoseconde |
| Dépendances | Zéro | ~55 Mo |
| Temps d'import | Instantané | ~284 ms |
| Conversion vers `datetime` | Oui (si année 1-9999) | Oui (si année 1-9999) |

### 2.5 Conclusion

`astropy.time` est une bibliothèque de haute précision pour l'astronomie,
mais elle est inadaptée comme datetime universel :

- Elle ne peut pas parser les années négatives depuis une chaîne ISO.
- Sa plage d'années en sortie ISO est limitée (~-4800 à ~+1.4M).
- Elle n'a pas de support timezone natif.
- Son format ISO est non conforme (pas de zero-padding).
- Ses 55 Mo de dépendances sont disproportionnés pour un datetime.

Son seul avantage sur UDT est la précision sub-nanoseconde et les échelles
de temps astronomiques (TAI, TT, TDB), qui ne sont pas des besoins de UDT.

---

## 3. Conclusion générale

### Pourquoi UDT reste nécessaire

Aucune des deux bibliothèques existantes ne couvre le cas d'usage de UDT :
un datetime universel, exact, avec support complet des fuseaux horaires et
des années illimitées.

| Besoin | cftime | astropy.time | UDT |
|---|---|---|---|
| Années négatives en ISO | Constructeur seul | **Non** | **Oui** |
| Fuseaux horaires | **Non** | **Non** | **Oui** |
| Arithmétique exacte | **Non** (flottants) | **Non** (flottants) | **Oui** (entiers) |
| Parsing ISO complet | **Non** | **Non** | **Oui** |
| Zéro dépendance | **Non** (C ext.) | **Non** (55 Mo) | **Oui** |
| Plage illimitée | **Non** (C long) | **Non** (ERFA) | **Oui** |

### Ce que UDT ne fait pas (et n'a pas besoin de faire)

- **Calendriers multiples** (cftime) : UDT utilise le proleptic Gregorian,
  suffisant pour un usage civil et historique.
- **Échelles astronomiques** (astropy) : UTC/TAI/TT/TDB ne sont pas
  pertinents pour un datetime à usage général.
- **Précision sub-nanoseconde** (astropy) : la microseconde est suffisante
  pour les cas d'usage visés.
- **`strftime()`** : pourrait être ajouté si nécessaire, mais `isoformat()`
  couvre la majorité des besoins.

### Pistes d'amélioration pour UDT

Fonctionnalités implémentées :

- `yearday()` — jour de l'année (1–366).
- `daysinmonth()` — nombre de jours dans le mois courant (28–31).
- Sérialisation pickle (via `__reduce__`).

Fonctionnalités écartées :

- **`strftime()` / `strptime()`** — `isoformat()` et `fromisoformat()`
  couvrent le besoin principal. Une implémentation maison serait coûteuse
  (la stdlib ne gère pas les années négatives) pour un gain marginal.
- **`timetuple()`** — `time.struct_time` ne supporte ni les années négatives
  ni les microsecondes. Pour l'interop stdlib, passer par `to_datetime()`.
- **DST (heure d'été)** — `Timezone` reste un offset UTC fixe. Raisons :
  (1) `tzinfo.utcoffset(dt)` attend un `datetime`, pas un `UDT`, donc
  inutilisable pour les années négatives ; (2) résoudre un `ZoneInfo` en
  offset fixe à la construction perdrait la conscience DST pour les
  opérations futures. Pour les dates modernes nécessitant le DST, passer
  par `from_datetime()` / `to_datetime()` avec un `datetime` timezone-aware.

---

## 4. Panorama complet de l'écosystème

Recherche web exhaustive réalisée le 2026-03-29 sur PyPI, GitHub et
Stack Overflow. 20 bibliothèques identifiées, classées par pertinence.

### 4.1 Tier 1 — Support étendu des années

#### metomi-isodatetime

Le candidat le plus proche de UDT. Parser/formateur ISO 8601 complet conçu
comme remplacement de `datetime`.

- **PyPI** : `metomi-isodatetime`
- **GitHub** : [metomi/isodatetime](https://github.com/metomi/isodatetime)
- **Dernière version** : v3.1.0, octobre 2024
- **Années négatives** : oui, via notation ISO 8601 étendue (`+XCCYY`)
- **Année 0** : oui (numérotation astronomique)
- **Plage** : configurable via "expanded year digits", jusqu'à ~1 million
- **Fuseaux horaires** : oui (UTC et offsets numériques)
- **Précision** : secondes fractionnaires (pas de microseconde entière)
- **Pur Python** : oui, zéro dépendance
- **Limites** : pas d'arithmétique entière en microsecondes — c'est un
  parser/formateur calendaire, pas un type timestamp. Modèle interne orienté
  calendrier, pas horodatage.

**Verdict** : le plus proche de UDT sur le parsing/formatage, mais ne
remplace pas un type timestamp avec arithmétique exacte.

#### NumPy datetime64

Le dtype `datetime64` de NumPy, pas une bibliothèque autonome.

- **Années négatives** : oui (numérotation astronomique)
- **Année 0** : oui
- **Plage** : dépend de l'unité — ~±292 271 ans en µs, ~±9.2 milliards en
  années
- **Fuseaux horaires** : **non** (déprécié depuis NumPy 1.11, conversion
  silencieuse en UTC)
- **Précision** : µs ou ns selon l'unité choisie
- **Arithmétique entière** : oui (int64 interne)
- **Pur Python** : non (extension C, dépendance NumPy)
- **Limites** : aucun support timezone. La plage dépend de l'unité choisie
  (ns = ~584 ans seulement). Pas de formatage calendaire avancé. Pas un
  remplacement de datetime.

**Verdict** : arithmétique entière correcte, mais pas de timezone et
nécessite NumPy.

### 4.2 Tier 2 — Support partiel (date-only ou limité)

#### convertdate

Bibliothèque de conversion entre 16+ systèmes calendaires.

- **PyPI** : `convertdate` — v2.4.1, février 2026
- **Années négatives** : oui (numérotation astronomique)
- **Fuseaux horaires** : non
- **Précision** : **jour uniquement** (pas de composante horaire)
- **Pur Python** : oui
- **Calendriers** : Grégorien, Julien, Hébreu, Islamique, Maya, Persan,
  Bahá'í, Indien, etc.

**Verdict** : utile pour la conversion calendaire, mais date-only.

#### edtf (python-edtf)

Implémentation du Extended Date Time Format (standard Library of Congress).

- **PyPI** : `edtf` — v5.0.1, mars 2026
- **Années négatives** : oui (via `LongYear`, ex. `Y-12000`)
- **Fuseaux horaires** : oui (offsets via `DateAndTime`)
- **Précision** : jour et heure, plus qualificateurs d'incertitude
- **Pur Python** : oui
- **Limites** : orienté parsing/formatage EDTF, pas arithmétique timestamp.
  Avertissement explicite : "Conversion to and from Julian Date numerical
  values can be inaccurate, especially for ancient dates."

**Verdict** : intéressant pour les dates incertaines/approximatives, pas
pour l'arithmétique exacte.

#### juliandate

Conversions simples Julian Date ↔ date calendaire.

- **PyPI** : `juliandate` — v1.0.5, décembre 2024
- **Années négatives** : oui
- **Fuseaux horaires** : non
- **Précision** : flottant (erreurs d'arrondi pour les dates anciennes)
- **Pur Python** : oui
- **Limites** : flottant, jour uniquement, API minimale.

#### historicaldate / python-historical-dates

Bibliothèques simples pour dates historiques.

- **Années négatives** : oui
- **Fuseaux horaires** : non
- **Précision** : **jour uniquement**
- **Pur Python** : oui
- **Limites** : pas de composante horaire, API très basique (comparaison et
  différence sur des tuples `(year, month, day)`).

### 4.3 Tier 3 — Astronomie / Niche

#### Skyfield

Bibliothèque d'astronomie avec support du calendrier proleptic Gregorian.

- **PyPI** : `skyfield` — v1.54, janvier 2026
- **Années négatives** : oui
- **Fuseaux horaires** : échelles astronomiques (UTC, TAI, TDB, TT)
- **Dépendances** : NumPy
- **Limites** : bibliothèque d'astronomie complète, surdimensionné pour un
  datetime.

#### rms-julian

Systèmes de temps astronomiques (SETI Institute).

- **PyPI** : `rms-julian`
- **Années négatives** : via Julian Day Numbers
- **Fuseaux horaires** : UTC, TAI, TDB, TT avec secondes intercalaires
- **Précision** : flottant
- **Dépendances** : NumPy

#### pyjams

Utilitaires scientifiques avec datetime étendu (wrapper cftime).

- **PyPI** : `pyjams` — v2.4, octobre 2025
- **Dépendances** : NumPy, SciPy, cftime, netCDF4, Matplotlib
- **Limites** : essentiellement un wrapper cftime avec des dépendances
  massives.

#### PyCalCal (pycalcal)

Port Python de "Calendrical Calculations" (Dershowitz & Reingold).

- **GitHub** : [espinielli/pycalcal](https://github.com/espinielli/pycalcal)
- **31 calendriers** supportés
- **Dernière version** : v2.0.0, octobre 2020 (dormant)
- **Précision** : jour uniquement

### 4.4 Tier 4 — Obsolètes ou non pertinentes

| Bibliothèque | Raison d'exclusion |
|---|---|
| **Pyslet** (`pyslet.iso8601`) | Abandonné depuis 2017, incompatible Python 3.12+ |
| **mxDateTime** (egenix) | Abandonné ~2019, extension C, ère Python 2 |
| **jdcal** | Abandonné ~2019, flottant, jour uniquement |
| **decimaldate** | Convertit en float (lossy), jour uniquement, pas sur PyPI |
| **paddate** | Padding de dates seulement, pas d'arithmétique |
| **FlexiDate** (datautil) | Dates stockées comme chaînes, ère Python 2, ~2011 |
| **eparkhontos** | Niche (années d'archonte grec), v0.0.1 |
| **attotime** | Ne supporte PAS les années négatives (wraps `datetime`) |
| **whenever** | Ne supporte PAS les années < 1 ou > 9999 |

### 4.5 Matrice de comparaison finale

| Bibliothèque | An. nég. | An. 0 | Plage | TZ | µs | Ent. | ISO | Py pur | Actif |
|---|---|---|---|---|---|---|---|---|---|
| **UDT** | **Oui** | **Oui** | **∞** | **Oui** | **Oui** | **Oui** | **Oui** | **Oui** | — |
| metomi-isodatetime | Oui | Oui | ~1M | Oui | Non | Non | Oui | Oui | 2024 |
| NumPy datetime64 | Oui | Oui | ~292K | Non | Oui | Oui | Partiel | Non | Oui |
| cftime | Oui | Oui | ±2.1G | Non | Oui | Non | Non | Non | Oui |
| astropy.time | Partiel | Oui | ~1.4M | Non | Non | Non | Partiel | Non | Oui |
| convertdate | Oui | Oui | ∞ | Non | Non | — | Non | Oui | 2026 |
| edtf | Oui | Oui | ∞ | Oui | Non | Non | EDTF | Oui | 2026 |
| juliandate | Oui | Oui | ∞ | Non | Non | Non | Non | Oui | 2024 |
| Skyfield | Oui | Oui | Large | Astro | Non | Non | Non | Non | 2026 |

Légende : An. = Années, TZ = Fuseaux horaires, µs = Précision microseconde,
Ent. = Arithmétique entière, ISO = Parsing ISO 8601, Py pur = Pur Python.

### 4.6 Conclusion

**Aucune bibliothèque existante ne couvre l'ensemble des besoins de UDT.**

La combinaison (années négatives + fuseaux horaires + microseconde exacte +
arithmétique entière + ISO 8601 étendu + pur Python + zéro dépendance)
n'existe dans aucune bibliothèque unique. UDT comble un vrai trou dans
l'écosystème Python.

Les deux candidats les plus proches sont :

1. **metomi-isodatetime** — couvre parsing/formatage + timezone, mais pas
   l'arithmétique entière en microsecondes.
2. **NumPy datetime64** — couvre l'arithmétique entière, mais pas les
   timezones et nécessite NumPy.

Combiner les deux introduirait de la complexité et une dépendance NumPy,
tout en laissant des lacunes sur les timezones.
