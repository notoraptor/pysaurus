# Intégrer searchexp dans Pysaurus

## Principe

Le filtre **sources** actuel (combinaison de flags booléens) coexiste avec un
nouveau filtre **searchexp** (expression structurée). L'expression est compilée
en SQL par le backend, au même endroit où les sources sont converties en WHERE.

La **recherche textuelle** (FTS5 via `SearchDef`) reste séparée et coexiste
avec searchexp. Les deux se combinent : searchexp filtre structurellement
(WHERE), FTS5 filtre textuellement (MATCH).

## Architecture

```
UI (onglet simple / onglet avancé)
    ↓
Expression string (ou flags sources)
    ↓
ExpressionParser.parse()                     (core/searchexp/)
    ↓
IR (AST)
    ↓
SqlExpressionCompiler.compile()              (database/saurus/)
    ↓
(sql_where: str, params: list)
    ↓
where_builder.append_query(...)              (video_mega_group)
```

## État d'implémentation

### Implémenté

- **`SqlExpressionCompiler`** (`database/saurus/sql_expression_compiler.py`) :
  compile l'IR en `(sql_where, params)`. Supporte tous les types de nœuds IR :
  comparaisons, booléens, `in`/`not in`, `len()`, opérateurs logiques (and, or,
  xor), `not`, dates (via UDT), propriétés custom (CAST, EXISTS).
- **`VIDEO_SEARCH_ATTRIBUTES`** : configuration du parser pour les attributs
  vidéo Pysaurus (29 attributs + champs set).
- **`ViewContext.source_expression`** : champ `str | None`, méthode
  `set_source_expression()`. `set_sources()` reset l'expression, et
  vice versa.
- **`video_mega_group`** : branchement conditionnel — si `source_expression`
  est défini, parse + compile l'expression ; sinon, chemin flags existant.
  Les propriétés custom sont chargées depuis la table `property`.
- **PySide6 UI** :
  - `SourcesDialog` avec deux onglets (Simple / Avancé)
  - `AppContext.get_source_expression()` / `set_source_expression()`
  - Raccourci **Ctrl+E** → ouvre le dialogue sur l'onglet avancé
  - Affichage : expression brute quand searchexp est actif, flags sinon
  - **Ctrl+Shift+T** efface aussi l'expression
- **Tests** : 43 tests unitaires du compilateur SQL couvrant chaque type
  de nœud IR.

### Mapping champs → SQL

| Champ searchexp | Expression SQL | Notes |
|-----------------|---------------|-------|
| `width`, `height`, `channels`, `bit_depth`, `sample_rate`, `audio_bit_rate`, `audio_bits` | `v.<même nom>` | Colonnes directes |
| `audio_codec`, `audio_codec_description`, `video_codec`, `video_codec_description`, `container_format`, `device_name`, `meta_title` | `v.<même nom>` | Colonnes directes (str) |
| `found` | `v.found` | Colonne générée (= `is_file`) |
| `readable` | `v.readable` | Colonne générée (= `1 - unreadable`) |
| `with_thumbnails` | `IIF(LENGTH(vt.thumbnail), 1, 0)` | LEFT JOIN `video_thumbnail` |
| `watched` | `v.watched` | Colonne directe (0/1) |
| `size` | `v.file_size` | Octets |
| `length` | `v.length_microseconds` | Colonne générée, microsecondes |
| `date` | `v.mtime` | Timestamp Unix (float) |
| `date_entry_modified` | `v.date_entry_modified_not_null` | Colonne générée |
| `date_entry_opened` | `v.date_entry_opened_not_null` | Colonne générée |
| `frame_rate` | `v.frame_rate` | Colonne générée (`num / den`) |
| `byte_rate` | `v.byte_rate` | Colonne générée |
| `extension` | `v.extension` | Colonne générée (via `_basename`) |
| `file_title` | `v.file_title` | Colonne générée (via `_basename`) |
| `filename` | `v.filename` | Texte (chemin complet) |
| `video_id` | `v.video_id` | Entier |

