# Recherche par expression

**Implémentation** : `pysaurus/core/searchexp/` (parser, tokenizer, IR, helpers).
Tests : `tests/unittests/test_searchexp.py`.
Spécification formelle (grammaire EBNF) : `docs/searchexp.spec.md`.

## Bilan des valeurs manipulables

### 1. Types des propriétés custom (`PropType`)

4 types primitifs possibles, définis dans `PROP_UNIT_TYPES` :

| Type | Python | Notes |
|------|--------|-------|
| `bool` | `bool` | Stocké 0/1 en SQL |
| `int` | `int` | |
| `float` | `float` | Les `int` sont auto-convertis en `float` si la prop est float |
| `str` | `str` | |

Chaque propriété a aussi un flag `multiple` (valeur unique vs liste de valeurs)
et un `enumeration` optionnel (ensemble de valeurs autorisées).

### 2. Attributs publics de `VideoPattern`

#### Types wrappers

| Classe | Contenu interne | Comparable | Conversion |
|--------|----------------|------------|------------|
| `Date` | `float` (timestamp) | `==`, `<`, `>=` | `__float__()`, `__str__()` → `"YYYY-MM-DD HH:MM:SS"` |
| `Duration` | `int` (microsecondes signées) | via `.t` | |
| `FileSize` | `int` (octets) | `__int__()`, `__float__()` | `__str__()` → `"1.5 GiB"` |
| `AbsolutePath` | `str` (chemin) | | `.extension`, `.file_title`, `.standard_path` |
| `SemanticText` | `str` + tri numérique intelligent | | |
| `StringedTuple` | tuple | | `__str__()` |

#### Attributs abstraits (stockés en base)

| Attribut | Type | Catégorie |
|----------|------|-----------|
| `audio_bit_rate` | `int` | audio |
| `audio_bits` | `int` | audio |
| `audio_codec` | `str` | audio |
| `audio_codec_description` | `str` | audio |
| `audio_languages` | `list[str]` | listes |
| `bit_depth` | `int` | vidéo |
| `channels` | `int` | audio |
| `container_format` | `str` | métadonnées |
| `date_entry_modified` | `Date` | dates |
| `date_entry_opened` | `Date` | dates |
| `device_name` | `str` | métadonnées |
| `errors` | `list[str]` | listes |
| `filename` | `AbsolutePath` | fichier |
| `found` | `bool` | état |
| `height` | `int` | vidéo |
| `meta_title` | `str` | métadonnées |
| `sample_rate` | `int` | audio |
| `subtitle_languages` | `list[str]` | listes |
| `video_codec` | `str` | vidéo |
| `video_codec_description` | `str` | vidéo |
| `video_id` | `int` | identifiant |
| `watched` | `bool` | état |
| `width` | `int` | vidéo |
| `with_thumbnails` | `bool` | état |

#### Attributs abstraits exclus

| Attribut | Type | Raison |
|----------|------|--------|
| `duration` | `float` | → `length` |
| `duration_time_base` | `int` | interne |
| `file_size` | `int` | → `size` |
| `frame_rate_den` | `int` | → `frame_rate` |
| `frame_rate_num` | `int` | → `frame_rate` |
| `discarded` | `bool` | vidéos ignorées par la db (folders retirés) — la recherche ne porte que sur les vidéos not discarded |
| `driver_id` | `int` | → `disk` |
| `move_id` | *(non annoté)* | déplacement |
| `moves` | `list[MoveType]` | déplacements |
| `mtime` | `float` | → `date` |
| `properties` | `dict[str, list[PropUnitType]]` | dict brut (→ `` `nom_prop` ``) |
| `similarity_id` | `int \| None` | → `similarity` |
| `similarity_id_reencoded` | `int \| None` | → `similarity_reencoded` |
| `thumbnail` | `bytes` | binaire |
| `unreadable` | `bool` | → `not readable` (inverse via langage) |

#### Propriétés calculées (concrètes)

| Attribut | Type | Dérivé de |
|----------|------|-----------|
| `bit_rate` | `FileSize` | `file_size * duration_time_base / duration` |
| `date` | `Date` | `Date(mtime)` |
| `extension` | `str` | `filename.extension` |
| `file_title` | `str` | `filename.file_title` |
| `frame_rate` | `float` | `frame_rate_num / frame_rate_den` |
| `length` | `Duration` | `duration * 1e6 / duration_time_base` |
| `readable` | `bool` | `not unreadable` |
| `similarity` | `str` | texte descriptif du similarity_id |
| `similarity_reencoded` | `str` | idem pour reencoded |
| `size` | `FileSize` | `FileSize(file_size)` |
| `title` | `str` | `meta_title or file_title` |

