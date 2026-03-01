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

### Problèmes backend (notifications manquantes)

| ID | Feature concernée | Description |
|----|------------------|-------------|
| P1 | `mark_as_watched` | Ne notifie pas le provider (champs `watched`, `date_entry_opened`) |
| P2 | `video_entry_del` | Ne notifie pas le provider |
| P3 | `video_entry_set_tags` | Ne notifie pas le provider pour les propriétés modifiées |
| P4 | `delete_property_values` | Pas de notification provider après suppression |
| P5 | `prop_type_del` | Groupement incohérent si groupé par la propriété supprimée |
| P6 | `change_video_file_title` | `video_entry_set_filename` ne notifie pas le provider |

### Problèmes UI PySide6

| ID | Description |
|----|-------------|
| U1 | `open_from_server` (VLC) : pas de refresh après ouverture |
| U2 | `mark_as_read` : notification provider manuelle (fragile) |
| U3 | Suppression batch : pas de `to_save()` pour grouper les sauvegardes |
| U4 | `apply_on_prop_value` non implémenté |

### Problèmes de blocage / double-exécution

| ID | Méthode | Risque | Description |
|----|---------|--------|-------------|
| B1 | `properties_page._on_create()` | Haut | Bouton persistant, double-clic crée deux propriétés |
| B2 | `videos_page._toggle_watched()` | Haut (théorique) | Aucune protection, toggle double = retour état initial |
| B3 | `PropertyValuesDialog` boutons internes | Moyen | Delete/modifiers sans désactivation après confirmation |
| B4 | `VideoPropertiesDialog` bouton OK | Moyen | Double-clic rapide avant fermeture du dialog |
| B5 | `databases_page._on_db_open()` | Moyen | Signal émis sans protection, double-clic naturel |
| B6 | `properties_page._on_convert()` | Moyen (théorique) | Toggle double après confirmation |
| B7 | `_on_confirm_unique_moves()` | Moyen | Bouton persistant sans désactivation |

### Features manquantes

| ID | Feature |
|----|---------|
| M1 | `apply_on_prop_value` (normalisation de valeurs) |
| M2 | i18n / sélection de langue |
