Interface graphique = combinaison d'informations et d'actions

Information: affichage de texte, d'images et de graphiques Action: exécutée lors d'un
clic ou d'un survol de la souris. Plusieurs types d'action:

- action qui exécute une fonction qui modifie des informations
- action qui affiche d'autres informations
- action qui propose d'autres actions. Par exemples:
    - menu
    - menu contextuel (pour le moment, on ne prendra pas en charge les menus
      contextuels)

information = object // print object action -> object.method() // edit object
attributes, return None action -> fonction() -> information // return an object action
-> function() -> list // return a list of functions, ie. a menu

By default, action = button action on hover: object method "on_hover()" must return a
list (ie. a menu)

menu1 = [f1, f2, f3]
menu2 = [f4, f5, f6, menu1, f7, f8]
menu3 = named("title", [f9, f10, f11])
menu4 = [f12, f13, menu3, f14, f15]