#### Propriétés calculées exclues

| Attribut | Type | Raison |
|----------|------|--------|
| `audio_bit_rate_kbps` | `int` | → `audio_bit_rate` (conversion triviale) |
| `disk` | `str \| int` | type mixte, → `"C:" in filename` |
| `day` | `int` | → `date` (précision jour) |
| `not_found` | `bool` | → `not found` (inverse via langage) |
| `file_title_numeric` | `SemanticText` | tri uniquement |
| `filename_length` | `int` | → `len(filename)` |
| `filename_numeric` | `SemanticText` | tri uniquement |
| `meta_title_numeric` | `SemanticText` | tri uniquement |
| `raw_microseconds` | `float` | → `length` |
| `size_length` | `StringedTuple` | composite |
| `thumbnail_base64` | `str \| None` | affichage |
| `thumbnail_path` | `str \| None` | affichage |
| `title_numeric` | `SemanticText` | tri uniquement |
| `without_thumbnails` | `bool` | → `not with_thumbnails` (inverse via langage) |
| `year` | `int` | → `date` (précision année) |

### 3. Résumé des types pour le langage d'expressions

Types effectifs à manipuler :

- **Scalaires comparables** : `bool`, `int`, `float`, `str`
- **Wrappers comparables** : `Date` (comparable, convertible en float),
  `FileSize` (comparable, convertible en int), `Duration` (comparable via `.t`)
- **Listes** : `list[str]` (audio_languages, subtitle_languages, errors) —
  pertinentes pour l'opérateur `in`
- **Propriétés custom** : `bool | int | float | str`, potentiellement multi-valuées

Décisions de conception :

- `filename` (`AbsolutePath`) traité comme `str` dans le langage
- Booléens : on garde les formes positives (`found`, `readable`, `with_thumbnails`).
  Les inverses s'expriment via `not`. Syntaxes supportées :
  `not expr`, `value is True`, `value is False`, `expr` seul (évalué à `True`)
- `disk` exclu : remplaçable par `"C:" in filename`
- Suffixes multiplicateurs numériques applicables à tout champ numérique :
  base 1000 (`k`, `m`, `g`, `t`) et base 1024 (`ki`, `mi`, `gi`, `ti`)
- Fonctions sur valeurs : `len()` supporté sur `str` et `set`
  (ex. `len(filename) > 100`, `len(audio_languages) > 2`)
- Tout ensemble (liste, set) est traité comme `set` dans le langage
- Comparaisons de chaînes sensibles à la casse
- Priorité des opérateurs : suit Python

### 4. Formats d'affichage des types wrappers

Ces wrappers sont affichés dans l'interface sous forme lisible. Le langage
d'expressions doit proposer des syntaxes littérales proches de ces formats
pour que l'utilisateur puisse écrire des comparaisons naturellement.

#### `Date` (`pysaurus/core/datestring.py`)

- **`__str__`** : `"YYYY-MM-DD HH:MM:SS"` — ex. `"2024-03-15 14:30:00"`
- **`.day`** : `"YYYY-MM-DD"` — ex. `"2024-03-15"`
- **`.year`** : `int` — ex. `2024`
- Stockage interne : `float` (timestamp Unix)
- Comparable via `==`, `<`, `>=`

#### `Duration` (`pysaurus/core/duration.py`)

- **`__str__`** : composants non-nuls avec suffixes, chacun sur 2 chiffres,
  séparés par un espace — ex. `"05m 30s"`, `"01h 25m 03s"`, `"02d 05h"`, `"00s"`
- **`ShortDuration.__str__`** : format horloge `HH:MM:SS` ou `DDd:HH:MM:SS`
- Composants : `d` (jours), `h` (heures), `m` (minutes), `s` (secondes), `µs` (microsecondes)
- Stockage interne : microsecondes signées (`.t`)
- Tous les opérateurs de comparaison supportés

#### `FileSize` (`pysaurus/core/file_size.py`)

- **`__str__`** : `"<valeur arrondie à 2 décimales> <unité>"` — ex. `"703.24 MiB"`, `"2.1 GiB"`
- Unités (base 1024) : `b`, `KiB`, `MiB`, `GiB`, `TiB`
- Sélection automatique de l'unité la plus adaptée
- Stockage interne : octets bruts (entier)
- Tous les opérateurs de comparaison supportés

