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
