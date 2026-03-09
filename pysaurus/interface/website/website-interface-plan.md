# Plan : Interface Website (`pysaurus/interface/website/`)

## Principe

Site web classique multi-pages, rendu côté serveur avec Flask + Jinja2.
Formulaires HTML standards, quasi zéro JavaScript.
Pattern POST/Redirect/GET pour chaque action.

## Contexte / Motivation

- L'interface PySide6 est la principale, la plus à jour
- Les interfaces web actuelles (pywebview, qtwebview) + le frontend React sont en retard, lourds à maintenir (Node.js, Babel, SystemJS)
- Objectif : un fallback léger, pur Python, sans dépendance système, qui fonctionne dans n'importe quel navigateur
- À terme : supprimer pywebview, qtwebview et le frontend React

## Structure des fichiers

```
pysaurus/interface/website/
    __init__.py
    main.py              # Point d'entrée : crée l'app Flask, lance le serveur + webbrowser.open()
    app.py               # Factory Flask, définition des routes
    context.py           # WebsiteContext : façade vers Application/Database
    static/
        style.css        # Fichier CSS unique (zéro CSS inline)
    templates/
        base.html        # Layout commun (nav, flash messages)
        databases.html   # Liste/ouverture/création de databases
        videos.html      # Tableau paginé de vidéos + recherche/tri/groupes
        video_detail.html  # Détail d'une vidéo + édition propriétés
        properties.html  # Gestion des types de propriétés
```

## Accès au backend

Accès direct aux couches (comme AppContext en PySide6), PAS via le système de proxy GuiAPI :

```
WebsiteContext
    .application        → Application
    .database           → AbstractDatabase
    .ops                → DatabaseOperations (db.ops)
    .algos              → DatabaseAlgorithms (db.algos)
    .provider           → AbstractVideoProvider (db.provider)
```

Tout est synchrone : la requête HTTP bloque jusqu'à ce que l'opération backend soit terminée.

Fichier de référence pour le pattern : `pysaurus/interface/pyside6/app_context.py`

## Pages et routes

### 1. Databases (`/`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/` | GET | Liste des databases | `app.get_database_names()` |
| `/open` | POST | Ouvrir une database | `app.open_database_from_name(name)` |
| `/create` | POST | Créer une database | `app.new_database(name, folders)` |
| `/delete` | POST | Supprimer une database | `app.delete_database_from_name(name)` |

Après ouverture → redirection vers `/videos`.

### 2. Videos (`/videos`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/videos` | GET | Liste paginée | `provider.get_current_state(page_size, page)` |
| `/videos/search` | POST → redirect GET | Rechercher | `provider.set_search(text, cond)` |
| `/videos/sort` | POST → redirect GET | Trier | `provider.set_sort(sorting)` |
| `/videos/group` | POST → redirect GET | Grouper | `provider.set_groups(field, ...)` |

Paramètres via query params : `?page=1&page_size=20&q=...&sort=...`

Tableau HTML : miniature, titre, durée, taille, résolution, statut.

### 3. Détail vidéo (`/video/<video_id>`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/video/<id>` | GET | Afficher détail | `db.get_videos(where={...})` |
| `/video/<id>/properties` | POST | Modifier propriétés | `db.video_entry_set_tags(...)` |
| `/video/<id>/toggle-watched` | POST | Basculer "vu" | `ops.mark_as_read(id)` |
| `/video/<id>/rename` | POST | Renommer | `ops.change_video_file_title(...)` |
| `/video/<id>/delete` | POST | Supprimer | `ops.delete_video(id)` |

### 4. Propriétés (`/properties`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/properties` | GET | Liste + formulaire création | `db.get_prop_types()` |
| `/properties/create` | POST | Créer | `db.prop_type_add(...)` |
| `/properties/<name>/rename` | POST | Renommer | `db.prop_type_set_name(...)` |
| `/properties/<name>/delete` | POST | Supprimer | `db.prop_type_del(...)` |

### 5. Miniatures (`/thumbnail/<video_id>`)

Route dédiée renvoyant le JPEG binaire. Utilisée via `<img src="/thumbnail/42">`.

## Intégration au point d'entrée

Ajouter `"website"` dans `pysaurus/__main__.py` :
```
uv run -m pysaurus website   # → Flask + webbrowser.open("http://localhost:PORT")
```

## Séquence d'implémentation

1. **Phase 1 - Squelette** : main.py, context.py, app.py, base.html, databases.html, modification de __main__.py
2. **Phase 2 - Videos** : videos.html, pagination, recherche, tri, route miniatures
3. **Phase 3 - Détail vidéo** : video_detail.html, édition propriétés, actions
4. **Phase 4 - Propriétés** : properties.html, CRUD
5. **Phase 5 - Raffinement** : groupement, filtrage par source, CSS

## Règles de bonne pratique

- **HTML5 à 100%** : doctype `<!DOCTYPE html>`, attributs natifs (`required`, `placeholder`, `pattern`, `autofocus`, etc.), validation côté navigateur quand possible.
- **Tags sémantiques HTML5** : utiliser au maximum les tags pertinents (`<nav>`, `<main>`, `<article>`, `<section>`, `<header>`, `<footer>`, `<aside>`, `<figure>`, `<details>/<summary>`, `<fieldset>/<legend>`, `<thead>/<tbody>`, etc.) pour donner du sens au HTML et faciliter le ciblage CSS.
- **Zéro CSS inline** : tout le CSS dans un fichier dédié unique (`static/style.css`). Cibler les éléments via sélecteurs d'éléments (`nav a`, `main table`, `form fieldset`...) et n'ajouter des classes que quand le sélecteur d'élément ne suffit pas. Jamais de `style="..."` dans le HTML.

## Points notables

- **Pas de dialogue fichier** : chemins de dossiers saisis en texte
- **Opérations longues** : bloquantes pour le MVP. Améliorable avec SSE ou polling
- **État du provider** : persiste en mémoire. Alternative : reconstruire depuis query params à chaque requête
- **Mono-thread** : suffisant (un seul utilisateur local)
- **Pas de Node.js, pas de build step** : templates HTML modifiables directement
