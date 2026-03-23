# Backlog Pysaurus

Backlog unifié, priorisé. Remplace `suggestions.md` et `notes.md`.

---

## P0 — Bugs critiques ✅

### Menus et navigation actifs pendant les opérations longues ✅

Les radio buttons "videos"/"properties" et plusieurs menus restent cliquables quand
la page de progression est affichée (par exemple pendant un update). Si une autre opération
est lancée en parallèle, cela pourrait corrompre la base de données.

**Correction attendue** : désactiver tous les contrôles de navigation et menus d'action
quand une opération longue est en cours.

### Propriétés écrasées par des valeurs par défaut à l'édition ✅

Quand on édite les propriétés d'une vidéo, certaines propriétés sont mises à jour avec
leur valeur par défaut, même si on n'avait rien entré pour ces propriétés. L'interface
envoie des valeurs par défaut pour les champs vides au lieu de préserver l'absence de valeur.

**Correction attendue** : n'envoyer que les valeurs précédentes (si elles existaient)
ou les valeurs nouvellement entrées par l'utilisateur. Rien d'autre.

### Menu de sélection et boutons désynchronisés ✅

Un bouton de sélection peut être désactivé alors que l'action correspondante dans le menu
reste cliquable. Les deux doivent refléter le même état.

---

## P1 — Bugs visuels ✅

### Surbrillance cassée en vue liste ✅

En vue liste, un clic droit sur une vidéo, puis une deuxième, puis une troisième,
laisse les trois en surbrillance bleue. La surbrillance ne devrait être visible que
pour la vidéo survolée par la souris.

De plus, la couleur de surbrillance de survol et la couleur de sélection sont au même
ton bleu. Les deux doivent être visuellement distinctes.

---

## P2 — Améliorations UX (PySide6) ✅

### Auto-continue après ouverture rapide de la base ✅

Quand on ouvre la base sans update, l'opération est quasi instantanée. Plutôt que
d'afficher le bouton "continuer", passer automatiquement à la page vidéos.

**Implémentation** : paramètre `autocontinue` sur la page de progression.
Si `True` (cas "open"), passage automatique. Si `False` (défaut), bouton "continuer".

### Progress ring au lieu de la barre de progression infinie ✅

Remplacer la barre de progression horizontale infinie par un progress ring (indicateur
circulaire) sur la page des opérations longues.

### Dialogues de confirmation enrichis ✅

Quand une boîte de dialogue confirme une opération sur une vidéo (supprimer, etc.) :
- Afficher le chemin fichier complet en police mono (pas seulement le titre)
- Afficher la miniature de la vidéo pour confirmation visuelle

### Ouvrir une vidéo par clic sur le chemin ✅

Permettre d'ouvrir une vidéo en cliquant directement sur son chemin fichier,
sans passer par clic droit → "open".

### Toggle watched en masse ✅

Quand plusieurs vidéos sont sélectionnées, proposer un bouton "toggle all watched"
à côté des autres boutons de sélection.

### Éditeur de propriétés en panneau split ✅

Panneau split avec table des matières à gauche et formulaire scrollable à droite.
Labels de section au-dessus des champs, fond alterné, focus + gras au clic,
scroll protégé (combo/spinbox), boutons Reset/Clear complets, feedback couleur
(bleu = modifié, italique = défaut).

### Panneau de groupes paginé (au lieu du dropdown) ✅

Dropdown supprimé. Panneau scrollable (QListWidget) en bas de la sidebar avec
navigation (<<, <, X/Y, >, >>), lignes alternées, sélection en surbrillance.
Group bar au-dessus des vidéos supprimée, bouton classifier déplacé dans le
header du panneau. Filtre Grouping compacté en 2 lignes.

### Compacter les filtres ✅

Pour chaque filtre, remplacer le bouton "edit"/"set" et le bouton rouge de réinitialisation
par deux petits boutons icône (paramétrage bleu/vert + réinitialisation rouge) placés à droite
du titre du filtre. Gain d'une ligne par filtre, libérant de la place pour le panneau de groupes.

