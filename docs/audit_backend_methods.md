# Audit : Méthodes publiques du backend (Point 2)

Ce document liste toutes les méthodes publiques des 4 classes qui permettent les interactions avec les bases de données.

---

## 1. AbstractDatabase (`pysaurus/database/abstract_database.py`)

### Méthodes abstraites (interface à implémenter)

| # | Méthode | Signature                                                                                       | Description |
|---|---------|-------------------------------------------------------------------------------------------------|-------------|
| 1 | `get_folders` | `() -> Iterable[AbsolutePath]`                                                                  | Retourne les dossiers sources |
| 2 | `get_prop_types` | `(*, name, with_type, multiple, with_enum, default) -> list[dict]`                              | Liste les types de propriétés (avec filtres optionnels) |
| 3 | `prop_type_add` | `(name, prop_type, definition, multiple) -> None`                                               | Crée un type de propriété |
| 4 | `prop_type_del` | `(name) -> None`                                                                                | Supprime un type de propriété |
| 5 | `prop_type_set_name` | `(old_name, new_name) -> None`                                                                  | Renomme un type de propriété |
| 6 | `prop_type_set_multiple` | `(name, multiple) -> None`                                                                      | Bascule single/multiple |
| 7 | `get_videos` | `(*, include, with_moves, where, count_only, exists_only) -> list[VideoPattern] \| int \| bool` | Requête vidéos (avec overloads) |
| 8 | `videos_get_terms` | `() -> dict[int, list[str]]`                                                                    | Termes extraits des noms de fichiers |
| 9 | `videos_get_moves` | `() -> Iterable[tuple[int, list[dict]]]`                                                        | Déplacements potentiels |
| 10 | `video_entry_del` | `(video_id) -> None`                                                                            | Supprime une entrée vidéo |
| 11 | `video_entry_set_filename` | `(video_id, path) -> AbsolutePath`                                                              | Change le chemin d'une vidéo |
| 12 | `videos_set_field` | `(field, changes: dict[int, Any]) -> None`                                                      | Modifie un champ pour plusieurs vidéos |
| 13 | `videos_add` | `(video_entries, runtime_info) -> None`                                                         | Ajoute des vidéos |
| 14 | `videos_tag_get` | `(name, indices) -> dict[int, list[PropUnitType]]`                                              | Lit les valeurs d'une propriété |
| 15 | `video_entry_set_tags` | `(video_id, properties, merge) -> None`                                                         | Définit plusieurs propriétés pour une vidéo |
| 16 | `videos_tag_set` | `(name, updates, action) -> None`                                                               | Définit une propriété pour plusieurs vidéos |

### Méthodes concrètes (non abstraites)

| # | Méthode | Signature | Description |
|---|---------|-----------|-------------|
| 17 | `get_name` | `() -> str` | Nom de la base de données |
| 18 | `rename` | `(new_name) -> None` | Renomme la base (change `ways`) |
| 19 | `save` | `() -> None` | Sauvegarde (si pas dans un save context) |
| 20 | `to_save` | `() -> DatabaseToSaveContext` | Contexte de sauvegarde différée |
| 21 | `reopen` | `() -> None` | Réouvre (no-op par défaut) |
| 22 | `__close__` | `() -> None` | Ferme la base |
| 23 | `ops` | *property* `-> DatabaseOperations` | Accès aux opérations |
| 24 | `algos` | *property* `-> DatabaseAlgorithms` | Accès aux algorithmes |

### Méthodes semi-privées utilisées par Ops/Algos

| Méthode | Description |
|---------|-------------|
| `_set_date(date)` | Définit la date de mise à jour |
| `_set_folders(folders)` | Définit les dossiers sources |
| `_thumbnails_add(mapping)` | Ajoute des thumbnails |
| `_notify_fields_modified(fields, is_property)` | Notifie les changements et sauvegarde |

---

## 2. DatabaseOperations (`pysaurus/database/database_operations.py`)

Accès via `db.ops`.

| # | Méthode | Signature | Description |
|---|---------|-----------|-------------|
| 1 | `set_folders` | `(folders) -> None` | Définit les dossiers (sauvegarde si changement) |
| 2 | `count_videos` | `(*flags, **forced_flags) -> int` | Compte les vidéos avec filtres |
| 3 | `has_video` | `(**fields) -> bool` | Vérifie l'existence d'une vidéo |
| 4 | `get_video_filename` | `(video_id) -> AbsolutePath` | Chemin d'une vidéo |
| 5 | `open_video` | `(video_id) -> None` | Ouvre la vidéo + mark as watched |
| 6 | `mark_as_watched` | `(video_id) -> None` | Marque comme vue (date + watched=True) |
| 7 | `mark_as_read` | `(video_id) -> bool` | Toggle watched, retourne la nouvelle valeur |
| 8 | `delete_video` | `(video_id) -> AbsolutePath` | Supprime fichier + entrée BDD |
| 9 | `trash_video` | `(video_id) -> AbsolutePath` | Envoie à la corbeille + supprime entrée |
| 10 | `change_video_file_title` | `(video_id, new_title) -> None` | Renomme le fichier vidéo |
| 11 | `move_video_entry` | `(from_id, to_id) -> None` | Déplace une entrée (délègue à algos) |
| 12 | `set_similarities` | `(similarities: dict) -> None` | Définit les IDs de similarité |
| 13 | `set_similarities_from_list` | `(video_indices, similarities) -> None` | Variante liste parallèle |
| 14 | `apply_on_prop_value` | `(prop_name, mod_name) -> None` | Applique un modificateur aux valeurs |
| 15 | `count_property_for_videos` | `(video_indices, name) -> list[list]` | Compte les valeurs pour des vidéos |
| 16 | `update_property_for_videos` | `(video_indices, name, to_add, to_remove) -> None` | Ajoute/retire des valeurs |
| 17 | `set_property_for_videos` | `(name, updates, merge) -> None` | Définit une propriété et notifie |
| 18 | `validate_prop_values` | `(name, values) -> list` | Valide des valeurs selon le type |

