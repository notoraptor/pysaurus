# Design : Interface Flask (`pysaurus/interface/flask/`)

## Principe

Site web classique multi-pages, rendu côté serveur avec Flask + Jinja2.
Formulaires HTML standards, JavaScript minimal (confirmations de suppression, page de progression, édition de propriétés multi-valuées, navigation par groupes).
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
    context.py           # FlaskContext : façade vers Application/Database (attribut de classe)
    static/
        style.css        # Fichier CSS unique (zéro CSS inline)
    templates/
        base.html        # Layout commun (nav, flash messages)
        databases.html   # Liste/ouverture/création de databases
        videos.html      # Tableau paginé de vidéos + recherche/tri/groupes
        video_detail.html  # Détail d'une vidéo + édition propriétés
        properties.html  # Gestion des types de propriétés
        prop_values.html # Gestion des valeurs d'une propriété
        sources.html     # Gestion des dossiers sources
        operation_progress.html  # Barre de progression + polling JS
```

## Accès au backend

Accès direct aux couches (comme AppContext en PySide6), PAS via le système de proxy GuiAPI :

```
FlaskContext
    .application        -> Application
    .database           -> AbstractDatabase
    .ops                -> DatabaseOperations (db.ops)
    .algos              -> DatabaseAlgorithms (db.algos)
```

`FlaskContext` est stocké comme **attribut de classe** sur la classe elle-même (`FlaskContext.instance`), initialisé au démarrage dans `main.py`. C'est plus propre qu'un singleton de module (pas de problème si le module est ré-importé par le reloader de développement Flask). Les routes accèdent au contexte via `FlaskContext.instance`. Pas besoin de `flask.g` (qui est per-request) ni d'attribut sur l'app Flask.

Pas de `ViewContext` persistant en mémoire. L'état de la vue (recherche, tri, groupement, page) est reconstruit à chaque requête depuis les query params de l'URL.

Les opérations courtes sont synchrones (la requête HTTP bloque). Les opérations longues (`algos.refresh()`, etc.) sont déléguées à un thread secondaire avec suivi de progression (voir section « Opérations longues »).

## Pages et routes

### 1. Databases (`/`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/` | GET | Liste des databases | `app.get_database_names()` |
| `/open` | POST | Ouvrir une database | `app.open_database_from_name(name)` → redirection vers `/videos` |
| `/create` | POST | Créer une database | `app.new_database(name, folders)` puis `algos.refresh()` en opération longue |
| `/delete` | POST | Supprimer une database (avec confirmation JS) | `app.delete_database_from_name(name)` |
| `/close` | POST | Fermer la database courante | `context.close_database()` |
| `/rename` | POST | Renommer la database courante | `context.rename_database(new_name)` |

Après ouverture, redirection directe vers `/videos` (pas de refresh automatique, comme en PySide6). Après création, `algos.refresh()` est lancé comme opération longue (la base est vide, il faut scanner les dossiers). La mise à jour manuelle est disponible via le bouton « Mettre à jour la base » sur la page vidéos.

La barre de navigation (`base.html`) affiche le nom de la database courante et un bouton « Fermer » quand une database est ouverte.

### 2. Vidéos (`/videos`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/videos` | GET | Liste paginée | `db.query_videos(view, page_size, page_number)` |
| `/videos/search` | POST -> redirect GET | Rechercher | Redirige avec query params `q` et `cond` |
| `/videos/sort` | POST -> redirect GET | Trier | Redirige avec query param `sort` |
| `/videos/group` | POST -> redirect GET | Grouper | Redirige avec query params `group_field`, `group_is_property`, etc. |
| `/videos/random` | GET | Vidéo aléatoire | Redirige vers `/video/<id>` d'une vidéo aléatoire de la vue |
| `/videos/playlist` | GET | Télécharger une playlist XSPF | `create_xspf_playlist(filenames)` sur toutes les vidéos de la vue |

État de la vue via query params : `?page=1&page_size=20&q=...&cond=and&sort=...&group_field=...&group_is_property=0&group_sorting=field&group_reverse=0&group_singletons=1&group=0`

Pour chaque requête GET sur `/videos`, un `ViewContext` éphémère est construit depuis les query params (`_build_view()`), passé à `db.query_videos()`, puis jeté.

Tableau HTML : miniature, titre (lien vers détail), durée, taille, résolution, statut (vu/non vu). Les vidéos non trouvées sur le disque sont affichées avec une opacité réduite (`tr.not-found`).

#### Recherche, tri, groupement

