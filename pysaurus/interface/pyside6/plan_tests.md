Il faut maintenant implémenter des unit tests simples mais solides, qui vérifient
le bon fonctionnement de l'interface pyside6. En résumé, que les boutons et autres
évènements de l'interface déclenchent les bonnes actions, récupèrent les bonnes
valeurs de la database, mettent à jour l'interface comme on s'y attend.

Le souci est que, si on utilise une db de test json ou sql, il y aura plein de lectures
sur disque, ce qui ralentira les tests et ne permettra peut-être pas de les rouler
en parallèle.

La solution serait de créer une MockDatabase:
- qui exploitera en interne des données de test précalculées, qui se chargent rapidement
  en mémoire (depuis un JSON, ou un dict Python ?)
- qui implémentera chaque méthode de AbstractDatabase, mais en plus rapide, car les méthodes
  n'auraont qu'à lire les données en mémoire

Ensuite, on pourra utiliser ce mock pour tester l'interface.

Le mock devrait être efficace pour les tests read-only sur la db, mais ce sera plus
compliqué pour les tests write sur db et write sur disk.
- pour les tests write sur disque (par exemple, delete permanently ou move to trash),
  il faudrait un module permettant de simuler un disque, mais qui fait tout en mémoire,
  en arrière-plan. Ça permettrait de juste vérifier que les bonnes méthodes de la
  database sont appelées, que les opérations sont effectivement exécutées sur le
  faux disque.
- pour les tests write sur db: vu que la db est en mémoire et propre à chaque test,
  ça devrait être facile.

Voici donc ce qu je propose:
- implémenter une mock database, capable de s'initialiser avec un JSON rapide à charger,
  ou un dict python
- implémenter un json ou dict python représentant une database de tests, capable de
  couvrir **tous** les cas d'usage possibles, permettant de tester **toutes** les
  méthodes de la database et tous leurs cas particuliers.

Qu'en penses-tu ?