#### Syntaxes littérales envisagées pour le langage

| Type | Syntaxe humaine | Exemples |
|------|-----------------|----------|
| Date | 6 niveaux de précision (voir ci-dessous) | `2024`, `2024-03`, `2024-03-15` |
| Duration | composants avec suffixes (voir ci-dessous) | `5min30s`, `1h25min`, `2d5h`, `45s` |
| Nombre avec multiplicateur | nombre + suffixe (voir ci-dessous) | `1.5gi`, `128k`, `500mi` |

**Précisions sur les dates** — 6 niveaux de précision supportés :

1. `YYYY` — année — ex. `2024`
2. `YYYY-MM` — mois — ex. `2024-03`
3. `YYYY-MM-DD` — jour — ex. `2024-03-15`
4. `YYYY-MM-DDTHH` — heure — ex. `2024-03-15T14`
5. `YYYY-MM-DDTHH:MM` — minute — ex. `2024-03-15T14:30`
6. `YYYY-MM-DDTHH:MM:SS` — seconde (complet) — ex. `2024-03-15T14:30:00`

Séparateur `T` (ISO 8601) entre la date et l'heure. Pas d'espace
(évite l'ambiguïté au parsing).

**Précisions sur les durées** — suffixes de composants :

- `d` — jours
- `h` — heures
- `min` — minutes (pas `m`, qui est le multiplicateur × 1 000 000)
- `s` — secondes
- `u` — microsecondes (alias pour `µs`, plus facile à saisir)

Règles :

- Toute combinaison de composants est acceptée (un seul suffit)
- Un nombre brut sans suffixe n'est pas une durée (`60` ≠ 60 secondes,
  il faut écrire `60s`)
- Le composant le plus grand est le jour (`d`)
- Les composants doivent être ordonnés par précision décroissante :
  `d` > `h` > `min` > `s` > `u`
- Exemples valides : `2d5min`, `1h30s`, `45s`, `3h`, `10min500u`
- Exemples rejetés : `5s7min` (ordre croissant), `30s2h` (secondes avant heures)
- Insensible à la casse : `5MIN30S` ≡ `5min30s`

**Suffixes multiplicateurs numériques** — syntaxe : `<nombre><suffixe>`

Les suffixes sont de purs multiplicateurs, indépendants de toute sémantique
bits/octets. Applicables à n'importe quel champ numérique.

Base 1000 :

| Suffixe | Multiplicateur |
|---------|---------------|
| `k` | × 1 000 |
| `m` | × 1 000 000 |
| `g` | × 1 000 000 000 |
| `t` | × 1 000 000 000 000 |

Base 1024 :

| Suffixe | Multiplicateur |
|---------|---------------|
| `ki` | × 1 024 |
| `mi` | × 1 048 576 |
| `gi` | × 1 073 741 824 |
| `ti` | × 1 099 511 627 776 |

Règles :

- Un seul suffixe par littéral
- Le nombre peut être décimal : `1.5gi`, `700.5mi`
- Insensible à la casse : `1.5GI` ≡ `1.5gi`
- Exemples :
  - `size > 1.5gi` → `> 1 610 612 736` (octets, base 1024)
  - `audio_bit_rate > 128k` → `> 128 000` (bits/s, base 1000)
  - `bit_rate > 5mi` → `> 5 242 880` (octets/s, base 1024)
  - `height > 1k` → `> 1 000` (fonctionne sur tout champ numérique)

### 5. Opérateurs et syntaxe du langage

#### Contrainte fondamentale

**Pour tout opérateur binaire : au moins un côté doit être un champ ou une
fonction. Jamais littéral vs littéral.**

Cela garantit qu'il y a toujours un champ dont le type est connu pour
résoudre les littéraux ambigus. Les littéraux ambigus (ex. `2024` — entier
ou date ?) sont gardés sous forme brute au tokenizing, puis résolus dans
une passe de typage une fois le champ de l'autre côté identifié.

| Expression | Validité | Inférence |
|-----------|----------|-----------|
| `width > 1080` | ✓ champ op littéral | champ → type du littéral |
| `1080 < width` | ✓ littéral op champ | champ → type du littéral |
| `width > height` | ✓ champ op champ | vérifier compatibilité |
| `len(filename) > len(title)` | ✓ fonction op fonction | vérifier compatibilité |
| `"eng" in audio_languages` | ✓ littéral in champ | champ → type du littéral |
| `extension in {".mp4", ".mkv"}` | ✓ champ in littéral | champ → type des éléments |
| `1080 < 2000` | ✗ littéral vs littéral | rejeté |
| `1 in {2, 3}` | ✗ littéral vs littéral | rejeté |

