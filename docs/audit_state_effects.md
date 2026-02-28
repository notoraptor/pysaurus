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
| **PySide6** | Appelle `ops.open_video()` puis `refresh()`. **Problème potentiel** : `open_video` appelle `mark_as_watched` qui appelle `videos_set_field` mais ne notifie PAS le provider via `manage_attributes_modified`. Si on est groupé par `watched`, le groupement ne se met pas à jour automatiquement. PySide6 ne corrige pas ce problème car il fait un `refresh()` complet qui re-fetch l'état. Mais l'interface web pourrait ne pas refléter le changement. |

### `mark_as_read` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`watched` toggle) |
| **Ce qui change** | Le champ `watched` de la vidéo |
| **UI requise** | Mettre à jour l'indicateur "watched", recalculer le groupement si groupé par `watched` |
| **PySide6** | `ops.mark_as_read()` puis **manuellement** `provider.manage_attributes_modified(["watched"])` puis `refresh()`. C'est correct mais la notification manuelle est fragile — `mark_as_read` devrait le faire en interne. |

### `delete_video` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:entry (supprimé) + FILE (supprimé du disque) |
| **Ce qui change** | La vidéo n'existe plus en BDD ni sur disque |
| **UI requise** | Retirer la vidéo de la vue, mettre à jour les compteurs, le groupement |
| **PySide6** | `ops.delete_video()` puis `refresh()`. OK. |

### `trash_video` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:entry (supprimé) + FILE (envoyé à la corbeille) |
| **Ce qui change** | Idem `delete_video` mais le fichier est récupérable |
| **UI requise** | Retirer la vidéo de la vue, mettre à jour les compteurs |
| **PySide6** | `ops.trash_video()` puis `refresh()`. OK. |

### `delete_video_entry` (Db)
| Aspect | Détail |
|--------|--------|
| **État** | DB:entry (supprimé, fichier conservé) |
| **Ce qui change** | La vidéo n'existe plus en BDD |
| **UI requise** | Retirer la vidéo de la vue, mettre à jour les compteurs |
| **PySide6** | `db.video_entry_del()` puis `refresh()`. **Problème** : `video_entry_del` ne notifie pas le provider (pas d'appel à `provider.delete()` ou `manage_attributes_modified`). Le `refresh()` complet de PySide6 compense, mais c'est un contournement. |

### `rename_video` (Ops → `change_video_file_title`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`filename` changé) + FILE (renommé) |
| **Ce qui change** | Le chemin et le titre du fichier |
| **UI requise** | Mettre à jour le titre affiché de la vidéo |
| **PySide6** | `ops.change_video_file_title()` puis `refresh()`. **Note** : `change_video_file_title` appelle `video_entry_set_filename` qui ne notifie pas le provider. Le refresh compense. |

### `open_from_server` (GuiAPI)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`watched=True`, `date_entry_opened=now`) + subprocess VLC |
| **Ce qui change** | Idem `open_video` mais via VLC/serveur |
| **UI requise** | Idem `open_video` |
| **PySide6** | `api.open_from_server()`. **Problème** : pas de `refresh()` après. L'indicateur "watched" n'est pas mis à jour dans la UI. |

---

## 2. Opérations sur les propriétés vidéo

### `set_video_properties` (Db → `video_entry_set_tags`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (propriétés d'une vidéo modifiées) |
| **Ce qui change** | Les valeurs de propriétés d'une vidéo spécifique |
| **UI requise** | Mettre à jour l'affichage des propriétés de la vidéo, recalculer le groupement si groupé par cette propriété |
| **PySide6** | Via `VideoPropertiesDialog`. Appelle `db.video_entry_set_tags()` puis le dialogue retourne un "modified" et `refresh()` est appelé. **Problème** : `video_entry_set_tags` ne notifie PAS le provider. Le `refresh()` compense, mais si on est groupé par la propriété modifiée, les groupes ne sont pas recalculés. |

### `apply_on_view` → `count_property_values` / `edit_property_for_videos`
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs ajoutées/retirées pour les vidéos sélectionnées) |
| **Ce qui change** | Les valeurs de propriétés pour un ensemble de vidéos |
| **UI requise** | Mettre à jour l'affichage des propriétés, recalculer le groupement |
| **PySide6** | `ctx.apply_on_view()` puis `refresh()`. L'opération `edit_property_for_videos` appelle `update_property_for_videos` qui appelle `set_property_for_videos` qui notifie le provider via `_notify_fields_modified`. OK. |

