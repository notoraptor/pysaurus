# Interface pyside6

La page des opérations longues affiche une barre de progression infinie horizontale en attendant la fin du processus.
Ce serait peut-être mieux d'afficher un progress ring infini, à la place.

Quand on ouvre la base de données ("open" au lieu de "update"), l'ouverture est très rapide avec PysaurusCollection.
C'était un peu plus lent avec JsonDatabase, mais l'ouverture sans update est censée être rapide, en général.
Je suggère donc que le processus d'ouverture passe automatiquement à la page suivante (video page) dès qu'il finit,
plutôt que d'afficher le bouton "continuer". La page de progression pourrait être configurable et accepter un paramètre
"autocontinue": si true, passe à la page suivante dès la fin du processus (cas "open database"); si false (defaut),
affiche un bouton pour continuer à la page précédente (cas de toutes les autres opérations longues).

Il y a un souci avec la surbrillance des vidéos (constaté en vu liste, je ne sais pas si c'est le cas en vue grille):
si je fais clic droit sur une vidéo, puis sur une seconde, puis une troisième ... Les trois vidéos seront en surbrillance
(bleue, bordure bleue foncée). Normalement, la surbrillance ne devrait être visible que pour la vidéo survolée par
la souris. Il faut aussi que la couleur de surbrillance de survol soit différente de la couleur de surbrillance de sélection.
Actuellement, les deux sont au même ton bleu, ce qui prête à confusion.

Quand on sélectionne plusieurs vidéos, il faut aussi une option "toggle all watched" pour toute la sélection. Sans doute
en bouton qui apparaît à côté des autres boutons de sélection quand il y a une sélection.

Les radio buttons "videos" et "properties" en haut à droite sont visibles quand on est sur la page de progression.
C'est anormal, car on ne peut pas choisir une de ces pages pendant qu'une longue opération est en cours. Pareil pour
plusieurs menus, ils sont encore actifs alors qu'on est en page de progression (par exemple, pendant qu'on update une database).
C'est très dangereux, car si ça permet de lancer une autre opération, alors ça pourrait corrompre la base de données.

On a un menu de sélection, et des boutons de sélection. Est-ce redondant ?
Il y a plusieurs boutons: n'est-ce pas mieux de les regrouper dans un dropdown, plutôt que de les afficher sur une ligne ?
Le menu de sélection et les boutons ne sont pas synchronisés: parfois, un bouton est désactivé, mais son action correspondante
dans le menu est toujours cliquable.

Quand une boîte de dialogue s'ouvre pour confirmer une opération sur une vidéo (par exemple, pour supprimer une vidéo):
- Il vaudrait mieux afficher le file path complet (en police mono), plutôt que seulement le titr
- Il vaudrait mieux afficher aussi la miniature de la vidéo. Pour que l'utilisateur ait la confirmation visuelle
  de la vidéo qu'il veut modifier.

Sur une vidéo, je veux pouvoir l'ouvrir en cliquant sur ton chemin fichier. Ce serait plus rapide que de devoir
chaque fois passer par clic droit -> "open".

Quand on édite les properties d'une vidéo, certaines propriétés sont mises à jour avec leur valeur par défaut, même
si on n'avait rien entré pour ces propriétés. Un peu comme si l'interface pyside6 envoyait des valeurs par défaut
pour les champs vides. Mais normalement, l'interface doit s'assurer d'envoyer uniquement: soit les valeurs précédentes
de la propriété (s'il y en avait), soit les valeurs nouvellement entrées par l'utilisateur. Rien d'autres.

La gestion de la sélection devrait-elle apparaître comme les fitlres, donc après la section "sorting" à gauche ?
Ça permettrait notamment d'avoir un simple bouton "x" pour effacer la sélection. Mais ça pourrait être compliqué,
car il y a beaucoup d'options pour gérer une sélection (sélectionner la page, sélectionner toute la vue, show only
selected, edit properties ...).

Faudrait-il implémenter la recherche inverse pour AND et OR ? 
C'est-à-dire "NOT AND" (not (a and b and ...)), et "NOT OR" (not (a or b or ...))?

