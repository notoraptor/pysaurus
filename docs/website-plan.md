# Plan : Interface Flask (`pysaurus/interface/flask/`)

## Principe

Site web classique multi-pages, rendu côté serveur avec Flask + Jinja2.
Formulaires HTML standards, quasi zéro JavaScript (sauf confirmations de suppression et page de progression).
Pattern POST/Redirect/GET pour chaque action.

## Contexte / Motivation

- L'interface PySide6 est la principale, la plus à jour
- Les interfaces web actuelles (pywebview, qtwebview) + le frontend React sont en retard, lourds à maintenir (Node.js, Babel, SystemJS)
- Objectif : un fallback léger, pur Python, sans dépendance système, qui fonctionne dans n'importe quel navigateur
- À terme : supprimer pywebview, qtwebview et le frontend React

## Structure des fichiers

```
pysaurus/interface/flask/
    __init__.py
    main.py              # Point d'entrée : crée l'app Flask, lance le serveur + webbrowser.open()
    app.py               # Factory Flask, définition des routes
    context.py           # FlaskContext : façade vers Application/Database
    static/
        style.css        # Fichier CSS unique (zéro CSS inline)
    templates/
        base.html        # Layout commun (nav, flash messages)
        databases.html   # Liste/ouverture/création de databases
        videos.html      # Tableau paginé de vidéos + recherche/tri/groupes
        video_detail.html  # Détail d'une vidéo + édition propriétés
        properties.html  # Gestion des types de propriétés
        sources.html     # Gestion des dossiers sources
```

## Accès au backend

Accès direct aux couches (comme AppContext en PySide6), PAS via le système de proxy GuiAPI :

```
FlaskContext
    .application        → Application
    .database           → AbstractDatabase
    .ops                → DatabaseOperations (db.ops)
    .algos              → DatabaseAlgorithms (db.algos)
```

`FlaskContext` est un **singleton de module** : instancié une seule fois dans `context.py` et importé par `app.py`. C'est le pattern le plus simple pour un serveur mono-utilisateur. Pas besoin de `flask.g` (qui est per-request) ni d'attribut sur l'app Flask.

Pas de `ViewContext` persistant en mémoire. L'état de la vue (recherche, tri, groupement, sources, page) est reconstruit à chaque requête depuis les query params de l'URL.

Les opérations courtes sont synchrones (la requête HTTP bloque). Les opérations longues (`algos.update()`, `algos.ensure_miniatures()`, etc.) sont déléguées à un thread secondaire avec suivi de progression (voir section « Opérations longues »).

Fichier de référence pour le pattern : `pysaurus/interface/pyside6/app_context.py`

## Pages et routes

### 1. Databases (`/`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/` | GET | Liste des databases | `app.get_database_names()` |
| `/open` | POST | Ouvrir une database | `app.open_database_from_name(name)` |
| `/create` | POST | Créer une database | `app.new_database(name, folders)` |
| `/delete` | POST | Supprimer une database (avec confirmation JS) | `app.delete_database_from_name(name)` |
| `/close` | POST | Fermer la database courante | `context.close_database()` |

Après ouverture → redirection vers `/videos`. Après fermeture → redirection vers `/`.

La barre de navigation (`base.html`) affiche le nom de la database courante et un bouton « Fermer » quand une database est ouverte. Pour changer de database, l'utilisateur ferme la courante puis en ouvre une autre.

### 2. Videos (`/videos`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/videos` | GET | Liste paginée | `db.query_videos(view, page_size, page_number)` |
| `/videos/search` | POST → redirect GET | Rechercher | `view.set_search(text, cond)` |
| `/videos/sort` | POST → redirect GET | Trier | `view.set_sort(sorting)` |
| `/videos/group` | POST → redirect GET | Grouper | `view.set_grouping(field, is_property, sorting, reverse, allow_singletons)` |

État de la vue via query params : `?page=1&page_size=20&q=...&cond=and&sort=...&group_field=...&sources=...`

Pour chaque requête GET sur `/videos`, un `ViewContext` éphémère est construit depuis les query params, passé à `db.query_videos()`, puis jeté.

Tableau HTML : miniature, titre, durée, taille, résolution, statut (vu/non vu).

