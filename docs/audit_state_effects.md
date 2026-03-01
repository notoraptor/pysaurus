# Audit : Effets d'état et mises à jour UI (Point 5)

Pour chaque feature, ce document identifie :
1. **Quel état backend change** (database, provider, fichiers)
2. **Quoi exactement change** (attribut vidéo, propriété, état provider, prop type...)
3. **Quoi doit se mettre à jour côté UI**
4. **Problèmes éventuels** dans PySide6

---

## Légende changements

- **DB:attr** = attribut vidéo en base (watched, filename, similarity_id, found...)
- **DB:prop** = valeur(s) de propriété vidéo en base
- **DB:proptype** = type de propriété (création, suppression, renommage...)
- **DB:entry** = ajout/suppression d'entrée vidéo
- **DB:folders** = dossiers sources de la base
- **DB:name** = nom de la base
- **PROV:X** = état du provider (sources, grouping, classifier, group, search, sort)
- **FILE** = fichier sur disque (ouverture, déplacement, suppression, renommage)

---

## 1. Opérations sur les vidéos

### `open_video` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`watched=True`, `date_entry_opened=now`) + FILE (ouverture) |
| **Ce qui change** | Le champ `watched` et `date_entry_opened` de la vidéo |
| **UI requise** | Mettre à jour l'indicateur "watched" de la vidéo dans la liste/grille |
| **PySide6** | `ctx.open_video()` appelle `mark_as_watched` qui notifie le provider via `_notify_fields_modified(["date_entry_opened", "watched"])`. `state_changed` est émis pour rafraîchir l'UI. OK. |

### `mark_as_read` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`watched` toggle) |
| **Ce qui change** | Le champ `watched` de la vidéo |
| **UI requise** | Mettre à jour l'indicateur "watched", recalculer le groupement si groupé par `watched` |
| **PySide6** | `ctx.mark_as_read()` émet `state_changed`. `mark_as_read` (Ops) notifie le provider en interne via `_notify_fields_modified(["watched"])`. OK. |

### `delete_video` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:entry (supprimé) + FILE (supprimé du disque) |
| **Ce qui change** | La vidéo n'existe plus en BDD ni sur disque |
| **UI requise** | Retirer la vidéo de la vue, mettre à jour les compteurs, le groupement |
| **PySide6** | `ctx.delete_video_file()` puis `refresh()`. OK. |

### `trash_video` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:entry (supprimé) + FILE (envoyé à la corbeille) |
| **Ce qui change** | Idem `delete_video` mais le fichier est récupérable |
| **UI requise** | Retirer la vidéo de la vue, mettre à jour les compteurs |
| **PySide6** | `ctx.trash_video()` puis `refresh()`. OK. |

### `delete_video_entry` (Db)
| Aspect | Détail |
|--------|--------|
| **État** | DB:entry (supprimé, fichier conservé) |
| **Ce qui change** | La vidéo n'existe plus en BDD |
| **UI requise** | Retirer la vidéo de la vue, mettre à jour les compteurs |
| **PySide6** | `ctx.delete_video_entry()` émet `state_changed`. `video_entry_del` appelle `provider.delete()` + `_notify_fields_modified(["move_id"])`. OK. `delete_video_entries` (batch) utilise `to_save()` pour regrouper les sauvegardes. |

### `rename_video` (Ops → `change_video_file_title`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`filename` changé) + FILE (renommé) |
| **Ce qui change** | Le chemin et le titre du fichier |
| **UI requise** | Mettre à jour le titre affiché de la vidéo |
| **PySide6** | `ctx.rename_video()` émet `state_changed`. `video_entry_set_filename` notifie le provider via `_notify_fields_modified`. OK. |

### `open_from_server` (GuiAPI)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`watched=True`, `date_entry_opened=now`) + subprocess VLC |
| **Ce qui change** | Idem `open_video` mais via VLC/serveur |
| **UI requise** | Idem `open_video` |
| **PySide6** | `ctx.open_from_server()` émet `state_changed`. `open_from_server` (GuiAPI) appelle `mark_as_watched` qui notifie le provider. OK. |

---

## 2. Opérations sur les propriétés vidéo

