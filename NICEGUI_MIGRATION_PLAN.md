# Plan de migration vers NiceGUI

Ce document décrit le plan pour réécrire l'interface graphique de Pysaurus avec NiceGUI, en remplacement de l'interface HTML+JavaScript actuelle.

## Contexte

L'interface actuelle (`pysaurus/interface/web/`) est codée en HTML+JavaScript (React-like) et communique avec le backend Python via `window.backend_call`. Cette architecture est complexe à maintenir (deux langages, synchronisation frontend/backend).

L'objectif est de créer une nouvelle interface 100% Python avec NiceGUI, potentiellement encapsulée dans une application desktop via PyTauri.

## Stack technique envisagée

| Composant | Technologie |
|-----------|-------------|
| Interface | NiceGUI |
| Desktop wrapper (optionnel) | PyTauri (pytauri-wheel) |
| État | Classe Python `AppState` |
| Backend | `GuiAPI` existant |

## Inventaire des fonctionnalités API

### FeatureAPI (feature_api.py)

| Catégorie | Méthodes |
|-----------|----------|
| **Base de données** | `get_database_names`, `create_database`, `open_database`, `delete_database`, `rename_database`, `close_database` |
| **Langues** | `get_language_names`, `set_language` |
| **Vidéos - Lecture** | `backend`, `open_video`, `open_random_video`, `open_from_server`, `playlist` |
| **Vidéos - Modification** | `rename_video`, `delete_video`, `delete_video_entry`, `mark_as_read`, `move_video_file`, `set_video_moved`, `confirm_move` |
| **Propriétés - Types** | `describe_prop_types`, `create_prop_type`, `remove_prop_type`, `rename_prop_type`, `convert_prop_multiplicity` |
| **Propriétés - Valeurs** | `set_video_properties`, `delete_property_values`, `replace_property_values`, `move_property_values`, `fill_property_with_terms`, `apply_on_prop_value` |
| **Vue - Sources** | `set_sources`, `set_video_folders` |
| **Vue - Groupement** | `set_group`, `set_groups`, `classifier_select_group`, `classifier_back`, `classifier_reverse`, `classifier_focus_prop_val`, `classifier_concatenate_path` |
| **Vue - Recherche/Tri** | `set_search`, `set_sorting` |
| **Vue - Actions batch** | `apply_on_view`, `confirm_unique_moves` |
| **Similarités** | `find_similar_videos`, `set_similarities` |
| **Utilitaires** | `clipboard`, `select_directory`, `select_file`, `open_containing_folder` |

### GuiAPI (gui_api.py)

| Méthode | Rôle |
|---------|------|
| `update_database` | Rafraîchir/scanner la BDD |
| `cancel_copy` | Annuler copie en cours |
| `close_app` | Fermer l'application |
| `_notify` | Callback notifications (à implémenter) |

## Architecture proposée

```
pysaurus/interface/nicegui/
├── __init__.py
├── main.py                 # Point d'entrée
├── app.py                  # Application NiceGUI + routing
├── state.py                # État global (classe AppState)
├── api_bridge.py           # Wrapper pour GuiAPI
│
├── pages/
│   ├── __init__.py
│   ├── databases_page.py   # Sélection/création BDD
│   ├── home_page.py        # Progression des jobs
│   ├── videos_page.py      # Page principale vidéos
│   └── properties_page.py  # Gestion des propriétés
│
├── components/
│   ├── __init__.py
│   ├── video_card.py       # Carte vidéo avec miniature
│   ├── video_grid.py       # Grille de vidéos
│   ├── group_panel.py      # Panneau de groupement
│   ├── search_bar.py       # Barre de recherche
│   ├── pagination.py       # Pagination
│   ├── source_tree.py      # Arborescence des sources
│   └── notifications.py    # Gestionnaire de notifications
│
├── dialogs/
│   ├── __init__.py
│   ├── confirm_dialog.py   # Confirmation générique
│   ├── search_dialog.py    # Recherche avancée
│   ├── sort_dialog.py      # Tri multi-critères
│   ├── group_dialog.py     # Configuration groupement
│   ├── property_edit.py    # Édition propriété (1 vidéo)
│   ├── batch_edit.py       # Édition batch (N vidéos)
│   ├── rename_dialog.py    # Renommage générique
│   └── move_dialog.py      # Déplacement vidéo
│
└── utils/
    ├── __init__.py
    ├── keyboard.py         # Gestion raccourcis
    └── formatters.py       # Formatage durée, taille, etc.
```

## Correspondance Pages / Fonctionnalités

### 1. DatabasesPage

Fonctionnalités :
- Liste des BDD existantes (`get_database_names`)
- Créer nouvelle BDD (`create_database` + `select_directory`)
- Ouvrir BDD (`open_database`)
- Supprimer BDD (`delete_database`)
- Renommer BDD (`rename_database`)
- Sélection langue (`get_language_names`, `set_language`)

### 2. HomePage (Progression)

Fonctionnalités :
- Affichage notifications temps réel (`_notify` callback)
- Barre de progression (notifications `JobStep`)
- Bouton annuler (`cancel_copy`)
- Callback `onReady` → redirection vers VideosPage

### 3. VideosPage (principale)

#### Panneau latéral
- Source tree (`set_sources`)
- Groupement (`set_groups`, `classifier_*`)
- Recherche rapide (`set_search`)
- Tri (`set_sorting`)

#### Zone centrale
- Grille vidéos (`backend` → videos)
- Pagination (`page_size`, `page_number`)
- Sélection multiple (`Selector`)

