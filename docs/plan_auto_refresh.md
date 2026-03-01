# Plan : Remplacement des refresh() manuels par un système automatique

## Contexte

L'interface PySide6 contenait **44 appels à `refresh()`** répartis dans 4 fichiers. Ces appels étaient fragiles : en oublier un signifiait que l'UI ne reflétait plus l'état interne. Ce plan vise à remplacer les refresh manuels liés aux changements d'état backend par un mécanisme automatique basé sur un signal `state_changed`.

## Analyse initiale

### Répartition des refresh() (avant modifications)

| Fichier | Total | Cat. A (backend) | Cat. B (UI pur) |
|---------|-------|-------------------|-----------------|
| videos_page.py | 34 | 29 | 5 |
| properties_page.py | 7 | 7 | 0 |
| main_window.py | 3 | 3 | 0 |
| databases_page.py | 0 | 0 | 0 |
| **Total** | **44** | **39 (89%)** | **5 (11%)** |

- **Catégorie A** : refresh après un changement d'état backend (écriture DB, changement de paramètre provider). Automatisable.
- **Catégorie B** : refresh après un changement UI pur (pagination, toggle vue). Doit rester manuel.

### Deux sources de changements

1. **Écritures DB** (delete video, set tags, create prop type, etc.)
2. **Changements provider** (set_groups, set_search, set_sources, set_sorting, set_group, classifier_*)

### Difficultés identifiées

1. **Batching** : `_delete_selected()` supprime N vidéos en boucle → N émissions potentielles.
2. **Pagination** : la plupart des refresh cat. A sont précédés de `self.page_number = 0`.
3. **Dialogs modaux** : `VideoPropertiesDialog` et `PropertyValuesDialog` font des changements backend pendant qu'ils sont ouverts.

## Plan d'implémentation

### Étape 1 : Signal `state_changed` dans AppContext ✅

Signal Qt `state_changed` ajouté dans AppContext, émis après chaque méthode façade mutante. `MainWindow._on_state_changed()` rafraîchit la page active.

### Étape 2 : Suppression des refresh() manuels de catégorie A ✅

**35 refresh manuels cat. A supprimés** (28 dans `videos_page.py`, 7 dans `properties_page.py`).

Cas multi-émissions résolus par 4 nouvelles méthodes dédiées dans AppContext :

| Méthode | Remplace | Émissions évitées |
|---------|----------|-------------------|
| `delete_video_entries(video_ids)` | boucle de `delete_video_entry` | N → 1 |
| `toggle_watched(video_id)` | `mark_as_read` + `notify_attributes_modified` | 2 → 1 |
| `set_random_video_search(video_id)` | `reset_grouping_and_classifier` + `set_search` | 2 → 1 |
| `query_on_view(selector_dict, op, *args)` | `apply_on_view` pour les lectures | 1 → 0 (lecture seule) |

### État actuel des refresh()

| Fichier | Restants | Nature |
|---------|----------|--------|
| videos_page.py | 7 | Cat. B : pagination (5), toggle show-only-selected (1), changement taille de page (1) |
| properties_page.py | 0 | — |
| main_window.py | 6 | Auto-refresh `_on_state_changed` (3) + navigation de page (3) |
| **Total** | **13** | Tous nécessaires (UI pur ou infrastructure auto-refresh) |

### Étape 3 : Correction des problèmes P1-P6 (à faire)

Corriger les notifications manquantes dans le backend (identifiées dans `audit_state_effects.md`). Grâce au système automatique, ces corrections se refléteront instantanément dans l'UI sans toucher au code PySide6.

| ID | Correction |
|----|-----------|
| P1 | Ajouter `_notify_fields_modified(["watched", "date_entry_opened"])` dans `mark_as_watched` |
| P2 | Ajouter `provider.delete(video_id)` dans `video_entry_del` |
| P3 | Ajouter `_notify_fields_modified(props)` dans `video_entry_set_tags` |
| P4 | Ajouter `_notify_fields_modified([name])` dans `delete_property_values` |
| P5 | Réinitialiser le groupement si groupé par la propriété supprimée dans `prop_type_del` |
| P6 | Ajouter notification dans `video_entry_set_filename` |

## Bénéfices attendus

- **Maintenabilité** : plus besoin de penser à ajouter un refresh après chaque opération
- **Fiabilité** : impossible d'oublier un refresh si le signal est émis automatiquement
- **Extensibilité** : toute nouvelle page ou widget peut se connecter au signal
- **Cohérence** : l'UI reflète toujours l'état réel du backend