#### Opérateurs de comparaison

`<`, `<=`, `>`, `>=`, `==`, `!=`

- Pas de comparaisons chaînées (`1000 < height < 2000` non supporté,
  utiliser `height > 1000 and height < 2000`)

#### Opérateurs logiques

`and`, `or`, `xor`, `not`

#### Opérateur d'identité

`is` — pour les booléens : `found is True`, `watched is False`

#### Opérateur d'appartenance

`in`, `not in`

- Sur `str` à droite : test de sous-chaîne (`"C:" in filename`)
- Sur `set` littéral à droite : test d'appartenance (`extension in {".mp4", ".mkv"}`)
- Sur champ `list[str]` à droite : test d'appartenance (`"eng" in audio_languages`)
- Sur propriété multi-valuée à droite : test d'appartenance (`"action" in \`category\``)

#### Parenthèses

`(`, `)` — pour surcharger la priorité des opérateurs

#### Ensembles littéraux

`{valeur1, valeur2, ...}` — uniquement avec `in` / `not in`.
Pas de `[]`. Pas de dicts.

#### Délimiteurs de chaînes

`"..."` et `'...'` — pour les littéraux `str`

#### Littéraux supportés

| Type | Exemples |
|------|----------|
| `bool` | `True`, `False` |
| `int` | `42`, `128k`, `1gi` |
| `float` | `3.14`, `1.5gi` |
| `str` | `"hello"`, `'world'` |
| Date | `2024`, `2024-03-15`, etc. (6 niveaux de précision) |
| Duration | `5min30s`, `1h25min`, `45s` |

#### Fonctions

| Fonction | Applicable à | Résultat |
|----------|-------------|----------|
| `len()` | `str`, `set` | `int` |

Exemples : `len(filename) > 100`, `len(audio_languages) > 2`, `len(errors) == 0`

#### Référence aux champs

- **Attribut vidéo** : nom nu — `audio_bit_rate`, `filename`, `found`
- **Propriété custom** : entre accents graves — `` `category` ``, `` `rating` ``

#### Typage des valeurs

Le type des littéraux est résolu par le type du champ dans l'expression.
Par exemple, `date > 2024` interprète `2024` comme une date (année), pas
comme un entier. En interne, les dates sont converties en `float` (timestamp)
pour les comparaisons.

Tout ensemble (liste, set) est traité comme un `set` dans le langage.
Une propriété multi-valuée a le type `set[type_de_base]` :
- `==` compare des ensembles entre eux
- `in` teste l'appartenance d'un élément

#### Sensibilité à la casse

- Comparaisons de chaînes : **sensible** à la casse
- Mots-clés (`and`, `or`, `xor`, `not`, `in`, `is`, `True`, `False`, `len`) :
  **insensible** à la casse (`AND` ≡ `and`, `true` ≡ `True`)
- Suffixes multiplicateurs (`k`, `ki`, etc.) : **insensible** à la casse
- Suffixes de durée (`d`, `h`, `min`, `s`, `u`) : **insensible** à la casse
- Noms d'attributs : **sensible** à la casse (noms exacts de `VideoPattern`)

#### Expression vide

Une expression vide ou constituée uniquement d'espaces est rejetée par le
parser (`ExpressionError`). C'est au code appelant de décider de ne pas
déclencher de recherche quand l'expression est vide.

#### ~~`is not`~~ (résolu)

Supporté. `found is not True` est équivalent à `found is False`, et
`found is not False` est équivalent à `found is True`.

#### Priorité des opérateurs

Suit la priorité Python (du plus prioritaire au moins prioritaire) :

1. `()` — parenthèses
2. Fonctions — `len()`
3. `not`
4. Comparaisons — `<`, `<=`, `>`, `>=`, `==`, `!=`, `is`, `in`, `not in`
5. `and`
6. `xor`
7. `or`

### 6. Architecture

#### Parser partagé → IR → backends d'évaluation

```
Expression texte
    → Parser (partagé, unique, indépendant de Pysaurus)
        → IR / AST (représentation intermédiaire)
            → Backend Python : parcourt l'AST, évalue sur chaque VideoPattern
            → Backend SQL : parcourt l'AST, génère une clause WHERE
```

- Le **parser** est unique et partagé : tokenisation, inférence de types,
  validation, messages d'erreur. Se situe dans le code commun, au même
  niveau que `AbstractDatabase`.
