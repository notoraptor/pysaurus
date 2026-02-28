# Audit : Caractère bloquant des features et protection contre les double-exécutions

Ce document analyse, pour chaque opération de l'interface PySide6 :
1. Si l'opération doit être **bloquante** (l'UI doit empêcher toute autre action pendant l'exécution)
2. Si PySide6 **gère correctement** ce caractère bloquant
3. Les **vulnérabilités** aux double-clics ou appels multiples

---

## Catégories de protection

- **ProcessPage** : opération longue exécutée dans un thread, avec une page de suivi qui bloque l'interaction
- **Dialog modal** : un dialog modal (`.exec()`) empêche toute interaction avec la fenêtre parente
- **Confirmation** : un `QMessageBox.question` précède l'action (protège le premier clic, mais pas un double-clic après confirmation)
- **Input dialog** : un `QInputDialog` ou dialog de saisie précède l'action (agit comme porte d'entrée)
- **Guard** : un test conditionnel empêche l'exécution si les conditions ne sont pas remplies
- **Idempotent** : l'opération peut être exécutée plusieurs fois sans effet supplémentaire
- **Aucune** : pas de protection

---

## 1. Opérations longues (threadées)

Ces opérations sont exécutées dans un thread via `_run_process()`, qui affiche une ProcessPage bloquant toute interaction. **Déjà correctement bloquantes.**

| Opération | Déclencheur | Protection | Risque |
|-----------|-------------|------------|--------|
| `create_database` | DatabasesPage → signal | ProcessPage | Faible |
| `open_database` | DatabasesPage → signal | ProcessPage | Faible |
| `update_database` | Menu / bouton toolbar | ProcessPage + confirmation | Faible |
| `find_similar_videos` | Bouton toolbar | ProcessPage + confirmation | Faible |
| `move_video_file` | Menu contextuel → signal | ProcessPage + file dialog + confirmation | Faible |

**Note** : `_run_process()` appelle `_cleanup_process_page()` avant de créer une nouvelle ProcessPage, ce qui offre une protection supplémentaire si le signal est émis deux fois. Cependant, l'opération backend elle-même pourrait être appelée deux fois avant le cleanup. Risque faible mais non nul.

---

## 2. Opérations via dialogs modaux

Ces opérations sont précédées par un dialog modal qui bloque l'interaction avec la fenêtre parente. **Le dialog lui-même est bloquant**, mais certains dialogs contiennent des boutons internes qui effectuent des opérations backend.

### 2.1. Dialogs purement modaux (opération backend après fermeture)

| Dialog | Déclencheur | Opération backend | Risque |
|--------|-------------|-------------------|--------|
| `GroupingDialog` | Bouton "Set..." sidebar | `ctx.set_groups()` après `.exec()` | Aucun |
| `SortingDialog` | Bouton "Set..." sidebar | `ctx.set_sorting()` après `.exec()` | Aucun |
| `SourcesDialog` | Bouton "Edit..." sidebar | `ctx.set_sources()` après `.exec()` | Aucun |
| `BatchEditPropertyDialog` | Menu "Edit Properties..." | `ctx.apply_on_view()` après `.exec()` | Aucun |
| `MoveValuesDialog` | Menu "Move Values..." | `ctx.move_property_values()` après `.exec()` | Aucun |

### 2.2. Dialogs avec opérations internes (backend pendant le dialog)

Ces dialogs effectuent des opérations backend **pendant qu'ils sont ouverts**, via des boutons internes. Le dialog empêche l'interaction avec la fenêtre parente, mais les boutons internes ne sont pas protégés contre les double-clics.

#### PropertyValuesDialog

| Bouton interne | Opération backend | Protection interne | Risque |
|----------------|-------------------|--------------------|--------|
| "Delete Selected" | `ctx.delete_property_values(name, values)` | Confirmation | **Moyen** : après confirmation, double-clic possible |
| "Rename Value..." | `ctx.replace_property_values(name, old, new)` | Input dialog | Faible : l'input dialog bloque |
| Modificateurs (Upper, Lower...) | `ctx.apply_on_prop_value(name, mod)` | Confirmation | **Moyen** : après confirmation, double-clic possible |

#### VideoPropertiesDialog

| Bouton interne | Opération backend | Protection interne | Risque |
|----------------|-------------------|--------------------|--------|
| OK (QDialogButtonBox) | `ctx.set_video_properties(id, props)` | Aucune | **Moyen** : double-clic rapide avant fermeture du dialog |

---

## 3. Opérations synchrones sans dialog

Ce sont les opérations les plus exposées. Elles s'exécutent dans le main thread (donc l'UI est gelée pendant l'exécution), mais rien n'empêche un double-clic de mettre en file deux appels successifs dans la boucle d'événements Qt.

### 3.1. Opérations destructives

