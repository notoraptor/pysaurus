# Audit : Features API et mapping backend (Points 1 + 3)

Ce document liste toutes les fonctionnalités exposées par FeatureAPI et GuiAPI, et indique quelles méthodes backend elles appellent.

---

## Légende

- **Proxy** : feature déclarée dans `_proxies` (appelable via `__run_feature__`)
- **Méthode** : méthode Python directe sur la classe
- **@process** : exécution dans un thread background (via décorateur `@process`)

---

## 1. FeatureAPI (`pysaurus/interface/api/feature_api.py`)

### 1.1. Features proxy (dans `_proxies`)

| # | Feature | Type proxy | Méthode backend | Classe | Retourne valeur ? |
|---|---------|------------|-----------------|--------|-------------------|
| 1 | `apply_on_view` | FromView | `View.apply_on_view` | VideoProvider | Oui |
| 2 | `apply_on_prop_value` | FromOps | `Ops.apply_on_prop_value` | DatabaseOperations | Non |
| 3 | `classifier_back` | FromView | `View.classifier_back` | VideoProvider | Non |
| 4 | `classifier_focus_prop_val` | FromView | `View.classifier_focus_prop_val` | VideoProvider | Non |
| 5 | `classifier_reverse` | FromView | `View.classifier_reverse` | VideoProvider | Oui |
| 6 | `classifier_select_group` | FromView | `View.classifier_select_group` | VideoProvider | Non |
| 7 | `confirm_unique_moves` | FromAlgo | `Algo.confirm_unique_moves` | DatabaseAlgorithms | Oui |
| 8 | `convert_prop_multiplicity` | FromDb | `Db.prop_type_set_multiple` | AbstractDatabase | Non |
| 9 | `create_prop_type` | FromDb | `Db.prop_type_add` | AbstractDatabase | Non |
| 10 | `delete_property_values` | FromAlgo | `Algo.delete_property_values` | DatabaseAlgorithms | Non |
| 11 | `delete_video` | FromOps | `Ops.delete_video` | DatabaseOperations | Non |
| 12 | `delete_video_entry` | FromDb | `Db.video_entry_del` | AbstractDatabase | Non |
| 13 | `trash_video` | FromOps | `Ops.trash_video` | DatabaseOperations | Non |
| 14 | `describe_prop_types` | FromDb | `Db.get_prop_types` | AbstractDatabase | Oui |
| 15 | `replace_property_values` | FromAlgo | `Algo.replace_property_values` | DatabaseAlgorithms | Non |
| 16 | `fill_property_with_terms` | FromAlgo | `Algo.fill_property_with_terms` | DatabaseAlgorithms | Non |
| 17 | `get_database_names` | FromApp | `Application.get_database_names` | Application | Oui |
| 18 | `get_language_names` | FromApp | `Application.get_language_names` | Application | Oui |
| 19 | `move_property_values` | FromAlgo | `Algo.move_property_values` | DatabaseAlgorithms | Non |
| 20 | `open_random_video` | FromView | `View.choose_random_video` | VideoProvider | Oui |
| 21 | `open_video` | FromOps | `Ops.open_video` | DatabaseOperations | Non |
| 22 | `mark_as_read` | FromOps | `Ops.mark_as_read` | DatabaseOperations | Oui |
| 23 | `remove_prop_type` | FromDb | `Db.prop_type_del` | AbstractDatabase | Non |
| 24 | `rename_database` | FromDb | `Db.rename` | AbstractDatabase | Non |
| 25 | `rename_prop_type` | FromDb | `Db.prop_type_set_name` | AbstractDatabase | Non |
| 26 | `rename_video` | FromOps | `Ops.change_video_file_title` | DatabaseOperations | Non |
| 27 | `set_group` | FromView | `View.set_group` | VideoProvider | Non |
| 28 | `set_groups` | FromView | `View.set_groups` | VideoProvider | Non |
| 29 | `set_search` | FromView | `View.set_search` | VideoProvider | Non |
| 30 | `set_similarities` | FromOps | `Ops.set_similarities_from_list` | DatabaseOperations | Non |
| 31 | `set_sorting` | FromView | `View.set_sort` | VideoProvider | Non |
| 32 | `set_sources` | FromView | `View.set_sources` | VideoProvider | Non |
| 33 | `set_video_folders` | FromOps | `Ops.set_folders` | DatabaseOperations | Non |
| 34 | `set_video_moved` | FromOps | `Ops.move_video_entry` | DatabaseOperations | Non |
| 35 | `confirm_move` | FromOps | `Ops.move_video_entry` | DatabaseOperations | Non |
| 36 | `set_video_properties` | FromDb | `Db.video_entry_set_tags` | AbstractDatabase | Non |

### 1.2. Méthodes directes de FeatureAPI

| # | Méthode | Appels backend | Description |
|---|---------|----------------|-------------|
| 37 | `get_constants` | Aucun (retourne `_constants`) | Constantes applicatives |
| 38 | `set_language` | `Application.open_language_from_name` | Change la langue |
| 39 | `backend` | `provider.get_current_state`, `db.get_name`, `db.get_folders`, `db.get_prop_types` | État complet (JSON) pour les interfaces web |
| 40 | `get_python_backend` | Idem `backend` mais retourne `DatabaseContext` | Variante Python-native |
| 41 | `classifier_concatenate_path` | `provider.get_classifier_path`, `provider.get_grouping`, `provider.set_classifier_path`, `provider.set_group`, `Algo.move_property_values` | Concatène le chemin classifieur |
| 42 | `playlist` | `provider.get_view_indices`, `Ops.get_video_filename`, `create_xspf_playlist` | Génère et ouvre une playlist XSPF |
| 43 | `open_containing_folder` | `Ops.get_video_filename`, `AbsolutePath.locate_file` | Ouvre le dossier contenant la vidéo |

