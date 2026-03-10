# Suggestions

Ideas and improvements extracted from the old `todo.md`.

## Features

- **Recherche conditionnelle**: supporter des opérateurs de comparaison dans
  la recherche, par exemple `bit_rate > 5000000` ou `length_seconds < 60`.
  Actuellement `VideoFieldQueryParser` ne génère que des clauses d'égalité (`=` / `IN`).
  Piste : la bibliothèque `simpleeval` permettrait d'évaluer des expressions
  comme `simple_eval("audio_bits > 8", names={"audio_bits": 16})`.

- **Propriété `date_added`**: enregistrer la date à laquelle une vidéo a été
  ajoutée à la base de données (distincte de `mtime`, `date_entry_modified`
  et `date_entry_opened` qui existent déjà).

- **Plugins en menu contextuel vidéo**: permettre d'ajouter des plugins
  apparaissant dans le menu contextuel d'une vidéo. Chaque plugin définirait
  un critère d'applicabilité et une action.

## Optimisations

- **Algorithme de similarité d'images**: la matrice de similarité dans
  `imgsimsearch/approximate_comparator_numpy.py` utilise encore un stockage
  en O(n²). Réduire à n·(n−1)/2 en ne stockant que le triangle supérieur.

- **Déplacement de fichiers en lot**: `database_algorithms.py:move_video_entries()`
  est lent pour de gros lots. Les suppressions individuelles en boucle
  pourraient être regroupées.

- **Fusionner les boucles d'enrichissement dans `_get_videos()`**:
  dans `saurus/sql/video_mega_utils.py`, 5 boucles séparées itèrent sur
  `videos` (errors, audio_languages, subtitle_languages, properties, moves).
  Les fusionner en une seule boucle (~10 lignes gagnées + légère amélioration perf).

## Nettoyage

- **Supprimer jsdb**: supprimer `JsonDatabase`, `JsonDatabaseVideoProvider`
  et le package `pysaurus/database/jsdb/`. Seul le backend SQL reste.
