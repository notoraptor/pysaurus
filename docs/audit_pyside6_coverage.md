# Audit : Couverture PySide6 des features API (Point 4)

PySide6 ne passe **pas** par `FeatureAPI.__run_feature__`. Il fait des appels directs aux classes backend via `AppContext`. Ce document compare chaque feature API avec son équivalent PySide6.

---

## Légende

- **Couvert** : PySide6 fait un appel équivalent directement
- **Manquant** : la feature existe dans l'API mais PySide6 ne l'implémente pas
- **N/A** : pas pertinent pour PySide6 (ex : features spécifiques web)

---

## 1. Features proxy de FeatureAPI

| # | Feature API | Couvert PySide6 ? | Appel PySide6 | Emplacement |
|---|-------------|---------------------|---------------|-------------|
| 1 | `apply_on_view` | **Oui** | `ctx.apply_on_view(...)` | videos_page:1719-1745 |
| 2 | `apply_on_prop_value` | **Manquant** | — | Aucun appel à `apply_on_prop_value` dans PySide6 |
| 3 | `classifier_back` | **Oui** | `ctx.classifier_back()` | videos_page:1938 |
| 4 | `classifier_focus_prop_val` | **Oui** | `ctx.classifier_focus_prop_val(...)` | videos_page:1302 |
| 5 | `classifier_reverse` | **Oui** | `ctx.classifier_reverse()` | videos_page:1945 |
| 6 | `classifier_select_group` | **Oui** | `ctx.classifier_select_group(...)` | videos_page:1931 |
| 7 | `confirm_unique_moves` | **Oui** | `ctx.confirm_unique_moves()` | videos_page:1511 |
| 8 | `convert_prop_multiplicity` | **Oui** | `ctx.database.prop_type_set_multiple(...)` | properties_page:465 |
| 9 | `create_prop_type` | **Oui** | `ctx.database.prop_type_add(...)` | properties_page:402 |
| 10 | `delete_property_values` | **Oui** | Via `PropertyValuesDialog` → `db.videos_tag_set` (action REMOVE) | property_values_dialog |
| 11 | `delete_video` | **Oui** | `ctx.ops.delete_video(...)` | videos_page:1670 |
| 12 | `delete_video_entry` | **Oui** | `ctx.database.video_entry_del(...)` | videos_page:1597,1614 |
| 13 | `trash_video` | **Oui** | `ctx.ops.trash_video(...)` | videos_page:1640 |
| 14 | `describe_prop_types` | **Oui** | `ctx.database.get_prop_types()` | properties_page:250, videos_page:1570,1684,1794 |
| 15 | `replace_property_values` | **Oui** | Via `PropertyValuesDialog` → `algos.replace_property_values` | property_values_dialog |
| 16 | `fill_property_with_terms` | **Oui** | `ctx.algos.fill_property_with_terms(...)` | properties_page:542 |
| 17 | `get_database_names` | **Oui** | `ctx.get_database_names()` | databases_page:249 |
| 18 | `get_language_names` | **Manquant** | — | Pas de sélecteur de langue dans PySide6 |
| 19 | `move_property_values` | **Oui** | `ctx.algos.move_property_values(...)` | properties_page:510 |
| 20 | `open_random_video` | **Oui (variante)** | `provider.get_random_found_video_id()` + `ops.open_video()` (décomposé) | videos_page:1878-1898 |
| 21 | `open_video` | **Oui** | `ctx.ops.open_video(...)` | videos_page:292,1309,1367 |
| 22 | `mark_as_read` | **Oui** | `ctx.ops.mark_as_read(...)` | videos_page:1518 |
| 23 | `remove_prop_type` | **Oui** | `ctx.database.prop_type_del(...)` | properties_page:447 |
| 24 | `rename_database` | **Oui** | `ctx.rename_database(...)` | main_window:451 |
| 25 | `rename_prop_type` | **Oui** | `ctx.database.prop_type_set_name(...)` | properties_page:427 |
| 26 | `rename_video` | **Oui** | `ctx.ops.change_video_file_title(...)` | videos_page:1430 |
| 27 | `set_group` | **Oui** | `ctx.provider.set_group(...)` | videos_page:2020 |
| 28 | `set_groups` | **Oui** | `ctx.provider.set_groups(...)` | videos_page:1800-1810 |
| 29 | `set_search` | **Oui** | `ctx.provider.set_search(...)` | videos_page:1822,1830,1890 |
| 30 | `set_similarities` | **Oui** | `ctx.ops.set_similarities_from_list(...)` | videos_page:1449,1466 |
| 31 | `set_sorting` | **Oui** | `ctx.provider.set_sort(...)` | videos_page:1874 |
| 32 | `set_sources` | **Oui** | `ctx.provider.set_sources(...)` | videos_page:1774 |
| 33 | `set_video_folders` | **Oui** | `ctx.ops.set_folders(...)` (via `ctx.set_database_folders`) | main_window:475 |
| 34 | `set_video_moved` / `confirm_move` | **Oui** | `ctx.confirm_move(...)` | videos_page:1492 |
| 35 | `set_video_properties` | **Oui** | Via `VideoPropertiesDialog` → `db.video_entry_set_tags` | video_properties_dialog |
| 36 | `set_video_properties` (doublon #35) | — | — | — |

### 1.2. Méthodes directes de FeatureAPI

| # | Feature API | Couvert PySide6 ? | Appel PySide6 | Notes |
|---|-------------|---------------------|---------------|-------|
| 37 | `get_constants` | **N/A** | — | Constants web uniquement (server port, etc.) |
| 38 | `set_language` | **Manquant** | — | Pas de sélecteur de langue |
| 39 | `backend` (JSON) | **N/A** | — | Spécifique web (sérialisation JSON) |
| 40 | `get_python_backend` | **Oui (équivalent)** | `ctx.get_videos(...)` → `provider.get_current_state(...)` | Accès direct au provider |
| 41 | `classifier_concatenate_path` | **Oui** | `ctx.classifier_concatenate_path(...)` | videos_page:1978 |
| 42 | `playlist` | **Oui** | `ctx.api.playlist()` | videos_page:331 |
| 43 | `open_containing_folder` | **Oui** | `ctx.api.open_containing_folder(...)` | videos_page:1377 |

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
| 47 | `open_from_server` | **Oui** | `ctx.api.open_from_server(...)` | videos_page:1372 |
| 48 | `cancel_copy` | **Oui** | `ctx.cancel_operation()` → `api.cancel_copy()` | app_context:214 |
| 49 | `close_database` | **Oui** | `ctx.close_database()` → `api.close_database()` | main_window:509 |
| 50 | `delete_database` | **Oui** | `ctx.delete_database()` → `api.delete_database()` | app_context:232 (+ appel direct dans databases_page:281) |
| 51 | `close_app` | **Oui** | `ctx.close_app()` → `api.close_app()` | main_window:582 |
| 52 | `create_database` | **Oui** | `ctx.create_database(...)` → `api.create_database(...)` | main_window:248 |
| 53 | `open_database` | **Oui** | `ctx.open_database(...)` → `api.open_database(...)` | main_window:240 |
| 54 | `update_database` | **Oui** | `ctx.update_database()` → `api.update_database()` | main_window:262 |
| 55 | `find_similar_videos` | **Oui** | `ctx.find_similar_videos()` → `api.find_similar_videos()` | main_window:270 |
| 56 | `move_video_file` | **Oui** | `ctx.move_video_file(...)` → `api.move_video_file(...)` | main_window:278 |

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

### 4.2. `get_language_names` / `set_language`

**Ce que ça fait** : Permet de changer la langue de l'interface.

**Backend** : `Application.get_language_names()`, `Application.open_language_from_name(name)`.

**Impact** : PySide6 n'a pas de système d'internationalisation — tous les textes sont en anglais codé en dur. Ajouter cette feature nécessiterait un travail d'i18n significatif. Priorité basse.

---

## 5. Appels directs PySide6 sans équivalent dans FeatureAPI

PySide6 fait aussi des appels directs qui n'ont pas de feature API correspondante :

| Appel PySide6 | Emplacement | Description |
|---------------|-------------|-------------|
| `db.get_videos(where={"video_id": ...})` | videos_page:1544,1565,1585,1625,1653 | Requête directe pour obtenir une vidéo spécifique |
| `db.get_folders()` | main_window:464, videos_page:1532 | Lecture directe des dossiers |
| `db.get_name()` | main_window:441,499,527 | Lecture directe du nom |
| `provider.get_current_state(1, 0)` | videos_page:1767,1783,1860 | Lecture de l'état courant pour pré-remplir les dialogues |
| `provider.get_random_found_video_id()` | videos_page:1882 | Version décomposée de `choose_random_video` |
| `provider.reset_parameters(...)` | videos_page:1885-1888 | Reset partiel du provider |
| `provider.manage_attributes_modified(...)` | videos_page:1521 | Notification manuelle après `mark_as_read` |
| `Application.delete_database_from_name(...)` | databases_page:281 | Suppression directe sans passer par GuiAPI |