### `set_similarities` (Ops)
| Aspect | Détail |
|--------|--------|
| **État** | DB:attr (`similarity_id` modifié) |
| **Ce qui change** | L'identifiant de similarité d'une ou plusieurs vidéos |
| **UI requise** | Mettre à jour le groupement si groupé par `similarity_id` |
| **PySide6** | `ops.set_similarities_from_list()` puis `refresh()`. `set_similarities` appelle `_notify_fields_modified(["similarity_id"])` ce qui met à jour le provider. OK. |

---

## 3. Opérations sur les types de propriétés

### `create_prop_type` (Db → `prop_type_add`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (nouveau type de propriété créé) |
| **Ce qui change** | La liste des types de propriétés |
| **UI requise** | Rafraîchir la liste des propriétés, les dialogues d'édition |
| **PySide6** | `db.prop_type_add()` puis `refresh()` de PropertiesPage. OK. |

### `remove_prop_type` (Db → `prop_type_del`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (type supprimé) + DB:prop (toutes les valeurs de cette propriété supprimées) |
| **Ce qui change** | La liste des types et toutes les valeurs associées |
| **UI requise** | Rafraîchir la liste des propriétés, si groupé par cette propriété → réinitialiser le groupement |
| **PySide6** | `db.prop_type_del()` puis `refresh()` de PropertiesPage. **Problème potentiel** : si on est groupé par la propriété supprimée, le retour à VideosPage pourrait planter ou montrer un état incohérent. Pas de réinitialisation du groupement du provider. |

### `rename_prop_type` (Db → `prop_type_set_name`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (nom changé) |
| **Ce qui change** | Le nom du type de propriété |
| **UI requise** | Rafraîchir la liste des propriétés, mettre à jour le groupement si groupé par cette propriété |
| **PySide6** | `db.prop_type_set_name()` puis `refresh()` de PropertiesPage. OK (le groupement utilise le nom, qui sera mis à jour au prochain `get_current_state`). |

### `convert_prop_multiplicity` (Db → `prop_type_set_multiple`)
| Aspect | Détail |
|--------|--------|
| **État** | DB:proptype (bascule single/multiple) |
| **Ce qui change** | La multiplicité du type de propriété |
| **UI requise** | Rafraîchir la liste des propriétés |
| **PySide6** | `db.prop_type_set_multiple()` puis `refresh()`. OK. |

---

## 4. Opérations sur les valeurs de propriétés (batch)

### `delete_property_values` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs supprimées pour toutes les vidéos) |
| **Ce qui change** | Les valeurs de la propriété pour potentiellement beaucoup de vidéos |
| **UI requise** | Rafraîchir la vue vidéo, recalculer le groupement |
| **PySide6** | Via `PropertyValuesDialog`. **Problème** : `delete_property_values` appelle `videos_tag_set(action=REMOVE)` mais ne notifie PAS le provider via `_notify_fields_modified`. Le dialogue set `was_modified` et la page fait `refresh()` au retour, mais le provider n'a pas recalculé ses groupes. |

### `replace_property_values` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs remplacées) |
| **Ce qui change** | Des valeurs de propriété sont renommées/fusionnées |
| **UI requise** | Rafraîchir la vue vidéo, recalculer le groupement |
| **PySide6** | Via `PropertyValuesDialog`. `replace_property_values` appelle `set_property_for_videos` qui notifie le provider. OK. |

### `move_property_values` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs déplacées de prop A vers prop B) |
| **Ce qui change** | Les valeurs de deux propriétés |
| **UI requise** | Rafraîchir les deux propriétés, recalculer le groupement si concerné |
| **PySide6** | `algos.move_property_values()` puis `refresh()`. La méthode appelle `_notify_fields_modified([from, to])`. OK. |

### `fill_property_with_terms` (Algo)
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (propriété remplie avec les termes extraits des noms de fichiers) |
| **Ce qui change** | Les valeurs d'une propriété pour potentiellement toutes les vidéos |
| **UI requise** | Rafraîchir la vue, recalculer le groupement |
| **PySide6** | `algos.fill_property_with_terms()` puis `refresh()`. La méthode appelle `set_property_for_videos` qui notifie. OK. |