### `set_video_properties` (Db → `video_entry_set_tags`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (propriétés d'une vidéo modifiées) |
| **Ce qui change** | Les valeurs de propriétés d'une vidéo spécifique |
| **UI requise** | Mettre à jour l'affichage des propriétés de la vidéo, recalculer le groupement si groupé par cette propriété |
| **PySide6** | `ctx.set_video_properties()` émet `state_changed`. `video_entry_set_tags` notifie le provider via `_notify_fields_modified(properties.keys(), is_property=True)`. OK. |

### `apply_on_view` → `count_property_values` / `edit_property_for_videos`
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs ajoutées/retirées pour les vidéos sélectionnées) |
| **Ce qui change** | Les valeurs de propriétés pour un ensemble de vidéos |
| **UI requise** | Mettre à jour l'affichage des propriétés, recalculer le groupement |
| **PySide6** | `ctx.apply_on_view(...)` puis `refresh()`. L'opération `edit_property_for_videos` appelle `update_property_for_videos` qui appelle `set_property_for_videos` qui notifie le provider via `_notify_fields_modified`. OK. |

### `set_similarities` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`similarity_id` modifié) |
| **Ce qui change** | L'identifiant de similarité d'une ou plusieurs vidéos |
| **UI requise** | Mettre à jour le groupement si groupé par `similarity_id` |
| **PySide6** | `ctx.dismiss_similarity()` / `ctx.reset_similarity()` puis `refresh()`. `set_similarities` appelle `_notify_fields_modified(["similarity_id"])` ce qui met à jour le provider. OK. |

---

## 3. Opérations sur les types de propriétés

### `create_prop_type` (Db → `prop_type_add`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (nouveau type de propriété créé) |
| **Ce qui change** | La liste des types de propriétés |
| **UI requise** | Rafraîchir la liste des propriétés, les dialogues d'édition |
| **PySide6** | `ctx.create_prop_type()` puis `refresh()` de PropertiesPage. OK. |

### `remove_prop_type` (Db → `prop_type_del`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (type supprimé) + DB:prop (toutes les valeurs de cette propriété supprimées) |
| **Ce qui change** | La liste des types et toutes les valeurs associées |
| **UI requise** | Rafraîchir la liste des propriétés, si groupé par cette propriété → réinitialiser le groupement |
| **PySide6** | `ctx.delete_prop_type()` émet `state_changed`. `prop_type_del` notifie le provider via `_notify_fields_modified([name], is_property=True)`, ce qui réinitialise le groupement si groupé par la propriété supprimée. OK. |

### `rename_prop_type` (Db → `prop_type_set_name`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (nom changé) |
| **Ce qui change** | Le nom du type de propriété |
| **UI requise** | Rafraîchir la liste des propriétés, mettre à jour le groupement si groupé par cette propriété |
| **PySide6** | `ctx.rename_prop_type()` puis `refresh()` de PropertiesPage. OK (le groupement utilise le nom, qui sera mis à jour au prochain `get_current_state`). |

### `convert_prop_multiplicity` (Db → `prop_type_set_multiple`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (bascule single/multiple) |
| **Ce qui change** | La multiplicité du type de propriété |
| **UI requise** | Rafraîchir la liste des propriétés |
| **PySide6** | `ctx.set_prop_type_multiple()` puis `refresh()`. OK. |

---

## 4. Opérations sur les valeurs de propriétés (batch)

### `delete_property_values` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs supprimées pour toutes les vidéos) |
| **Ce qui change** | Les valeurs de la propriété pour potentiellement beaucoup de vidéos |
| **UI requise** | Rafraîchir la vue vidéo, recalculer le groupement |
| **PySide6** | `ctx.delete_property_values(...)` émet `state_changed`. `delete_property_values` notifie le provider via `_notify_fields_modified([name], is_property=True)`. OK. |

### `replace_property_values` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs remplacées) |
| **Ce qui change** | Des valeurs de propriété sont renommées/fusionnées |
| **UI requise** | Rafraîchir la vue vidéo, recalculer le groupement |
| **PySide6** | Via `PropertyValuesDialog` → `ctx.replace_property_values(...)`. `replace_property_values` appelle `set_property_for_videos` qui notifie le provider. OK. |

