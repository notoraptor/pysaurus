# Saurus SQL — Refactoring TODO

**Date:** 2026-03-08
**Objectif:** Réduire, simplifier et rendre plus lisible le code Saurus/SQL (~3 839 lignes)
**Gain estimé:** ~455-590 lignes (15-20%)

---

## Priorité haute

### 1. `SQLVideoWrapper` : remplacer les properties répétitives par `__getattr__`

- **Fichier:** `sql_video_wrapper.py`
- **Problème:** 45 `@property` quasi identiques pour de simples lookups `self.data[F.xxx]`
- **Action:** Utiliser `__getattr__` dynamique. Garder explicites uniquement les propriétés avec logique spéciale (`duration`, `frame_rate`, `move_id`, `found`, etc.)
- **Gain estimé:** ~150-180 lignes
- **Effort:** Moyen

### 2. `video_mega_group.py` : consolider les query builders

- **Fichier:** `video_mega_group.py` (597 lignes, plus gros fichier)
- **Problèmes:**
  - 4 fonctions de query building avec ~70% de code commun :
    - `_query_property_groups_with_classifier()` (~45 lignes)
    - `_query_property_groups_without_classifier()` (~37 lignes)
    - `_query_field_groups()` (~40 lignes)
    - `_query_move_id_groups()` (~38 lignes)
  - `_filter_by_no_moves()` duplique un sous-query de `_query_move_id_groups()`
  - `_filter_by_selected_property_group()` : 4 branches SQL similaires
- **Action:** Extraire les fragments SQL communs, paramétrer les différences
- **Gain estimé:** ~80-120 lignes
- **Effort:** Élevé

### 3. Unifier `videos_tag_set` et `video_entry_set_tags`

- **Fichier:** `pysaurus_collection.py`
- **Problème:** Deux méthodes (90 + 40 lignes) font la même chose :
  valider propriétés → DELETE existants → INSERT nouveaux → update FTS.
  Les INSERT (lignes 141-148 vs 171-179) sont quasi identiques.
- **Action:** Extraire un helper `_update_property_values(video_ids, property_updates, action)`
- **Gain estimé:** ~35-45 lignes
- **Effort:** Moyen

### 4. Helper `make_placeholders()`

- **Fichiers:** `pysaurus_collection.py`, `video_mega_group.py`
- **Problème:** `','.join(['?'] * len(items))` répété 8+ fois
- **Action:** Créer dans `sql_utils.py` :
  ```python
  def sql_placeholders(count: int) -> str:
      return ','.join(['?'] * count)
  ```
- **Gain estimé:** ~15-20 lignes
- **Effort:** Faible

---

## Priorité moyenne

### ~~5. Supprimer `GroupDisplayFormatter`~~ ✅ Fait

- Déplacé dans `pysaurus/interface/common/common.py` (commit 6d7ad534)

### 6. Optimiser `QueryMaker`

- **Fichier:** `sql_utils.py` (lignes 118-230)
- **Problème:** Utilise `deepcopy()` pour `.copy()`, coûteux et excessif.
  Trois copies créées d'un coup dans `video_mega_group.py` (count, select, page).
- **Action:** Copie légère ou builder immutable
- **Gain estimé:** ~30-40 lignes + amélioration perf
- **Effort:** Moyen

### 7. Extraire helper `_map_filenames_to_video_ids()`

- **Fichier:** `pysaurus_collection.py`
- **Problème:** Pattern dupliqué entre `videos_add` (lignes 410-417) et `_add_pure_new_entries` (lignes 502-508)
- **Action:** Extraire en méthode helper
- **Gain estimé:** ~15-20 lignes
- **Effort:** Faible

### 8. Cacher `_get_property_metadata()`

- **Fichier:** `video_mega_group.py`
- **Problème:** Appelée 3+ fois avec les mêmes arguments lors d'un grouping (lignes 274, 321, 484)
- **Action:** `lru_cache` ou passer le résultat en paramètre
- **Gain estimé:** 0 lignes (gain perf : 2-3 round-trips DB en moins)
- **Effort:** Faible

### 9. Standardiser la gestion d'erreur sur property lookup

- **Fichiers:** `pysaurus_collection.py` (l.288-295), `video_mega_group.py` (l.582-597)
- **Problème:** Comportement incohérent quand une propriété n'existe pas
  (retour silencieux vs accès `row[0]` sans vérification None)
- **Action:** Créer un helper `_get_required_property(db, name)` qui lève `ValueError`
- **Gain estimé:** ~10-15 lignes + robustesse
- **Effort:** Faible

---

## Priorité basse

### 10. Fusionner les boucles d'enrichissement dans `_get_videos()`

- **Fichier:** `video_mega_utils.py` (lignes 92-109)
- **Problème:** 5 boucles séparées sur `videos` (errors, audio_languages, subtitle_languages, properties, moves)
- **Action:** Fusionner en une seule boucle
- **Gain estimé:** ~10 lignes + légère amélioration perf
- **Effort:** Faible

---

## Résumé

| # | Refactoring | Gain lignes | Effort |
|---|-------------|-------------|--------|
| 1 | SQLVideoWrapper `__getattr__` | ~150-180 | Moyen |
| 2 | video_mega_group consolidation | ~80-120 | Élevé |
| 3 | Unifier property update methods | ~35-45 | Moyen |
| 4 | Helper `sql_placeholders()` | ~15-20 | Faible |
| 5 | ~~Supprimer GroupDisplayFormatter~~ ✅ Déplacé | — | — |
| 6 | Optimiser QueryMaker | ~30-40 | Moyen |
| 7 | Extraire _map_filenames_to_video_ids | ~15-20 | Faible |
| 8 | Cache _get_property_metadata | 0 (perf) | Faible |
| 9 | Standardiser error handling propriétés | ~10-15 | Faible |
| 10 | Fusionner boucles _get_videos | ~10 | Faible |
| **Total** | | **~455-590** | |
