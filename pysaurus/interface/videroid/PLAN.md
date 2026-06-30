# Plan — Interface videre pour Pysaurus (`videroid`)

> Statut : **implémenté** (phases 0–8 ; cf. §0). Ce document reste la référence
> de cadrage et la grille de parité.
> Objectif : réimplémenter l'interface de Pysaurus avec le framework **videre**,
> en reprenant **au moins toutes** les fonctionnalités de l'interface kyuti
> actuelle (`pysaurus/interface/kyuti/`), qui reste la **référence**.
> Bénéfice secondaire assumé : **éprouver videre en conditions réelles**
> (backend de rendu, moteur de texte, performances sur grosse UI) et
> **débusquer les insuffisances** de ses widgets.

---

## 0. État d'avancement (2026-06-29)

**Phases 0–8 faites et committées — parité de cœur avec kyuti :**
- **Phase 0** Fondations (`app.py`, `context.py`, `pages/base_page.py`, `run_with_videroid.py`) — Window, navigation, pont de notifications.
- **Phase 1** Page **Databases** (liste expand/collapse, Open/Update/Delete, création + sélecteur de fichiers natif `videre.Dialog`).
- **Phase 2** Page **Process** (`pages/process_page.py`) — spinner, barres de jobs, log, Continue.
- **Phase 3** Page **Videos — affichage** (`pages/videos_page.py`, `widgets/video_card.py`) — cartes (~20 champs, vignette PIL), pagination, status bar.
- **Phase 4** **Filtres** (sidebar) : Search + Sorting (`dialogs/sorting_dialog.py`), Grouping + Groups + classifier (`dialogs/grouping_dialog.py`), Sources (`dialogs/sources_dialog.py`).
- **Phase 5** **Sélection + actions** — multi-sélection (cases à cocher + menu ⚙) ; menus contextuels via `Window.set_context` ; actions par vidéo (watched/open/dossier/copier/renommer/supprimer×3) ; `dialogs/batch_edit_property_dialog.py`.
- **Phase 6** Page **Properties** + dialogs (`property_values`, `move_values`, `fill_property`, `batch_edit_property`).
- **Phase 7** Page **Files** (scan, 2 onglets, corbeille).
- **Phase 8** **Coquille** (barre de menus composée de `ContextButton`, titre in-app, status bar, page-size, `Window(alert_on_exceptions=…)`) + dialogs Rename DB / Edit Folders.

**Reste à faire :**
- **Raccourcis clavier** (G-KBD) — manque videre de fond : le dispatch keydown est mono-cible, sans bubbling ; à traiter au niveau `Window`/`WindowLayout`. Cf. `GAPS.md`.
- **video_properties_dialog** — édition des propriétés *par vidéo* depuis le ⚙ de la carte (différé en Phase 6).
- **Niche** : Find Similar / Re-encoded, Random / Generate Playlist, Session Log ; classifier *concat* ; titre OS dynamique (G-TITLE) + mise à l'échelle DPI (G-DPI).
- **Enrichir videre** : bâtir les vrais widgets (Table, Tabs, MenuBar, virtualisation…) maintenant que les besoins sont éprouvés (cf. §4.2 + `GAPS.md`).

**Perf (verdict 2026-06-28) :** le premier rendu d'une page de cartes est ~72 % « shaping » de texte (CPU 100 %) contre ~0,2 % rasterisation → un backend GPU n'accélérerait **pas** le texte. Seul levier d'ordre de grandeur : **virtualiser le build** (ne pas shaper les cartes hors écran ; G9). Bench durables : `wip/videroid_perf/` (cf. §6).

## 1. Contexte & principes

- **Référence** : `pysaurus/interface/kyuti/` (27 modules, ~10 000 LOC, 5 pages
  + 1 page dynamique, 13 dialogs, 4 widgets custom). La parité se mesure contre elle.
- **Le backend est partagé et agnostique du frontend.** La couche API est en 3
  niveaux : `FeatureAPI` → `GuiAPI` → `KyutiAPI`. Seul le dernier est lié à Qt.
  Une interface videre réutilise `GuiAPI` **tel quel**.