Les contrôles de recherche, tri et configuration de groupement sont dans des sections `<details>/<summary>` repliables. Quand une recherche ou un groupement est actif, la section correspondante est ouverte par défaut.

La recherche supporte quatre modes : ET (tous les mots), OU (au moins un mot), expression exacte, et ID vidéo.

Le formulaire de groupement propose les champs vidéo (depuis `FIELD_MAP.allowed` dans `pysaurus/interface/common/common.py`) et les propriétés utilisateur dans des `<optgroup>` séparés. Un champ caché `group_is_property` est mis à jour via un `onchange` sur le `<select>` de champ, pour distinguer attributs vidéo et propriétés.

#### Navigation par groupes

Quand un groupement est actif, une barre de navigation s'affiche au-dessus du tableau :

- **Compteur** : « Groupe X/N » (index 1-based / total)
- **`<select>`** peuplé depuis `classifier_stats`, chaque `<option>` affiche « valeur (nombre) ». Le `onchange` soumet le formulaire pour naviguer vers le groupe sélectionné
- **Liens Préc./Suiv.** : simples `<a href="...">` avec le query param `group` incrémenté/décrémenté. Désactivés (texte sans lien) quand on est au premier/dernier groupe
- **Lien « Supprimer le groupement »** : lien vers `/videos` sans les query params `group_*`

### 3. Détail vidéo (`/video/<video_id>`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/video/<id>` | GET | Afficher détail | `db.get_videos(where={"video_id": id})` |
| `/video/<id>/properties` | POST | Modifier propriétés | `db.video_entry_set_tags(video_id, properties)` |
| `/video/<id>/toggle-watched` | POST | Basculer « vu » | `ops.mark_as_read(video_id)` |
| `/video/<id>/rename` | POST | Renommer | `ops.change_video_file_title(video_id, new_title)` |
| `/video/<id>/play` | POST | Ouvrir dans le lecteur système | `ops.open_video(video_id)` |
| `/video/<id>/trash` | POST | Mettre à la corbeille (avec confirmation JS) | `ops.trash_video(video_id)` |
| `/video/<id>/delete` | POST | Supprimer définitivement (avec confirmation JS) | `ops.delete_video(video_id)` |
| `/video/<id>/open-folder` | POST | Ouvrir le dossier contenant | `ops.locate_file(video_id)` |

La page affiche les informations de la vidéo (codec, résolution, FPS, date, etc.) dans un tableau, puis les actions (lire, ouvrir dossier, copier titre/chemin, renommer, supprimer). Les boutons « Copier le titre » et « Copier le chemin » utilisent `navigator.clipboard.writeText()` avec un feedback visuel « Copié ! » (~8 lignes de JS).

#### Édition des propriétés multi-valuées

Les propriétés booléennes utilisent un `<select>` (Oui/Non). Les propriétés scalaires utilisent un `<input type="text">`. Les propriétés multi-valuées utilisent des lignes dynamiques avec boutons +/− en JavaScript (~15 lignes) :

- Chaque valeur est un `<input type="text">` dans une ligne `.multi-value-row` avec un bouton « − » pour la supprimer
- Un bouton « + Ajouter » ajoute dynamiquement une nouvelle ligne
- Côté serveur, `request.form.getlist()` récupère toutes les valeurs du même champ

### 4. Propriétés (`/properties`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/properties` | GET | Liste + formulaire création | `db.get_prop_types()` |
| `/properties/create` | POST | Créer | `db.prop_type_add(name, prop_type, definition, multiple)` |
| `/properties/<name>/rename` | POST | Renommer | `db.prop_type_set_name(old_name, new_name)` |
| `/properties/<name>/toggle-multiple` | POST | Convertir single ↔ multiple | `db.prop_type_set_multiple(name, bool)` |
| `/properties/<name>/delete` | POST | Supprimer (avec confirmation JS) | `db.prop_type_del(name)` |
| `/properties/<name>/values` | GET | Liste des valeurs avec comptes | `db.videos_tag_get(name)` |
| `/properties/<name>/values/delete` | POST | Supprimer des valeurs (avec confirmation JS) | `algos.delete_property_values(name, values)` |
| `/properties/<name>/values/rename` | POST | Renommer une valeur | `algos.replace_property_values(name, [old], new)` |

Le formulaire de création accepte : nom, type (str/int/float/bool), multiple (checkbox), valeur par défaut, et énumération (valeurs séparées par des virgules, pour type str uniquement). Le paramètre `definition` passé à `prop_type_add` est soit un scalaire (valeur par défaut), soit une liste (énumération).

