# KYUTI_REFERENCE.md — spec visuel & comportemental de l'interface de référence

Inventaire **exhaustif** des caractéristiques de l'interface **kyuti**
(`pysaurus/interface/kyuti/`, PySide6/Qt), relevé **dans le code** (revue
minutieuse, `file:line` + valeurs exactes). C'est la **référence de parité** : la
grille `PARITY.md` se remplit contre ce document, et tout ce que videre ne peut
pas reproduire devient une entrée `GAPS.md`.

> ⚠️ **Caractéristique structurante : kyuti n'a AUCUN stylesheet global.** `main.py`
> crée `QApplication` sans `setStyleSheet`/`setStyle("Fusion")`. Toute la chrome
> (barre de menus, radios, barres de défilement, en-têtes de table, popups de
> combo, `QMessageBox`, `QGroupBox`, spin arrows) est rendue par le **thème Qt
> natif de l'OS**. Seuls quelques `setStyleSheet` **inline** (listés ci-dessous)
> ajoutent des couleurs. → videre, qui dessine ses propres widgets, **ne peut pas**
> reproduire la chrome native à l'identique (différence de framework inhérente).

---

## 0. Global / coquille

**Application & police (`main.py`)**
- `QApplication`, `setApplicationName/OrganizationName("Pysaurus")`.
- **Scaling DPI de la police** (`main.py:18-97`) : `MIN_FONT_SIZE_PT=11`, `DPR_SCALE_FACTOR=0.20` ; `final_scale = max(11/pt, 1.0) + 0.20·max(0, DPR−1)`, **borné [1.0, 2.5]** ; appliqué seulement si `>1.0`. → police de base **≥ 11pt**, dynamique par écran. **Beaucoup de tailles de widgets sont multipliées par `app.font().pointSize()/9`** (cf. carte vidéo).
- Exceptions (`main.py:100-129`) : `ApplicationError`/`OSError` → `QMessageBox.warning` **non fatal** (app continue) ; tout le reste → `QMessageBox(Critical, "Fatal Error", …)` + **traceback dans `setDetailedText`** + `exit(1)`. Exceptions de threads de fond ré-émises sur le thread principal → même hook.

**Fenêtre (`main_window.py`)**
- `resize(1200, 800)`, **redimensionnable**, pas de min/max. Central = `QStackedWidget` (databases=0, videos=1, properties=2, files=3 ; process ajoutée dynamiquement).
- **Titre** : `Pysaurus - Databases` / `Pysaurus - {db}` (videos) / `Pysaurus - Properties - {db}` / `Pysaurus - Files - {db}` / `Pysaurus - {process_title}`.
- **Navigation** : `QStackedWidget` + **sélecteur radio en corner widget haut-droite** (`Videos`/`Properties`/`Files`, natif, `spacing 8`, margins `(0,0,4,0)`) — **caché sans base et pendant un process**. Pas de radio pour Databases.
- **Barre de menus** (ordre G→D : Database, View, Options, Help) — voir §0b.
- **Barre de statut** : `"Ready"` par défaut, **clic = effacer** (eventFilter), messages persistants (timeout 0) + toasts 3 s ; **journal de session** horodaté → fichier `{db}/session_log.txt` + `SessionLogDialog` (700×500, `QPlainTextEdit` read-only).

