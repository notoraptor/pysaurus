# Saurus SQL — Refactoring TODO

**Date:** 2026-03-08
**Objectif:** Réduire, simplifier et rendre plus lisible le code Saurus/SQL (~3 839 lignes)
**Gain estimé:** ~10 lignes (restant: #10, optionnel)

---

## Priorité haute

### ~~1. `SQLVideoWrapper` : remplacer les properties répétitives~~ — Abandonné

- Les properties explicites sont préférées pour le support IDE (autocomplétion, navigation, refactoring).
- `__getattr__` et la génération dynamique via `setattr` ont été évalués et rejetés.

### ~~2. `video_mega_group.py` : consolider les query builders~~ — Abandonné

- Après analyse détaillée, les 4 fonctions sont structurellement différentes :
  chacune a sa propre logique SQL (sous-requêtes, CTE, COALESCE, SqlFieldFactory, etc.).
- Le "70% de code commun" se réduit à `FROM video AS v WHERE v.discarded = 0` — trop petit pour une abstraction.
- Forcer un helper commun ajouterait de l'indirection sans gain réel de lisibilité.

### ~~3. Unifier `videos_tag_set` et `video_entry_set_tags`~~ — Abandonné

- Après analyse détaillée, la duplication est superficielle (seul le statement INSERT est commun).
- La validation (1 prop vs N props), le DELETE (4 branches vs 2), et la sémantique
  (REPLACE/REMOVE/ADD vs merge/replace) sont trop différents pour un helper commun utile.

### ~~4. Helper `sql_placeholders()`~~ ✅ Fait

- `sql_placeholders()` ajouté dans `sql_utils.py`, appliqué dans tous les fichiers concernés
- `FieldQuery` déplacé de `video_parser.py` vers `sql_utils.py` pour éliminer la dépendance circulaire

---

## Priorité moyenne

### ~~5. Supprimer `GroupDisplayFormatter`~~ ✅ Fait

- Déplacé dans `pysaurus/interface/common/common.py` (commit 6d7ad534)

### ~~6. Optimiser `QueryMaker`~~ — Abandonné

- Les objets copiés sont trop petits pour que `deepcopy` pose un problème de perf.
- Un `copy()` manuel ajouterait du code de maintenance sans gain réel.

### ~~7. Extraire helper `_map_filenames_to_video_ids()`~~ ✅ Fait

- Fonction module-level `_map_filenames_to_video_ids(db, entries, strict=False)` dans `pysaurus_collection.py`
- Utilisée par `videos_add()` et `_add_pure_new_entries()`

### ~~8. Cacher `_get_property_metadata()`~~ ✅ Fait

- Résultat calculé une fois dans `video_mega_group()` et passé en paramètre `prop_meta`
- `_filter_by_selected_property_group` n'a plus besoin de `sql_db`
- 1 round-trip DB au lieu de 2-3

### ~~9. Standardiser la gestion d'erreur sur property lookup~~ — Abandonné

- Après investigation, le comportement silencieux est **intentionnel** :
  les tests montrent que `is_property=True` peut être passé avec un champ vidéo,
  le code doit alors retourner gracieusement zéro résultats (pas lever une erreur).
- `prop_type_set_name`/`prop_type_set_multiple` : le silence est le contrat de l'interface abstraite.

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
| 1 | ~~SQLVideoWrapper~~ Abandonné | — | — |
| 2 | ~~video_mega_group consolidation~~ Abandonné | — | — |
| 3 | ~~Unifier property update methods~~ Abandonné | — | — |
| 4 | ~~Helper `sql_placeholders()`~~ ✅ Fait | — | — |
| 5 | ~~Supprimer GroupDisplayFormatter~~ ✅ Déplacé | — | — |
| 6 | ~~Optimiser QueryMaker~~ Abandonné | — | — |
| 7 | ~~Extraire _map_filenames_to_video_ids~~ ✅ Fait | — | — |
| 8 | ~~Cache _get_property_metadata~~ ✅ Fait | 0 (perf) | — |
| 9 | ~~Standardiser error handling propriétés~~ Abandonné | — | — |
| 10 | Fusionner boucles _get_videos | ~10 | Faible |
| **Total restant** | | **~10** | |