---

## 5. Opérations Provider (filtrage/tri/groupement)

### `set_sources`, `set_groups`, `set_search`, `set_sort`, `set_group`
| Aspect | Détail |
|--------|--------|
| **État** | PROV:sources / PROV:grouping / PROV:search / PROV:sort / PROV:group |
| **Ce qui change** | Le filtre/tri/groupement actif |
| **UI requise** | Recalculer et réafficher la liste de vidéos, mettre à jour les indicateurs de filtre dans la sidebar |
| **PySide6** | Appel direct au provider puis `refresh()`. OK. |

### `classifier_select_group`, `classifier_back`, `classifier_reverse`, `classifier_focus_prop_val`
| Aspect | Détail |
|--------|--------|
| **État** | PROV:classifier + PROV:group |
| **Ce qui change** | Le chemin du classifieur et le groupe sélectionné |
| **UI requise** | Mettre à jour l'affichage du chemin classifieur, la barre de groupes, et la liste de vidéos |
| **PySide6** | Appel via `ctx.classifier_*()` puis `refresh()`. OK. |

### `classifier_concatenate_path`
| Aspect | Détail |
|--------|--------|
| **État** | DB:prop (valeurs déplacées) + PROV:classifier (réinitialisé) + PROV:group (réinitialisé) |
| **Ce qui change** | Les valeurs de propriétés + l'état du classifieur |
| **UI requise** | Rafraîchir tout |
| **PySide6** | `ctx.classifier_concatenate_path()` puis `refresh()`. OK. |

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
| **PySide6** | `ctx.set_database_folders()` puis question "rescan now?". OK. |

---

## 8. Synthèse des problèmes identifiés

### Problèmes de notification provider

| # | Feature | Problème | Sévérité | Correction suggérée |
|---|---------|----------|----------|---------------------|
| P1 | `open_video` / `open_from_server` | `mark_as_watched` ne notifie pas le provider. Si groupé par `watched`, pas de mise à jour auto. | Moyenne | Ajouter `_notify_fields_modified(["watched", "date_entry_opened"])` dans `mark_as_watched` |
| P2 | `video_entry_del` | Ne notifie pas le provider. | Basse (compensé par `refresh()` dans PySide6) | Ajouter `provider.delete(video_id)` + `save()` |
| P3 | `video_entry_set_tags` | Ne notifie pas le provider si les propriétés modifiées affectent le groupement. | Moyenne | Ajouter `_notify_fields_modified(list(properties.keys()), is_property=True)` |
| P4 | `delete_property_values` | `videos_tag_set(action=REMOVE)` sans notification provider. | Moyenne | Ajouter `_notify_fields_modified([name], is_property=True)` dans `delete_property_values` |
| P5 | `prop_type_del` | Si on est groupé par la propriété supprimée, état incohérent. | Haute | Réinitialiser le groupement si `grouping.field == name` |
| P6 | `change_video_file_title` | `video_entry_set_filename` ne notifie pas le provider pour le changement de `filename`. | Basse (compensé par `refresh()`) | Ajouter notification si besoin |

### Problèmes UI PySide6

| # | Feature | Problème | Sévérité | Correction suggérée |
|---|---------|----------|----------|---------------------|
| U1 | `open_from_server` (VLC) | Pas de `refresh()` après ouverture VLC → indicateur "watched" non mis à jour | Moyenne | Ajouter `self.refresh()` ou notifier le changement |
| U2 | `mark_as_read` | Appel manuel à `manage_attributes_modified` → fragile, devrait être dans Ops | Basse | Déplacer la notification dans `mark_as_read` de DatabaseOperations |
| U3 | `video_entry_del` (batch Delete) | Appelle `video_entry_del` dans une boucle sans `to_save()` → N sauvegardes | Basse (perf) | Utiliser `db.to_save()` pour regrouper les sauvegardes |
| U4 | `apply_on_prop_value` | Feature non implémentée dans PySide6 | Basse | Ajouter dans PropertiesPage ou PropertyValuesDialog |

### Features manquantes

| # | Feature | Impact |
|---|---------|--------|
| M1 | `apply_on_prop_value` | Pas de normalisation de valeurs (strip, lower...) depuis PySide6 |
| M2 | `set_language` / `get_language_names` | Pas d'i18n dans PySide6 (tout en anglais) |