---

## 2. GuiAPI (`pysaurus/interface/api/gui_api.py`)

### 2.1. Proxies additionnels

| # | Feature | Type proxy | Méthode backend | Description |
|---|---------|------------|-----------------|-------------|
| 44 | `clipboard` | FromPyperclip | `pyperclip.copy` | Copie dans le presse-papier |
| 45 | `select_directory` | FromTk | `filedial.select_directory` | Dialogue sélection dossier |
| 46 | `select_file` | FromTk | `filedial.select_file_to_open` | Dialogue sélection fichier |

### 2.2. Méthodes directes de GuiAPI

| # | Méthode | Threading | Appels backend | Description |
|---|---------|-----------|----------------|-------------|
| 47 | `open_from_server` | Thread simple | `Ops.mark_as_watched`, subprocess VLC | Ouvre une vidéo via le serveur Flask + VLC |
| 48 | `cancel_copy` | Non | `FileCopier.cancel` ou `notify(Cancelled)` | Annule la copie en cours |
| 49 | `close_database` | Non | `self.database = None` | Ferme la base courante |
| 50 | `delete_database` | Non | `Application.delete_database_from_name`, `self.database = None` | Supprime la base |
| 51 | `close_app` | Non | Threads, notifier, server, `__close__` | Ferme toute l'application |
| 52 | `create_database` | @process | `Application.new_database` | Crée une base (thread) |
| 53 | `open_database` | @process | `Application.open_database_from_name` | Ouvre une base (thread) |
| 54 | `update_database` | @process | `Algo.refresh` | Met à jour la base (thread) |
| 55 | `find_similar_videos` | @process | `DbSimilarVideos.find_similar_videos`, `provider.set_groups(similarity_id)` | Cherche les similarités (thread) |
| 56 | `move_video_file` | @process(finish=False) | `Ops.get_video_filename`, `FileCopier.move`, `db.video_entry_set_filename`, `provider.refresh` | Déplace un fichier vidéo (thread) |

---

## 3. Méthodes backend NON exposées par l'API

Ces méthodes publiques des 4 classes backend ne sont appelées par aucune feature de FeatureAPI/GuiAPI :

### AbstractDatabase

| Méthode | Raison probable |
|---------|----------------|
| `get_name` | Utilisée indirectement dans `backend()` |
| `save` | Appelée en interne par les opérations |
| `to_save` | Contexte interne pour batch |
| `reopen` | Pas de cas d'usage dans l'interface |
| `__close__` | Appelée dans `close_app` |
| `videos_get_terms` | Exposée indirectement via `fill_property_with_terms` |
| `videos_get_moves` | Exposée indirectement via `confirm_unique_moves` |
| `videos_add` | Utilisée uniquement par `Algo.update` |
| `videos_set_field` | Utilisée en interne par Ops/Algos |

### DatabaseOperations

| Méthode | Raison probable |
|---------|----------------|
| `count_videos` | Pas de feature directe (utilisé dans CLI) |
| `has_video` | Utilitaire interne |
| `mark_as_watched` | Appelée par `open_video` (pas d'accès direct) |
| `get_video_filename` | Utilitaire interne (utilisé par `playlist`, etc.) |
| `count_property_for_videos` | Exposée via `apply_on_view` |
| `update_property_for_videos` | Exposée via `apply_on_view` |
| `set_property_for_videos` | Utilitaire interne |
| `validate_prop_values` | Utilitaire interne |
| `set_similarities` | Variante dict de `set_similarities_from_list` |

### DatabaseAlgorithms

| Méthode | Raison probable |
|---------|----------------|
| `update` | Appelée par `refresh` (pas d'accès direct) |
| `ensure_miniatures` | Appelée indirectement par `GuiAPI.find_similar_videos` → `DbSimilarVideos.find_similar_videos` → `db.algos.ensure_miniatures()` |
| `get_unique_moves` | Appelée par `confirm_unique_moves` |
| `move_video_entries` | Appelée par `Ops.move_video_entry` |

### AbstractVideoProvider

| Méthode | Raison probable |
|---------|----------------|
| `get_sources` | Retourné via `get_current_state` |
| `get_grouping` | Retourné via `get_current_state` |
| `get_classifier_path` | Utilisé en interne par `classifier_concatenate_path` |
| `get_group` | Retourné via `get_current_state` |
| `get_search` | Retourné via `get_current_state` |
| `get_sort` | Retourné via `get_current_state` |
| `get_view_indices` | Utilisé en interne par `playlist` et `apply_on_view` |
| `get_group_def` | Retourné via `get_current_state` dans le web |
| `get_classifier_stats` | Retourné via `get_current_state` |
| `count_source_videos` | Pas de feature directe |
| `get_random_found_video_id` | Appelé par `choose_random_video` |
| `refresh` | Appelé par `Algo.refresh` |
| `reset` | Pas de feature directe |
| `reset_parameters` | Utilisé en interne |
| `manage_attributes_modified` | Appelé par `_notify_fields_modified` |
| `delete` | Pas de feature directe |

---

## Résumé

| Source | Nombre de features |
|--------|-------------------|
| FeatureAPI (proxies) | 36 |
| FeatureAPI (méthodes) | 7 |
| GuiAPI (proxies) | 3 |
| GuiAPI (méthodes) | 10 |
| **Total features** | **56** |
