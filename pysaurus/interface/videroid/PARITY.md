# PARITY.md — parité kyuti ↔ videroid

Grille de **parité fonctionnelle ET visuelle** entre l'interface de référence
**kyuti** (`pysaurus/interface/kyuti/`, PySide6/Qt, mature, ~10 000 LOC, 5 pages
+ Process, 13 dialogs) et **videroid** (`pysaurus/interface/videroid/`, sur
videre). Source de vérité = le **code kyuti** ; cette grille (héritée de l'ancien
`PLAN.md §3`) est la checklist de la revue.

**Légende** : ✅ présent (équivalent fonctionnel) · 🟡 simplifié / dégradé ·
❌ absent · ❓ **à vérifier** (statut non confirmé).

> **ÉTAT (2026-07-01, après les Lots 1-17)** : les audits visuel (Étapes 1-2 +
> Lots 1-6), interaction (Lot 7), **comportemental** (4 agents, Lot 8) et
> fonctionnel (Lots 9-17) sont FAITS ; **les « oublis videroid » sont épuisés**
> (348 tests, 100 % de couverture). Les tableaux ci-dessous gardent l'historique
> écart par écart ; les blocs « Lot N — FAIT » (fin de fichier) résument ce qui a
> été corrigé. **Tout écart restant est imputable à un manque videre** → voir
> **`GAPS.md`** (la TODO d'enrichissement de videre = le prochain chantier).
> Pour reprendre : lire le « Cap » tout en bas, puis GAPS.md.

---

## 1. Coquille & navigation — **comparaison détaillée (étape 2 faite)**
> Réf `KYUTI_REFERENCE §0` vs `app.py`.

| Caractéristique kyuti | videroid | Statut | Cause / écart |
|---|---|---|---|
| Fenêtre **1200×800** | `Window(width=1200, height=800)` | ✅ | — |
| Central = `QStackedWidget` (4 pages + process) | `_content.control` échangé ; pages construites une fois | ✅ | mécanisme équivalent |
| **Titre OS dynamique** (5 formes) | **titre OS figé "Pysaurus"** + **label in-app** au texte **identique** (5 formes) | 🟡 | **manque videre (G-TITLE)** : pas de setter `Window.title` ; le texte est correct, mais dans la fenêtre |
| **Scaling DPI police** (≥11pt + `pt/9`) | police **fixe 14px**, pas d'accès DPR | ❌ | **manque videre (G-DPI)** |
| **Sélecteur radio natif top-right** (spacing 8, margins 0,0,4,0), caché sans base/process | `Button`s `● Videos/○ …` (glyphe), poussés à droite (`space=6`), cachés sans base/process | 🟡 | **manque videre (G10)** (radio simulé) + oubli mineur (espacement 6≠8) ; **caché correctement ✅** |
| **Barre de statut « Ready »** | `Text("Ready")` | ✅ | — |
| Statut : `QStatusBar` **passif**, clic = **vider** | barre = **`Div` stylé passif** ✅ (3 états identiques → aucun effet bouton ; était un Div-bouton bizarre, corrigé) + **clic = vider** ✅ (kyuti `clearMessage`) | ✅ | apparence + clic conformes |
| Statut : **toasts 3 s/5 s** auto-effacés | message **persistant**, aucun timer | ❌ | **manque videre (G25)** : pas de scheduling temporisé (`call_later` = tick suivant, sans délai) |
| **Journal de session** (fichier + `SessionLogDialog` 700×500) | fait (**Lot 16**) : mémoire + `session_log.txt` + fancybox lecture-seule | ✅ | monospace = G17 |
| Exceptions : **warning (non fatal) vs fatal (`exit(1)`) + traceback détaillé** | fait (**Lot 17**) : `(ApplicationError, OSError)` = alerte ; le reste = arrêt propre + re-levée (traceback console, exit ≠ 0) | ✅ | reste : dialogue fatal avec traceback AVANT sortie (limite videre) |
| **0 stylesheet global → chrome Qt natif** | videre **dessine** tous ses widgets | ✅ acté | **inhérent** (différence de framework, non corrigeable) |

## 2. Barre de menus — **comparaison détaillée**
> 4 menus natifs `QMenuBar` (kyuti) → **4 `ContextButton` plats** (videroid, `app.py:118-129`) = **manque videre G3/G10** (pas de chrome natif, pas de séparateurs, pas de sous-menus ni items cochables/radio natifs). Ordre/libellés top-niveau OK.

| Item kyuti | videroid | Statut | Cause / écart |
|---|---|---|---|
| **Database** : Rename, Edit Folders, Close | présents | ✅ | — |
| **Database** : Update Database | présent mais **placé en 1er** | 🟡 | oubli videroid (ordre) |
| **Database** : Find Similar / Re-encoded | **absents** | ❌ | oubli videroid |
| **Database** : Session Log… | **absent** | ❌ | oubli videroid |
| **Database** : Quit | présent mais **désactivé sans base** | 🟡 | oubli (kyuti = Quit toujours actif) |
| **View** : Random Video, Generate Playlist | **absents** | ❌ | oubli videroid (+ G-KBD) |
| **View** : Refresh View | présent, **sans `(Ctrl+R)`** + aucun raccourci | 🟡 | oubli (libellé) + **G-KBD** |
| **Options** : Page Size 10/20/50/100, **défaut 20** | items plats `●/○ Page size N`, **défaut 100** | ❌ | **BUG parité** : `videos_page.py:37` `VIDEO_DEFAULT_PAGE_SIZE=PAGE_SIZES[-1]=100` (à forcer à 20) + radio simulé (G10) |
| **Options** : toggle « Confirm deletion **for entries not found** » (défaut ON) | `☑/☐ Confirm deletion **of missing entries**` (défaut ON) | 🟡 | défaut ✅ ; **libellé différent** + coche-glyphe (G10) |
| **Help** : About (texte 2 lignes) | About (alert 1 ligne) | 🟡 | oubli (texte abrégé) + popup dessiné (inhérent) |
| Séparateurs de menu (Database ×4, View ×1, Options ×1) | **aucun** | ❌ | **manque videre (G10)** |

## 3. Page Databases *(kyuti: databases_page.py)*

| Fonction | Statut | Note |
|---|---|---|
| 2 colonnes liste / création | ❓ | **mise en page à vérifier** |
| Items expand/collapse, un seul ouvert | ✅ | |
| Double-clic = ouvrir | ❓ | à vérifier (G-KBD/souris) |
| Open / Update (confirm) / Delete (rouge, confirm) | ✅ | |
| Création : Name, Sources (📁/📄), Add Folder/File, Remove | ✅ | file-picker via `videre.Dialog` |
| Create (validation nom + ≥1 source, confirm) | ✅ | |

## 4. Page Videos — le cœur *(kyuti: videos_page.py, video_list_item.py)*

### 4a. Carte vidéo — **comparaison détaillée (étape 2 faite)**
> Réf = `KYUTI_REFERENCE §B` (`widgets/video_list_item.py`) vs `widgets/video_card.py`.

| Caractéristique kyuti | videroid actuel | Statut | Cause / écart exact |
|---|---|---|---|
| Disposition `QHBox` margins (8,8,8,8) spacing **12** ; détails `QVBox` spacing **3** | `Container` padding (v8,**h4**) + `Row` space **6** ; `Column` space **2** | 🟡 | **oubli videroid** : padding/spacing différents (videre pose la valeur exacte) |
| **Vignette = cadre FIXE 180×100 + AlignCenter (toujours)** | placeholder `Container(180×100)` ✅ ; **vraie vignette `Container(picture, align CENTER)` SANS width/height** | ❌ | **oubli videroid (ton exemple)** : taille variable → colonne gauche non alignée. Fix = `Container(picture, width=180, height=100, h/v_align=CENTER)` |
| Vignette fond `#e0e0e0`, bordure `1px #ccc`, radius 2 | aucun | ❌ | **oubli videroid** (Container fait bg/bordure/radius) |
| Vignette image `KeepAspectRatio` | PIL `thumbnail((180,100))` | ✅ | — |
| **Titre** gras+**souligné**, noir, **clic=toggle** | `Text(strong, underline)` **cliquable** (`_Clickable` → toggle sélection) | ✅ | soulignement (Lot 3) + clic-toggle (Lot 7) faits |
| Meta-titre italique `#666666` | `Text(italic, color=gray)` | 🟡 | **oubli videroid** : couleur approximative |
| **Nom fichier** : 2 états, **monospace**, fonds+bordure, **survol→souligné**, **clic→ouvre** | 2 états + fonds/bordure (Lot 3) ; **survol→souligné + clic→ouvre** (Lot 7, `_Clickable`) | 🟡 | tout fait sauf **monospace = manque videre (G17)** |
| **Format** badge EXT `#333`, codecs `#666`, badge byte-rate | 1 `Text` plat | ❌ | **manque videre (G17)** : couleurs/badges inline impossibles dans 1 `Text` |
| **Specs** durée `#0066cc`, w/h `#006600`, audio `#666` | 1 `Text` plat | ❌ | **manque videre (G17)** |
| **Dates** monospace `#996600`, `(entry/opened)` `#888` | 1 `Text` plat | ❌ | **manque videre (G17)** (monospace + couleurs) |
| **Langues** labels `#333`, valeurs `#555`, `(none)` `#aaa` | 1 `Text` plat | 🟡 | **manque videre (G17)** (couleurs inline) |
| Statuts NOT FOUND `#cc0000` / Unreadable `#cc6600` / Watched `#008800` | `Text(red/darkorange/green)` | ✅ | couleurs nommées **approximatives** |
| Similarity `#0066cc` / **Re-encoded `#9900cc`** | `Text("Similarity:…")` sans couleur ; **Re-encoded absent** | 🟡 | **oubli videroid** : couleur + Re-encoded |
| Diff de groupe (champ `#ffcccc`, caractère `#ff9999`) | absent | ❌ | **oubli videroid** (+ couleur inline G17) |
| Erreurs `#cc0000` | `Text(red)` | ✅ | — |
| **Propriétés** : chips `#1976d2` soulignés sur `#e3f2fd`, **clic→filtrer**, **`FlowLayout`** (enroule) | chips `#1976d2` soulignés sur `#e3f2fd` (Lot 3) **+ clic→filtrer** (Lot 7) | 🟡 | style+clic faits ; reste **enroulement = manque videre (G16)** |
| **6 états visuels** (survol/sélection/not-found × bordure + radius 6, survol manuel) | **les 6 états** (`_card_style` + `__capture_mouse__` + `handle_mouse_enter/exit`, Lot 7) ; zébrure retirée (Lot 1) | ✅ | tous faits sauf **radius 6 = manque videre (G18)** |

**Bilan carte** : écart **important**, dominé par des **oublis videroid** corrigeables (cadre fixe vignette, bordures+radius, 6 états de survol, soulignement, handlers de clic, couleurs exactes, retrait de la zébrure) et **3 vrais manques videre** : **G16** (badges qui n'enroulent pas), **G17** (lignes specs/format/dates à couleurs inline + monospace), et le tracking de survol à 6 états (events présents mais non câblés). Plus gros gain visuel = **vignette à cadre fixe** + **les 6 états de carte** + décomposition des lignes colorées (ou G17 dans videre).

### 4b. Pagination & sélection
| Fonction | Statut | Note |
|---|---|---|
| `<< < Page X/Y > >>` (boutons bornés) | ✅ | |
| Goto dialog (saisie n° page) | ❌ | G5 ; clic Page X/Y = ❓ |
| Sélection checkbox + clic titre = toggle | 🟡 | checkbox OK ; clic titre ❓ |
| Ctrl+A / Ctrl+Shift+A / Échap / Ctrl+Shift+D | ❌ | tous les raccourcis (G-KBD) ; équivalents souris présents (Page/All/✕/Show-Only) |
| Compteur « N selected » + sélecteur persistant cross-page | ✅ | |

### 4c. Sidebar de filtres
| Section | Statut | Note |
|---|---|---|
| **Sources** (All readable / liste / expression ; ⚙ dialog) | 🟡 | dialog Simple/Advanced ; **liste à plat** (pas l'arbre Qt) |
| **Grouping** (champ + tri + flèche) | ✅ | « Confirm all unique moves » (move_id) = ❌ |
| **Classifier path** (badges + ✕ ; Reverse) | 🟡 | Reverse OK ; **Concat…** ❌ |
| **Search** (champ + AND/OR/Exact/ID + ✕) | 🟡 | modes OK ; placeholder « Search… » = manuel (G12) |
| **Sorting** (liste ▲/▼) | ✅ | réordre par Move Up/Down (G8) |
| **Selection** (compteur + Page/All/✕) | ✅ | |
| **Groups** (liste + nav `|< < n > >|` + ✙) | ✅ | |
| Disposition générale de la sidebar (largeur, sections) | ❓ | largeur fixe 240 (G7) — **à auditer (visuel)** |

### 4d. Menus contextuels & raccourcis
| Fonction | Statut | Note |
|---|---|---|
| Menu par vidéo : Toggle Watched, Open, Open Folder, Copy (Title/File Title/Path/ID), Rename…, Delete×3 | ✅ | menu **plat** ⚙ (G10), pas clic-droit |
| Menu par vidéo : Open in VLC | ❓ | à vérifier (open_video) |
| Menu par vidéo : Move to…, similarité (Dismiss/Reset, Generalize…), Confirm move, **Properties…** | ❌ | différés (niche + video_properties_dialog) |
| Menu de sélection ⚙ : Show Only Selected, Toggle Watched, Edit Properties (par prop → BatchEdit) | ✅ | |
| **Tous les raccourcis clavier** (Home/End/←/→/↑/↓/Ctrl+…) | ❌ | **G-KBD** — aucun |
| Préservation/reset du scroll, tooltips | ❌ | tooltips (G6) ; scroll ❓ |

## 5. Page Properties *(kyuti: properties_page.py)*

| Fonction | Statut | Note |
|---|---|---|
| Table 6 colonnes (couleurs alternées) + Refresh | 🟡 | table maison (G1) ; **zébrure/visuel à vérifier** |
| Fill with Terms… | ✅ | |
| Actions par propriété (Manage/Rename/Convert/Move/Delete) | ✅ | |
| Création (Name/Type/Multiple/Enum/Default + Reset/Create) | ✅ | |

## 6. Page Files *(kyuti: files_page.py)*

| Fonction | Statut | Note |
|---|---|---|
| Scan / Rescan + résumé (X other / Y indexed / Z unknown) | ✅ | |
| Onglet Others : table exts (+ Trash all) / fichiers (Open folder, Send to trash, filtre) | ✅ | tables maison (G1), onglets maison (G2) |
| Confirmation corbeille (aperçu 5, alerte > 500) | ✅ | |
| Onglet Video stats (lecture seule) | ✅ | |
| Disposition / visuel des 2 tables | ❓ | **à auditer (visuel)** |

## 7. Process page & notifications *(kyuti: process_page.py, app_context.py)*

| Fonction | Statut | Note |
|---|---|---|
| Titre, spinner, conteneur de jobs (% par job), Activity Log, Continue | 🟡 | spinner = barre animée (pas de cercle) ; barre de scan dédiée → dans le log ; **Clear** ❌ ; autocontinue ❌ |
| `JobToDo`/`JobStep`/`DatabaseReady`/`Done`/`End` → réactions UI | ✅ | |
| `FolderScanProgress` → barre de scan dédiée | 🟡 | va dans le log |
| `state_changed` → refresh page courante | ✅ | impératif (pas de signal auto) |
| `notification_received` → Session Log | 🟡 | Lot 16 : le journal capte les **messages de statut** (entonnoir `_set_status`), pas le flux brut de notifications |
| Routage Process-active vs pages | ✅ | |

## 8. Les 13 dialogs *(kyuti: dialogs/)*

| Dialog | Statut | Note |
|---|---|---|
| video_properties_dialog (Properties/Info, éditeurs par type) | ✅ | **Lot 15** — 2 onglets, éditeurs par type ; sentinelle « (no value) » au lieu de Clear ; stylage-modifié/Reset/scroll-to sautés (G24/G21/G20) |
| batch_edit_dialog (multi-propriétés, case par prop) | ❌ | seul batch_edit_property (1 prop) existe |
| batch_edit_property_dialog (3 colonnes, 1 prop) | ✅ | |
| grouping_dialog | ✅ | combo champ **à plat** (pas type+champ dépendant) |
| sorting_dialog (multi-niveaux, Up/Down au lieu de drag) | ✅ | G8 |
| sources_dialog (Simple cases / Advanced expression) | 🟡 | onglets maison (G2) ; cases **à plat** (pas l'arbre) ; expression 1 ligne (G11) |
| edit_folders_dialog | ✅ | |
| rename_dialog | ✅ | inline (G-MODAL) |
| goto_page_dialog (spin 1..N) | ❌ | G5 |
| fill_property_dialog | ✅ | |
| move_values_dialog | ✅ | |
| property_values_dialog (valeurs + Delete/Rename/modificateurs) | ✅ | menu contextuel → boutons + prompts inline (G10/G-MODAL) |
| video_confirm_dialog (confirm destructif + vignette 160×90) | 🟡 | confirm présent ; **vignette + chemin monospace** ❓/❌ |
| **Conventions** : modaux, Entrée=OK/Échap=Cancel, feedback bleu/italique | 🟡 | Entrée/Échap = G-KBD ; feedback visuel ❓ |

---

## Synthèse des chantiers de parité (à confirmer par la revue)

1. **Visuel / mise en page** *(priorité — non audité)* : états de carte (survol/sélection/not-found), couleurs, espacements, largeurs, alignements, fidélité des tables et de la sidebar. Requalifier les ✅ visuels.
2. **Raccourcis clavier** : tout absent → dépend de **G-KBD** (enrichir videre).
3. **Dialogs manquants** : `video_properties_dialog`, `batch_edit_dialog` (multi), `goto_page_dialog`.
4. **Niche** : Find Similar / Re-encoded, Random / Playlist, Session Log, actions similarité (Dismiss/Reset/Generalize/Move/Confirm-move), classifier **Concat**, clic-pour-filtrer sur les valeurs de propriété.
5. **Process** : Clear log, autocontinue, barre de scan dédiée, spinner circulaire.
6. **Sources** : passer de la liste à plat à l'arbre (cases hiérarchiques).

---

# ÉTAPE 2 — Résultats consolidés (revue détaillée faite, 2026-06-30)

Comparaison KYUTI_REFERENCE ↔ videroid sur **toutes** les zones (carte §4a + coquille §1-2 détaillés ci-dessus ; dialogs §8 ; ci-dessous le reste). Chaque écart classé **oubli videroid** (videre sait faire) / **manque videre (G#)** / **inhérent** (chrome Qt natif).

## Verdict par zone
| Zone | Verdict | Écarts dominants |
|---|---|---|
| **Coquille / menus** | 🟡 fonctionnel | menus plats (G3/G10, pas de séparateurs/sous-menus/radio natifs), titre in-app (G-TITLE), **BUG page-size défaut 100≠20**, items absents (Find Similar/Re-encoded, Random, Playlist, Session Log), Quit désactivé sans base |
| **Carte vidéo** | ❌ gros écart visuel | cf. §4a : vignette non fixe, 6 états absents, zébrure en trop, couleurs inline (G17), badges sans flow (G16), pas de radius (G18) |
| **Page Videos** | 🟡 logique mûre, visuel en retrait | sélection cross-page ✅ ; **0 raccourci (G-KBD)** ; pas de splitter (G7, sidebar 240 fixe) ; boutons sidebar non colorés/non 0.8× (G19) ; sections sans fond ni radius (G18) ; compteur sans couleur/gras ; ordre des sections différent ; menu ⚙ plat (G10) ; reload = reconstruction (G9) |
| **Databases** | 🟡 | états d'item couleurs ✅ mais **radius 4 absent (G18)**, **hover mauvaises couleurs + l'expansé perd son bleu au survol** (régression), Delete non rouge (G19), titres non centrés, double-clic-ouvrir absent (G22), curseur main absent (G23) |
| **Properties** | 🟡 | splitter→largeur fixe (G7, ratio 3:1≠2:1), table maison sans sélection/tri/zébrure-native (G1), **Multiple "Yes" non vert** (oubli trivial), activation conditionnelle multiple/enum absente (G21), placeholders absents (G12), Create non gras (G19), header/Back absents |
| **Files** | 🟡 fonctionnel | splitter (G7), pas de zébrure liste (G1), onglets maison (G2), **pas de filtre live** (G24, bouton Apply), Trash-all non rouge, extensions sans point `.`, nombres non alignés-droite, état vide non centré, marges absentes |
| **Process** | 🟡 la + en retrait | `ProgressBar` **non stylable** (noir≠`#0078d4`, étend G14), **spinner = barre glissante** (pas d'anneau+checkmark), Clear/header-log absents, autocontinue absent, jobs+log fusionnés (pas de zones séparées), Continue non vert/non-désactivé-avant-fin |

## Répartition des causes
- **Oubli videroid (≈ la moitié — corrigeable sans toucher videre)** : couleurs/styles **de `Text`/`Container`** non posés (compteur sélection ✅, Multiple-vert ✅, fonds/bordures de carte ✅, fonds de sections), centrages, largeurs (28/32×24/200/220), désactivation aux bornes (`Button.disabled` **existe**), troncatures, ordre des sections, libellés, items de menu absents, video_confirm sans vignette, OK jamais grisé, alignements à droite. *(Les **couleurs/gras de boutons** — sidebar ⚙/✕/✙, Delete/Trash-all rouge, Continue vert, Create gras — ne sont **pas** des oublis : elles butent sur **G19**, cf. ci-dessous.)* **C'est le gros du visuel manquant.**
- **Manque videre (structurel, → GAPS.md)** : G1 (Table), G2 (Tabs), G3/G10 (menus), G5 (spin), G7 (splitter), G9 (virtualisation/slot-reuse), G11 (TextArea), G12 (placeholder), G15 (Dropdown scroll), G16 (flow), G17 (rich-text/monospace), **G18 (border-radius — PARTOUT)**, **G19 (`Button`/`ContextButton` non stylables : `style=` lève `TypeError` → ni couleur ni taille/gras — vérifié)**, **G20 (ScrollView scroll-to)**, **G21 (Dropdown on_change / Checkbox disabled)**, G22 (double-clic), G23 (curseur), G24 (TextInput on_change), G-KBD (raccourcis), G-MODAL (fancybox 80% fixe, mini-tailles ignorées, Entrée≠OK), G-TITLE, G-DPI ; + `ProgressBar` non stylable et pas de spinner circulaire (étendent G14).
- **Inhérent (non corrigeable — différence de framework)** : chrome Qt natif (barre de menus, scrollbars, **zébrures `AlternateBase`**, en-têtes de table, popups de combo, `QMessageBox`, `QGroupBox`, fenêtres `QDialog`). videre dessine ses propres widgets.

## Fonctions ABSENTES (à porter)
`video_properties_dialog` (gros), `batch_edit` multi-prop (test-only chez kyuti), `goto_page` (G5), **Session Log**, **Find Similar / Re-encoded**, **Random Video / Generate Playlist**, actions de similarité (Dismiss/Reset/Generalize), **Move to…**, **classifier Concat**, statut **Re-encoded**, **clic-valeur = filtrer**, **Open in VLC**, **Copy File Title**, vignette du confirm destructif, « Confirm all unique moves ».

## Correctifs videroid prioritaires (impact visuel élevé, coût faible)

**Lot 1 — FAIT (2026-06-30, 259 tests verts, couverture 100 %)** :
1. ✅ **Page-size défaut → 20** (`videos_page.py:37`). *Bug net.*
2. ✅ **Carte** : vignette en cadre fixe 180×100 (centrée, fond `#e0e0e0`/bordure `#ccc`) ; zébrure **retirée** ; états **sélection + not-found** (fonds + bordures par état).
3. ✅ **Compteur de sélection** `#0078d4` + gras/italique selon l'état.
4. ✅ **Multiple "Yes" en vert** (`#006400`).

**Lot 2 — FAIT (2026-06-30, 263 tests verts, couverture 100 % ; vérifié visuellement)** :
5. ✅ **Sidebar** : **fonds de sections** alternés `#f0f0f0`/`#ffffff` (`theme.SECTION_BG_A/B`, alternance par position au peuplement). *(Les **couleurs des boutons** ⚙/✕/✙ restent bloquées par **G19**.)*
6. ✅ **Databases** : bug de **survol** corrigé — `hover`/`click` explicites (expansé reste bleu ; replié `#e8e8e8`/`#bbb`), neutralise le gris par défaut de videre.
7. ✅ **Files** : extensions avec point `.` (`.mp4`), nombres **alignés à droite** (`table.cell(align=END)`), état vide **centré** (Container CENTER/CENTER). *(marges/menus fins reportés.)*

**Lot 3 — carte (visuel) FAIT (2026-06-30, 264 tests verts, 100 % ; vérifié visuellement)** :
8a. ✅ Col space 2→3 ; **titre gras + souligné** noir ; méta-titre `#666666` ; **nom de fichier en cadre** 2 états (non-vu `#8c8cfa`/`#fafafa`+bordure `#f0f0fa` ; vu `#a0a0a0`/`#f8f8f8`) ; **couleurs de statut exactes** (NOT FOUND `#cc0000`, Unreadable `#cc6600`, Watched `#008800`, Similarity `#0066cc`, Errors `#cc0000`) ; **chips** `#1976d2` **soulignés** sur `#e3f2fd` + noms `#666`.

**Lot 7 — carte (interaction) FAIT (2026-07-01, 279 tests verts, 100 % ; vérifié visuellement + routage souris réel testé)** :
8b. ✅ **Carte interactive** (miroir kyuti `VideoListItem`) : **6 états de survol** (`_card_style`, couleurs exactes kyuti — normal/survol/sélection/sélection+survol/introuvable/introuvable+survol ; radius 6 omis = G18) via `VideoCard.__capture_mouse__` + `handle_mouse_enter/exit` (tracking manuel, car 6 > 3 états `Div`) ; **clic titre = toggle sélection** (pilote la checkbox → re-style sur place, sans reload) ; **clic nom de fichier = ouvrir** + **survol = souligné** ; **clic chip = filtrer** (`video_filter_property` → `context.focus_prop_val`). Widget interne `_Clickable` (wrapper transparent capture-souris) pour les 3 zones ; enter/exit émis sur toute la **lignée** → la carte reste survolée même quand le curseur est sur un enfant cliquable. *(monospace = G17 ; enroulement chips = G16 ; statut Re-encoded `#9900cc` = feature absente.)*
**Lot 4 — menus + centrages FAIT (2026-06-30, 265 tests verts, 100 % ; vérifié visuellement)** :
9a. ✅ **Menus** : ordre kyuti (Rename, Edit Folders, Update, Close, Quit) ; **Quit toujours accessible** (menu Database jamais désactivé — sans base il ne montre que Quit, car videre ne grise pas les items d'un menu plat, G10) ; **About sur 2 lignes**.
9b. ✅ **Centrages** : titres Databases (« Existing Databases » / « Create New Database ») ; infos de section sidebar (Sources/Sorting/Grouping) centrées.

**Lot 5 — FAIT (2026-07-01, 265 tests verts, 100 % ; vérifié visuellement)** :
9c. ✅ **Properties ratio 2:1** (table `weight=2` / formulaire `weight=1`, = kyuti `setSizes([600,300])`).
9d. ✅ **video_confirm avec vignette** : le confirm de suppression vidéo (delete-entry / trash / delete-file) montre la **vignette 160×90** (helper `video_card._thumbnail(video, box)` paramétré + réutilisé) au-dessus du message.

**Reste — oublis videroid (sans toucher videre)** :
10. **Centrages restants** : rangée de boutons des items Databases (bloqué : items non pleine-largeur dans le `ScrollView` de videre — layout à creuser). Labels de raccourcis (`(Ctrl+R)` etc.) **volontairement omis** (promettraient un raccourci non fonctionnel — G-KBD). Items de menu **Find Similar/Re-encoded, Random, Playlist, Session Log** = features absentes (à porter, pas de simples libellés). *Polish : champs du formulaire Properties étroits (content-sized) — leur donner un `weight`.*
**Lot 6 — status + process FAIT (2026-07-01, 268 tests verts, 100 % ; vérifié visuellement)** :
11a. ✅ **Statut** : barre passive **+ clic = vider** (`Div` stylé, 3 états identiques → pas d'effet bouton ; `on_click` = `_set_status("")`). *Toasts auto-effacés = **manque videre G25** (pas de scheduling temporisé) — non faisable proprement.*
11b. ✅ **Process** : zones **jobs / log séparées** (jobs encadrés à hauteur bornée, log scrollable) ; bouton **Clear** log ; **Continue désactivé** jusqu'à la fin (`Button.disabled`) ; **autocontinue** (ouvrir une base sans update → enchaîne direct, kyuti). *(Continue vert = G19 ; spinner circulaire = ~G14 — non faits.)*

**Lot 8 — réactivité & feedback FAIT (2026-07-01, 284 tests verts, 100 % ; jitter MESURÉ, feedback testé)** — issu de l'**audit comportemental** (4 agents, kyuti↔videroid, sur la couche réactive que la revue visuelle-statique avait ratée) :
12a. ✅ **`video_open` → reload** : ouvrir marque la vidéo « vue » mais videroid n'a pas de `state_changed` auto (refresh impératif) → l'indicateur **Watched** ne s'affichait jamais. `_reload()` ajouté (seule action vidéo qui l'oubliait).
12b. ✅ **Feedback de statut** (persistant + clic-vider, = kyuti `status_message_requested` **sans** le timeout G25) via helper `Page.set_status` → `app._set_status` : delete-entry/trash/delete-file (par vidéo), batch-delete, et Properties **Move/Fill/Rename/Convert** (les popups de succès kyuti).
12c. ✅ **Boutons grisés aux bornes** (`Button.disabled`) : pagination (`_set_pagination`), navigation de groupes (`_populate_groups`), et ✕ Clear sélection quand vide.
12d. ✅ **Jitter de carte corrigé** (ton exemple) : padding compensé `Padding.all(9 - border_width)` → padding+bordure constant, taille extérieure **stable** (mesuré : not-found = 203px normal ET survol ; l'ancien non-compensé sautait à 205px).
12e. ✅ Micros : garde recherche vide (`_on_mode` strip + no-op, = kyuti `if query:`), reverse-classifier conserve la page (`_reload` au lieu de `_reset_and_reload`).

**Lot 9 — features rapides + robustesse FAIT (2026-07-01, 298 tests verts, 100 %)** — oublis videroid de type *fonctionnalité* (dispo kyuti, sans toucher videre) :
13a. ✅ **Menu par vidéo** : **Open in VLC** (`context.open_from_server` → `_api.open_from_server` ; le serveur existe en run réel) + **Copy File Title** (`video_copy(video, "file_title")`).
13b. ✅ **Menu View** : **Random Video** (`open_random_video` + refresh) + **Generate Playlist** (`playlist()` + statut).
13c. ✅ **classifier Concat…** : bouton dans la section Classifier → dialogue (`Dropdown` des propriétés `str`) → `classifier_concatenate_path` (kyuti `_on_classifier_concatenate`).
13d. ✅ **Robustesse** : `_VideroidAPI._run_thread` override (comme `KyutiAPI`) → les exceptions d'op backend en thread remontent via `context.set_exception_sink` → `app._on_thread_exception` → `window.call_later(window.error, exc)` (alerte au lieu du « succès » silencieux). *(**Confirm all unique moves** REPOUSSÉ : couplé au groupement `move_id`, pas « rapide ».)*

**Lot 10 — similarité FAIT (2026-07-01, 306 tests verts, 100 %)** — oublis videroid du sous-système similarité :
14a. ✅ **Menu Database** : **Find Similar Videos** + **Find Re-encoded Videos** (confirm → `run_process` ; `context.find_similar_videos` / `find_similar_videos_reencoded` = des `@process`).
14b. ✅ **Menu par vidéo** : **Dismiss / Reset Similarity** (conditionnels sur `similarity_id` / `similarity_id_reencoded` ; Dismiss seulement pour un match `>= 0`, kyuti) → `context.dismiss_similarity`/`reset_similarity` (synchrones : `_ops.set_similarities_from_list [-1]`/`[None]`) + reload.

**Lot 11 — Move to… FAIT (2026-07-01, 309 tests verts, 100 %)** : item ⚙ « Move to… » → `videre.Dialog.select_directory` → confirm → **`run_process`** de `context.move_video_file` → `_api.move_video_file` (`@process(finish=False)` — déplace le fichier via `FileCopier`, émet Done/Cancelled/End ; kyuti route AUSSI Move-to par la page de progression). **Testé sans déplacer de fichier** (dialogue + process/op mockés) ; *kyuti ne teste PAS l'op de move*.

**Lot 12 — Confirm move / Confirm all unique moves FAIT (2026-07-01, 316 tests verts, 100 %)** — le sous-système *moves* (métadonnées d'une vidéo disparue → son fichier retrouvé) :
16a. ✅ **Menu par vidéo** : items **« Confirm move to `<filename>` »** (un par destination candidate, plats — kyuti a un sous-menu, G10), présents seulement si `video.moves` → confirm (message kyuti « Transfer metadata… ») → `context.confirm_move` (`_ops.move_video_entry`, synchrone) + reload + statut « Video move confirmed ».
16b. ✅ **Bouton « Confirm all unique moves »** dans la section Grouping, **visible seulement si groupé par `move_id`** (holder `_confirm_moves_holder`, géré dans `_update_grouping` ; vert kyuti = G19) → confirm → `context.confirm_unique_moves` (`_algos.confirm_unique_moves`, synchrone, retourne le compte) + reload + statut « Confirmed N video move(s) ». *(Le groupement « moved files (potentially) » était déjà accessible — `move_id` ∈ `FIELD_MAP.allowed`.)*

**Lot 13 — Generalize title FAIT (2026-07-01, 322 tests verts, 100 %)** : items ⚙ **« Generalize meta/file title into property... »** (meta seulement si `video.meta_title`), visibles ssi `page.grouped_by_similarity()` (= groupé par un champ de `SIMILARITY_FIELDS` **et** >1 vidéo affichée, kyuti `videos_page.py:1427`) → gardes (titre vide / aucune propriété str non-enum → alerte) → dialogue (`Dropdown` des propriétés `str` non-enum) → `context.add_property_value_for_videos(other_ids, prop, [title])` (`_ops.set_property_for_videos`, merge si multiple, synchrone) + reload + statut kyuti « Property "X" set to "Y" for N video(s) ».

**Lot 14 — barre de scan dédiée FAIT (2026-07-01, 324 tests verts, 100 % ; vérifié visuellement)** : `ProcessPage` intercepte **`FolderScanProgress`** AVANT le collector (→ **plus d'inondation du log** à ~5 Hz, kyuti `process_page.py:279`) et alimente une **barre dédiée** (holder caché jusqu'au premier événement ; `value = folders_done / max(1, folders_discovered)` — le max grandit pendant le parcours ; libellé « N / M folders — F files »).

**Lot 17 — exceptions warning/fatale FAIT (2026-07-01, 348 tests verts, 100 %)** : `alert_on_exceptions=(Exception,)` → **`(ApplicationError, OSError)`** (le partage kyuti `main.py PySide6ExceptHook`) — erreurs applicatives/OS = **alerte non fatale** ; tout le reste = bug → videre arrête la boucle proprement et **`Window.run()` re-lève** (traceback console + exit non-zéro via `sys.exit(app.run())`). Les **exceptions de thread** (`_on_thread_exception`) re-lèvent dans la boucle UI via `call_later` → passent par le **même aiguillage** (miroir du `_handle_exception` kyuti). La fixture `videroid_app` construit sa `StepWindow` avec le même tuple. *Non fait (limite videre) : le dialogue « Fatal Error » avec traceback détaillé AVANT de quitter — le cycle de vie videre ne permet pas montrer-puis-quitter.*

**Lot 16 — Session Log FAIT (2026-07-01, 347 tests verts, 100 % ; vérifié visuellement)** : chaque **message de statut** passe par `_set_status` (l'entonnoir unique — vider la barre n'est pas journalisé) → horodaté `[YYYY-mm-dd HH:MM:SS]`, gardé en mémoire (`_session_log`, semé d'un en-tête « Session started ») **et** ajouté à **`<dossier de la base>/session_log.txt`** quand une base est ouverte (en-tête flushé une fois par base, kyuti `main_window.py:354-384`). Item **« Session Log... »** (menu Database, entre Close et Quit) → fancybox lecture seule scrollée en bas (kyuti `SessionLogDialog` ; monospace = G17). `context.get_database_folder_path()` ajouté. ⚠️ **Tests** : la fixture `videroid_app` **neutralise l'écriture fichier** (le dossier de la base mémoire = données de test partagées sur disque + xdist concurrent) ; l'écrivain réel a ses tests dédiés sur `tmp_path`.

**Lot 15 — `video_properties_dialog` FAIT (2026-07-01, 343 tests verts, 100 % ; vérifié visuellement, 2 onglets)** — *le plus gros manque* : item ⚙ **« Properties... »** → `dialogs/video_properties_dialog.py` (`VideoPropertiesDialog(video, prop_types)`, fancybox OK/Cancel). **2 onglets** (widget `Tabs`) : **Properties** = une section par propriété (fonds alternés) avec éditeur par type — simple str/int/float → `TextInput` (**champ vide = pas de valeur** ; saisie int/float invalide **ignorée**, kyuti) ; simple enum/bool → `Dropdown` avec sentinelle **« (no value) »** (remplace le bouton Clear kyuti — tout l'état se lit des widgets, aucun drapeau caché) ; multiple enum → colonne de `Checkbox` ; multiple libre → liste ✕-par-valeur + champ + « + » + Clear (erreur de parsing affichée) ; **Info** = groupes File/Video/Audio/Status en lecture seule (gardes « N/A »). **`get_changes()`** = diff pur contre les valeurs chargées → `{nom: [valeurs]}` (`[]` = suppression) → `context.set_video_properties` (**`db.video_entry_set_tags`**, synchrone) + reload. Sautés (gaps videre, documentés dans le docstring) : stylage « modifié » bleu + Reset par propriété (G24/G21 pas d'`on_change`), liste-sommaire + scroll-to (G20), gras-au-focus, spinbox (G5), placeholders (G12) ; une propriété **indéfinie charge vide/sentinelle** (pas le défaut : sans l'italique kyuti, un défaut pré-rempli se lirait comme une valeur posée) ; Cancel = reset global.

---

## AUDIT COMPORTEMENTAL — reste à faire (2026-07-01)
Écarts CONFIRMÉS par l'audit mais **non corrigés** — chacun bloqué par un manque videre, ou relevant de la robustesse / des features. Les oublis videroid *purs* de la couche réactive sont, eux, épuisés (Lot 8).

**Bloqués par un manque videre — à trancher : enrichir videre ?**
- **G20 (scroll-to)** : scroll pas remis en haut après saut de page/groupe (le `ScrollView` garde l'offset) ; le groupe courant n'est pas suivi dans sa liste.
- **G24 (`TextInput.on_change`)** : filtre Files caché derrière un bouton **Apply** (kyuti = *live* à la frappe) ; validations live (OK grisé si invalide) absentes.
- **G21 (`Dropdown.on_change`)** : formulaire Properties non réactif (griser multiple/enum selon le type choisi).
- **G-KBD** : aucun raccourci (Escape/Ctrl+A/Suppr/Entrée/flèches) + **Entrée = OK** dans les dialogues.
- Mineurs : **G22** double-clic (Databases + cartes), **G23** curseur main, **G12** placeholders, **G6** tooltips, **G10** griser un item de menu plat.

**Robustesse — OUBLI VIDEROID (PAS un manque videre → ne va PAS dans GAPS.md)**
- ✅ **FAIT (Lot 9)** — exceptions d'op backend en thread : elles ne sont plus silencieuses (`_VideroidAPI._run_thread` les capture → alerte `window.error`, plus de « succès » trompeur).
- **Reste** : plus de distinction exception **warning vs fatale** ni de traceback (`app.py` `alert_on_exceptions=(Exception,)` uniforme) — corrigeable côté videroid.

**Oublis videroid — fonctionnalités entières RESTANTES** (dispo kyuti, sans toucher videre ; rapides = Lot 9, similarité = Lot 10) :
> **Cap : les oublis videroid sont ÉPUISÉS (Lots 1-17).** Tout ce qui était faisable sans toucher videre est fait — visuel, interactions, réactivité, fonctionnalités (VLC/Random/Playlist/Concat/similarité/moves/Generalize/scan/Properties-dialog/Session-Log), robustesse (exceptions thread + warning/fatale). **Ce qui manque encore à la parité est bloqué par les manques videre** (GAPS.md : G-KBD raccourcis, G20 scroll-to, G24/G21 on_change, G17 rich-text/monospace, G16 flow, G18 radius, G19 style boutons, G10 menus, G25 timers, G-DPI…) — **les combler dans videre est le prochain chantier, et le but même du projet.**