- **Pas de `__run_feature__`.** Ce dispatcher générique (hérité de l'ère web/JSON)
  n'a plus aucun appelant. kyuti fait des **appels Python directs** :
  - opérations longues → méthodes de `GuiAPI` (threadées via `@process`) ;
  - opérations synchrones → accès **direct** à `api.database` / `.ops`
    (`DatabaseOperations`) / `.algos` (`DatabaseAlgorithms`) / `.view`
    (`ViewContext`).
  `videroid` fera pareil.
- **`AppContext` (app_context.py, 731 LOC) est le modèle à répliquer** : c'est le
  « ViewModel » qui traduit UI ↔ backend. Sa logique est réutilisable presque
  telle quelle ; seuls les `signal.emit()` Qt sont à remplacer par le mécanisme
  de notification de videre.
- **Repartir propre** dans `pysaurus/interface/videroid/` (et non reprendre le
  `wip/.../using_videre` abandonné). Ce dernier (~1244 LOC, ~50 % couvert) sert de
  **source d'inspiration / cannibalisation** : son `backend.py` (façade sur
  `GuiAPI`), son `video_view.py` (carte vidéo) et son `path_set_view.py` sont
  réutilisables après dépoussiérage (un seul vrai cassage d'API : l'import disparu
  `videre.core.pygame_utils`).

---

## 2. Architecture cible

```
videroid/
  __init__.py
  run_with_videroid.py        # point d'entrée (équivalent de kyuti/main.py)
  app.py                      # Application : Window videre + navigation entre pages
  context.py                  # ViewModel = réplique d'AppContext (sans Qt)
  notifications.py            # pont notifications backend -> rafraîchissements UI
  pages/
    databases_page.py
    videos_page.py
    properties_page.py
    files_page.py
    process_page.py
  widgets/
    video_card.py             # carte vidéo (cf. video_view.py de using_videre)
    menu_bar.py               # barre de menus (construite sur ContextButton)
    table.py                  # widget Table maison (gap videre, cf. §4)
    tabs.py                   # widget Onglets maison (gap videre, cf. §4)
    ...
  dialogs/
    ...                       # un module par dialog (cf. §3.7)
```

**Couture backend (`context.py`)** : tient une instance de `GuiAPI`
(sous-classée pour brancher `_notify` sur videre, comme `KyutiAPI` le fait pour
Qt). Expose les actions par appels directs ; branche un callback de notifications.

**Boucle / navigation (`app.py`)** : une `Window` videre dont les `controls`
basculent entre pages (équivalent du `QStackedWidget`). Les opérations longues
basculent vers la `process_page` ; le retour de notification `End` ramène à la
page précédente.

**Threading** : `GuiAPI` lance déjà ses opérations longues en threads. Il faut
acheminer les notifications depuis le thread de fond vers le thread UI de videre
de façon sûre — videre expose `Window.call_later` / `call_async` / `call_now`
pour réinjecter des callbacks dans la boucle (à utiliser comme `AppContext` le
fait avec les `QueuedConnection`).

---

## 3. Inventaire exhaustif des fonctionnalités à reprendre

> Source de vérité : les fichiers `pysaurus/interface/kyuti/**`. Référence le
> fichier par section ; voir le code pour le détail ligne à ligne.

### 3.1 Coquille applicative & navigation
*(main.py, main_window.py)*

- Fenêtre 1200×800, titre dynamique selon page/base :
  « Pysaurus - Databases / [DB] / Properties - [DB] / Files - [DB] / [Process]… ».
- Démarrage sur la page **Databases**. Aucune restauration d'état (ni dernière
  base, ni géométrie).
- **Mise à l'échelle DPI** de la police (min 11 pt ; facteur selon device pixel
  ratio ; borné 1.0–2.5×).