### `move_property_values` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs déplacées de prop A vers prop B) |
| **Ce qui change** | Les valeurs de deux propriétés |
| **UI requise** | Rafraîchir les deux propriétés, recalculer le groupement si concerné |
| **PySide6** | `ctx.move_property_values(...)` puis `refresh()`. La méthode appelle `_notify_fields_modified([from, to])`. OK. |

### `fill_property_with_terms` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (propriété remplie avec les termes extraits des noms de fichiers) |
| **Ce qui change** | Les valeurs d'une propriété pour potentiellement toutes les vidéos |
| **UI requise** | Rafraîchir la vue, recalculer le groupement |
| **PySide6** | `ctx.fill_property_with_terms(...)` puis `refresh()`. La méthode appelle `set_property_for_videos` qui notifie. OK. |

---

## 5. Opérations Provider (filtrage/tri/groupement)

### `set_sources`, `set_search`, `set_sort`
| Aspect | Détail |
|--------|--------|
| **État** | PROV:sources / PROV:search / PROV:sort |
| **Ce qui change** | Le filtre/tri actif |
| **UI requise** | Recalculer et réafficher la liste de vidéos, mettre à jour les indicateurs de filtre dans la sidebar |
| **PySide6** | Appel via façade AppContext (`ctx.set_sources()`, `ctx.set_search()`, `ctx.set_sorting()`) puis `refresh()`. OK. |

### `set_groups`
| Aspect | Détail |
|--------|--------|
| **État** | PROV:grouping (+ réinitialise PROV:classifier, PROV:group, PROV:search, PROV:sort) |
| **Ce qui change** | Le groupement actif ; les layers en aval (classifieur, groupe sélectionné, recherche, tri) sont réinitialisés |
| **UI requise** | Afficher la barre de groupes avec la liste des groupes et leurs compteurs, sélectionner le premier groupe par défaut, recalculer et réafficher la liste de vidéos du groupe sélectionné, mettre à jour les indicateurs de filtre dans la sidebar |
| **PySide6** | `ctx.set_groups(...)` puis `refresh()`. OK. |

### `set_group`
| Aspect | Détail |
|--------|--------|
| **État** | PROV:group |
| **Ce qui change** | Le groupe sélectionné dans le groupement actif |
| **UI requise** | Mettre à jour la sélection dans la barre de groupes, recalculer et réafficher la liste de vidéos du nouveau groupe sélectionné |
| **PySide6** | `ctx.set_group(...)` puis `refresh()`. OK. |

### `classifier_select_group`, `classifier_back`, `classifier_reverse`, `classifier_focus_prop_val`
| Aspect | Détail |
|--------|--------|
| **État** | PROV:classifier + PROV:group |
| **Ce qui change** | Le chemin du classifieur et le groupe sélectionné |
| **UI requise** | Mettre à jour l'affichage du chemin classifieur, la barre de groupes, et la liste de vidéos |
| **PySide6** | Appel via façade `ctx.classifier_select_group()`, `ctx.classifier_back()`, `ctx.classifier_reverse()`, `ctx.classifier_focus_prop_val()` puis `refresh()`. OK. |

### `classifier_concatenate_path`
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs déplacées) + PROV:classifier (réinitialisé) + PROV:group (réinitialisé) |
| **Ce qui change** | Les valeurs de propriétés + l'état du classifieur |
| **UI requise** | Rafraîchir tout |
| **PySide6** | Via façade `ctx.classifier_concatenate_path()` puis `refresh()`. OK. |

---

## 6. Opérations longues (threaded)

### `create_database` / `open_database`
| Aspect | Détail |
|--------|--------|
| **État** | `api.database` (nouvelle instance) |
| **Ce qui change** | La base de données active |
| **UI requise** | Naviguer vers VideosPage, afficher les vidéos |
| **PySide6** | Via ProcessPage → signal `database_ready` → `show_videos_page()`. OK. |

### `update_database`
| Aspect | Détail |
|--------|--------|
| **État** | DB:entry (ajouts/suppressions), DB:attr (found, thumbnails...), PROV (refresh) |
| **Ce qui change** | Potentiellement tout : nouvelles vidéos, vidéos non trouvées, thumbnails |
| **UI requise** | Rafraîchir complètement la vue |
| **PySide6** | Via ProcessPage → `show_videos_page()` qui fait `refresh()`. OK. |

