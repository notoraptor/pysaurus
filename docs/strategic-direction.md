# Direction stratégique Pysaurus

## Contexte

Pysaurus en tant que gestionnaire vidéo personnel est dans un marché saturé (Plex, Jellyfin, Stash, tinyMediaManager, digiKam). La valeur différenciante serait de pivoter partiellement vers la **curation de datasets vidéo pour la recherche ML/IA**.

L'objectif est double : garder Pysaurus pour un usage personnel tout en le rendant utile à d'autres, notamment dans le domaine ML où le créneau de la curation de datasets vidéo est sous-exploité (outils existants : FiftyOne, CVAT, Label Studio, DVC).

## Briques existantes réutilisables pour le ML

- Propriétés typées (bool, int, float, str) avec valeurs multiples
- Recherche avancée avec FTS5
- Détection de similarité d'images (NumPy)
- Backend SQLite solide

## Axes d'amélioration identifiés

Par ordre de priorité :

1. **API programmatique (Python SDK)** — les chercheurs veulent `import pysaurus` dans un notebook, pas uniquement une GUI.
2. **Scalabilité** — support de datasets 100k+ vidéos.
3. **Import/export formats ML** — COCO, YOLO, WebDataset, Hugging Face datasets.
4. **Intégration embeddings** — stocker et chercher par vecteurs (CLIP, etc.) plutôt que par similarité pixel.
5. **Annotations** — bounding boxes, segments temporels, labels par frame.
