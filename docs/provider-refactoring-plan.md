# Plan de refactoring : Remplacer le VideoProvider par ViewContext + query_videos()

## Principe

Séparer le provider actuel (qui mélange état et calcul) en deux composants :

1. **`ViewContext`** — classe universelle de gestion des paramètres de vue (pur état, zéro dépendance DB)
2. **`AbstractDatabase.query_videos()`** — méthode abstraite stateless, implémentée par chaque backend

## ViewContext

Classe légère contenant les paramètres de la vue + logique de navigation.
Indépendante de la base de données, sérialisable, testable sans DB.

### Attributs

- `sources: list[list[str]]` — filtres de source (readable, found, etc.)
- `grouping: GroupDef` — configuration de groupement (field, is_property, sorting, reverse, allow_singletons)
- `classifier: list[str]` — chemin de classification (hiérarchie de valeurs de propriété)
- `group: int` — index du groupe sélectionné
- `search: SearchDef` — texte et condition de recherche
- `sorting: list[str]` — champs de tri

### Méthodes de mutation (avec cascade)

- `set_sources(paths)` — change les sources
- `set_grouping(field, is_property, sorting, reverse, allow_singletons)` — change le groupement, réinitialise classifier, group, search
- `set_group(group_id)` — change le groupe sélectionné
- `set_search(text, cond)` — change la recherche
- `set_sort(sorting)` — change le tri
- `classifier_select(value)` — ajoute une valeur au chemin classifier (prend une VALEUR, pas un index)
- `classifier_back()` — pop le dernier élément du chemin
- `classifier_reverse()` — inverse le chemin
- `reset()` — réinitialise tout aux valeurs par défaut

### Cascade de réinitialisation (logique actuelle de reset_parameters)

- Changer grouping → reset classifier, group, search
- Changer classifier → reset group
- Autres paramètres → pas de cascade

### Sérialisation

ViewContext doit être facilement sérialisable en :
- Query params (pour l'interface website)
- Session Flask
- JSON

## AbstractDatabase.query_videos()

```python
@abstractmethod
def query_videos(self, view: ViewContext,
                 page_size: int, page_number: int,
                 selector: Selector = None) -> VideoSearchContext:
    ...
```

- Prend le ViewContext (ou ses champs) en entrée
- Retourne un VideoSearchContext complet (vidéos, groupes, stats, pagination, view_indices)
- Stateless : pas d'état interne, tout vient des paramètres
- Chaque backend l'implémente comme il veut

### Implémentation SQL (PysaurusCollection)

Délègue à `video_mega_group()` qui est déjà une fonction stateless.

## Flux d'utilisation

```
Interface (AppContext / Flask / autre)
    │
    ├── possède un ViewContext (état de la vue)
    ├── possède _last_result: VideoSearchContext (dernier résultat)
    │
    ├── Mutation des paramètres → ViewContext.set_*()
    ├── Calcul de la vue → db.query_videos(view_context, page_size, page)
    │   └── retourne VideoSearchContext
    │
    ├── Navigation classifier :
    │   ├── value = _last_result.result_groups[group_id].value
    │   ├── view_context.classifier_select(value)  ← valeur, pas index
    │   └── db.query_videos(view_context, ...)
    │
    ├── Accès aux view_indices :
    │   └── _last_result.view_indices (stockés dans le dernier résultat)
    │
    ├── Random video :
    │   └── random.choice(_last_result.view_indices)
    │
    └── Apply on view :
        └── L'interface boucle sur _last_result.view_indices
```

## Ce que ça remplace

### Supprimé

- `AbstractVideoProvider` (~263 lignes)
- `SaurusProvider` (~180 lignes)
- `JsonDatabaseVideoProvider` (~570 lignes) — si jsdb supprimé avant
- Attribut `provider` sur `AbstractDatabase`
- Proxy `FromView` dans FeatureAPI
- `MockProvider` dans les tests

### Ajouté

- `ViewContext` (~100 lignes estimées)
- `AbstractDatabase.query_videos()` — méthode abstraite + implémentation SQL
- Logique de navigation dans chaque interface (AppContext, Flask routes, etc.)

## Impact sur les fichiers existants

### PySide6 AppContext (~21 appels provider à migrer)

Tous les appels `self._provider.*` deviennent :
- Mutations → `self.view.*` (ViewContext)
- Requêtes → `self.db.query_videos(self.view, ...)`
- view_indices → `self._last_result.view_indices`

### FeatureAPI / GuiAPI

- Supprimer les proxies `FromView`
- Les features qui modifient la vue modifient un ViewContext
- Les features qui lisent la vue appellent `query_videos()`

### DatabaseOperations

- Supprimer `_notify_fields_modified()` lié au provider
- Pas besoin de `query_videos()` ici si c'est sur AbstractDatabase directement

### Tests (~50+ cas)

- Remplacer `db.provider.*` par ViewContext + `db.query_videos()`
- Simplifier les mocks (MockProvider → pas besoin)

## Séquence d'implémentation recommandée

1. Supprimer jsdb (réduit la surface de refactoring)
2. Créer ViewContext (classe indépendante, testable unitairement)
3. Ajouter AbstractDatabase.query_videos() + implémentation SQL
4. Migrer AppContext PySide6 (le plus gros morceau)
5. Migrer FeatureAPI/GuiAPI (si encore utilisé)
6. Migrer les tests
7. Supprimer le provider

## Avantages

- Séparation nette état / calcul
- ViewContext testable sans DB
- ViewContext sérialisable (website, session, query params)
- Chaque backend n'implémente qu'UNE méthode au lieu de ~20
- Interfaces stateless possibles (website)
- ~1000 lignes de provider supprimées