---

## 3. DatabaseAlgorithms (`pysaurus/database/database_algorithms.py`)

Accès via `db.algos`.

| # | Méthode | Signature | Description |
|---|---------|-----------|-------------|
| 1 | `refresh` | `() -> None` | `update()` + `provider.refresh()` |
| 2 | `update` | `() -> None` | Scanne les dossiers, ajoute/met à jour les vidéos |
| 3 | `ensure_miniatures` | `() -> list[Miniature]` | Génère les miniatures manquantes |
| 4 | `confirm_unique_moves` | `() -> int` | Confirme les déplacements 1-to-1 |
| 5 | `get_unique_moves` | `() -> list[tuple[int, int]]` | Liste des déplacements uniques |
| 6 | `move_video_entries` | `(moves: list[tuple]) -> None` | Déplace plusieurs entrées |
| 7 | `move_property_values` | `(values, from_name, to_name, *, concatenate) -> int` | Déplace des valeurs entre propriétés |
| 8 | `delete_property_values` | `(name, values) -> None` | Supprime des valeurs d'une propriété |
| 9 | `replace_property_values` | `(name, old_values, new_value) -> bool` | Remplace des valeurs (renommage) |
| 10 | `fill_property_with_terms` | `(prop_name, only_empty) -> None` | Remplit une propriété avec les termes |

---

## 4. AbstractVideoProvider (`pysaurus/video_provider/abstract_video_provider.py`)

Accès via `db.provider`.

### Setters (layers du pipeline)

| # | Méthode | Signature | Description |
|---|---------|-----------|-------------|
| 1 | `set_sources` | `(paths: Sequence[Sequence[str]]) -> None` | Filtre par sources |
| 2 | `set_groups` | `(field, is_property, sorting, reverse, allow_singletons) -> None` | Groupement |
| 3 | `set_classifier_path` | `(path: Sequence[str]) -> None` | Chemin du classifieur |
| 4 | `set_group` | `(group_id) -> None` | Sélection de groupe |
| 5 | `set_search` | `(text, cond="and") -> None` | Recherche textuelle |
| 6 | `set_sort` | `(sorting: Sequence[str]) -> None` | Tri |

### Getters

| # | Méthode | Signature                                                  | Description |
|---|---------|------------------------------------------------------------|-------------|
| 7 | `get_sources` | `() -> list[list[str]]`                                    | Sources actives |
| 8 | `get_grouping` | `() -> GroupDef`                                           | Groupement actif |
| 9 | `get_classifier_path` | `() -> list[str]`                                          | Chemin classifieur |
| 10 | `get_group` | `() -> int`                                                | Groupe sélectionné |
| 11 | `get_search` | `() -> SearchDef`                                          | Recherche active |
| 12 | `get_sort` | `() -> list[str]`                                          | Tri actif |
| 13 | `get_view_indices` | `() -> Sequence[int]`                                      | IDs vidéos filtrées |
| 14 | `get_current_state` | `(page_size, page_number, selector) -> VideoSearchContext` | État complet paginé |
| 15 | `get_group_def` | `() -> dict \| None`                                       | Définition du groupement avec stats |
| 16 | `get_classifier_stats` | `() -> list[FieldStat]`                                    | Statistiques du classifieur |
| 17 | `count_source_videos` | `() -> int`                                                | Nombre total de vidéos sources |
| 18 | `get_random_found_video_id` | `() -> int`                                                | ID aléatoire (found, readable, unwatched) |

### Actions composées

| # | Méthode | Signature | Description |
|---|---------|-----------|-------------|
| 19 | `choose_random_video` | `(open_video=True) -> str` | Choisit, ouvre, configure la recherche |
| 20 | `classifier_select_group` | `(group_id) -> None` | Ajoute au chemin classifieur |
| 21 | `classifier_focus_prop_val` | `(prop_name, field_value) -> None` | Focus sur une valeur de propriété |
| 22 | `classifier_back` | `() -> None` | Retour en arrière dans le classifieur |
| 23 | `classifier_reverse` | `() -> list` | Inverse le chemin classifieur |
| 24 | `apply_on_view` | `(selector, db_fn_name, *args) -> Optional` | Applique une opération sur la vue |
| 25 | `refresh` | `() -> None` | Force la mise à jour depuis LAYER_SOURCE |
| 26 | `reset` | `() -> None` | Réinitialise tous les layers |
| 27 | `reset_parameters` | `(*layer_names) -> None` | Réinitialise des layers spécifiques |
| 28 | `manage_attributes_modified` | `(properties, is_property) -> None` | Notifie que des attributs ont changé |
| 29 | `delete` | `(video_id) -> None` | Supprime une vidéo du provider |

---

## Résumé

| Classe | Méthodes publiques | Rôle |
|--------|-------------------|------|
| AbstractDatabase | 24 | Interface minimale + persistence |
| DatabaseOperations | 18 | CRUD + logique métier |
| DatabaseAlgorithms | 10 | Batch + algorithmes lourds |
| AbstractVideoProvider | 29 | Filtrage, tri, groupement, classifieur |
| **Total** | **81** | |
