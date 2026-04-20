"""
NB: Le texte de cette docstring est en français pour mieux décrire le cahier des charges, et parce que ce script est
un prototype. Mais le véritable code de Pysaurus (noms, commentaires et docstrings) continue d'être en français.

Je veux ajouter une nouvelle fonctionnalité à Pysaurus qui permet de gérer les fichiers non-vidéos présents dans les
dossiers d'une base de données. En effet, les dossiers d'une db peuvent contenir des vidéos, mais aussi des miniatures,
des fichiers texte associés, des fichiers partiels de téléchargement, etc. Or, ces fichiers ne sont pas toujours
utiles. Il faut donc un moyen de les gérer: on doit pouvoir les supprimer massivement, mais aussi les parcourir
afin de les supprimer individuellement.

Le script actuel récupère tous les fichiers des dossiers d'une db, les classe par extension, puis les sépare
par deux catégories "videos" et "non-videos", puis affiche le nombre et la taille cumulée pour chaque extension.
Mais je veux aller plus loin.

# Accélérer la récupération des fichiers
D'abord, je veux que le script puisse collecter les fichiers en parallèle. Je suppose que le plus simple serait de
classer les dossiers par disque (mount point) puis de lancer la collecte en parallèle avec 1 processus par disque ?
Ou bien, peut-on paralléliser aussi sur un même disque ?

# Gestion fine des fichiers
Je considère que, pour 1 fichier donné, les seules informations importantes sont le path, l'extension, et la taille.
On ne veut pas viaualiser les fichiers (et les fichier vidéos sont déjà gérés par la db). On veut simplement une
interface pour rapidement aller voir les fichiers sur disque si nécessaire .

Je propose une interface intégrée à l'interface Pyside6. Cette dernière a actuellement deux pages: "videos" et
"properties". On pourrait ajouter une troisième page "all db files" ou "db file stats".

Quant on va sur cette page pour la première fois (à la première ouverture de la db), on a un bouton de scan avec un
texte qui explique que le bouton va scanner tous les dossiers de la db pour récolter tous les fichiers (y compris
les fichiers non-vidéo) afin qu'on puisse les traiter finement.

En appuyan sur le bouton, le scan se lance via une page de processus (comme le font d'autres processus longs de Pysaurus)/
Ça veut dire que l'algorithme de collecte des fichiers devra aussi émettre des notifications, comme le fait, par exemple,
l'algorithme d'ouverture/update de database, ou les algorithmes de recherche de vidéos similaires.

La collecte des vidéos doit retourner:
- pour chaque fichier, une structure contenant {path: AbsolutePath, extension: str, file_size: int}
- l'ensemble des fichiers ainsi collectés devraient être classés en deux catégories: "videos" et "others".
- Dans chaque catégorie, les fichiers devraient être groupés par extension.
La structure globale pourrait ressembler à ceci:
{
  "videos": {<extension>: [liste de fichiers]},
  "others": {<extension>: [liste de fichiers]},
}

Une fois les données disponibles, on doit les afficher dans une interface efficace. Idées:
- deux onglets: "others" et "video stats".
- L'onglet "video stats" affiche seulement les staistiques des fichiers vidéos (compte et taille totale par extension).
  Pas besoin de plus, car les vidéos sont censées être gérées dans la page "Videos".
- L'onglet "others", par contre, est l'onglet affiché par défaut quand on charge cette page "db file stats". Il
  s'agira d'une interface complète pour gérer les autres fichiers.
- Au dessus des onglets, un bouton "rescan" pour rescanner les dossiers et mettre à jour toute la page.

# Onglet "others"
Deux panneaux:
- à gauche, la liste  des extensions, une par ligne.
  - affiche l'extension, le nombre de fichiers, la tailel totale.
  - bouton "tout supprimer", avec confirmation bien rouge. Si oui, on supprime tous les fichiers de cette extension.
    Par précaution, mieux vaut peut-être un bouton "tout à la corbeille" ?
  - Par défaut, quand on clique sur une lignee hors du bouton de suppression, le panneau à droite se met à jour
    pour afficher les fichiers associés à l'extension.
  - Les extensions sont triées par ordre décroissant de taille totale, comme dans le script ici.
  - Par défaut, la première ligne est sélectionnée/
- à droite, la liste des fichiers de l'extension sélectionnée.
  - Une liste de fichiers, un par ligne. Sur chaque ligne:
    - bouton "dossier" => ouvre le dossier parennt du fichier (une option similaire existe pour les vidéos)
    - bouton "supprimer": ou "corbeille" ? Pour supprimer ce fichier précis.
    - affiche le path complet. Wraap peut-être nécessaire, ou alors ellision + tooltip.
    - Liste paginée ? (il peut y avoir beaucoup de fichiers)

Ainsi donc, le panneau à gauche permet la gestion en 1 coup de tous les fichiers d'une extension, tandis que le panneau
à droite permet la gestiun fine, fichier par fichier.
"""
import os
import sys
from collections import defaultdict

from strarr import strarr
from tqdm import tqdm

from pysaurus.application.application import Application
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.core.file_size import FileSize


def main():
    if len(sys.argv) < 2:
        print("Database name expected")
        sys.exit(1)
    database_name = sys.argv[1]
    app = Application()
    if database_name not in app.get_database_names():
        print("Database not found")
        sys.exit(1)
    database = app.open_database_from_name(database_name, update=False)
    folders = database.get_folders()
    extension_count: dict[str, int] = defaultdict(int)
    extension_size: dict[str, int] = defaultdict(int)
    todo: list[AbsolutePath] = [folder for folder in folders if folder.exists()]
    nb_done = 0
    nb_todo = len(todo)
    with tqdm("folders") as pbar:
        while todo:
            path = todo.pop()

            nb_done += 1
            pbar.total = nb_done + len(todo)
            pbar.n = nb_done
            pbar.refresh()

            if path.isdir():
                todo.extend(AbsolutePath(entry.path) for entry in os.scandir(path.path))
            else:
                path_string = str(path)
                index_of_pint = path_string.rfind('.')
                if index_of_pint < 0:
                    extension = ""
                else:
                    extension = path_string[index_of_pint + 1:]
                extension = extension.lower()
                file_size = path.get_size()
                extension_count[extension] += 1
                extension_size[extension] += file_size

    report_videos = []
    report_others = []
    for extension, size in sorted(extension_size.items(), key=lambda item: (-item[1], item[0])):
        report = dict(extension=extension, count=extension_count[extension], size=FileSize(size))
        if extension in VIDEO_SUPPORTED_EXTENSIONS:
            report_videos.append(report)
        else:
            report_others.append(report)
    if report_videos:
        print("VIDEOS")
        print(strarr(report_videos))
    if report_others:
        print("OTHERS")
        print(strarr(report_others))


if __name__ == '__main__':
    main()
