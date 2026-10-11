# Audit de l'interface Kyuti

## Statut

Audit réalisé le 2026-10-11. Deux volets :

- **Code** : lecture intégrale de `pysaurus/interface/kyuti/` (≈12 800 lignes :
  `main_window`, `app_context`, les 5 pages, 19 dialogues, 9 widgets) et des
  helpers partagés `interface/common/`.
- **Visuel** : 83 captures en anglais et 83 en français, une par page, dialogue,
  menu et état notable, produites par `pysaurus/scripts/capture_kyuti.py` dans
  `ignored/kyuti_audit/<lang>/` (dossier ignoré par git), puis lues une à une.

Livrable : ce rapport, par page, problèmes classés par gravité, propositions
concrètes séparées de ce qui relève du goût. Les quatre bugs de gravité P0
trouvés (durée fausse dans l'onglet Info, Entrée qui validait des suppressions,
Suppr limitée à la page courante, suppression d'une base sans dire ce qui
disparaît) ont été corrigés le jour même et ne figurent plus ici.

Ce qui n'a **pas** été vérifié : les survols et infobulles, les flux réels
(mise à jour, similarité, déplacement de fichier), VLC, le glisser-déposer, les
performances sur une grande base, le mode sombre de Windows.

## Regénérer les captures

```bash
uv run -m pysaurus.scripts.capture_kyuti            # ignored/kyuti_audit/en/
uv run -m pysaurus.scripts.capture_kyuti --lang fr  # ignored/kyuti_audit/fr/
```

Le script ouvre une copie **en mémoire** de `example_db_in_pysaurus` (90 vidéos
sans donnée privée), avec `tests/home_dir_test` comme dossier personnel, donc
aucune base réelle n'est lue et rien n'est écrit sur disque. La copie est
enrichie pour que chaque chemin d'affichage ait quelque chose à montrer :
vignettes de synthèse, trois groupes de similarité, une paire réencodée, des
vidéos vues, deux recherches sauvegardées.

### Recette vérifiée

- `QApplication` sur le vrai plugin Windows, puis sur chaque widget
  `setAttribute(WA_DontShowOnScreen)` **avant** `show()`, `processEvents()`,
  `grab().save()`. Aucune fenêtre n'apparaît, les layouts sont activés (ce que
  `grab()` sans `show()` ne garantit pas), le rendu est le style `windows11`
  natif au facteur d'échelle de l'écran (1,5 ici : une fenêtre 1200×800 donne
  un PNG 1800×1200).
- Après chaque rafraîchissement, vider les `deleteLater()` avec
  `QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)` : la
  liste vidéo remplace ses widgets slot par slot et, sans cela, les anciens
  restent peints derrière les nouveaux dans la capture (artefact de capture,
  pas de l'application).
- Les menus se rendent avec `popup()` puis `grab()`. Les menus construits dans
  le code (menu contextuel, menu de sélection) sont attrapés en remplaçant
  `LeftClickMenu.exec` par une fonction qui capture et retourne `None` ; les
  dialogues construits inline de la même façon via `QDialog.exec`.
- **Ne jamais appeler `QAction.menu()`** : dans PySide6 6.11, le wrapper
  retourné prend la propriété du sous-menu, qui est détruit côté C++ dès que
  le wrapper temporaire disparaît (`libshiboken: Internal C++ object already
  deleted` au prochain accès). Parcourir
  `menu.findChildren(QMenu, FindDirectChildrenOnly)` à la place.
- Limites : pas de survol, d'infobulle ni d'animation. L'état coché des
  boutons radio et la surbrillance de ligne des tables (style `windows11`)
  sortent très pâles dans les captures ; les deux remarques qui en dépendent
  ci-dessous sont à confirmer à l'écran.

## Synthèse

L'interface est cohérente et fonctionnelle : la barre latérale de filtres
compacte, la mise en évidence des différences dans un groupe de similarité, le
menu contextuel bien hiérarchisé (actions destructrices en bas, en rouge), les
confirmations avec vignette et chemin, la page de progression et le dialogue
de propriétés sont des points forts.

Les faiblesses se regroupent en quatre familles :

1. **Des affichages bruts** : microsecondes partout, lignes techniques à zéro
   pour les vidéos illisibles, vue vide muette avec « Page 0/1 »,
   `Message(message='…')` dans le journal d'activité.
2. **Rien n'est persistant** côté options (taille de page, confirmation des
   entrées non trouvées).
