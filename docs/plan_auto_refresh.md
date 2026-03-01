# Plan : Remplacement des refresh() manuels par un système automatique

## Contexte

L'interface PySide6 contient **44 appels à `refresh()`** répartis dans 4 fichiers. Ces appels sont fragiles : en oublier un signifie que l'UI ne reflète plus l'état interne. Ce plan vise à remplacer les refresh manuels liés aux changements d'état backend par un mécanisme automatique basé sur les notifications.

## Analyse

### Répartition des refresh()

| Fichier | Total | Cat. A (backend) | Cat. B (UI pur) |
|---------|-------|-------------------|-----------------|
| videos_page.py | 34 | 29 | 5 |
| properties_page.py | 7 | 7 | 0 |
| main_window.py | 3 | 3 | 0 |
| databases_page.py | 0 | 0 | 0 |
| **Total** | **44** | **39 (89%)** | **5 (11%)** |

- **Catégorie A** : refresh après un changement d'état backend (écriture DB, changement de paramètre provider). Automatisable.
- **Catégorie B** : refresh après un changement UI pur (pagination, toggle vue). Doit rester manuel.

### Infrastructure de notification existante

Le système de notification est déjà en place :

```
Backend (thread)
  → notifier.notify(notification)
    → Information queue (thread-safe)
      → GuiAPI._notification_callback()
        → PySide6API._notify()
          → AppContext._notification_from_thread (signal interne, QueuedConnection)
            → AppContext._process_notification() (main thread)
              → notification_received.emit(notification)  (signal public)
              → handler (ProcessPage) si défini
```

Signaux publics existants dans AppContext : `database_ready`, `notification_received`, `operation_done`, `operation_cancelled`, `job_started`, `job_progress`, etc.

### Deux sources de changements

1. **Écritures DB** (delete video, set tags, create prop type, etc.)
   - Déjà notifiées via `_notify_fields_modified()` pour la plupart
   - Sauf les problèmes P1-P6 identifiés dans `audit_state_effects.md`

2. **Changements provider** (set_groups, set_search, set_sources, set_sorting, set_group, classifier_*)
   - Pas de notification aujourd'hui : ce sont des setters synchrones appelés par l'UI
   - La façade AppContext peut émettre un signal après chaque appel

### Difficultés à gérer

1. **Batching** : `_delete_selected()` supprime N vidéos en boucle → N notifications potentielles. Solution : coalescer les refresh via `QTimer.singleShot(0, ...)` ou flag `_refresh_pending`.

2. **Pagination** : la plupart des refresh catégorie A sont précédés de `self.page_number = 0`. Le mécanisme automatique doit aussi reset la pagination quand c'est approprié.

3. **Dialogs modaux** : `VideoPropertiesDialog` et `PropertyValuesDialog` font des changements backend pendant qu'ils sont ouverts. Le refresh ne doit pas se déclencher sous le dialog — suspendre et reprendre après fermeture.

## Plan d'implémentation

### Étape 1 : Signal `state_changed` dans AppContext

Ajouter un signal Qt `state_changed` dans AppContext, émis automatiquement après chaque méthode façade qui modifie l'état backend (écriture DB ou setter provider). Les pages se connectent à ce signal et appellent leur `refresh()`.

À ce stade, les refresh manuels restent en place (double refresh temporaire mais sans risque). Cela permet de valider le mécanisme avant de supprimer les refresh manuels.

### Étape 2 : Suppression des refresh() manuels de catégorie A

Supprimer les 39 refresh manuels de catégorie A un par un, en vérifiant que le refresh automatique fonctionne correctement dans chaque cas. Garder les 5 refresh de catégorie B.

Gérer les cas particuliers :
- Batching pour les opérations en boucle
- Reset de pagination automatique
- Suspension pendant les dialogs modaux

### Étape 3 : Correction des problèmes P1-P6

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