La page de gestion des valeurs (`/properties/<name>/values`) affiche toutes les valeurs distinctes d'une propriété, triées par nombre décroissant de vidéos. Chaque valeur peut être renommée (formulaire inline dans un `<details>`) ou supprimée (avec confirmation JS).

### 5. Sources (`/sources`)

| Route | Méthode | Action | Backend |
|---|---|---|---|
| `/sources` | GET | Liste des dossiers sources | `db.get_folders()` |
| `/sources/update` | POST | Modifier les dossiers | `ops.set_folders(folders)` |

Chemins de dossiers saisis dans un `<textarea>` (un par ligne), pas de dialogue fichier.

### 6. Miniatures

Les miniatures sont chargées en une seule requête SQL lors du rendu de la page, encodées en base64, et embarquées directement dans le HTML via des data URIs (`<img src="data:image/jpeg;base64,...">`).

- `FlaskContext.get_thumbnails_base64(video_ids)` retourne un `dict[int, str]` mappant chaque `video_id` à son data URI
- Sur `/videos`, tous les thumbnails de la page courante sont chargés d'un coup
- Sur `/video/<id>`, le thumbnail unique est passé au template

Pas de route `/thumbnail/<id>` séparée : tout est inline, ce qui élimine N requêtes HTTP supplémentaires et les problèmes de concurrence thread liés à skullite.

## Décorateurs de routes

Trois décorateurs réutilisables, composables entre eux :

### `@require_database`

Redirige vers `/` avec un message flash si aucune database n'est ouverte.

### `@require_no_operation`

Redirige vers `/operation/progress` si une opération longue est en cours. Ceci est cohérent avec le pattern PySide6 (`_run_process()` affiche une `ProcessPage` qui bloque toute interaction).

### `@handle_errors`

Capture les `ApplicationError` et les affiche via `flash()`, en redirigeant vers la page précédente. Les autres exceptions (bugs, `TypeError`, `AttributeError`, etc.) ne sont **pas attrapées** : elles remontent en erreur 500 avec le traceback dans les logs. C'est le même comportement que l'interface PySide6, où seules les `ApplicationError` sont affichées en warning.

Composition typique : `@require_database @require_no_operation @handle_errors`.

## Opérations longues

Certaines opérations backend peuvent durer longtemps : `algos.refresh()` (scan des dossiers, extraction de métadonnées, génération de miniatures), `DbSimilarVideos.find_similar_videos()` (recherche de vidéos visuellement similaires), `DbSimilarReencoded.find_similar_reencoded()` (détection de ré-encodages). Le backend émet des notifications de progression (`JobToDo`, `JobStep`, `End`) pendant ces opérations.

### Mécanisme : thread secondaire + polling JS

1. L'opération est lancée dans un **thread secondaire daemon** via `FlaskContext.start_operation(callable, redirect_url)`
2. Les notifications `JobToDo`/`JobStep`/`End` sont interceptées via `Information.handle_with()` et mettent à jour un `OperationState` partagé
3. La page `/operation/progress` affiche une barre `<progress>` + ~20 lignes de JS qui interrogent `/operation/status` toutes les secondes
4. `/operation/status` retourne `{"percent": 45, "message": "...", "done": false, "error": null, "redirect": "/videos"}`
5. Quand l'opération finit, le JS redirige automatiquement. En cas d'erreur, le message est affiché sur place

### Propriétés du mécanisme

- **Générique** : accepte n'importe quel callable + URL de redirection
- **Mono-instance** : une seule opération longue à la fois
- **Non lié à la session** : si le navigateur se ferme et rouvre, l'opération tourne toujours et la page de progression retrouve l'état

### État serveur minimal

L'`OperationState` est le **seul état en mémoire** du serveur (tout le reste — vue, tri, recherche — vit dans les query params). Cet état est éphémère : il n'existe que pendant la durée de l'opération.

### Pourquoi le polling et pas autre chose

- **WebSockets** (bidirectionnel, serveur ↔ client) : overkill, on n'a besoin que du sens serveur → client. Nécessite `flask-socketio`, un serveur ASGI ou eventlet, et plus de JS côté client
- **SSE — Server-Sent Events** (unidirectionnel, serveur → client) : technologie native du navigateur où le serveur envoie des événements en temps réel via une connexion HTTP longue maintenue ouverte. Côté client : `new EventSource("/url")` reçoit les messages automatiquement avec reconnexion intégrée. Côté serveur Flask : on retourne un `Response` avec `content-type: text/event-stream` et on `yield` des lignes `data: ...`. Élégant sur le papier, mais problème pratique : Flask WSGI est mono-thread — si l'opération longue bloque le thread, Flask ne peut pas simultanément envoyer les événements SSE. Il faut de toute façon un thread secondaire, et à ce stade le polling est plus simple pour un gain quasi nul (un seul utilisateur local)
- **`<meta http-equiv="refresh">`** (auto-refresh HTML) : zéro JS mais flash blanc à chaque rechargement de page, mauvaise expérience
- **Polling JS** : ~20 lignes de JS, aucune dépendance, fonctionne avec Flask WSGI standard. Le thread secondaire fait le travail, Flask reste libre de servir les requêtes de polling. L'intervalle de 1 seconde est largement suffisant pour un utilisateur unique local