- L'**IR** (AST) est la représentation intermédiaire de l'expression validée.
- Chaque implémentation de DB n'implémente qu'un **évaluateur d'AST**,
  pas un parser.
- En v1, seul le backend Python (évaluation sur `VideoPattern`) est nécessaire.
  Le backend SQL (traduction en `WHERE`) est une optimisation future.

#### Indépendance du parser

Le parser est **indépendant de Pysaurus**. Il ne connaît ni `VideoPattern`
ni le système de propriétés. Son vocabulaire :
- **Attribut** = nom nu → attribut d'un objet
- **Propriété** = nom entre backticks → clé d'un dictionnaire

##### Entrées du parser

Le parser reçoit à l'initialisation deux dictionnaires `{nom: FieldType}` :

1. **`attributes`** — attributs reconnus (noms nus). Optionnel.
2. **`properties`** — propriétés custom (noms entre backticks). Optionnel.

Au moins un des deux doit être fourni. Si les deux sont absents, le parser
lève une `ValueError` car il ne pourrait reconnaître aucun champ. Il n'y a
pas de mode lax : tout nom rencontré doit correspondre à un champ déclaré.

Le parser ne reçoit jamais de classe Python — l'introspection est déléguée
à la fonction helper `fields_from_class()`, qui produit un dict à partir
d'une classe annotée.

##### Helper `fields_from_class`

Fonction utilitaire qui introspecte les annotations d'une classe et produit
un `dict[str, FieldType]` consommable par le parser :

```python
fields_from_class(
    cls,
    *,
    type_mapping={Date: FieldType.DATE, Duration: FieldType.DURATION, ...},
    exclude={"duration", "file_size", "mtime", ...},
) -> dict[str, FieldType]
```

- Les types Python standard (`bool`, `int`, `float`, `str`) sont mappés
  automatiquement. `list[str]` est mappé en `FieldType.SET`.
- Les types custom sont résolus via `type_mapping`.
- Les attributs dans `exclude` sont omis du résultat.

##### Système de types interne

Le parser définit ses propres types abstraits, sans dépendance externe :

```python
class FieldType(Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    DATE = "date"
    DURATION = "duration"
    FILESIZE = "filesize"
    SET = "set"
```

##### IR en sortie

L'IR est une arborescence de **dataclasses** avec des types Python basiques
et des **enums**. Aucune référence à Pysaurus. Entièrement sérialisable
(JSON, YAML, etc.).

Nœuds principaux :
- `FieldRef(name, source: "attribute"|"property", field_type)` — référence
  à un champ
- `LiteralValue(value, field_type)` — valeur constante (convertie en valeur
  brute : date → timestamp float, durée → microsecondes int, etc.)
- `Comparison(left, op, right)` — comparaison binaire
- `IsOp(left, value: bool)` — opérateur `is` / `is not` (booléens uniquement)
- `InOp(left, right, negated: bool)` — opérateur `in` / `not in`
- `LogicalOp(left, op, right)` — opération logique (and, or, xor)
- `NotOp(operand)` — négation
- `FunctionCall(name, arg, result_type)` — appel de fonction (len)
- `SetLiteral(elements, element_type)` — ensemble littéral

##### Interprétation par Pysaurus

Quand la DB évalue l'IR :
- `FieldRef(source="attribute")` → `getattr(video, name)`
- `FieldRef(source="property")` → `video.properties[name]`
- Les wrappers (`Date`, `Duration`, `FileSize`) sont convertis en valeurs
  brutes pour la comparaison (timestamp, microsecondes, octets)

#### Complémentarité avec la recherche textuelle

La recherche par expression et la recherche textuelle (FTS5) sont
complémentaires et coexistent :
- La recherche textuelle filtre par contenu (titres, noms de fichiers)
- La recherche par expression filtre par attributs/propriétés structurés

À terme, un query builder GUI pourra générer des expressions textuelles,
offrant deux modes d'accès (formulaire visuel et saisie directe) au même
moteur d'évaluation.

### 7. Questions ouvertes (implémentation)

#### Intégration UI

Comment ce mode de recherche s'intègre-t-il dans l'interface ?
Nouveau mode dans le filtre Search existant ? Champ séparé ?

#### ~~Stratégie d'évaluation~~ (résolu)

Le parser produit un IR (AST) indépendant de tout backend. Chaque backend
implémente un évaluateur d'AST :
- V1 : évaluation Python sur les objets `VideoPattern` (à implémenter).
- Futur : traduction en clause SQL `WHERE` (optimisation si nécessaire).