### 3. Détail vidéo (`/video/<video_id>`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/video/<id>` | GET | Afficher détail | `db.get_videos(where={"video_id": id})` |
| `/video/<id>/properties` | POST | Modifier propriétés | `db.video_entry_set_tags(video_id, properties)` |
| `/video/<id>/toggle-watched` | POST | Basculer "vu" | `ops.mark_as_read(video_id)` |
| `/video/<id>/rename` | POST | Renommer | `ops.change_video_file_title(video_id, new_title)` |
| `/video/<id>/delete` | POST | Supprimer définitivement (avec confirmation JS) | `ops.delete_video(video_id)` |
| `/video/<id>/trash` | POST | Mettre à la corbeille (avec confirmation JS) | `ops.trash_video(video_id)` |
| `/video/<id>/play` | POST | Ouvrir dans le lecteur système + marquer comme vu | `ops.open_video(video_id)` |

**Note sur les propriétés multi-valuées** : l'édition de propriétés de type `str` avec valeurs multiples via un formulaire HTML pur est limitée en ergonomie. En phase 3, une implémentation basique suffit (un `<textarea>` avec une valeur par ligne, ou un `<select multiple>`). En phase 7, un peu de JS pourra être ajouté pour permettre l'ajout/suppression dynamique de valeurs (boutons +/−) sans rechargement de page.

### 4. Propriétés (`/properties`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/properties` | GET | Liste + formulaire création | `db.get_prop_types()` |
| `/properties/create` | POST | Créer | `db.prop_type_add(name, prop_type, definition, multiple)` |
| `/properties/<name>/rename` | POST | Renommer | `db.prop_type_set_name(old_name, new_name)` |
| `/properties/<name>/delete` | POST | Supprimer (avec confirmation JS) | `db.prop_type_del(name)` |

### 5. Sources (`/sources`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/sources` | GET | Liste des dossiers sources | `db.get_folders()` |
| `/sources/update` | POST | Modifier les dossiers | `ops.set_folders(folders)` |

Chemins de dossiers saisis en texte (pas de dialogue fichier). La page affiche la liste actuelle des dossiers et un formulaire pour les modifier.

Les sources servent aussi au filtrage dans `/videos` : le query param `sources` encode les chemins sélectionnés, passés à `view.set_sources(paths)` lors de la construction du `ViewContext` éphémère.

### 6. Miniatures (`/thumbnail/<video_id>`)

Route dédiée renvoyant le JPEG binaire. Utilisée via `<img src="/thumbnail/42">`.

Si la miniature n'existe pas pour une vidéo, renvoyer un placeholder (image par défaut intégrée dans `static/`).

## Sécurité CSRF

Protection CSRF activée dès le départ via `flask-wtf` (dépendance légère). Même sur `127.0.0.1`, un site malveillant visité dans le même navigateur pourrait envoyer un POST vers `http://127.0.0.1:PORT/video/42/delete` — l'écoute locale ne protège pas contre les requêtes cross-origin.

Mise en place :
- `CSRFProtect(app)` dans la factory Flask
- `{{ form.hidden_tag() }}` ou `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` dans chaque formulaire POST
- L'endpoint JSON `/operation/status` (GET) n'est pas concerné

Le serveur Flask doit écouter uniquement sur `127.0.0.1` (jamais `0.0.0.0`).

## Garde d'accès à la database

Toute route nécessitant une database ouverte (`/videos`, `/video/<id>`, `/properties`, `/sources`, `/operation/*`) doit vérifier que `context.database` n'est pas `None`. Si aucune database n'est ouverte, redirection vers `/` avec un message flash.

Implémentation recommandée : un décorateur `@require_database` appliqué aux routes concernées :

```python
def require_database(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if context.database is None:
            flash("Veuillez d'abord ouvrir une database.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper
```

De même, si une opération backend échoue (exception), l'erreur doit être capturée, affichée via `flash()`, et l'utilisateur redirigé vers la page précédente plutôt que de voir une page d'erreur 500. Implémentation recommandée : un décorateur `@handle_errors` réutilisable :

```python
def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            flash(str(e), "error")
            return redirect(request.referrer or url_for("index"))
    return wrapper
```

Les deux décorateurs se composent : `@require_database @handle_errors def my_route(): ...`

## Confirmations de suppression

Toute opération de suppression (database, vidéo, propriété) nécessite une confirmation utilisateur. On utilise un `onsubmit="return confirm('...')"` sur le formulaire.

## Opérations longues

Certaines opérations backend peuvent durer longtemps : `algos.update()` (scan des dossiers, extraction de métadonnées), `algos.ensure_miniatures()` (génération des miniatures), `algos.refresh()`. Le backend émet déjà des notifications de progression (`JobToDo(title, total)`, `JobStep(title, progress)`, `Done(title)`) pendant ces opérations.

