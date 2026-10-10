# Audit de l'interface Kyuti

## Statut

Prochaine étape prévue, pas commencée. Objectif : un audit complet de
l'interface Kyuti (PySide6) : qualité, ergonomie, cohérence des libellés et des
raccourcis, densité des volets, logique des menus, états désactivés, messages
d'erreur. Livrable : un rapport par page, problèmes classés par gravité, avec
des propositions concrètes, séparées de ce qui relève du goût.

## Voir l'interface depuis une session Claude

Aucun outil de contrôle du bureau n'était disponible ; les outils navigateur
ne servent à rien pour une application Qt. En revanche, les widgets Kyuti se
rendent en PNG que Claude lit ensuite comme des images. Deux recettes vérifiées
le 2026-10-10.

### Recette native (à privilégier)

Créer la `QApplication` sur le vrai plugin Windows, construire le widget, le
redimensionner, puis `grab()` **sans jamais appeler `show()`**. Aucune fenêtre
n'apparaît, et l'image a le style natif `windows11` au facteur d'échelle de
l'écran (1,5 sur la machine de référence). Le résultat correspond aux captures
de l'utilisateur, barre de titre de l'OS exceptée.

```python
import sys
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
from pysaurus.interface.kyuti.dialogs.sources_dialog import SourcesDialog

dialog = SourcesDialog(start_tab=1, ctx=...)
dialog.resize(450, 480)
dialog.grab().save("sources_dialog.png")
```

### Recette hors écran (repli)

Sans session bureau, le plugin `offscreen` fonctionne mais rend le style
générique de Qt. Deux réglages sont indispensables sous Windows, sinon les
glyphes sont des carrés, puis une police de symboles :

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_QPA_FONTDIR"] = r"C:\Windows\Fonts"
# après QApplication(...) :
app.setFont(QFont("Segoe UI", 9))
# puis widget.show(), app.processEvents(), widget.grab().save(path)
```

### Limites

`grab()` fige l'état initial : pas de survol, pas d'infobulle, pas de menu ni
de popup de combo ouverts. Ces états doivent être provoqués explicitement par
le script avant la capture, ou complétés par des captures de l'utilisateur.

## Données

Toujours la base de test `tests/home_dir_test/.Pysaurus/databases/example_db_in_pysaurus`
(90 vidéos avec propriétés, aucune donnée privée), jamais une base réelle.
Pour un `AppContext` réel sur une base en mémoire, suivre la fixture `ctx` de
`tests/interface/kyuti_interface/test_app_context.py` et
`tests/utils.py::get_saurus_sql_database`.

## Plan

1. Un script de capture (emplacement à décider, par exemple
   `pysaurus/scripts/`) qui ouvre l'application sur la base de test et
   parcourt chaque page, chaque dialogue et chaque état notable : une image
   par vue, dans un dossier ignoré par git.
2. Lecture des images en parallèle du code qui les produit.
3. Rapport structuré par page, avec gravité et propositions.
