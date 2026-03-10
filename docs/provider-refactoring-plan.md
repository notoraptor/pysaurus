# Plan de refactoring : Remplacer le VideoProvider par ViewContext + query_videos()

## Principe

Séparer le provider actuel (qui mélange état et calcul) en deux composants :

1. **`ViewContext`** — classe universelle de gestion des paramètres de vue (pur état, zéro dépendance DB)
2. **`AbstractDatabase.query_videos()`** — méthode abstraite stateless, implémentée par chaque backend

## Progression

### Fait

- [x] Créer `ViewContext` (`pysaurus/video_provider/view_context.py`, 72 lignes)
- [x] Ajouter `AbstractDatabase.query_videos()` (méthode abstraite)
- [x] Implémenter `PysaurusCollection.query_videos()` (SQL, stateless via `video_mega_group()`)
- [x] Implémenter `JsonDatabase.query_videos()` (JSON, orchestre le provider interne)
- [x] Migrer `FeatureAPI` : supprimer `FromView`, méthodes de vue explicites, `view = ViewContext()`
- [x] Migrer `AppContext` PySide6 : délégation à FeatureAPI, suppression de `_last_result`
- [x] Migrer `GuiAPI` : `find_similar_videos()` / `find_similar_videos_reencoded()` utilisent `self.view`
- [x] Simplifier `DatabaseOperations._notify_fields_modified()` (plus d'appel au provider)
- [x] Simplifier `DatabaseAlgorithms.refresh()` (plus d'appel à `provider.refresh()`)
- [x] Migrer `console/run.py` (`BenchmarkAPI` utilise ViewContext)
- [x] Migrer `using_videre/backend.py` (`open_random_video` via API)
- [x] Restructurer les tests : supprimer comparisons JSON/SQL, dé-dupliquer les YAML
- [x] Ajouter tests ViewContext, AppContext, database CRUD
- [x] Migrer `MockDatabase.query_videos()` pour accepter ViewContext

### Reste à faire

- [ ] Supprimer jsdb (`JsonDatabase`, `JsonDatabaseVideoProvider`)
- [ ] Supprimer `AbstractVideoProvider` et `SaurusProvider`
- [ ] Supprimer l'attribut `provider` de `AbstractDatabase`
- [ ] Supprimer `MockProvider` des tests
- [ ] Nettoyer les imports résiduels du provider

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

### Cascade de réinitialisation

- Changer grouping → reset classifier, group, search
- Changer classifier → reset group
- Autres paramètres → pas de cascade

## AbstractDatabase.query_videos()

```python
@abstractmethod
def query_videos(self, view: ViewContext,
                 page_size: int, page_number: int,
                 selector: Selector = None) -> VideoSearchContext:
    ...
```

- Prend le ViewContext en entrée
- Retourne un VideoSearchContext complet (vidéos, groupes, stats, pagination)
- Stateless : pas d'état interne, tout vient des paramètres
- Chaque backend l'implémente comme il veut

## Flux d'utilisation (actuel)

```
Interface (AppContext / FeatureAPI / BenchmarkAPI / Flask)
    │
    ├── possède un ViewContext (état de la vue)
    │
    ├── Mutation des paramètres → ViewContext.set_*()
    ├── Calcul de la vue → db.query_videos(view, page_size, page)
    │   └── retourne VideoSearchContext
    │
    ├── Navigation classifier :
    │   ├── FeatureAPI.classifier_select_group(group_id)
    │   │   └── query fresh → result_groups[group_id].value → view.classifier_select(value)
    │   └── view.classifier_back() / view.classifier_reverse()
    │
    ├── Apply on view :
    │   └── FeatureAPI.apply_on_view(selector, fn_name, *args)
    │       └── query_videos(view, None, None) → view_indices → operation
    │
    └── Random video :
        └── FeatureAPI.open_random_video()
            └── query db.get_videos(where=flags) → random pick → set search by ID
```

## Ce qui reste à supprimer

- `AbstractVideoProvider` (~263 lignes)
- `SaurusProvider` (~180 lignes)
- `JsonDatabaseVideoProvider` (~570 lignes) — quand jsdb sera supprimé
- Attribut `provider` sur `AbstractDatabase`
- `MockProvider` dans les tests