Harmoniser aussi le filtre "Search" en déplaçant son bouton de réinitialisation à droite du titre.

### Redondance menu/boutons de sélection ✅

Le menu de sélection et les boutons de sélection sont potentiellement redondants.
Résolution : la sélection est gérée dans la sidebar (comme un filtre), avec un
bouton ⚙ ouvrant un menu contextuel (Show Only Selected, Toggle Watched, Edit
Properties), des boutons Page/All, et un bouton ✕ pour clear. Le menu Selection
de la barre de menu a été supprimé.

---

## P3 — Nouvelles fonctionnalités

### Propriété `date_added`

Enregistrer la date à laquelle une vidéo a été ajoutée à la base de données.
Distincte de `mtime`, `date_entry_modified` et `date_entry_opened`.

### Recherche inverse (NOT AND, NOT OR)

Ajouter la négation des modes de recherche existants :
- "not and" : `NOT (a AND b AND ...)`
- "not or" : `NOT (a OR b OR ...)`

### Recherche par expression

Mini-langage de requête pour des recherches avancées. Exemples :
```
bit_rate > 5000000
length_seconds < 60
audio_bitrate > 200kbps and `category` == "this category"
```

**Syntaxe envisagée** :
- Nom classique (ex. `audio_bitrate`) pour les attributs vidéo
- Nom entre accents graves (ex. `` `category` ``) pour les propriétés custom
- Expressions purement booléennes : `and`, `or`, `xor`, `not`, parenthèses
- Types : str, bool, int, float
- Comparaisons : `==`, `!=`, `<`, `>`, `<=`, `>=`
- Opérateurs spéciaux : `is` (booléens), `in` (appartenance à set/liste)
- Syntaxes de valeurs spéciales :
  - Bit rates : `203.4kbps` (converti en bps × 1024)
  - Dates : `2023-02-05` (jour), `2025-01-01-23:55` (minute), `2025-01-01-23:55:05` (seconde)
  - Durées : `2min12s` ou nombre brut en secondes

**Questions ouvertes** :
- Code distinct ou intégré aux options de recherche actuelle ?
- Quelle optimisation SQL ? (traduction en WHERE clause vs évaluation Python)

**Note** : la "recherche conditionnelle" (comparaisons simples dans `VideoFieldQueryParser`)
pourrait être une première étape avant le langage complet.

### Plugins en menu contextuel vidéo

Système de plugins apparaissant dans le menu contextuel d'une vidéo.
Chaque plugin définit un critère d'applicabilité et une action.

### Annulation des opérations longues

Actuellement, il est impossible d'interrompre un processus en cours (update, similarité, etc.).
Le menu Database → Quit reste disponible sur la page de progression, mais quitter pendant
une opération revient à tuer le processus brutalement. Les opérations longues utilisent
souvent du multi-processus, ce qui rend l'annulation propre difficile à implémenter.

**Difficulté** : élevée. Nécessite un mécanisme de cancellation coopératif dans les
algorithmes de traitement (`database_algorithms.py`, `imgsimsearch/`), probablement
via un flag partagé vérifié à chaque étape.

---

## P4 — Optimisations

### Matrice de similarité O(n²)

`imgsimsearch/approximate_comparator_numpy.py` stocke la matrice complète.
Réduire à n·(n−1)/2 en ne stockant que le triangle supérieur.

### Déplacement de fichiers en lot

`database_algorithms.py:move_video_entries()` est lent pour de gros lots.
Regrouper les suppressions individuelles en batch SQL.

### Fusionner les boucles d'enrichissement dans `_get_videos()`

`saurus/sql/video_mega_utils.py` : 5 boucles séparées itèrent sur `videos`
(errors, audio_languages, subtitle_languages, properties, moves).
Les fusionner en une seule boucle.