### Stratégie choisie : thread secondaire + polling JS

1. **POST** `/operation/start` → lance l'opération dans un **thread secondaire**, stocke la progression dans une structure partagée alimentée par les `Notification` existantes, redirige vers la page de progression
2. **GET** `/operation/progress` → affiche une page avec barre de progression + ~6 lignes de JS qui interrogent le serveur périodiquement
3. **GET** `/operation/status` → retourne `{"percent": 45, "message": "Miniatures 45/100", "done": false}` (lecture de la structure partagée)
4. Quand le thread finit → `{"done": true, "redirect": "/videos"}`

```html
<progress id="bar" max="100"></progress>
<p id="status"></p>
<script>
(function poll() {
    fetch("/operation/status")
        .then(r => r.json())
        .then(data => {
            document.getElementById("bar").value = data.percent;
            document.getElementById("status").textContent = data.message;
            if (data.done) window.location = data.redirect;
            else setTimeout(poll, 1000);
        });
})();
</script>
```

### Mécanisme réutilisable

Le système d'opérations longues doit être **générique et réutilisable**, pas codé en dur pour `algos.update()`. D'autres opérations longues seront ajoutées à terme (recherche de similarité d'images via `imgsimsearch/`, `algos.ensure_miniatures()`, etc.). Le mécanisme doit donc :

- Accepter n'importe quel callable comme opération à exécuter dans le thread secondaire
- Capturer les `Notification` de progression de manière uniforme
- Permettre de spécifier l'URL de redirection à la fin de l'opération

```python
def start_operation(callable, redirect_url="/videos"):
    """Lance une opération longue dans un thread secondaire."""
    ...
```

### État serveur minimal

C'est le **seul état en mémoire** du serveur (tout le reste — vue, tri, recherche, sources — vit dans les query params). Cet état est :

- **Éphémère** : n'existe que pendant la durée de l'opération, puis nettoyé
- **Mono-instance** : une seule opération longue à la fois (cohérent avec le pattern `_run_process()` de PySide6 qui bloque toute interaction)
- **Non lié à la session** : si le navigateur se ferme et rouvre, l'opération tourne toujours et la page de progression retrouve l'état

### Pourquoi cette stratégie et pas une autre

**WebSockets** (bidirectionnel, serveur ↔ client) : éliminé. On n'a besoin que du sens serveur → client. Nécessite `flask-socketio`, un serveur ASGI ou eventlet, et plus de JS côté client. Overkill pour un utilisateur unique local.

**SSE — Server-Sent Events** (unidirectionnel, serveur → client) : éliminé. Technologie native du navigateur où le serveur envoie des événements en temps réel via une connexion HTTP longue maintenue ouverte. Côté client : `new EventSource("/url")` reçoit les messages automatiquement avec reconnexion intégrée. Côté serveur Flask : on retourne un `Response` avec `content-type: text/event-stream` et on `yield` des lignes `data: ...`. Élégant sur le papier, mais problème pratique : Flask WSGI est mono-thread — si l'opération longue bloque le thread, Flask ne peut pas simultanément envoyer les événements SSE. Il faut de toute façon un thread secondaire, et à ce stade le polling est plus simple pour un gain quasi nul (un seul utilisateur local).

**`<meta http-equiv="refresh">` (auto-refresh HTML)** : éliminé. Zéro JS mais flash blanc à chaque rechargement de page, mauvaise expérience.

**Polling JS** : retenu. ~6 lignes de JS, aucune dépendance, fonctionne avec Flask WSGI standard. Le thread secondaire fait le travail, Flask reste libre de servir les requêtes de polling. L'intervalle de 1 seconde est largement suffisant pour un utilisateur unique local.

## Intégration au point d'entrée

Ajouter `"flask"` dans `pysaurus/__main__.py` :
```
uv run -m pysaurus flask   # → Flask + webbrowser.open("http://localhost:PORT")
```

## Mode desktop (pywebview)

L'interface Flask peut aussi fonctionner comme application desktop via pywebview, sans aucune modification du code du site. Pywebview ouvre une fenêtre native contenant un navigateur qui pointe vers `http://localhost:PORT` — le site fonctionne identiquement dans pywebview et dans un vrai navigateur.

```python
server_thread = threading.Thread(target=flask_app.run, daemon=True)
server_thread.start()

window = webview.create_window("Pysaurus", "http://localhost:PORT")
webview.start()  # bloque jusqu'à fermeture de la fenêtre
# → le thread daemon Flask est tué automatiquement ici
```

Le thread Flask est un **daemon** : Python le tue automatiquement quand le processus principal se termine (fermeture de la fenêtre). Cependant, si une opération longue est en cours (écriture en base), une interruption brutale pourrait corrompre des données. Pour un arrêt propre :

```python
shutdown_event = threading.Event()

# Dans le thread d'opération longue, vérifier périodiquement :
if shutdown_event.is_set():
    return  # abandon propre

# À la fermeture de pywebview :
webview.start()  # bloque jusqu'à fermeture
shutdown_event.set()
# Attendre que l'opération en cours se termine (avec timeout)
if operation_thread and operation_thread.is_alive():
    operation_thread.join(timeout=5)
```

Le `shutdown_event` est partagé avec le mécanisme d'opérations longues. Si aucune opération n'est en cours, le daemon est tué immédiatement sans risque.

C'est beaucoup plus simple que l'interface pywebview actuelle, qui injecte un pont JS complexe (`pywebview.api.call`, `System.import`, interception de `console.log`). Ici, pywebview n'est qu'une fenêtre navigateur — zéro pont JS, zéro injection. **Une seule base de code** pour les deux modes (navigateur et desktop).

## Séquence d'implémentation

1. **Phase 1 - Squelette** : main.py, context.py, app.py, base.html, databases.html, modification de __main__.py
2. **Phase 2 - Videos** : videos.html, pagination, recherche, tri, route miniatures (+ placeholder).
   - **Dépendance phase 6** : l'ouverture d'une database déclenche normalement `algos.update()` et `algos.ensure_miniatures()`, qui sont des opérations longues. Tant que la phase 6 n'est pas implémentée, deux options :
     - **(a) Exécution bloquante** : lancer ces opérations de manière synchrone dans la requête POST `/open`. Acceptable pour les petites collections, mais risque de timeout HTTP pour les grosses.
     - **(b) Skip temporaire** : ne pas lancer `update()`/`ensure_miniatures()` à l'ouverture. L'utilisateur travaille avec les données existantes en base. Ces opérations seront débloquées en phase 6.
   - L'option **(b)** est recommandée : elle permet de développer et tester les pages sans blocage, et l'update sera disponible dès la phase 6.
3. **Phase 3 - Détail vidéo** : video_detail.html, édition propriétés (basique : `<textarea>` ou `<select multiple>` pour les propriétés multi-valuées), actions (delete, trash, toggle, rename)
4. **Phase 4 - Propriétés** : properties.html, CRUD
5. **Phase 5 - Sources** : sources.html, gestion des dossiers, filtrage par source dans `/videos`
6. **Phase 6 - Opérations longues** : mécanisme générique réutilisable (thread secondaire + polling JS), page de progression, endpoint `/operation/status`. Première utilisation : `algos.update()` et `algos.ensure_miniatures()` à l'ouverture d'une database. Ce mécanisme servira ensuite pour d'autres opérations (recherche de similarité d'images, etc.)
7. **Phase 7 - Raffinement** : groupement avancé, CSS, amélioration de l'édition des propriétés multi-valuées (ajout/suppression dynamique en JS)