| Méthode | Fichier | Déclencheur | Opération backend | Protection | Risque |
|---------|---------|-------------|-------------------|------------|--------|
| `_delete_selected()` | videos_page | Touche Delete | `ctx.delete_video_entry()` en boucle | Confirmation | **Moyen** |
| `_delete_video()` | videos_page | Menu ctx "Delete from database" | `ctx.delete_video_entry(id)` | Confirmation (sauf "not found" si désactivé) | **Moyen** |
| `_trash_video()` | videos_page | Menu ctx "Move to Trash" | `ctx.trash_video(id)` | Confirmation | Faible |
| `_delete_video_file()` | videos_page | Menu ctx "Delete permanently" | `ctx.delete_video_file(id)` | Warning + défaut "No" | Faible |
| `_on_delete()` | properties_page | Menu "Delete" propriété | `ctx.delete_prop_type(name)` | Confirmation | **Moyen** |
| `_on_db_delete()` | databases_page | Bouton "Delete" database | `ctx.delete_database_by_name(name)` | Confirmation | **Moyen** |

**Vulnérabilité commune** : la confirmation empêche le premier clic accidentel, mais après avoir cliqué "Yes", un double-clic rapide sur le bouton d'origine pourrait relancer l'opération une deuxième fois (la confirmation est déjà passée, le handler est rappelé).

**Atténuation naturelle** : en pratique, le menu contextuel se ferme après le premier clic, ce qui empêche le double-clic sur l'item de menu. Le risque réel existe surtout pour les boutons persistants (toolbar, sidebar).

### 3.2. Opérations de modification

| Méthode | Fichier | Déclencheur | Opération backend | Protection | Risque |
|---------|---------|-------------|-------------------|------------|--------|
| `_on_create()` | properties_page | Bouton "Create" | `ctx.create_prop_type(...)` | Validation input | **Haut** : double-clic → doublon, erreur |
| `_on_convert()` | properties_page | Menu "Convert" | `ctx.set_prop_type_multiple(...)` | Confirmation | **Moyen** : double-clic → toggle double = retour à l'état initial |
| `_on_rename()` | properties_page | Menu "Rename..." | `ctx.rename_prop_type(...)` | Input dialog | Faible |
| `_on_fill_with_terms()` | properties_page | Bouton "Fill..." | `ctx.fill_property_with_terms(...)` | Dialog + confirmation | Faible |
| `_on_move_values()` | properties_page | Menu "Move Values..." | `ctx.move_property_values(...)` | Dialog modal | Faible |
| `_rename_video()` | videos_page | Menu ctx "Rename..." | `ctx.rename_video(id, title)` | Input dialog | Faible |
| `_toggle_watched()` | videos_page | Menu ctx "Toggle Watched" | `ctx.mark_as_read(id)` | **Aucune** | **Haut** : double-clic → toggle double = retour à l'état initial |
| `_dismiss_similarity()` | videos_page | Menu ctx "Dismiss" | `ctx.dismiss_similarity(id)` | Confirmation | Faible |
| `_reset_similarity()` | videos_page | Menu ctx "Reset" | `ctx.reset_similarity(id)` | Confirmation | Faible |
| `_confirm_move()` | videos_page | Menu ctx "Confirm move" | `ctx.confirm_move(src, dst)` | Confirmation + défaut "No" | Faible |
| `_on_confirm_unique_moves()` | videos_page | Bouton sidebar | `ctx.confirm_unique_moves()` | Confirmation + défaut "No" | **Moyen** : bouton persistant |
| `_on_rename_database()` | main_window | Menu "Rename..." | `ctx.rename_database(name)` | Input dialog | Faible |
| `_on_edit_folders()` | main_window | Menu "Edit Folders..." | `ctx.set_database_folders(folders)` | Dialog modal | Faible |
| `_on_close_database()` | main_window | Menu "Close Database" | `ctx.close_database()` | Confirmation | Faible (idempotent) |

### 3.3. Opérations de navigation/filtrage (idempotentes)

Ces opérations sont **sûres** car idempotentes : les exécuter deux fois produit le même résultat qu'une seule exécution. Pas de protection nécessaire.

| Méthode | Opération | Protection |
|---------|-----------|------------|
| `_do_search()` | `ctx.set_search(query, mode)` | Idempotent |
| `_clear_search()` | `ctx.set_search("", "and")` | Idempotent |
| `_clear_sources()` | `ctx.set_sources(None)` | Idempotent |
| `_clear_grouping()` | `ctx.clear_groups()` | Idempotent |
| `_clear_sorting()` | `ctx.set_sorting(None)` | Idempotent |
| `_select_group()` | `ctx.set_group(index)` | Idempotent |
| `_on_classifier_add_group()` | `ctx.classifier_select_group(id)` | Idempotent |
| `_on_classifier_unstack()` | `ctx.classifier_back()` | Guard (`if self._classifier_path`) |
| `_on_classifier_reverse()` | `ctx.classifier_reverse()` | Non idempotent (double = retour initial), mais inoffensif |
| Pagination (first/prev/next/last) | Affichage seulement | Idempotent |
| Sélection (select all/clear) | UI seulement | Idempotent |
| `_open_video()` | `ctx.open_video(id)` | Idempotent (ouvre le même fichier) |
| `_open_in_vlc()` | `ctx.open_from_server(id)` | Idempotent (ouvre le même fichier) |
| Copie (titre, path, ID) | Clipboard | Idempotent |