### `find_similar_videos`
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (similarity_id pour toutes les vidéos) + PROV:grouping (passé à similarity_id) |
| **Ce qui change** | Les IDs de similarité + le groupement actif |
| **UI requise** | Afficher les groupes de vidéos similaires |
| **PySide6** | Via ProcessPage → `show_videos_page()` qui fait `refresh()`. OK. |

### `move_video_file`
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (filename) + FILE (déplacé) + PROV (refresh) |
| **Ce qui change** | Le chemin du fichier vidéo |
| **UI requise** | Mettre à jour le chemin affiché |
| **PySide6** | Via ProcessPage → `show_videos_page()`. OK. |

---

## 7. Opérations sur la base de données

### `rename_database`
| Aspect | Détail |
|--------|--------|
| **État** | DB:name (changé) + Application.databases (clé mise à jour) |
| **Ce qui change** | Le nom de la base |
| **UI requise** | Mettre à jour le titre de la fenêtre, la liste des bases |
| **PySide6** | `ctx.rename_database()` + mise à jour titre fenêtre. OK. |

### `close_database`
| Aspect | Détail |
|--------|--------|
| **État** | `api.database = None` |
| **Ce qui change** | Plus de base active |
| **UI requise** | Naviguer vers DatabasesPage, désactiver les menus |
| **PySide6** | `ctx.close_database()` → mise à jour menus → `show_databases_page()`. OK. |

### `set_video_folders` (Ops → `set_folders`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:folders (nouveaux dossiers sources) |
| **Ce qui change** | Les dossiers surveillés |
| **UI requise** | Proposer un rescan |
| **PySide6** | Via façade `ctx.set_database_folders()` puis question "rescan now?". OK. |

---

## 8. Synthèse des problèmes identifiés

### Problèmes de notification provider

| # | Feature | Problème | Statut |
|---|---------|----------|--------|
| P1 | `mark_as_watched` / `mark_as_read` | Ne notifiaient pas le provider | **Corrigé** — `_notify_fields_modified` ajouté dans `database_operations.py` |
| P2 | `video_entry_del` | Les deux implémentations appellent déjà `provider.delete()` + `_notify_fields_modified(["move_id"])` | Non-problème |
| P3 | `video_entry_set_tags` (SQL) | Ne notifiait pas le provider | **Corrigé** — `_notify_fields_modified` ajouté dans `pysaurus_collection.py` |
| P4 | `delete_property_values` | `videos_tag_set(action=REMOVE)` sans notification provider | **Corrigé** — `_notify_fields_modified` ajouté dans `database_algorithms.py` |
| P5 | `prop_type_del` | Si groupé par la propriété supprimée, état incohérent | **Corrigé** — `_notify_fields_modified` ajouté dans `json_database.py` et `pysaurus_collection.py` |
| P6 | `change_video_file_title` | Les deux implémentations de `video_entry_set_filename` appellent déjà `_notify_fields_modified` | Non-problème |

### Problèmes UI PySide6

| # | Feature | Problème | Statut |
|---|---------|----------|--------|
| U1 | `open_video` / `open_from_server` | Pas de `state_changed` après ouverture → indicateur "watched" non mis à jour | **Corrigé** — `state_changed.emit()` ajouté dans `app_context.py` |
| U2 | `mark_as_read` / `toggle_watched` | Appel redondant à `manage_attributes_modified` dans `toggle_watched` | **Corrigé** — notification déplacée dans `mark_as_read` (Ops), appel redondant retiré de `app_context.py` |
| U3 | `delete_video_entries` (batch) | Appelle `video_entry_del` dans une boucle sans `to_save()` → N sauvegardes | **Corrigé** — `to_save()` ajouté dans `app_context.py` |
| U4 | `apply_on_prop_value` | Feature non implémentée dans PySide6 | Ouvert (basse priorité) |

### Features manquantes

| # | Feature | Impact | Note |
|---|---------|--------|------|
| M1 | `apply_on_prop_value` | Pas de normalisation de valeurs (strip, lower...) depuis PySide6 | Ouvert (basse priorité) |
| M2 | `set_language` / `get_language_names` | Pas d'i18n dans PySide6 (tout en anglais) | Ignoré — le système des langages doit être entièrement repensé |