- Navigation : 4 pages permanentes (Databases, Videos, Properties, Files) +
  **Process** dynamique. Sélecteur **radio en haut à droite** : Videos /
  Properties / Files (Databases sans radio = point d'entrée). Radios + menus
  **désactivés** pendant une opération (page Process visible) et **cachés** sans
  base ouverte.
- **Barre de statut** : message persistant, **clic = effacer**, messages
  horodatés journalisés ; « Ready » au départ.
- **Fermeture** : confirmation « Are you sure you want to quit? » → `close_app()`.
- **Exceptions non gérées** : dialog d'avertissement (ApplicationError/OSError)
  ou « Fatal Error » avec traceback détaillé.

### 3.2 Barre de menus
*(main_window.py)*

- **Database** : `Rename Database…`, `Edit Folders…`, `Update Database`,
  `Find Similar Videos`, `Find Re-encoded Videos`, `Close Database`,
  `Session Log…`, `Quit`. (Tous désactivés tant qu'aucune base n'est ouverte.)
- **View** (actif seulement sur la page Videos avec base) : `Random Video (Ctrl+O)`,
  `Generate Playlist (Ctrl+L)`, `Refresh View (Ctrl+R)`.
- **Options** : sous-menu **Page Size** (radio exclusif **10 / 20 / 50 / 100**,
  défaut 20 ; actif sur Videos) ; **toggle** « Confirm deletion for entries not
  found » (coché par défaut).
- **Help** : `About`.

### 3.3 Page Databases
*(databases_page.py)*

- Deux colonnes : liste des bases (gauche) / création (droite).
- **Liste** : items expand/collapse, **un seul ouvert à la fois** ; **double-clic
  = ouvrir** directement.
- Boutons par base (révélés à l'expansion) : **Open** (sans update), **Update**
  (open + scan, avec confirmation), **Delete** (rouge, confirmation).
- **Création** : champ `Name` ; liste `Sources (folders and files)` (📁/📄) ;
  boutons **Add Folder**, **Add File** (filtre extensions vidéo, multi-sélection,
  dédoublonnage), **Remove** ; bouton **Create Database** (validation : nom non
  vide + ≥ 1 source ; confirmation).

### 3.4 Page Videos (cœur — videos_page.py, video_list_item.py)

**Carte vidéo** — champs affichés : vignette 180×100 (placeholder si absente) ;
titre fichier (checkbox + gras souligné, **diff caractère** en groupe de
similarité) ; meta-titre (italique gris) ; chemin (bleu-violet si non vu / gris
italique si vu) ; badges EXT / taille / conteneur / codecs / débit ; durée
(bleu) / résolution (vert) @ fps / profondeur / échantillonnage / audio ; dates
(fichier, modif, ouverture) ; langues audio & sous-titres (ou « (none) ») ;
statuts **NOT FOUND** (rouge) / **Unreadable** (orange) / **Watched** (vert) /
Similarity ID / Re-encoded ID ; messages d'erreur ; **propriétés custom
(nom : valeur)** avec **valeurs cliquables** (clic = filtrer par
propriété=valeur).

**États visuels de la carte** : neutre / survol / sélection / sélection+survol /
**not-found (jaune)**, chacun avec fond + bordure spécifiques ; soulignement du
chemin au survol.

**Pagination** : `<<` `<` `Page X/Y` (clic = goto) `>` `>>` ; boutons
désactivés en bornes ; **goto dialog**.

**Sélection** : checkbox ; clic titre = toggle ; **Ctrl+A** (page),
**Ctrl+Shift+A** (vue entière), **Échap** (vider), **Ctrl+Shift+D** (n'afficher
que la sélection) ; compteur « N selected » ; **sélecteur persistant cross-page**.

**Sidebar de filtres** (chaque section : libellé + ⚙ réglages + ✕ effacer) :
- **Sources** : « All readable » / liste / expression ; ⚙ ouvre SourcesDialog.
- **Grouping** : champ + tri + flèche ; bouton « Confirm all unique moves »
  (visible si groupé par move_id).
- **Classifier path** (propriété multiple) : badges du chemin + ✕ sur le dernier ;
  **Reverse**, **Concat…**.
- **Search** : champ (placeholder « Search… (Ctrl+F) ») + modes **AND / OR /
  Exact / ID** (le mode actif en gras) + ✕.
- **Sorting** : liste de champs avec ▲/▼.
- **Selection** : compteur + **Page** / **All** / ✕.
- **Groups** (si groupement actif) : liste des groupes + navigation
  `|<<` `<` count `>` `>>|` + ✙ (ajouter au classifier).

**Menu contextuel par vidéo** (clic droit) : `Toggle Watched`, `Open`,
`Open in VLC`, `Open Folder`, sous-menu **Copy** (Title / File Title / File Path /
Video ID), `Rename…`, `Move to…`, similarité (`Dismiss`/`Reset`, + variantes
re-encoded), `Generalize meta/file title into property…` (en groupe de
similarité), `Confirm move to […]`, `Properties…`, `Delete from database`,
`Move to Trash`, `Delete permanently`.

**Menu de sélection** (⚙) : `Show Only Selected (Ctrl+Shift+D)` (toggle),
`Toggle Watched`, sous-menu `Edit Properties` (une entrée par propriété →
BatchEditPropertyDialog).

**Raccourcis clavier (page Videos)** — checklist :
`Home`/`End` (1ʳᵉ/dernière page), `←`/`→` (page préc./suiv.), `↑`/`↓` (groupe
préc./suiv.), `Ctrl+A` / `Ctrl+Shift+A` (sélection), `Échap` (vider),
`Ctrl+Shift+D` (show only selected), `Entrée` (ouvrir), `Suppr` (supprimer),
`Ctrl+L` (playlist), `Ctrl+G` / `Ctrl+Shift+G` (grouping / clear),
`Ctrl+F` / `Ctrl+Shift+F` (recherche / clear), `Ctrl+Shift+S` (sorting),
`Ctrl+T` / `Ctrl+E` / `Ctrl+Shift+T` (sources simple / expression / reset),
`Ctrl+O` (random), `Ctrl+R` (refresh), `Ctrl+P` (page Properties).

**Autres comportements** : préservation du scroll lors des MAJ ; reset du scroll
au changement de page/groupe/filtre ; status bar « N videos | taille | durée » ;
recalcul des tailles d'items au redimensionnement ; tooltips.

### 3.5 Page Properties
*(properties_page.py)*

- **Table** 6 colonnes : Name / Type / Default / Multiple / Enum / Actions
  (lecture seule, couleurs alternées). Bouton **Refresh**.
- **Fill with Terms…** (remplir une propriété depuis les termes des noms de
  fichiers).
- **Actions par propriété** (menu) : `Manage Values…` (str), `Rename…`,
  `Convert to Single/Multiple Value`, `Move Values…` (str-multiple), `Delete`.
- **Création** : `Name` ; `Type` (str/int/float/bool) ; `Allow multiple` (str) ;
  `Use enumeration` + `Enum values` (CSV) ; `Default` (parsé selon le type) ;
  boutons **Reset** / **Create Property** (validations).

### 3.6 Page Files
*(files_page.py)*

- État initial : bouton **Scan folders**. Ensuite **Rescan folders** + résumé
  « X other files (size) · Y indexed · Z unknown ».
- **Onglet « Others »** : à gauche table extensions (Extension / Count / Total
  size / **Trash all**) ; à droite fichiers de l'extension sélectionnée (**Open
  folder**, **Send to trash**, **filtre** texte ; table Path/Size multi-sélection).
  Confirmation de mise en corbeille (aperçu 5 chemins, alerte si > 500).
- **Onglet « Video stats »** (lecture seule) : Extension / Indexed (count, size) /
  Unknown (count, size).

### 3.7 Process page & notifications
*(process_page.py, app_context.py)*

- Page **dynamique** : titre, **spinner**, barre de scan dossier conditionnelle,
  **conteneur de jobs** (une `JobProgressWidget` par job, % affiché),
  **Activity Log** (défilant + bouton **Clear**), bouton **Continue** (vert,
  activé à la fin ; mode **autocontinue** possible).
- Chaque opération a son **collecteur de notifications** indépendant.
- **Notifications backend → réactions UI** (à répliquer) :
  `DatabaseReady` → recharger la vue ; `JobToDo` → créer une barre de job ;
  `JobStep` → avancer ; `FolderScanProgress` → barre de scan ;
  `ProfilingStart/End` → entrées de log ; `Done`/`Cancelled`/`End` → activer
  Continue, stopper le spinner ; `state_changed` → rafraîchir la page courante ;
  `notification_received` → journal de session.
- **Routage** : quand la Process page est active, les notifications vont à elle ;
  sinon aux pages via le mécanisme de rafraîchissement.

### 3.8 Les 13 dialogs
*(dialogs/)*

1. **video_properties_dialog** (le plus gros) — 2 onglets : **Properties**
   (liste des propriétés + formulaire défilant ; éditeurs **par type** : enum =
   combo/cases, bool = case, int = spin, float/str = champ ; multi-valeurs =
   liste add/remove ou cases ; boutons Reset/Clear par propriété ; feedback
   italique=défaut, bleu=modifié) ; **Info** (métadonnées lecture seule : File /
   Video / Audio / Status). OK n'envoie **que les valeurs changées**.
2. **batch_edit_dialog** — éditer des propriétés sur N vidéos ; **case d'activation
   par propriété** ; seules les cochées s'appliquent.
3. **batch_edit_property_dialog** — édition d'**une** propriété sur N vidéos ;
   interface **3 colonnes** (To remove / Current / To add) + ajout d'une nouvelle
   valeur (éditeur par type) ; règles distinctes single/multiple.
4. **grouping_dialog** — Type (attribut/propriété) + champ ; tri (valeur / nombre
   de vidéos / longueur) ; `Reverse order` ; `Allow singletons` ; boutons Apply /
   Clear Grouping / Cancel.
5. **sorting_dialog** — liste **multi-niveaux** réordonnable (drag-drop **ou**
   Move Up/Down) ; Toggle Direction ; Remove ; ajout d'un champ (Add ↑ / Add ↓) ;
   Apply / Reset / Cancel.
6. **sources_dialog** — 2 onglets : **Simple** (cases Readable/Unreadable ×
   found/not-found × with/without thumbnails ; Select All / None / Valid Only) ;
   **Advanced** (éditeur d'**expression** + affichage d'erreur ; Shift+Entrée =
   valider).
7. **edit_folders_dialog** — liste de sources multi-sélection ; Add Folder… /
   Add File… / Remove Selected (confirmation) ; compteur ; ≥ 1 source requise.
8. **rename_dialog** — champ pré-rempli, validation (non vide, différent), OK
   désactivé tant qu'invalide.
9. **goto_page_dialog** — spin 1..N + « / N ».
10. **fill_property_dialog** — combo (propriétés **str-multiple** seulement) +
    case « Only fill videos without values ».
11. **move_values_dialog** — liste de valeurs (avec compte) + propriété cible
    (combo) + case **Concatenate**.
12. **property_values_dialog** — liste des valeurs (avec compte) + menu contextuel
    (Delete / Rename / Copy) + boutons (Delete Selected, Rename Value…) +
    **modificateurs** dynamiques (Lowercase / Uppercase / …) ; bouton Close.
13. **video_confirm_dialog** — confirmation destructive avec **vignette** 160×90 +
    chemin (monospace, sélectionnable) + message ; Yes / No.

**Conventions transverses** : dialogs **modaux** ; `Entrée`=OK / `Échap`=Cancel
(sauf champs multi-lignes) ; validations + confirmations destructives ; feedback
bleu (modifié) / italique (défaut) ; chargement de l'état à l'ouverture, résultat
seulement sur OK.

---

## 4. Correspondance videre & insuffisances à traiter

### 4.1 Couvert par videre (réutilisation directe)

| Besoin pysaurus | Widget videre |
|---|---|
| Conteneurs / disposition | `Column`, `Row`, `Container`, `Div`, `ScrollView` |
| Texte / libellés | `Text`, `Label` |
| Boutons | `Button`, `SubmitButton`, `AbstractButton` |
| Cases / radios | `Checkbox`, `Radio`, `RadioGroup` |
| Listes déroulantes | `Dropdown` |
| Menus & popups | `ContextButton` (plat) **+ `Window.set_context()`** (popup attaché → menus / sous-menus / barre de menus par composition) |
| **Vignettes** (depuis `bytes`) | `Picture` (charge `bytes`/`BytesIO` via PIL) ✅ — **redimensionner via PIL en amont** (cf. G13) |
| Champs de saisie | `TextInput` (mono-ligne — cf. G11/G12) |
| Formulaires | `Form` (`.values()` collecte TextInput/Checkbox/Dropdown/RadioGroup par `.name`) + `SubmitButton` |
| Barres / spinner de progression | `ProgressBar`, `Progressing` |
| **Modales / dialogs** | `Window.set_fancybox()` + `Fancybox` / `FancyCloseButton` ; **prêts : `Window.confirm()` / `alert()` / `error()`** |
| **Sélecteur de fichiers/dossiers** (natif, cross-platform) | `Dialog.select_directory` / `select_file_to_open` / `select_many_files` / `select_file_to_save` (via `filedial` = `tkinter.filedialog`) ✅ |
| Styles / états (hover/click) | `Div` + `Style`/`StyleDef` |
| Presse-papier | `Clipboard` |
| **Notifications applicatives** | `Window.notify()` + `set/add/remove_notification_callback` (bus intégré pour le pont backend→UI) |
| Planification & threads | `Window.call_later/call_async/call_now` + `TaskManager` + `launch_thread` (post_task thread-safe) |
| Raccourcis clavier | `handle_keydown` + `KeyboardEntry` (`ctrl`/`alt`/`shift` + `.unicode`) — **câblage manuel**, pas de registre |
| Tests headless | `StepWindow` + `FakeUser` (click / clavier / molette / resize) |

### 4.2 Insuffisances videre (manques confirmés)

> Ce sont les **insuffisances à débusquer** annoncées. Pour chacune : un
> contournement v1 (côté `videroid`) **et** la piste d'enrichissement videre.

| # | Manque | Impacte | Contournement v1 | Piste videre |
|---|---|---|---|---|
| G1 | **Pas de widget Table** | Properties, Files | `Column` de `Row` (cellules) ; tri/colonnes maison | créer un `Table` dans videre |
| G2 | **Pas d'onglets** | video_properties, sources, Files | boutons + bascule de contenu | créer un `Tabs`/`TabView` |
| G3 | Pas de **barre de menus** native | coquille | **atténué** : barre de `Div`/`Button` + `Window.set_context()` (déroulants par composition) | `MenuBar` dédié |
| ~~G4~~ | ✅ **RÉSOLU** : `videre.Dialog` (`filedial` → `tkinter.filedialog`, natif cross-platform) | Databases, edit_folders | utiliser `Dialog.*` directement | (optionnel) exposer `filetypes`/`initialdir` + retirer le `print` parasite |
| G5 | **Pas de champ numérique** (SpinBox) | goto_page, propriétés int/float | `TextInput` + validation | `NumberInput` |
| G6 | **Aucun tooltip** | partout (UX) | différer ; libellés explicites | survol/tooltip dans videre |
| G7 | **Pas de splitter** ajustable | sidebars, splitters | `Row`/`Column` à largeurs fixes | `Splitter` redimensionnable |
| G8 | **Pas de drag-drop** | sorting_dialog | boutons Move Up/Down (déjà présents en parallèle) | drag-drop générique |
| G9 | **`ScrollView`/`Column`/`Row` non virtualisés** (confirmé : rendent tous les enfants) | listes longues | la **pagination** (≤100) borne le besoin | virtualisation (axe perf) |
| G10 | `ContextButton` **plat** (pas de sous-menus / items cochables / icônes) | Copy, Edit Properties, Show-Only-Selected | **atténué** : menus custom via `Window.set_context()` (sous-menus par composition ; coche via glyphe ☑) | menus riches natifs |
| G11 | **`TextInput` mono-ligne** | sources_dialog (expression) | éditeur 1 ligne ou champs multiples | `TextArea` multi-ligne |
| G12 | **`TextInput` sans placeholder** | Search, etc. | texte grisé géré à la main / label adjacent | placeholder natif |
| G13 | **`Picture` ne redimensionne pas** (taille native) | vignettes (180×100) | **redimensionner via PIL en amont** (on a les bytes) | `width`/`height`/fit dans `Picture` |
| G14 | **`ProgressBar` sans libellé %** | page Process | superposer un `Text` | label intégré |

> **Décision (tranchée le 2026-06-25) : on CONTOURNE d'abord, on enrichit videre
> APRÈS.** `videroid` est codé avec videre **tel quel** ; chaque manque rencontré
> est noté (`GAPS.md`, cf. §6) avec son contournement, et l'enrichissement de videre
> (Table, Tabs, MenuBar, virtualisation…) viendra dans un second temps, une fois les
> besoins réels éprouvés.

---

## 5. Découpage en phases

Chaque phase est **exécutable et testable** (ouvrir l'appli, comparer à kyuti),
et éprouve un aspect précis de videre.

- **Phase 0 — Fondations.** `context.py` (façade `GuiAPI` ; pont backend→UI via
  `Window.notify` + `call_async`/`TaskManager`), `app.py` (Window + navigation de
  pages), squelette des pages vides, point d'entrée. *Éprouve : boucle, threading,
  pont de notifications.*
- **Phase 1 — Page Databases.** Liste expand/collapse, Open/Update/Delete,
  formulaire de création (sélecteur de fichiers/dossiers via `videre.Dialog`,
  **déjà fourni** — cf. G4). *Éprouve : formulaires, listes, file-picker.*
- **Phase 2 — Process page + notifications.** Indispensable (open/update/scan sont
  longs). Spinner, barres de jobs, activity log, Continue/autocontinue, routage.
  *Éprouve : `ProgressBar`/`Progressing`, réactivité notifications.*
- **Phase 3 — Page Videos (affichage).** Carte vidéo complète (~20 champs),
  pagination, status bar (vignettes redimensionnées via PIL — cf. G13). *Éprouve :
  `Picture`, **rendu de texte massif**, layout des cartes, **perf de scroll**
  non virtualisé (objectif initial — cf. G9).*
- **Phase 4 — Page Videos (filtres).** Sidebar (Sources, Grouping, Search,
  Sorting), Groups panel, classifier ; dialogs grouping / sorting / sources.
  *Éprouve : interactions, onglets (G2), expression.*
- **Phase 5 — Page Videos (sélection + actions).** Multi-sélection, menus
  contextuels (via `Window.set_context`), actions par vidéo
  (open/rename/delete×3/move/similarity/copy), **tous les raccourcis clavier**
  (`handle_keydown`), confirmations via `Window.confirm`. *Éprouve : menus custom
  (G10), clavier global.*
- **Phase 6 — Page Properties + dialogs propriétés.** Table (G1), CRUD,
  video_properties_dialog, batch_edit(_property), fill_property, move_values,
  property_values. *Éprouve : Table, éditeurs par type.*
- **Phase 7 — Page Files.** Scan, 2 onglets (G2), tables (G1), trash. *Éprouve :
  Table + Tabs en conditions réelles.*
- **Phase 8 — Coquille & finitions.** Barre de menus complète (G3), session log,
  exception handling, mise à l'échelle DPI, polish visuel, parité finale.

> Au plus tôt utilisable de bout en bout : fin de Phase 3 (ouvrir une base et
> parcourir ses vidéos) — c'est aussi le premier vrai **benchmark perf**.

---

## 6. Stratégie de test & validation

- **Test manuel comparatif** : lancer `videroid` et `kyuti` sur la **même base
  réelle**, comparer écran par écran et action par action (la checklist du §3 sert
  de grille de parité).
- **Journal des insuffisances videre** : tenir un fichier (p. ex.
  `videroid/GAPS.md`) recensant chaque manque rencontré, son contournement, et la
  décision (enrichir videre / contourner). Alimente le travail sur videre.
- **Perf** (objectif initial) : mesurer le rendu de la page Videos sur grosse base
  (centaines de cartes, scroll), comparer au profil déjà établi (le coût est
  côté pipeline Python, pas la rasterisation ; surveiller la virtualisation G9).
- **Tests automatisés** : **disponible** — videre fournit `StepWindow` (rendu
  headless : `render()` / `screenshot()` / `find()`) + `FakeUser` (click / clavier
  / molette / resize). À utiliser au moins pour les widgets custom (Table, Tabs,
  MenuBar) et le ViewModel (`context.py`).

---

## 7. Risques & décisions ouvertes

1. **Enrichir videre vs contourner** — ✅ **tranché : contourner d'abord, enrichir
   après** (cf. §4.2). videre est utilisé tel quel ; les gaps sont consignés dans
   `GAPS.md`.
2. **Sélecteur de fichiers (G4)** — ✅ **résolu** : `videre.Dialog`
   (`filedial` → `tkinter.filedialog`) fournit les dialogs natifs cross-platform.
   Nuances mineures : modal (gèle l'UI le temps de la sélection — normal), pas de
   filtre `filetypes` ni `initialdir` exposés pour les fichiers, un `print`
   parasite à la fermeture ; tkinter requis (`python3-tk` sur certaines distros).
3. **Threading & notifications** — ✅ **outillé** : `TaskManager` (post_task
   thread-safe drainé dans la boucle) + `call_async`/`call_later`/`launch_thread`
   + `Window.notify`. Reste à câbler proprement avant la Phase 2.
4. **Virtualisation (G9)** — **confirmé non virtualisé** (`ScrollView`/`Column`/
   `Row` rendent tous les enfants). La pagination suffit en v1 ; axe perf majeur
   ensuite (et c'est l'objet de l'étude perf initiale).
5. **i18n** — kyuti est **tout en anglais en dur** (pas d'i18n actif), alors que
   le core a un système de langue (`set_language`, english/français). Hors parité
   stricte ; à considérer comme amélioration possible.
6. **Récupération de `using_videre`** — décider quels fichiers cannibaliser
   (`backend.py`, `video_view.py`, `path_set_view.py`) après dépoussiérage de
   l'API videre actuelle.