### 3.4. Signaux émis (risque de double émission)

| Méthode | Fichier | Signal | Récepteur | Risque |
|---------|---------|--------|-----------|--------|
| `_on_db_open()` | databases_page | `database_opening` | MainWindow → `_run_process()` | **Moyen** : signal émis sans protection |
| `mouseDoubleClickEvent()` | databases_page | `open_clicked` | `_on_db_open()` | **Moyen** : conçu pour réagir au double-clic |
| `_on_create_clicked()` | databases_page | `database_creating` | MainWindow → `_run_process()` | Faible : après confirmation |
| `update_database_requested` | videos_page | signal | MainWindow → `_run_process()` | Faible : après confirmation |
| `find_similar_requested` | videos_page | signal | MainWindow → `_run_process()` | Faible : après confirmation |
| `move_video_requested` | videos_page | signal | MainWindow → `_run_process()` | Faible : après file dialog + confirmation |

---

## 4. Synthèse des problèmes

### Risque haut

| # | Méthode | Problème | Correction suggérée |
|---|---------|----------|---------------------|
| B1 | `properties_page._on_create()` | Bouton persistant, pas de protection : double-clic crée deux propriétés (la 2e échoue avec erreur) | Désactiver le bouton pendant l'exécution |
| B2 | `videos_page._toggle_watched()` | Menu contextuel, aucune protection : double-clic toggle deux fois (retour état initial, déroutant pour l'utilisateur) | Non prioritaire : le menu contextuel se ferme après le premier clic, empêchant le double-clic. Risque théorique. |

### Risque moyen

| # | Méthode | Problème | Correction suggérée |
|---|---------|----------|---------------------|
| B3 | `PropertyValuesDialog` : boutons "Delete Selected" et modificateurs | Boutons persistants dans un dialog ouvert, confirmation mais pas de désactivation après | Désactiver le bouton après l'opération, ou rafraîchir la liste (ce qui invalide la sélection) |
| B4 | `VideoPropertiesDialog` : bouton OK | Double-clic rapide avant fermeture → double appel `set_video_properties` | Désactiver le bouton OK dans `_on_accept()` avant l'appel backend |
| B5 | `databases_page._on_db_open()` | Signal `database_opening` émis sans protection ; `mouseDoubleClickEvent` émet aussi le signal | Ajouter un guard flag dans `_on_db_open()` ou ignorer les signaux quand un process est déjà en cours dans MainWindow |
| B6 | `properties_page._on_convert()` | Après confirmation, double-clic toggle deux fois → retour état initial | Même remarque que B2 : via menu contextuel, risque faible en pratique |
| B7 | `_on_confirm_unique_moves()` | Bouton persistant en sidebar, après confirmation pas de désactivation | Désactiver le bouton pendant l'exécution |

### Pas de risque significatif

- Toutes les opérations via **ProcessPage** (section 1)
- Toutes les opérations via **dialogs purement modaux** (section 2.1)
- Toutes les opérations **idempotentes** (section 3.3)
- Les opérations protégées par **input dialog** (rename, move) : le dialog bloque tant que l'utilisateur n'a pas saisi et validé
- Les opérations via **menu contextuel** avec confirmation : le menu se ferme au premier clic, empêchant le double-clic sur l'item de menu. La confirmation ajoute une deuxième barrière.

---

## 5. Recommandations

### Pattern général recommandé

Pour les boutons persistants (toolbar, sidebar, dialogs) qui déclenchent des opérations non-idempotentes :

```python
def _on_action(self):
    self.btn_action.setEnabled(False)
    try:
        # ... confirmation dialog si nécessaire ...
        # ... opération backend ...
        self.refresh()
    except Exception as e:
        QMessageBox.critical(self, "Error", str(e))
    finally:
        self.btn_action.setEnabled(True)
```

### Pour les signaux (double émission)

Ajouter un guard dans `MainWindow._run_process()` :

```python
def _run_process(self, title, operation, on_end):
    if self._process_page is not None:
        return  # Déjà en cours
    # ...
```

### Priorités

1. **B1** (`_on_create`) : correction simple, risque réel (bouton persistant, erreur visible)
2. **B5** (`_on_db_open`) : correction simple, risque réel (double-clic naturel sur un item de liste)
3. **B4** (`VideoPropertiesDialog` OK) : correction simple
4. **B3** (`PropertyValuesDialog` boutons internes) : correction simple
5. **B7** (`_on_confirm_unique_moves`) : correction simple
6. **B2, B6** : risque théorique faible (menu contextuel se ferme), correction optionnelle