#### Code existant : `VideoFieldQueryParser`

Le backlog mentionne une "recherche conditionnelle" existante. Vérifier
s'il y a du code réutilisable ou à remplacer.

#### ~~Format exact des littéraux date~~ (résolu)

Séparateur `T` (ISO 8601) entre date et heure : `2024-03-15T14:30:00`.
Le format `__str__` de `Date` utilise un espace, mais le langage
d'expressions utilise `T` pour éviter l'ambiguïté au parsing.

#### ~~Conversion interne des wrappers pour les comparaisons~~ (résolu)

La conversion se fait **au parsing**. Les littéraux typés sont convertis en
valeurs brutes et stockés dans le nœud `LiteralValue` de l'IR :
- `Date` → `float` (timestamp Unix, heure locale pour cohérence avec
  l'affichage `Date.__str__` qui utilise `datetime.fromtimestamp`)
- `Duration` → `int` (microsecondes)
- `FileSize` → `int` (octets bruts)
- Nombre avec multiplicateur → `int` ou `float` (résultat de la multiplication)

L'évaluateur n'a qu'à comparer des valeurs brutes.

#### ~~Gestion des erreurs~~ (résolu)

Toutes les erreurs remontent, jamais silencieuses. Toute validation se fait
au parsing (avant l'évaluation sur les vidéos), à condition d'avoir accès
à la liste des propriétés custom (noms et types) à ce moment-là.

Erreurs détectées au parsing :
- Expression syntaxiquement invalide
- Propriété custom inexistante (`` `nonexistent` ``)
- Types incompatibles (`width > "hello"`, `found > True`)
- Opérateur invalide pour le type (`found > True`, `set < set`)

L'évaluation n'exécute que des expressions déjà validées.

#### ~~Chaînes de caractères — séquences d'échappement~~ (résolu)

Pas d'échappement en v1. Les deux délimiteurs (`"` et `'`) couvrent
les cas pratiques (noms de codecs, extensions, catégories, chemins, langues).

Cas non couvert : une chaîne contenant à la fois `"` et `'`
(ex. `he said "it's fine"`). Extrêmement rare dans le contexte de Pysaurus.
À résoudre dans le futur si le besoin se présente (ex. séquences `\"`, `\'`).

#### ~~Opérateurs sur types spécifiques~~ (résolu)

Opérateurs restreints par type. Combinaisons invalides rejetées.

##### Matrice opérateurs × types

| Opérateur | `bool` | `int` | `float` | `str` | `Date` | `Duration` | `FileSize` | `set[T]` |
|-----------|--------|-------|---------|-------|--------|------------|------------|----------|
| `==`, `!=` | oui | oui | oui | oui | oui | oui | oui | oui |
| `<`, `<=`, `>`, `>=` | non | oui | oui | oui | oui | oui | oui | non |
| `is` | oui | non | non | non | non | non | non | non |
| `in` (sous-chaîne) | — | — | — | oui | — | — | — | — |
| `in` (appartenance, gauche) | oui | oui | oui | oui | oui | oui | oui | — |
| `in` (appartenance, droite) | — | — | — | — | — | — | — | oui |
| `len()` | non | non | non | oui | non | non | non | oui |

Notes sur `in` :
- Sous-chaîne : `str in str` (`"C:" in filename`)
- Appartenance : `T in set[T]` — tout type scalaire à gauche, `set` à droite
  (`height in {720, 1080}`, `"eng" in audio_languages`)

##### Compatibilités croisées entre types

Les types wrappers (`Date`, `Duration`, `FileSize`) sont comparables avec
les numériques bruts (`int`, `float`) car ils sont stockés en interne comme
des numériques.

| Croisement | Autorisé | Valeur interne |
|-----------|----------|---------------|
| `int` ↔ `float` | oui | promotion numérique |
| `FileSize` ↔ `int` | oui | octets bruts |
| `FileSize` ↔ `float` | oui | octets bruts |
| `Duration` ↔ `int` | oui | microsecondes |
| `Duration` ↔ `float` | oui | microsecondes |
| `Date` ↔ `int` | oui | timestamp Unix |
| `Date` ↔ `float` | oui | timestamp Unix |
| `FileSize` ↔ `Duration` | non | sans rapport |
| `FileSize` ↔ `Date` | non | sans rapport |
| `Duration` ↔ `Date` | non | sans rapport |