## Modes de lancement

Deux modes de lancement, partageant le même code serveur et les mêmes templates :

### Mode navigateur (`flask`)

```
uv run -m pysaurus flask
```

Lance le serveur Flask, ouvre automatiquement le navigateur par défaut sur `http://127.0.0.1:5000`, puis bloque sur `app.run()`. L'utilisateur interagit via son navigateur. Le serveur tourne tant que le processus n'est pas interrompu (Ctrl+C).

### Mode desktop (`flaskview`)

```
uv run -m pysaurus flaskview
```

Lance le serveur Flask dans un **thread daemon**, puis ouvre une fenêtre native via `pywebview` pointant vers `http://127.0.0.1:5000`. `webview.start()` bloque jusqu'à la fermeture de la fenêtre. À la fermeture :
- Si une opération longue est en cours, on attend qu'elle finisse (timeout 5s) via `FlaskContext.wait_for_operation()` pour éviter une interruption pendant une écriture en base
- Le thread daemon Flask est tué automatiquement par Python à la sortie du processus

C'est beaucoup plus simple que l'interface pywebview actuelle (`using_pywebview/`), qui injecte un pont JS complexe. Ici, pywebview n'est qu'une fenêtre navigateur — zéro pont JS, zéro injection. **Une seule base de code** pour les deux modes.

### Code partagé

Les deux modes appellent `_init()` qui crée l'`Application`, initialise `FlaskContext.instance` et retourne l'app Flask. Le tout dans un contexte `Information()` pour les notifications.

## Règles de bonne pratique

- **HTML5 à 100%** : doctype `<!DOCTYPE html>`, attributs natifs (`required`, `placeholder`, `autofocus`, etc.), validation côté navigateur quand possible
- **Tags sémantiques HTML5** : `<nav>`, `<main>`, `<section>`, `<header>`, `<details>/<summary>`, `<fieldset>/<legend>`, `<thead>/<tbody>`, etc.
- **Zéro CSS inline** : tout le CSS dans `static/style.css`. Cibler les éléments via sélecteurs d'éléments (`nav a`, `main table`, `form fieldset`...) et n'ajouter des classes que quand le sélecteur d'élément ne suffit pas
- **Pas de dialogue fichier** : chemins de dossiers saisis en texte
- **Écoute locale uniquement** : le serveur Flask doit écouter sur `127.0.0.1` (jamais `0.0.0.0`) pour éviter d'exposer l'application sur le réseau
- **Mono-thread** : suffisant (un seul utilisateur local). Le seul thread secondaire est celui des opérations longues
- **Pas de Node.js, pas de build step** : templates HTML modifiables directement
- **JavaScript minimal** : uniquement pour les confirmations de suppression (`confirm()`), la page de progression (polling `fetch`), la navigation par groupes (`onchange`), l'édition de propriétés multi-valuées (boutons +/−), la sélection de vidéos (tout cocher/décocher + compteur), et la copie dans le presse-papiers (`navigator.clipboard`)
- **Confirmations de suppression** : toute opération de suppression (database, vidéo, propriété) utilise `onsubmit="return confirm('...')"` sur le formulaire pour demander une confirmation avant exécution

## Fonctionnalités non implémentées

- **Filtrage par source** dans `/videos` (query param `sources` + `view.set_sources()`) : prévu mais pas encore implémenté
- **Protection CSRF** : pas de `flask-wtf`, pas de tokens CSRF dans les formulaires. Le serveur écoute uniquement sur `127.0.0.1`, ce qui limite le risque. Cependant, même en écoute locale, un site malveillant visité dans le même navigateur pourrait envoyer un POST cross-origin vers `http://127.0.0.1:PORT/video/42/delete` — l'écoute locale ne protège pas contre les requêtes cross-origin. Une protection CSRF via `flask-wtf` (`CSRFProtect(app)` + `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` dans chaque formulaire POST) serait souhaitable à terme