3. **Fuites d'internationalisation** : titres de champs, « Readable »,
   « Database ready! » restent en anglais ; la page Fichiers se casse en
   français.
4. **Dette de code** : `videos_page.py` fait 3 000 lignes, deux fichiers morts.

Échelle de gravité : **P1** gêne réelle à l'usage ; **P2** finition et
cohérence. Les questions de goût sont à part.

## Fenêtre principale et menus

- **P1 – Options non persistantes.** Taille de page (`main_window.py:204-218`)
  et « Confirm deletion for entries not found » (`:222-236`) repartent à
  leur défaut à chaque lancement. Proposition : les stocker dans
  `config.json` à côté de la langue.
- **P2 – Infobulle jamais visible.** L'infobulle de l'action « Confirm
  deletion… » (`main_window.py:228`) ne s'affiche pas : un `QMenu` n'affiche
  les infobulles de ses actions qu'avec `setToolTipsVisible(True)` (fait pour
  le sous-menu des recherches sauvegardées, pas pour Options).
- **P2 – Sélecteur de page.** Les trois boutons radio dans le coin de la barre
  de menus sont une solution inhabituelle ; sur les captures, l'état coché est
  quasi invisible (à confirmer à l'écran). La page Propriétés garde en plus un
  bouton « < Back to Videos » qui fait doublon. Proposition : un vrai
  `QTabBar` ou des `QToolButton` cochables avec un état visible, et retirer le
  bouton Retour.
- **P2 – Code mort.** `_update_database_menu_state` n'est qu'un alias marqué
  obsolète (`main_window.py:662-667`), `_on_notification` est un `pass`
  (`:440-442`), `AppContext.notify_attributes_modified` n'a aucun appelant
  (`app_context.py:623-626`).
- **P2 – Journal de session.** Écrit à chaque message d'état dans
  `session_log.txt` du dossier de la base (`main_window.py:481-504`), sans
  rotation ; l'initialisation paresseuse par `hasattr` est un signe que cet
  état devrait vivre dans `__init__`.
- **Goût.** « Quitter » et « Journal de session » rangés sous Base de
  données ; la question « Are you sure you want to quit? » posée même sans
  base ouverte.

## Page Bases de données

- **P2 – Formulaire vidé avant de savoir.** `_on_create_clicked` émet le
  signal puis efface nom et sources (`:436-440`) ; si la création échoue, tout
  est à ressaisir.
- **P2 – Sources portées par le texte.** Les chemins sont stockés dans le
  libellé avec un préfixe emoji puis reparsés par `text[2:]` (`:339-349`,
  `:405-412`). Fragile ; mettre le chemin dans `UserRole`.
- **Goût.** Les trois boutons apparaissent au clic sur une carte ; un
  double-clic ouvre. Le bouton rouge « Delete » est collé à « Update ».

## Page Vidéos

### Liste

- **P1 – Durées en microsecondes.** « 07s 240000µs » sur chaque vidéo
  (`video_list_item.py:265`, `str(video.length)`) et « 15m 45s 753169µs »
  dans les statistiques (`videos_page.py:1075-1082`). `Duration.__str__`
  (`core/duration.py:75-86`) est un format de débogage ; `Duration.short()`
  existe (`:89`). Proposition : un format arrondi à la seconde pour tout ce
  qui est affiché (« 7 s », « 1 h 02 min 15 s »).
- **P1 – Lignes techniques à zéro.** Une vidéo illisible affiche
  « MOV 2.0 b / (, ) Byte rate 0 b/s » puis
  « 00s | 0 x 0 @ 0 fps, 8 bits | 0 Hz x 32 bits (0 ch), 0 b/s »
  (`video_list_item.py:221-317`). Une vidéo sans piste audio affiche
  « (h264, ) » et « 0 Hz x 32 bits (0 ch), 0 b/s ». Proposition : masquer les
  deux lignes quand `not readable`, écrire « no audio » quand `channels == 0`,
  ne pas laisser la virgule orpheline.
- **P1 – Vue vide muette.** Aucune vidéo : la zone reste blanche, la
  pagination affiche « Page 0/1 » et les boutons Suivant/Dernier restent
  actifs (`videos_page.py:1084-1098`), parce que le backend borne la page à
  `nb_pages - 1 = -1` (`video_mega_group.py:363`). Proposition : borner à 0
  côté page, afficher « Page 1/1 », et un libellé centré « No video matches
  the current filters ».
- **P2 – Puces de propriétés coupées.** Une valeur longue se replie à
  l'intérieur de sa puce (« unknown audio / codec ») car chaque valeur a
  `setWordWrap(True)` (`video_list_item.py:491`) dans un `FlowLayout` qui sait
  déjà passer à la ligne entre puces.
- **P2 – Date « (opened) » trompeuse.** `date_entry_opened` vaut la date du
  fichier quand la vidéo n'a jamais été ouverte (`database.sql:75`), donc
  chaque vidéo affiche une date d'ouverture. À n'afficher que si elle diffère
  du mtime, comme c'est déjà fait pour `date_added`
  (`video_list_item.py:353-361`).
- **P2 – Deux rangées en bas.** Statistiques à gauche sur une ligne, pagination
  centrée sur une autre, encadrée. Fusionnables en une seule barre.

### Barre latérale

- **P1 – Largeur plafonnée à 200 px** (`videos_page.py:441`). Les valeurs de
  groupe sont tronquées (« unknown audio code… ») sans infobulle, et 110
  groupes se parcourent dans une colonne étroite même en plein écran.
  Proposition : laisser le `QSplitter` aller jusqu'à ~400 px, poser le texte
  complet en infobulle sur chaque ligne de groupe.
- **P2 – Résumés cryptiques.** « Not found, Unreadable » pour les sources
  (`:1321-1332`) ne dit pas que « Not found » est « lisible mais introuvable » ;
  « "Category" (#) ▼ », « 1 groups (# > 1) » (`:1422-1438`) ; le nom de
  propriété est passé par `.title()`. Proposition : phrases courtes
  (« by Category, most frequent first », « 1 group, singletons hidden »), noms
  de propriétés tels quels.
- **P2 – Libellés non traduits.** « Readable » et « date modified » viennent
  de `path.capitalize()` et de `FIELD_MAP` (`common.py`) sans passer par
  `say()`. Voir Internationalisation.
- **Goût.** Les boutons « 𝄛 » et « ∀ » de la sélection ne se devinent pas
  sans infobulle ; les boutons de la barre latérale ont une police à 80 % du
  reste ; sections alternées gris/blanc.

### Sélection, clavier

- **P2 – Entrée.** `_open_selected` (`:362-372`) ouvre la dernière vidéo
  cliquée, ou une vidéo arbitraire de la sélection (`next(iter(set))`).
- **P2 – Erreur avalée.** `AppContext.open_random_video` attrape toute
  exception et renvoie `None` (`app_context.py:706-720`) ; `NoVideos`
  (`feature_api.py:189-190`) ne produit donc aucun retour visible quand il ne
  reste rien à voir. Un message d'état suffirait.
- **P2 – « Afficher seulement la sélection ».** Décocher une vidéo dans ce
  mode ne la retire pas de la vue avant le prochain rafraîchissement
  (`videos_page.py:1612-1620`).

### Groupes et classifieur

- **P2 – « (No value) » dans un chemin de classifieur** (`:1195`,
  `common.py:format_group_value`) : après avoir empilé une valeur, le premier
  groupe est « (No value) (61) », c'est-à-dire « aucune autre valeur ». Un
  libellé dédié (« (only this value) ») lèverait l'ambiguïté.
- **P2 – Message de concaténation.** « No single-value string properties
  available » (`:2869-2877`) alors que le filtre accepte toute propriété
  `str`, multiple ou non.

## Menu contextuel vidéo

Bien construit : état vu, ouverture, copie, renommage, similarité, propriétés,
puis les trois suppressions en bas, les deux irréversibles en rouge. Dans un
groupe de similarité, les quatre sous-menus de généralisation et de copie sont
clairs et listent les partenaires par chemin complet.

- **P2 – « Delete from database » sur une vidéo présente.** L'entrée est
  recréée à la prochaine mise à jour ; rien ne le dit. Une ligne dans la
  confirmation suffirait.

## Dialogues de la page Vidéos

- **P1 – Champ par défaut du regroupement.** Le dialogue s'ouvre sur
  « (size and length) », premier titre par ordre alphabétique
  (`grouping_dialog.py:118-128`). Proposer un champ courant (extension, année)
  ou mémoriser le dernier.
- **P2 – Combo des recherches sauvegardées** tronquée à « Wide and fou » :
  `AdjustToMinimumContentsLengthWithIcon` (`sources_dialog.py:171-176`) dans
  un dialogue de 450 px.
- **P2 – Aller à une durée.** Le placeholder « 1h30m15s / 1:30:15 » est coupé
  (`goto_duration_dialog.py:30`, largeur minimale 320).
- **P2 – Édition par lot.** La colonne centrale a une barre de défilement
  horizontale (la largeur des lignes dépasse la colonne) ; les trois colonnes
  n'ont pas le même fond. Sinon le dialogue est lisible.
- **P2 – « Delete permanently »** n'est pas en rouge dans le dialogue
  « Replace with » (`DestructiveRole` n'est pas coloré sous Windows), alors
  qu'il l'est dans le menu contextuel.

## Confirmations (toutes pages)

- **P2 – Une vingtaine de `QMessageBox.question` quasi identiques.** Chaque
  site répète titre, texte, `Yes | No` et le bouton par défaut Non
  (`videos_page.py`, `databases_page.py`, `properties_page.py`,
  `property_values_dialog.py`, `main_window.py`). Proposition : un helper
  unique `ask_yes_no(parent, title, text)` avec Non par défaut, pour que la
  règle ne dépende plus de chaque appel.
- **P2 – Boîtes « Success ».** La page Propriétés confirme chaque création,
  renommage, conversion, déplacement, remplissage par une boîte modale
  (`properties_page.py:617, 647, 700, 741, 786`) alors que la barre d'état sert
  exactement à cela ailleurs.

## Page Propriétés

Table claire, formulaire de création bien gardé (énumération et multiple
désactivés pour un booléen, valeur par défaut verrouillée quand elle serait
ignorée), menu Actions par ligne adapté au type.

- **P2 – Numéros de ligne** de la table affichés (en-tête vertical non masqué,
  `:126-148`) ; ils n'apportent rien.
- **P2 – Champ d'énumération** affiché, vide et désactivé, pour un type
  booléen ; le masquer avec son libellé.

## Page Fichiers

Bonne page : scan à la demande, deux onglets, confirmation avec aperçu des
chemins et seuil pour les lots.

- **P1 – Cassée en français.** « Trash all » devient « Tout mettre à la
  corbeille » ; la colonne est en `ResizeToContents` (`files_page.py:255`) dans
  un volet de 320 px (`:309`) : la taille totale et les boutons sortent de la
  vue, il faut une barre horizontale pour les atteindre, et l'en-tête
  « Taille totale » n'est plus visible. Proposition : un bouton icône
  (corbeille) avec infobulle, ou un libellé court, et une largeur minimale du
  volet calculée depuis le contenu.
- **P2 – Ligne sélectionnée peu visible** dans la table des extensions (à
  confirmer à l'écran) ; le titre « Files — .part (1) » est le seul repère.
- **P2 – Onglet « Others »** : « Other files » serait plus clair.

## Page de progression

Lisible : titre, anneau, barre de scan, barres par tâche, journal, bouton
Continuer vert une fois fini.

- **P1 – Journal brut.** `add_log_entry(str(notification))`
  (`process_page.py:125-127`) affiche `Message(message='3 videos could not be
  read')`, `FinishedCollectingVideos(count=…)`, etc. : `Message` et plusieurs
  notifications n'ont pas de `__str__` (`core/notifications.py`). « Database
  ready! » vient de `End.__str__` et n'est pas traduit. Proposition : un
  `__str__` lisible par notification, ou un formatteur côté page qui connaît
  les types, et passer le texte final par `say()`.
- **P2 – Pourcentage dans la barre** en blanc, illisible sous 50 %
  (`process_page.py:79-99`) et redondant avec le libellé de droite ; retirer le
  texte de la barre.
- **P2 – Aucune annulation** (déjà au backlog).

## Internationalisation

Le passage en français est globalement bon (menus, barre latérale, dialogues,
menus contextuels). Fuites constatées :

- Titres de champs (`FIELD_MAP`, `common.py`) : tri « date modified »,
  dialogues de regroupement et de tri, « (size and length) ».
- Sources : « Readable », « Not found » (`videos_page.py:1326-1332`).
- « Database ready! » et les autres `End` (`notifications.py`).
- Pluriels : « 1 groups », « video(s) » partout ; `say()` n'a pas de pluriel.
- Mise en page : page Fichiers (ci-dessus). Les autres pages tiennent.

Proposition : traduire les titres de champ au moment de l'affichage
(`say(field_info.title)` avec des titres extractibles), et un helper de
pluriel minimal.

## Code

- **P1 – `videos_page.py` : 3 005 lignes.** Candidats à l'extraction :
  construction de la barre latérale, menu contextuel et actions de
  similarité (`_add_generalize_*`, `_copy_similarity_infos`, `_replace_video`,
  ≈600 lignes), actions de sélection, navigation groupes/pages.
- **P2 – Fichiers morts.** `dialogs/batch_edit_dialog.py` (`BatchEditDialog`,
  238 lignes, aucun appelant ; remplacé par `BatchEditPropertyDialog`) et
  `widgets/unused/qts_alerter.py`.
- **P2 – Thème.** Couleurs en dur dans une douzaine de feuilles de style
  (`video_list_item.py:588-613`, `videos_page.py:443-487`,
  `databases_page.py:90-110`) : bleus différents (#0078d4, #1976d2, #4fc3f7,
  #0055cc), un vert, un rouge. Rien ne suivra le mode sombre de Windows 11.
  Tailles de police en `px` dans les feuilles de style (`videos_page.py:749,
  909`, `process_page.py:175-183`, `properties_page.py:85`) alors que la police
  de l'application est mise à l'échelle en points (`main.py`). Proposition :
  un petit module de constantes (couleurs, tailles) et des tailles relatives.
- **P2 – Monkey-patching d'instances.** `label.mousePressEvent = …` dans
  `video_list_item.py:174, 213-215, 502` ; une sous-classe `ClickableLabel`
  avec un signal est plus lisible et testable.
- **P2 – `AppContext.rename_database`** manipule `application.databases`
  directement (`app_context.py:329-342`) : logique métier dans la façade.
- **P2 – `WrappingLabel.heightForWidth`** ne fait que rappeler `super()`
  (`video_list_item.py:57-58`).

## Questions de goût

À trancher par l'utilisateur, pas des défauts :

- Densité : trois vidéos par écran en 1200×800 (vignette 220×120, huit lignes
  de texte). Une variante compacte (vignette plus petite, lignes format et
  langues fusionnées) en doublerait presque le nombre.
- Le chemin complet en police mono dans un cadre, sous un titre souligné : deux
  styles forts l'un sur l'autre.
- Les badges noirs « MP4 » et « Byte rate ».
- Le rose des différences dans un groupe de similarité, qui couvre presque
  toute la carte quand les vidéos diffèrent beaucoup.
- Le sélecteur de page dans le coin de la barre de menus plutôt qu'un onglet.
- Les boutons icône « ⚙ » / « ✕ » colorés par rôle (bleu, rouge, vert).

## Plan proposé

Par ordre de rendement :

1. **P1 rapides** : durées arrondies ; lignes à zéro masquées ; vue vide
   avec message et « Page 1/1 » ; journal d'activité lisible ; infobulles sur
   les groupes et largeur de la barre latérale ; page Fichiers en français.
2. **P1 structurants** : options persistantes ; découpage de
   `videos_page.py`.
3. **P2** : helper de confirmation unique, code mort, boîtes « Success »,
   numéros de ligne, résumés de la barre latérale, combo et placeholder
   tronqués, pourcentage dans la barre, constantes de thème, traduction des
   titres de champ, touche Entrée.