### Champs set (tables relationnelles)

| Champ | Table SQL | Colonne valeur | Filtre |
|-------|-----------|---------------|--------|
| `audio_languages` | `video_language` | `lang_code` | `stream = 'a'` |
| `subtitle_languages` | `video_language` | `lang_code` | `stream = 's'` |
| `errors` | `video_error` | `error` | — |

Compilés en sous-requêtes `EXISTS` / `NOT EXISTS` / `SELECT COUNT(*)`.

### Propriétés custom

Compilées en sous-requêtes sur `video_property_value` + `property` :
- Comparaisons : `CAST(vpv.property_value AS INTEGER/REAL)` selon le type
- Booléens : `vpv.property_value = '1'` / `'0'`
- Sets (multi-valuées) : `vpv.property_value = ?`
- Substring : `INSTR(vpv.property_value, ?) > 0`
- `len()` : `SELECT COUNT(*) FROM video_property_value ...`

### Champs dérivés du filename

`extension` et `file_title` sont extraits de `filename` via des colonnes
générées SQLite dans `database.sql` :

- `_basename` : colonne helper (extrait le nom de fichier du chemin complet,
  normalise les séparateurs `\` → `/`, utilise le trick `RTRIM`)
- `extension` : partie après le dernier `.`, en minuscules (dotfiles gérés)
- `file_title` : nom de fichier sans extension

### Attributs exclus du langage

| Attribut | Raison |
|----------|--------|
| `title` | Redondant : `meta_title` et `file_title` disponibles séparément |
| `similarity` | Dérivation complexe (texte descriptif), peu utile en filtrage |
| `similarity_reencoded` | Idem |

### Opérateurs → SQL

| IR | SQL |
|----|-----|
| `Comparison(==)` | `=` |
| `Comparison(!=, <, <=, >, >=)` | identique |
| `IsOp(field, True/False)` | `field = 1` / `field = 0` |
| `InOp(val, set_literal)` | `val IN (?, ?, ...)` |
| `InOp(val, str_field)` | `INSTR(field, ?) > 0` |
| `InOp(val, set_field)` | `EXISTS (SELECT 1 FROM ...)` |
| `NotOp` | `NOT (...)` |
| `LogicalOp(and/or)` | `(...) AND/OR (...)` |
| `LogicalOp(xor)` | `(A AND NOT B) OR (NOT A AND B)` |
| `FunctionCall(len, str)` | `LENGTH(...)` |
| `FunctionCall(len, set)` | `(SELECT COUNT(*) FROM ...)` |
| `DateLiteral` | Timestamp float (via UDT, heure locale) |
| `DateTimestamp` | Valeur float directe |

## Points d'attention

- **`with_thumbnails`** nécessite un LEFT JOIN sur `video_thumbnail`.
  Le JOIN est déjà systématique dans `video_mega_group`.
- **Propriétés custom** : le compilateur charge la liste des propriétés
  (nom, type, multiple) depuis la table `property` à chaque compilation
  via `_compile_source_expression()`.
- **XOR** n'existe pas en SQL standard. Compilé en
  `(A AND NOT B) OR (NOT A AND B)`.
- **Performance** : les sous-requêtes EXISTS sont efficaces grâce aux
  index existants (`idx_video_language_video_id`, `idx_vpv_video_id`).
- **Dates** : converties via `UDT` (calendrier grégorien proleptique) pour
  supporter l'année 0 et les dates avant l'epoch Unix.

## Prochaines étapes possibles

- Validation de l'expression dans le dialogue PySide6 (feedback en temps réel)
- Support des 5 attributs calculés manquants (colonnes générées SQLite)
- Autocomplétion dans le champ de saisie d'expression
- Construction graphique d'expressions (formulaire visuel)
