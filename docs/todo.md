Bien. Avant d'aller plus loin, je veux consolider cette interface.

1) Fais la liste de toutes les fonctionnalités exposées par FeatureAPI et GuiAPI via leurs proxies.

2) Fais la liste de toutes les méthodes publiques dans AbstractDatabase, DatabaseOperations, DatabaseAlgorithms et AbstractVideoProvider. Ce sont les 4 classes qui, à ma connaissance, permettent les interactions avec les dbs.

3) Pour chaque fonctionnalité du point 1, détermine quelles méthodes du point 2 sont appelées, et quelles méthodes ne sont pas exposées par ces fonctionnalités.

4) Pour chaque fonctionnalité du point 1, détermine si elles ont un équivalent dans pyside6. Il me semble que pyside6 ne passe pas par FeatureAPI, mais fait plutôt des appels directs aux classes du point 2. Je veux donc savoir si, par ces appels, pyside6 couvre toutes les fonctionnalités du point 1. On en déduira aussi les fonctionnalités du point 1 qui ne sont pas couvertes par pyside6.

5) Pour chaque fonctionnalité du point 1, détermine quel état (database ou provider) change après leur exécution, qu'est-ce qui change (video attribute ? video property value spécifique ? prop type ? provider sources, group, search ?), et qu'est-ce qui doit être mis à jour dans une interface graphique pour réfléter ce changement. Attention, il se peut qu'il y ait actuellement des insuffisances (par exemple, des changements non reportés dans pyside6, ou des notifications non émises, etc.). C'est justement mon but de régler ce problème, donc il faut d'abord déterminer, de façon abstraite et générale, ce qui change en arrière-plan, et quel genre de changement ça doit impliquer en avant-plan (dans les interfaces graphiques). Exemple: si une vidéo s'ouvre (fonctionnalité disponible dans FeatureAPI) -> watche devrait changer -> si la vidéo est visible dans l'interface, son affichage doit se mettre à jour, etc.

À partir de tout ça, j'espère qu'on pourra déduire une suite de corrections à faire, non seulement en arrière-plan, mais aussi dans les interfaces graphiques, en particulier Pyside6 qui est désormais l'interface principale. Ça nous aidera aussi à écrire des unit tests solides, car il n'y en a pas encore vraiment ni assez, actuellement.

Produis un rapport détaillé et complet dans ce dossier docs/.