#### Actions vidéo (menu contextuel)
- Ouvrir (`open_video`, `open_from_server`)
- Ouvrir dossier (`open_containing_folder`)
- Renommer (`rename_video`)
- Déplacer (`move_video_file`)
- Supprimer (`delete_video`, `delete_video_entry`)
- Marquer lu (`mark_as_read`)
- Copier (`clipboard`)
- Éditer propriétés → dialog

#### Actions globales (toolbar)
- Rafraîchir BDD (`update_database`)
- Vidéo aléatoire (`open_random_video`)
- Playlist (`playlist`)
- Similarités (`find_similar_videos`)
- Édition batch → dialog

### 4. PropertiesPage

Fonctionnalités :
- Liste propriétés (`describe_prop_types`)
- Créer (`create_prop_type`)
- Renommer (`rename_prop_type`)
- Supprimer (`remove_prop_type`)
- Convertir unique/multiple (`convert_prop_multiplicity`)
- Éditer valeurs (`replace_property_values`, `delete_property_values`)

## Dialogs requis

| Dialog | Utilisation |
|--------|-------------|
| `confirm_dialog` | Confirmation suppression, actions irréversibles |
| `search_dialog` | Recherche avancée (AND/OR/EXACT/ID) |
| `sort_dialog` | Tri multi-critères (jusqu'à 5 champs) |
| `group_dialog` | Configuration groupement (champ, ordre, singletons) |
| `property_edit` | Édition propriétés d'une vidéo |
| `batch_edit` | Édition batch (interface 3-colonnes: enlever/actuel/ajouter) |
| `rename_dialog` | Renommage générique (vidéo, propriété, BDD) |
| `move_dialog` | Déplacement vidéo vers dossier |

## Raccourcis clavier à implémenter

| Raccourci | Action |
|-----------|--------|
| `Ctrl+T` | Sélectionner sources |
| `Ctrl+G` | Grouper vidéos |
| `Ctrl+F` | Rechercher |
| `Ctrl+S` | Trier |
| `Ctrl+P` | Gérer propriétés |
| `Ctrl+O` | Ouvrir vidéo aléatoire |
| `Ctrl+L` | Playlist |
| `Ctrl+R` | Recharger base |
| `Flèches` | Navigation pages/groupes |

## Estimation effort

| Partie | Complexité | Durée estimée |
|--------|------------|---------------|
| Structure + AppState + APIBridge | Simple | 1 jour |
| DatabasesPage | Simple | 1 jour |
| HomePage (notifications) | Moyen | 2 jours |
| VideosPage (grille + pagination) | Moyen | 3 jours |
| VideosPage (groupement + classifier) | Complexe | 4 jours |
| VideosPage (actions + menus) | Moyen | 2 jours |
| PropertiesPage | Simple | 2 jours |
| Dialogs (6-8) | Moyen | 4 jours |
| Raccourcis clavier | Simple | 1 jour |
| Tests + polish | — | 3 jours |
| **Total** | | **~23 jours** |

## Plan d'implémentation progressif

### Phase 1 : Validation de la stack (2-3 jours)
- [ ] Créer structure de base (`main.py`, `app.py`, `state.py`, `api_bridge.py`)
- [ ] Implémenter DatabasesPage minimal
- [ ] Implémenter HomePage avec notifications
- [ ] Tester avec/sans PyTauri

### Phase 2 : PropertiesPage (2 jours)
- [ ] Liste des propriétés
- [ ] CRUD complet
- [ ] Dialogs de renommage/conversion

### Phase 3 : VideosPage - Base (5 jours)
- [ ] Grille de vidéos avec miniatures
- [ ] Pagination
- [ ] Sélection simple/multiple
- [ ] Menu contextuel basique

### Phase 4 : VideosPage - Avancé (6 jours)
- [ ] Panneau sources (arborescence)
- [ ] Groupement simple
- [ ] Classifier (navigation imbriquée)
- [ ] Recherche et tri

### Phase 5 : Dialogs et finitions (5 jours)
- [ ] Tous les dialogs
- [ ] Édition batch (interface 3-colonnes)
- [ ] Raccourcis clavier
- [ ] Tests et corrections

## Notes techniques

### Communication avec le backend

NiceGUI permet d'appeler directement le code Python, contrairement à l'interface actuelle qui passe par `window.backend_call`. L'appel sera donc :

```python
# Ancienne approche (JS)
window.backend_call("open_video", [video_id])

# Nouvelle approche (NiceGUI)
api.open_video(video_id)
```

### Gestion de l'état

L'état sera centralisé dans une classe `AppState` :

```python
@dataclass
class AppState:
    current_page: str = "databases"
    database_name: str | None = None
    page_size: int = 20
    page_number: int = 0
    selected_videos: set[int] = field(default_factory=set)
    # ...
```

### Notifications temps réel

NiceGUI supporte les mises à jour temps réel via `ui.timer` ou les WebSockets intégrés. Le callback `_notify` de `GuiAPI` sera connecté pour pousser les notifications vers l'UI.

## Dépendances à ajouter

```toml
# pyproject.toml
dependencies = [
    # ... existant ...
    "nicegui>=2.0.0",
    # Optionnel pour desktop
    "pytauri>=0.8.0",
]
```

## Risques identifiés

| Risque | Mitigation |
|--------|------------|
| PyTauri trop jeune | Fallback sur mode navigateur NiceGUI |
| Performances grille vidéos | Virtualisation / lazy loading |
| Raccourcis clavier limités | `ui.keyboard` de NiceGUI |
| Interface 3-colonnes complexe | Composant custom dédié |