### 0b. Barre de menus (libellés exacts, `main_window.py:114-225`)
- **Database** : `Rename Database…`, `Edit Folders…`, —, `Update Database`, —, `Find Similar Videos`, `Find Re-encoded Videos`, —, `Close Database`, —, `Session Log…`, `Quit`. Tous `setEnabled(has_db)` sauf Quit.
- **View** (actif si `has_db` et page Videos) : `Random Video (Ctrl+O)`, `Generate Playlist (Ctrl+L)`, —, `Refresh View (Ctrl+R)`. ⚠️ Les « Ctrl+… » sont du **texte de libellé**, pas des accélérateurs — les vrais `QShortcut` sont sur la page Videos (§B5).
- **Options** : sous-menu `Page Size` = **`QActionGroup` exclusif** (radio) 10/20/50/**100** (défaut **20**) ; toggle **`Confirm deletion for entries not found`** (cochable, **défaut ON**).
- **Help** : `About` (`QMessageBox.about`).

---

## A. Palette de couleurs récurrente (à reproduire exactement)

| Rôle | Couleur(s) |
|---|---|
| Accent bleu (sélection counter, barre de progression, spinner, page-link) | `#0078d4` ; hover `#005a9e` |
| Bleu « modifié » (valeurs de propriété éditées, recherche active) | `#0055cc` |
| Bleu sélection carte / chips propriété | `#e3f2fd` (fond) · `#1976d2` (bordure/texte) · sélection+survol `#d0e8fc`/`#1565c0` |
| Vert succès (Continue activé, checkmark spinner, classifier btn) | `#4CAF50` ; hover `#45a049` ; Watched `#008800` |
| Rouge danger (clear btn, delete db, NOT FOUND, errors) | `#cc3333`/hover `#dd4444` · `#cc0000` · trash-all `#a40000` · delete-db `#cc3333`/`#dd4444` |
| Orange (Unreadable, not-found survol) | `#cc6600` · `#ff9800`/`#ffecb3` · not-found `#fffde7`/`#ffe082` |
| Gris muet (textes secondaires, infos sidebar) | `#555` · `#666` · `#888` · `#aaa` |
| Fonds gris clairs / zébrures custom | sidebar `#f0f0f0`/`#ffffff` · badges props `#f5f5f5` · pistes `#e0e0e0`/`#f0f0f0` · bordures `#ccc`/`#ddd`/`#bbb` |
| Badges format | fond `#333` texte blanc |
| Specs vidéo | durée `#0066cc` · résolution `#006600` · dates `#996600` |
| Diffs de groupe | champ `#ffcccc` · caractère `#ff9999` |

> **Zébrures de table** (Properties, Files) = `setAlternatingRowColors(True)` = **`AlternateBase` natif Qt**, PAS un hex custom. Idem en-têtes de table : natifs.

---

## B. Carte vidéo (`widgets/video_list_item.py`, `VideoListItem(QFrame)`) — la pièce maîtresse

**Layout** : `QHBoxLayout` margins `(8,8,8,8)` spacing **12** = `[vignette | détails]` ; détails = `QVBoxLayout` spacing **3**, stretch 1. `SizePolicy(Expanding, Preferred)`.

### B1. ⚑ Vignette = cadre FIXE centré
- `QLabel` **`setFixedSize(180, 100)`** (× `pt/9`) + **`setAlignment(AlignCenter)`** → tous les cadres identiques, **colonne de gauche alignée quel que soit le ratio**.
- Pixmap `scaled(180,100, KeepAspectRatio, SmoothTransformation)` (letterboxé, centré). Fond `#e0e0e0`, bordure `1px #ccc`, **radius 2px**.
- ⚠ Placeholder « No thumbnail » (`#e0e0e0`/`#666`/`1px #ccc`) **omet le radius** → coins carrés vs arrondis selon l'état.

### B2. Lignes de détails (toutes en `WrappingLabel`, rich text)
- `WrappingLabel` (`:44-62`) : `wordWrap`, `heightForWidth`, **`sizeHint` plafonné à 400px de large** → grandit en hauteur (pilote la hauteur de carte).
1. **Titre** : `QCheckBox` (à gauche) + label **gras+souligné** `#000000`, curseur main, **clic = toggle checkbox**.
2. **Meta-titre** (si présent) : italique `#666666`.
3. **Nom de fichier** (clic = ouvrir, **survol = souligné**) — 2 états : non-vu `#8c8cfa` **gras** sur `#fafafa` + bordure `#f0f0fa` ; vu `#a0a0a0` italique sur `#f8f8f8` ; **monospace** `<code>`.
4. **Format** : badge EXT (`#333`/blanc), `taille / conteneur (codec, codec)` codecs gris `#666`, badge « Byte rate », débit.
5. **Specs** : durée **`#0066cc`** gras · largeur/hauteur **`#006600`** gras · fps/bits/audio gris `#666`.
6. **Dates** : monospace **`#996600`** ; `(entry)`/`(opened)` italique `#888`.
7. **Langues** : `Audio:`/`Subtitles:` gras `#333`, valeurs `#555`, `(none)` `#aaa`.
8. **Statuts** : `NOT FOUND` **`#cc0000` gras** · `Unreadable` **`#cc6600` gras** · `Watched` `#008800` · `Similarity ID:n` `#0066cc` (`(no match)` `#666`) · `Re-encoded ID:n` `#9900cc`.
9. **Erreurs** : `#cc0000`.
10. **Propriétés** : `FlowLayout(margin 4, h 4, v 2)` ; nom gras `#666` ; **chips de valeur** `#1976d2` soulignés sur `#e3f2fd` (radius 3, padding 1×4), **clic = filtrer** (`property_value_clicked`) ; conteneur `#f5f5f5` radius 2. Diffs : champ `#ffcccc`, caractère `#ff9999` gras.

### B3. ⚑ 6 états visuels (`_apply_style`, survol **manuel** via enter/leaveEvent, jamais CSS `:hover`)
| État | fond | bordure | largeur |
|---|---|---|---|
| sélection + survol | `#d0e8fc` | `#1565c0` | 2px |
| sélection | `#e3f2fd` | `#1976d2` | 2px |
| survol + not-found | `#ffecb3` | `#ff9800` | 2px |
| not-found | `#fffde7` | `#ffe082` | 1px |
| survol | `#f5f9ff` | `#90caf9` | 1px |
| normal | `#ffffff` | `#dddddd` | 1px |

**`border-radius: 6px` toujours.** Survol maintenu pendant l'ouverture d'un menu contextuel.

### Widgets support
- `flow_layout.py` `FlowLayout` : layout qui passe à la ligne (badges propriété).
- `left_click_menu.py` `LeftClickMenu(QMenu)` : ne déclenche une action qu'au **relâchement clic-GAUCHE**.
- `spinner_widget.py` `SpinnerWidget` : **48×48**, anneau `#0078d4` (arc 90°, −6°/30ms) ; `stop()` → anneau plein + **checkmark vert `#4CAF50`**.

---

## C. Page Videos (`pages/videos_page.py`, 2232 lignes)

**Layout** : `QVBoxLayout` margins 0 → `QSplitter(H)` `setSizes([150, 850])` (sidebar `setMaximumWidth(200)` → **150–200px**, glissable) + **barre de pagination** (`QFrame` `setMaximumHeight(36)`).

### C1. Sidebar de filtres
- Sections à **fond alterné** `#f0f0f0`/`#ffffff`, `QFrame` radius 3, margins `(4,4,4,8)`, spacing 2. **Boutons sidebar à 0.8× la police.** Chaque header = label gras + **⚙ (width 28)** + **✕ (width 28)**.
- Styles boutons : `#clearBtn` `#cc3333`/hover `#dd4444`/disabled `#cccccc`·`#888888` ; `#settingsBtn` `#1976d2`/hover `#1565c0` ; `#classifierBtn` `#4CAF50`/hover `#45a049`.
- Ordre : **Sources → Grouping → Classifier Path (caché) → Search → Sorting → Selection → Groups (caché)**.
  - **Sources** : `QLabel("All readable")` gris `#555` centré ; ⚙ = SourcesDialog ; tronqué à 47+`…` au-delà de 50 car.
  - **Grouping** : `"No grouping"` ; affiche `"Field" (#)`/`|| … ||` + `▼`/`▲` + ligne `"{n} groups"` (`(# > 1)` si singletons off) ; bouton **« Confirm all unique moves »** (`#4CAF50`, caché sauf groupé par `move_id`).
  - **Classifier Path** (caché) : badges `#e0e0e0` radius 3 ; **seul le dernier** a un ✕ (`setFixedSize(20,20)`, `#cc3333`) ; boutons Reverse, Concat…
  - **Search** : `QLineEdit` placeholder **`"Search... (Ctrl+F)"`** ; boutons **AND/OR/Exact/ID** (actif en **gras**) ; texte du champ `#0055cc` quand == recherche active ; restauration au focus-out.
  - **Sorting** : `"Date ▼"` ; rich text `<b>{title}</b> {▲|▼}` par `<br>`.
  - **Selection** : compteur **`"N selected"` `#0078d4` gras** / `"no selection"` `#0078d4` italique ; boutons **Page** / **All** ; ⚙ = menu (`Show Only Selected` cochable `Ctrl+Shift+D`, `Toggle Watched`, sous-menu `Edit Properties` par propriété).
  - **Groups** (caché, stretch 1) : nav **`<< < count > >>`** (width 28) ; `groups_list` `QListWidget` (zébrure native, `ElideRight`, sélection texte blanc) ; **auto-scroll** vers le groupe courant (`setCurrentRow`) ; ✙ add-to-classifier (props multiples).

### C2. Liste vidéo (zone de contenu)
- `list_widget` `QListWidget` : **`NoFrame`**, **scroll H désactivé**, **`ScrollPerPixel`**, **`NoSelection`** (sélection par checkbox), **`setAutoScroll(False)`**, **spacing 2**, fond transparent, **`singleStep 20`** (molette). Barre de stats `"N videos | taille | durée"` (font 12px).
- ⚑ **Refresh slot-par-slot** (`setItemWidget` sur items existants) → **position de scroll préservée** sur `state_changed` ; **reset en haut** sur saut de page/groupe ; `sizeHint` recalculé au **viewport réel** sur `resizeEvent` (à cause du plafond 400px de `WrappingLabel`).

### C3. Pagination (bas, `QFrame` max-height 36, centré)
- **`<< < "Page X/Y" > >>`** ; flèches `setFixedSize(32,24)` ; **« Page X/Y »** = bouton **plat souligné `#0078d4`** (hover `#005a9e`) → **GoToPageDialog** ; désactivés aux bornes.

### C4. Sélection cross-page
- `Selector(include/exclude)` persistant. `Page` = page courante ; `All` = `select_all()` (mode exclude = toute la vue). Compteur sur **toute la vue** (`size_from(view_count)`).

### C5. ⚑ Raccourcis clavier (`_setup_shortcuts`, `QShortcut`)
`Ctrl+G` grouping · `Ctrl+F` focus search · `Ctrl+Shift+S` sorting · `Ctrl+T` sources · `Ctrl+E` source-expression · `Ctrl+Shift+T` clear sources · `Ctrl+Shift+G` clear grouping · `Ctrl+Shift+F` clear search · `Ctrl+O` random · `Ctrl+R` refresh · `Ctrl+L` playlist · `Ctrl+P` properties · `←/→` page préc/suiv · `Home/End` 1ʳᵉ/dernière page · `↑/↓` groupe préc/suiv · `Ctrl+A` sélection page · `Ctrl+Shift+A` sélection vue · `Échap` vider · `Ctrl+Shift+D` show-only-selected · `Entrée` ouvrir (ou lance la recherche si champ focus) · `Suppr` supprimer.

### C6. Menu contextuel par vidéo (`LeftClickMenu`)
`Toggle Watched` · — · `Open` / `Open in VLC` / `Open Folder` · — · sous-menu **Copy** (Title/File Title/File Path/Video ID) · — · `Rename…` / `Move to…` · — · similarité conditionnelle (`Dismiss`/`Reset` × {similarity, re-encoded}) · `Generalize meta/file title into property…` (en groupe de similarité) · sous-menu `Confirm move to…` · `Properties…` · — · `Delete from database` / `Move to Trash` / `Delete permanently` (chacun via **VideoConfirmDialog**).

> **Note** : le combo « page size » de cette page est **DEAD CODE** (`_on_page_size_changed` jamais branché) ; `page_size` est fixé à **20** (réglé via le menu Options).

---

## D. Page Databases (`pages/databases_page.py`)
- `QHBoxLayout` 2 colonnes (gauche = liste scrollable, droite = formulaire), split ~égal.
- **Gauche** : titre `"Existing Databases"` gras `pt×1.6` centré ; `QScrollArea` (scroll H **off**) + VBox spacing 4.
- **`DatabaseItemWidget`** (`QFrame` `StyledPanel`, curseur main) : nom gras centré ; rangée boutons (cachée jusqu'à expansion) centrée : **Open**, **Update**, **Delete** (`#cc3333`/hover `#dd4444`). **États** : expansé `#e3f2fd`/`#1976d2` radius 4 ; replié `#f5f5f5`/`#ddd` + **hover `#e8e8e8`/`#bbb`**. **Simple-clic = expand** (accordéon : un seul ouvert) ; **double-clic = ouvrir** ; Update = confirm question ; Delete = confirm question.
- **Droite** : titre `"Create New Database"` gras `pt×1.6` ; `Name:` + `QLineEdit` placeholder `"Enter database name"` ; `QListWidget` sources (préfixes **`📁 `/`📄 `**) ; boutons **Add Folder/Add File/Remove** ; **Create Database** ; validations + confirm.

## E. Page Properties (`pages/properties_page.py`)
- `QVBoxLayout` margins `(10,10,10,10)` ; header = **`< Back to Videos`** + addStretch + titre `<b>Property Management</b>` (font 16px) centré.
- **`QSplitter(H)` `setSizes([600, 300])`** (2:1) : gauche = table+actions, droite = formulaire.
- **Table** = **`QTableWidget` 6 colonnes** `[Name, Type, Default, Multiple, Enum, Actions]` ; `SelectRows`/`SingleSelection` ; col Name **`Stretch`**, col Actions `ResizeToContents` ; **`setAlternatingRowColors(True)` (zébrure native)** ; en-tête natif ; col **Multiple** `Yes` en **`darkGreen`** ; col **Enum** `"a, b, c (count)"`/`"-"` ; col **Actions** = bouton+`QMenu` (`Manage Values…` str, `Rename…`, `Convert…` str, `Move Values…` str-multiple, —, `Delete`). Bouton **Refresh** ; **Fill with Terms…** dans un `QFrame StyledPanel`.
- **Formulaire** = **`QGroupBox("Create New Property")`** : `Name`+placeholder ; `Type` = **`QComboBox` `[str,int,float,bool]`** ; `Allow multiple`/`Use enumeration` (cases, activées seulement si type==str) ; `Enum values` placeholder `"value1, value2, value3"` (désactivé sauf si enum) ; `Default` ; **Reset** / **Create Property** (gras).

## F. Page Files (`pages/files_page.py`)
- `QStackedWidget` (état vide / scanné). **Vide** : titre `<b>Database file inventory</b>` (16px) centré + desc gris `#555` + bouton **Scan folders** `setFixedWidth(200)` centré.
- **Scanné** : **Rescan folders** + résumé `"{n} other files ({size})  ·  {n} indexed …  ·  {n} unknown …"` (`#555`) ; **`QTabWidget`** (`Others` / `Video stats`, natif).
- **Others** : **`QSplitter(H)` `setSizes([320, 700])`**.
  - Gauche = `QTableWidget(0,4)` `[Extension, Count, Total size, ""]` (pas de zébrure ; col2 `Stretch`) ; **« Trash all »** par ligne (texte rouge `#a40000`) ; tri par taille décroissante ; row 0 auto-sélectionnée.
  - Droite = titre `<b>Files — .{ext}</b> ({count})` ; **Open folder** + **Send to trash** + filtre `QLineEdit` placeholder `"Substring match on path"` `setFixedWidth(220)` (clear button) ; **`QTableView`** (modèle virtualisé) `[Path(Stretch), Size]`, **`ExtendedSelection`**, **zébrure native**.
- **Video stats** : `QTableWidget(0,5)` (Extension `Stretch`, **`NoSelection`**, pas de zébrure).
- **Corbeille** : `BULK_CONFIRM_THRESHOLD=500` ; aperçu 5 chemins + `"… (+N more)"` ; **avertissement bulk si > 500** ; `QMessageBox.question` Yes/No **défaut No**.

## G. Page Process (`pages/process_page.py`)
- VBox : titre `"{title}..."` (18px gras) · task label (14px `#555`) · **SpinnerWidget(48)** centré · barre de scan dossier (`QProgressBar`, cachée au départ, `"%v / %m folders — {n} files"`) · **conteneur de jobs** (`QFrame StyledPanel`) dans **`QScrollArea` hauteur fixe 150–200 + auto-scroll bas** · **Activity Log** (`QScrollArea` stretch 1, auto-scroll bas) + bouton **Clear** (width 60) · bouton **Continue** (right) **vert `#4CAF50` seulement `:enabled`**.
- **`JobProgressWidget`** (par job) : `QFrame StyledPanel`, HBox margins `(8,4,8,4)` ; titre `setMinimumWidth(200)` ; **`QProgressBar`** `setFixedHeight(20)` stylée (`border 1px #ccc` radius 3, **chunk `#0078d4`**, texte blanc, gras pt−1) ; **label % séparé** `AlignRight` width 50 (le % EST affiché).

---

## H. Les 13 dialogs (`dialogs/`) — tous **modaux** (`exec()`), **redimensionnables**, **Entrée=OK / Échap=Cancel** (sauf exceptions)

- **video_properties_dialog** (le + gros, **absent de videroid**) : `setMinimum 500×400` ; **Enter neutralisé** (`setAutoDefault(False)`) ; `QTabWidget` [Properties, Info]. **Properties** = `QSplitter [150,350]` (TOC `QListWidget` | **`QScrollArea` resizable**) ; sections par propriété **zébrées** (`Window.darker(107)`), header `pt+2` **gras au focus** ; éditeur **par type** (enum=`ScrollSafeComboBox`, bool=`QCheckBox`, int=`ScrollSafeSpinBox` ±1e9, float/str=`QLineEdit`) + multi=`MultipleValuesWidget` (`QListWidget` maxH 100, +/− width 30) ; **Reset/Clear** (width 50, visibilité selon `(defined,cleared,modified)`) ; **italique=défaut**, **bleu `#0055cc`=modifié**. **Info** = `QScrollArea` + 4 `QGroupBox` (File/Video/Audio/Status) en `QFormLayout` read-only.
- **batch_edit_property_dialog** (édition 1 prop sur N) : `setMinimumWidth(700)` ; **3 colonnes égales** (To remove / Current / To add), chacune un `_EntryList` (`QScrollArea` `StyledPanel`) ; rangées avec boutons `setFixedWidth(24)`, **hover `#0078d4`** ; éditeur nouvelle valeur par type (combo/spin ±2e9/doublespin ±1e15·6déc/lineedit) ; règles single (remplace tout) vs multiple.
- **property_values_dialog** : `setMinimum 500×400` ; bouton **Close** seul ; `QListWidget` (`ExtendedSelection` + **menu contextuel `LeftClickMenu`** : Delete/Rename…/Copy Value) ; boutons Delete Selected / Rename Value… ; **modificateurs** `Capitalize/Lowercase/Strip/Titlecase/Uppercase` ; stats label.
- **video_confirm_dialog** (destructif) : `setMinimumWidth(450)` ; ⚑ **vignette fixe 160×90 centrée KeepAspectRatio** (`#e0e0e0`/`#ccc`/radius 2) + chemin **monospace 9pt sélectionnable** (`#f5f5f5`/`#ddd`/radius 3) + message multi-ligne ; **Yes/No, No par défaut**.
- **batch_edit_dialog** : **test-only, PAS dans l'UI live** (édition multi-prop avec case d'activation par propriété ; éditeur grisé tant que non coché).
- **grouping_dialog** : `setMinimumWidth(350)` ; `QGroupBox` Group By (`QFormLayout`) : **type combo** (2 items) + **field combo (34 items, alpha)** ; `QGroupBox` Sort Groups = radio (By field value / By video count / By field value length) ; cases **Reverse order** / **Allow singletons** ; boutons **Apply / Clear Grouping / Cancel** (Clear = accept-with-null).
- **sorting_dialog** : `setMinimum 400×350` ; `QListWidget` **`InternalMove` (drag-drop) + Move Up/Down** + Toggle Direction + Remove ; combo Add (**33 items, ordre littéral**) + Add ↑ / Add ↓ ; Reset = vide la liste (reste ouvert).
- **sources_dialog** : `setMinimumWidth(450)` ; `QTabWidget` [Simple, Advanced]. **Simple = `QGroupBox` imbriqués + cases plates indépendantes** (PAS un arbre ; `SOURCE_TREE` inutilisé) : Readable{Found,NotFound}×{With,Without thumbnails}, Unreadable{Found,NotFound} + Select All/None/Valid Only. **Advanced = `QTextEdit` multi-ligne** plain-text, placeholder exemple, **Shift+Enter = valider** (Entrée = nouvelle ligne), label d'erreur **rouge**.
- **goto_page_dialog** : `setModal(True)` (seul) ; `setMinimumWidth(250)` ; **`QSpinBox` 1..total** (pas 1) + label `/ N`.
- **fill_property_dialog** : `setMinimumWidth(400)` ; desc `#666` ; combo props **str-multiple** (disabled si aucune) + case **Only fill videos without values** ; OK disabled si aucune éligible ; warning `#c00`.
- **move_values_dialog** : `setMinimum 500×400` ; `QListWidget` **multi-select** + combo cible str + case **Concatenate** ; OK disabled si aucune cible ; warning si sélection vide.
- **rename_dialog** : `setMinimumWidth(400)` ; `QLineEdit` `selectAll` ; **OK désactivé tant que vide OU inchangé**.
- **edit_folders_dialog** : `setMinimum 500×400` ; `QListWidget` **multi-select** ; Add Folder/Add File/Remove (disabled sans sélection) ; compteur pluralisé ; confirmations (Remove No-défaut, liste vide → warning).

---

## I. Caractéristiques transverses critiques pour la parité

1. **Chrome 100% Qt natif** (menus, radios, scrollbars, en-têtes de table, popups de combo, `QMessageBox`, `QGroupBox`, spin, onglets) — videre dessine ses propres widgets → **ne reproduit pas le rendu OS** (différence inhérente, à acter, pas un simple oubli).
2. **Cadres fixes à contenu centré** (vignette carte 180×100, vignette video_confirm 160×90) — `setFixedSize` + `AlignCenter` + `KeepAspectRatio`. **videre PEUT** (Container `width/height` + `horizontal/vertical_alignment`) → **oubli videroid à corriger**.
3. **Scroll automatique sur listes longues** : popups de **`QComboBox`** (grouping 34 / sorting 33 items) auto-scrollent (Qt, `maxVisibleItems=10`) ; `QScrollArea` partout (forms de propriétés, jobs, log…) ; `groups_list` auto-scroll. ⚠ **videre `Dropdown` n'a PAS de ScrollView** (`dropdown.py:104` rend tous les options) → **manque videre (G15)** ; les autres scrolls = `videre.ScrollView`, faisable.
4. **États au survol (6) de la carte**, suivi **manuel** — videre `Div` a hover (3 états) mais 6 combinaisons (sélection×survol×not-found) → tracking manuel via `mouse_enter/exit` ; faisable mais non fait.
5. **Splitters glissables** (videos `[150,850]`, properties `[600,300]`, files `[320,700]`) — **manque videre (G7)**, videroid = largeurs fixes.
6. **Tables natives + zébrure `AlternateBase`** (Properties, Files) — **manque videre (G1)**, tables maison sans zébrure native.
7. **Scaling DPI de la police** + **multiplicateur `pt/9`** sur la carte + **0.8× sur les boutons sidebar** — **manque videre (G-DPI)**.
8. **Glyphes exacts** : `⚙` `✕` `✙` `▲`(▲) `▼`(▼) `<<` `<` `>` `>>` ; ZWS `​` (opportunités de coupure dans titres/chemins).
9. **Comportements** : préservation/reset du scroll (slot-par-slot diff), clic-titre=toggle, clic-nom=ouvrir, survol-nom=souligné, clic-valeur=filtrer, Yes/No **No par défaut** sur destructif, OK désactivé tant qu'invalide, validations bloquantes.