Le dialogue de modification des propriétés d'une vidéo est un peu pénible à manipuler. On est obligé de descendre
pour éditer une propriété quand il y en a plusieurs. Je me demande si ce ne serait pas mieux d'organiser les
propriétés en onglet: un onglet par propriétés, comme ça, moins de risque de défilement. Si on craint un mauvais affichage
en cas de nombreuses propriétés, je pourrais suggérer un affichage vertical des onglets. Et en fait, des onglets conceptuels
c'est-à-dire: un panneau vertical avec les noms des propriétés, à gauche, et quand on clique sur une d'entre elles,
on affiche le panneau d'édition de la propriété à droite. Chacun des deux panneaux étant indépendamment scrollable.

Dans l'ancienne interface web/react, quand on groupait les vidéos, les groupes étaient affichés dans un panneau paginé
en dessous des filtres. Ça permettait en un coup d'oeil d'apprécier la diversité des groupes, en voyant les noms et
comptes de plusieurs groupes à la fois. Actuellement, dans pyside6, c'est un dropdown au dessus de la vue des vidéos.
Moins pratique, car il faut chaque fois déplier le dropdown pour voir plus d'info sur les autres groupes.

Actuellement, dans les filtres, pour chaque filtre, on a une ligne avec un bouton "edit" (ou "set") et un petit bouton 
rouge en croix pour réinitialiser le groupe. Je me dis qu'on pourrait compacter ça:
- en remplaçant le bouton edit/set par un petit bouton avec une icône symbolisant le paramétrage. Le bouton serait bleu
  ou vert (par opposition au bouton rouge de réinitialisation)
- en plaçant les deux petits boutons à droite du titre du filtre, plutôt qu'en bas de la section de filtrage. Cela
  ferait gagner une ligne, donc libérerait de la place en bas des filtrages, si on décidait éventuellement d'y mettre
  un panneau de groupes.
Cette optimisation de l'espace serait par contre inutile pour le filtre "search". Mais ça pourrait valoir la peine
d'y déplacer quand même le bouton de réinitialisation vers la droite du titre "Search", pour harmoniser la vue.

## Recherche par expression

Il faudrait que je puisse ajouter la feature de recherche par expression. Par exemple:
audio_bitrate > 200kbps and `category` == "this category". Mais ce serait un gros morceau. Il faudrait:
- définir la syntaxe des expressions. Par exemple:
  - nom de variable classique (exemple audio_bitrate) pour les attributs de vidéo (membres et @property de VideoPattern)
  - nom entre accents graves (exemple `category`) pour les propriétés de vidéo (noms de prop types)
  - lex expressions sont purement booléennes, par d'affectation:
    - a and|or|xor b
    - not a
    - support des parenthèses et des expressions chaînées (par exemple: a and b and c and not(d) or (e xor f) ...)
  - support des types Python basiques: str, bool, int, float
  - support des opérateurs de comparaison: ==, !=, <, >, <=, >=
    - support de l'opérateur is pour les booléens (a is True)
    - support de l'opérateur in (a in b)
      - donc, support des sets: on acceptera les accolades (sets python) et les crochets (listes python),
        tous traités comme des sets. Exemple: a in [1, 2, 3] or b in {1, 2, 3}
  - support de syntaxes supplémentaires pour certaines right values
    - par exemple: bit_rate >= 203.4kbps
      - On doit supporter 203.4kbps, à convertir simplement en bps (bits per seconds), donc * 1024
    - support des dates. Exemples:
      - day < 2023-02-05 (jour)
      - date_modified > 2025-01-01-23:55 (jusqu'à la minute)
      - date_entry_opened < 2025-01-01-23:55:05 (jusqu'à la seconde)
- code distinct, ou intégré aux options de recherche actuelle ?
  - si distinct: nom, arguments et emplacement de la méthode dans le code
- à quel point une telle recherche serait rapide/optimisable dans l'implémentation SQL ?

Ça va être un gros morceau. Travail préliminaire:
- lister les types possibles de prop types
- lister les attributs et property python de video pattern, et pour chacune, 
  - les types disponibles
  - les façons d'exprimer ces types
    - par exemple, pour les dates, utiliser des strings formatées (2023-01-01..., etc), et non le pur timestamp
    - pour les durées, utiliser des strings formatées (exemple, 2min12s), OU un nombre brut (nombre de secondes)
    - pour les bit rates, nombre brut (bits, per seconde), ou strings formatées (23kbps, 12mbps ?)