## Règles de bonne pratique

- **HTML5 à 100%** : doctype `<!DOCTYPE html>`, attributs natifs (`required`, `placeholder`, `pattern`, `autofocus`, etc.), validation côté navigateur quand possible.
- **Tags sémantiques HTML5** : utiliser au maximum les tags pertinents (`<nav>`, `<main>`, `<article>`, `<section>`, `<header>`, `<footer>`, `<aside>`, `<figure>`, `<details>/<summary>`, `<fieldset>/<legend>`, `<thead>/<tbody>`, etc.) pour donner du sens au HTML et faciliter le ciblage CSS.
- **Zéro CSS inline** : tout le CSS dans un fichier dédié unique (`static/style.css`). Cibler les éléments via sélecteurs d'éléments (`nav a`, `main table`, `form fieldset`...) et n'ajouter des classes que quand le sélecteur d'élément ne suffit pas. Jamais de `style="..."` dans le HTML.

## Points notables

- **Pas de dialogue fichier** : chemins de dossiers saisis en texte
- **Mono-thread** : suffisant (un seul utilisateur local). Le seul thread secondaire est celui des opérations longues
- **Pas de Node.js, pas de build step** : templates HTML modifiables directement
- **JavaScript minimal** : uniquement pour les confirmations de suppression (`confirm()`) et la page de progression (polling `fetch`)
