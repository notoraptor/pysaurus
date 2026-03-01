# Rapport d'audit de l'interface Pysaurus

## Ordre de lecture

Lire les documents dans cet ordre :

1. **[todo.md](todo.md)** — Le cahier des charges de l'audit (contexte et objectifs)

2. **[audit_backend_methods.md](audit_backend_methods.md)** — *Point 2* : inventaire complet des 81 méthodes publiques des 4 classes backend (AbstractDatabase, DatabaseOperations, DatabaseAlgorithms, AbstractVideoProvider)

3. **[audit_api_features.md](audit_api_features.md)** — *Points 1 + 3* : les 56 features exposées par FeatureAPI/GuiAPI, chacune mappée à ses méthodes backend. Identifie aussi les méthodes backend qui ne sont pas directement exposées par l'API.

4. **[audit_pyside6_coverage.md](audit_pyside6_coverage.md)** — *Point 4* : couverture de PySide6 par rapport aux features API. 51/54 features pertinentes couvertes (94%). Identifie 3 features manquantes et les appels directs de PySide6 sans équivalent API.

5. **[audit_state_effects.md](audit_state_effects.md)** — *Point 5* : pour chaque feature, analyse de l'état qui change en backend et de ce qui doit se mettre à jour dans l'UI. Identifie 6 problèmes de notification provider (P1-P6), 4 problèmes UI PySide6 (U1-U4), et 2 features manquantes (M1-M2).

6. **[audit_blocking.md](audit_blocking.md)** — Caractère bloquant des opérations et protection contre les double-exécutions. Analyse chaque handler PySide6 pour déterminer s'il est correctement protégé contre les double-clics et les appels multiples. Identifie 7 problèmes (B1-B7) classés par priorité.

7. **[plan_auto_refresh.md](plan_auto_refresh.md)** — Plan pour remplacer les 39 refresh() manuels (sur 44) par un système automatique basé sur un signal `state_changed` dans AppContext. Trois étapes : signal automatique, suppression des refresh manuels, correction des notifications backend P1-P6.

## Résumé des problèmes identifiés

Tous les problèmes identifiés ont été résolus (corrigés ou classés non-problèmes).

### Problèmes backend (notifications manquantes)

| ID | Feature concernée | Description | Statut |
|----|------------------|-------------|--------|
| P1 | `mark_as_watched` / `mark_as_read` | Ne notifiaient pas le provider | **Corrigé** |
| P2 | `video_entry_del` | Appelle déjà `provider.delete()` + `_notify_fields_modified` | Non-problème |
| P3 | `video_entry_set_tags` (SQL) | Ne notifiait pas le provider | **Corrigé** |
| P4 | `delete_property_values` | Pas de notification provider après suppression | **Corrigé** |
| P5 | `prop_type_del` | Groupement incohérent si groupé par la propriété supprimée | **Corrigé** |
| P6 | `change_video_file_title` | `video_entry_set_filename` appelle déjà `_notify_fields_modified` | Non-problème |

### Problèmes UI PySide6

| ID | Description | Statut |
|----|-------------|--------|
| U1 | `open_video` / `open_from_server` : pas de `state_changed` après ouverture | **Corrigé** |
| U2 | `toggle_watched` : appel redondant à `manage_attributes_modified` | **Corrigé** |
| U3 | Suppression batch : pas de `to_save()` pour grouper les sauvegardes | **Corrigé** |
| U4 | `apply_on_prop_value` supposé non implémenté | Non-problème (déjà dans `PropertyValuesDialog`) |

### Problèmes de blocage / double-exécution

| ID | Méthode | Risque | Statut |
|----|---------|--------|--------|
| B1 | `properties_page._on_create()` | Haut | **Corrigé** — bouton désactivé pendant l'exécution |
| B2 | `videos_page._toggle_watched()` | Théorique | Non-problème — menu contextuel se ferme au premier clic |
| B3 | `PropertyValuesDialog` boutons internes | Moyen | **Corrigé** — boutons désactivés pendant l'opération |
| B4 | `VideoPropertiesDialog` bouton OK | Moyen | **Corrigé** — bouton OK désactivé dans `_on_accept()` |
| B5 | `databases_page._on_db_open()` | Moyen | **Corrigé** — guard dans `_run_process()` |
| B6 | `properties_page._on_convert()` | Théorique | Non-problème — via menu contextuel, risque faible |
| B7 | `_on_confirm_unique_moves()` | Moyen | **Corrigé** — bouton désactivé pendant l'exécution |

### Features manquantes

| ID | Feature | Statut |
|----|---------|--------|
| M1 | `apply_on_prop_value` (normalisation de valeurs) | Non-problème — déjà accessible via `PropertyValuesDialog` |
| M2 | i18n / sélection de langue | Ignoré — le système des langages doit être entièrement repensé |
