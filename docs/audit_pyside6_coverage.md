# Audit : Couverture PySide6 des features API (Point 4)

PySide6 ne passe **pas** par `FeatureAPI.__run_feature__`. Il fait des appels aux classes backend **via la façade `AppContext`**. Depuis le refactoring façade, tout le code PySide6 (pages et dialogs) passe exclusivement par les méthodes d'`AppContext`, sans accéder directement à ses attributs internes (`_database`, `_ops`, `_algos`, `_provider`, `_api`, `_application`). Ce document compare chaque feature API avec son équivalent PySide6.

---

## Légende

- **Couvert** : PySide6 fait un appel équivalent via AppContext
- **Manquant** : la feature existe dans l'API mais PySide6 ne l'implémente pas
- **N/A** : pas pertinent pour PySide6 (ex : features spécifiques web)

---

## 1. Features proxy de FeatureAPI

| # | Feature API | Couvert PySide6 ? | Appel PySide6 | Emplacement |
|---|-------------|---------------------|---------------|-------------|
| 1 | `apply_on_view` | **Oui** | `ctx.apply_on_view(...)` | videos_page |
| 2 | `apply_on_prop_value` | **Manquant** | — | Aucun appel à `apply_on_prop_value` dans PySide6 |
| 3 | `classifier_back` | **Oui** | `ctx.classifier_back()` | videos_page |
| 4 | `classifier_focus_prop_val` | **Oui** | `ctx.classifier_focus_prop_val(...)` | videos_page |
| 5 | `classifier_reverse` | **Oui** | `ctx.classifier_reverse()` | videos_page |
| 6 | `classifier_select_group` | **Oui** | `ctx.classifier_select_group(...)` | videos_page |
| 7 | `confirm_unique_moves` | **Oui** | `ctx.confirm_unique_moves()` | videos_page |
| 8 | `convert_prop_multiplicity` | **Oui** | `ctx.set_prop_type_multiple(...)` | properties_page |
| 9 | `create_prop_type` | **Oui** | `ctx.create_prop_type(...)` | properties_page |
| 10 | `delete_property_values` | **Oui** | Via `PropertyValuesDialog` → `ctx.delete_property_values(...)` | property_values_dialog |
| 11 | `delete_video` | **Oui** | `ctx.delete_video_file(...)` | videos_page |
| 12 | `delete_video_entry` | **Oui** | `ctx.delete_video_entry(...)` | videos_page |
| 13 | `trash_video` | **Oui** | `ctx.trash_video(...)` | videos_page |
| 14 | `describe_prop_types` | **Oui** | `ctx.get_prop_types()` | properties_page, videos_page |
| 15 | `replace_property_values` | **Oui** | Via `PropertyValuesDialog` → `ctx.replace_property_values(...)` | property_values_dialog |
| 16 | `fill_property_with_terms` | **Oui** | `ctx.fill_property_with_terms(...)` | properties_page |
| 17 | `get_database_names` | **Oui** | `ctx.get_database_names()` | databases_page |
| 18 | `get_language_names` | **Manquant** | — | Pas de sélecteur de langue dans PySide6 |
| 19 | `move_property_values` | **Oui** | `ctx.move_property_values(...)` | properties_page |
| 20 | `open_random_video` | **Oui (variante)** | `ctx.get_random_video_id()` + `ctx.open_video()` (décomposé) | videos_page |
| 21 | `open_video` | **Oui** | `ctx.open_video(...)` | videos_page |
| 22 | `mark_as_read` | **Oui** | `ctx.mark_as_read(...)` | videos_page |
| 23 | `remove_prop_type` | **Oui** | `ctx.delete_prop_type(...)` | properties_page |
| 24 | `rename_database` | **Oui** | `ctx.rename_database(...)` | main_window |
| 25 | `rename_prop_type` | **Oui** | `ctx.rename_prop_type(...)` | properties_page |
| 26 | `rename_video` | **Oui** | `ctx.rename_video(...)` | videos_page |
| 27 | `set_group` | **Oui** | `ctx.set_group(...)` | videos_page |
| 28 | `set_groups` | **Oui** | `ctx.set_groups(...)` | videos_page |
| 29 | `set_search` | **Oui** | `ctx.set_search(...)` | videos_page |
| 30 | `set_similarities` | **Oui** | `ctx.dismiss_similarity(...)` / `ctx.reset_similarity(...)` | videos_page |
| 31 | `set_sorting` | **Oui** | `ctx.set_sorting(...)` | videos_page |
| 32 | `set_sources` | **Oui** | `ctx.set_sources(...)` | videos_page |
| 33 | `set_video_folders` | **Oui** | `ctx.set_database_folders(...)` | main_window |
| 34 | `set_video_moved` / `confirm_move` | **Oui** | `ctx.confirm_move(...)` | videos_page |
| 35 | `set_video_properties` | **Oui** | Via `VideoPropertiesDialog` → `ctx.set_video_properties(...)` | video_properties_dialog |
| 36 | `set_video_properties` (doublon #35) | — | — | — |

### 1.2. Méthodes directes de FeatureAPI

| # | Feature API | Couvert PySide6 ? | Appel PySide6 | Notes |
|---|-------------|---------------------|---------------|-------|
| 37 | `get_constants` | **N/A** | — | Constants web uniquement (server port, etc.) |
| 38 | `set_language` | **Manquant** | — | Pas de sélecteur de langue |
| 39 | `backend` (JSON) | **N/A** | — | Spécifique web (sérialisation JSON) |
| 40 | `get_python_backend` | **Oui (équivalent)** | `ctx.get_videos(...)` | Accès via façade AppContext |
| 41 | `classifier_concatenate_path` | **Oui** | `ctx.classifier_concatenate_path(...)` | videos_page |
| 42 | `playlist` | **Oui** | `ctx.playlist()` | videos_page |
| 43 | `open_containing_folder` | **Oui** | `ctx.open_containing_folder(...)` | videos_page |

---

## 2. Features de GuiAPI

### 2.1. Proxies additionnels

| # | Feature API | Couvert PySide6 ? | Appel PySide6 | Notes |
|---|-------------|---------------------|---------------|-------|
| 44 | `clipboard` | **Oui (natif Qt)** | `QApplication.clipboard().setText(...)` | Utilise le clipboard Qt natif au lieu de pyperclip |
| 45 | `select_directory` | **Oui (natif Qt)** | `QFileDialog.getExistingDirectory(...)` | Dialogue Qt natif |
| 46 | `select_file` | **Oui (natif Qt)** | `QFileDialog.getOpenFileNames(...)` | Dialogue Qt natif |

### 2.2. Méthodes directes de GuiAPI

| # | Feature API | Couvert PySide6 ? | Appel PySide6 | Notes |
|---|-------------|---------------------|---------------|-------|
| 47 | `open_from_server` | **Oui** | `ctx.open_from_server(...)` | videos_page |
| 48 | `cancel_copy` | **Oui** | `ctx.cancel_operation()` | app_context |
| 49 | `close_database` | **Oui** | `ctx.close_database()` | main_window |
| 50 | `delete_database` | **Oui** | `ctx.delete_database()` | app_context, databases_page |
| 51 | `close_app` | **Oui** | `ctx.close_app()` | main_window |
| 52 | `create_database` | **Oui** | `ctx.create_database(...)` | main_window |
| 53 | `open_database` | **Oui** | `ctx.open_database(...)` | main_window |
| 54 | `update_database` | **Oui** | `ctx.update_database()` | main_window |
| 55 | `find_similar_videos` | **Oui** | `ctx.find_similar_videos()` | main_window |
| 56 | `move_video_file` | **Oui** | `ctx.move_video_file(...)` | main_window |

---

## 3. Résumé de couverture

| Catégorie | Total | Couvert | Manquant | N/A |
|-----------|-------|---------|----------|-----|
| FeatureAPI proxies | 36 | 34 | 2 | 0 |
| FeatureAPI méthodes | 7 | 4 | 1 | 2 |
| GuiAPI proxies | 3 | 3 | 0 | 0 |
| GuiAPI méthodes | 10 | 10 | 0 | 0 |
| **Total** | **56** | **51** | **3** | **2** |

**Couverture : 51/54 features pertinentes = 94%**

---

## 4. Features manquantes dans PySide6

### 4.1. `apply_on_prop_value` (modifier les valeurs d'une propriété)

**Ce que ça fait** : Applique une fonction de transformation (ex : `strip`, `lower`, `capitalize`) sur les valeurs d'une propriété string pour toutes les vidéos.

**Backend** : `Ops.apply_on_prop_value(prop_name, mod_name)` → itère sur `videos_tag_get`, applique le modifier, puis `set_property_for_videos`.

**Impact** : Feature utile pour normaliser les valeurs (ex : supprimer les espaces, uniformiser la casse). Pourrait être ajoutée dans `PropertyValuesDialog` ou `PropertiesPage` comme action "Normalize values" avec un menu de transformations.

**Façade** : la méthode `ctx.apply_on_prop_value(prop_name, modifier)` existe déjà dans AppContext.

### 4.2. `get_language_names` / `set_language`

**Ce que ça fait** : Permet de changer la langue de l'interface.

**Backend** : `Application.get_language_names()`, `Application.open_language_from_name(name)`.

**Impact** : PySide6 n'a pas de système d'internationalisation — tous les textes sont en anglais codé en dur. Ajouter cette feature nécessiterait un travail d'i18n significatif. Priorité basse.

---

## 5. Appels via la façade AppContext

Depuis le refactoring façade, PySide6 n'accède plus directement aux objets backend. Tous les appels passent par des méthodes de `AppContext` :

| Méthode AppContext | Backend délégué | Utilisé par |
|--------------------|-----------------|-------------|
| `ctx.has_database()` | `self._database is not None` | main_window, videos_page, properties_page |
| `ctx.get_database_name()` | `self._database.get_name()` | main_window |
| `ctx.get_database_folder_path()` | `str(self._database.ways.db_folder)` | main_window |
| `ctx.get_database_folders()` | `self._database.get_folders()` | videos_page |
| `ctx.get_video_by_id(id)` | `self._database.get_videos(where=...)` | videos_page |
| `ctx.get_prop_types(...)` | `self._database.get_prop_types(...)` | properties_page, videos_page |
| `ctx.get_provider_state()` | `self._provider.get_current_state(1, 0)` | videos_page |
| `ctx.get_random_video_id()` | `self._provider.get_random_found_video_id()` | videos_page |
| `ctx.notify_attributes_modified(...)` | `self._provider.manage_attributes_modified(...)` | videos_page |
| `ctx.reset_grouping_and_classifier()` | `self._provider.reset_parameters(...)` | videos_page |
| `ctx.delete_database_by_name(name)` | `self._application.delete_database_from_name(name)` | databases_page |
| `ctx.get_property_values(name)` | `self._database.videos_tag_get(name)` | property_values_dialog, move_values_dialog |
| `ctx.set_video_properties(id, props)` | `self._database.video_entry_set_tags(id, props)` | video_properties_dialog, batch_edit_dialog |
