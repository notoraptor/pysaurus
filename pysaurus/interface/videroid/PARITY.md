# PARITY.md — parité kyuti ↔ videroid

Grille de **parité fonctionnelle ET visuelle** entre l'interface de référence
**kyuti** (`pysaurus/interface/kyuti/`, PySide6/Qt, mature, ~10 000 LOC, 5 pages
+ Process, 13 dialogs) et **videroid** (`pysaurus/interface/videroid/`, sur
videre). Source de vérité = le **code kyuti** ; cette grille (héritée de l'ancien
`PLAN.md §3`) est la checklist de la revue.

**Légende** : ✅ présent (équivalent fonctionnel) · 🟡 simplifié / dégradé ·
❌ absent · ❓ **à vérifier** (statut non confirmé).

> ⚠️ **Le visuel et la mise en page n'ont PAS encore été audités.** Un « ✅ » ci-dessous
> porte sur la **fonction**, pas sur la **fidélité visuelle**. Retour utilisateur :
> videroid « a laissé énormément, notamment sur le plan visuel ». La revue doit
> repasser **chaque écran** contre kyuti (couleurs, espacements, états de survol,
> tailles, alignements) et requalifier les ✅ en 🟡 le cas échéant.
> Les manques liés à un gap videre renvoient à **`GAPS.md`**.

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
| Statut : **clic = vider** | clic = **réinitialise à "Ready"** (pas vide) | 🟡 | **oubli videroid** |
| Statut : **toasts 3 s/5 s** auto-effacés | message **persistant**, aucun timer | ❌ | **oubli videroid** (faisable via `call_later`) |
| **Journal de session** (fichier + `SessionLogDialog` 700×500) | **totalement absent** | ❌ | **oubli videroid** (différé ; faisable) |
| Exceptions : **warning (non fatal) vs fatal (`exit(1)`) + traceback détaillé** | `alert_on_exceptions` → **tout** en alerte non fatale, **sans** distinction ni traceback | 🟡 | **oubli videroid** (atténuable) + format `error()` fixe |
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
| **Titre** gras+**souligné**, noir, **clic=toggle** | `Text(strong)` seul | 🟡 | **oubli videroid** : soulignement (arg `underline`), couleur noire, clic-toggle (via `Div`) |
| Meta-titre italique `#666666` | `Text(italic, color=gray)` | 🟡 | **oubli videroid** : couleur approximative |
| **Nom fichier** : 2 états, **monospace**, fonds+bordure, **survol→souligné**, **clic→ouvre** | 2 états (couleurs approx), reste absent | 🟡 | états ✅ ; **monospace = manque videre (G17)** ; fond/bordure/survol/clic = **oubli videroid** |
| **Format** badge EXT `#333`, codecs `#666`, badge byte-rate | 1 `Text` plat | ❌ | **manque videre (G17)** : couleurs/badges inline impossibles dans 1 `Text` |
| **Specs** durée `#0066cc`, w/h `#006600`, audio `#666` | 1 `Text` plat | ❌ | **manque videre (G17)** |
| **Dates** monospace `#996600`, `(entry/opened)` `#888` | 1 `Text` plat | ❌ | **manque videre (G17)** (monospace + couleurs) |
| **Langues** labels `#333`, valeurs `#555`, `(none)` `#aaa` | 1 `Text` plat | 🟡 | **manque videre (G17)** (couleurs inline) |
| Statuts NOT FOUND `#cc0000` / Unreadable `#cc6600` / Watched `#008800` | `Text(red/darkorange/green)` | ✅ | couleurs nommées **approximatives** |
| Similarity `#0066cc` / **Re-encoded `#9900cc`** | `Text("Similarity:…")` sans couleur ; **Re-encoded absent** | 🟡 | **oubli videroid** : couleur + Re-encoded |
| Diff de groupe (champ `#ffcccc`, caractère `#ff9999`) | absent | ❌ | **oubli videroid** (+ couleur inline G17) |
| Erreurs `#cc0000` | `Text(red)` | ✅ | — |
| **Propriétés** : chips `#1976d2` soulignés sur `#e3f2fd`, **clic→filtrer**, **`FlowLayout`** (enroule) | `Row` de `Container(Text, bg BADGE_BG, padding)` ; pas de clic | 🟡 | style+clic = **oubli videroid** ; **enroulement = manque videre (G16)** |
| **6 états visuels** (survol/sélection/not-found × bordure + radius 6, survol manuel) | **sélection** ✅ + **zébrure** (que kyuti n'a pas) ; rien d'autre | ❌ | **MAJEUR** : bordure/radius = **oubli videroid** ; survol = **oubli videroid** (events `mouse_enter/exit`, tracking manuel car 6 > 3 états `Div`) ; **zébrure à RETIRER** (kyuti normal = `#ffffff`) |

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
| `notification_received` → Session Log | ❌ | |
| Routage Process-active vs pages | ✅ | |

## 8. Les 13 dialogs *(kyuti: dialogs/)*

| Dialog | Statut | Note |
|---|---|---|
| video_properties_dialog (Properties/Info, éditeurs par type) | ❌ | **le plus gros manque** ; différé |
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
- **Oubli videroid (≈ la moitié — corrigeable sans toucher videre)** : couleurs/styles non posés (boutons sidebar, compteur sélection, Multiple-vert, Trash-all rouge), centrages, fonds de sections, largeurs (28/32×24/200/220), désactivation aux bornes, troncatures, ordre des sections, libellés, items de menu absents, video_confirm sans vignette, OK jamais grisé, alignements à droite. **C'est le gros du visuel manquant.**
- **Manque videre (structurel, → GAPS.md)** : G1 (Table), G2 (Tabs), G3/G10 (menus), G5 (spin), G7 (splitter), G9 (virtualisation/slot-reuse), G11 (TextArea), G12 (placeholder), G15 (Dropdown scroll), G16 (flow), G17 (rich-text/monospace), **G18 (border-radius — PARTOUT)**, **G19 (Button : taille/gras du label)**, **G20 (ScrollView scroll-to)**, **G21 (Dropdown on_change / Checkbox disabled)**, G22 (double-clic), G23 (curseur), G24 (TextInput on_change), G-KBD (raccourcis), G-MODAL (fancybox 80% fixe, mini-tailles ignorées, Entrée≠OK), G-TITLE, G-DPI ; + `ProgressBar` non stylable et pas de spinner circulaire (étendent G14).
- **Inhérent (non corrigeable — différence de framework)** : chrome Qt natif (barre de menus, scrollbars, **zébrures `AlternateBase`**, en-têtes de table, popups de combo, `QMessageBox`, `QGroupBox`, fenêtres `QDialog`). videre dessine ses propres widgets.

## Fonctions ABSENTES (à porter)
`video_properties_dialog` (gros), `batch_edit` multi-prop (test-only chez kyuti), `goto_page` (G5), **Session Log**, **Find Similar / Re-encoded**, **Random Video / Generate Playlist**, actions de similarité (Dismiss/Reset/Generalize), **Move to…**, **classifier Concat**, statut **Re-encoded**, **clic-valeur = filtrer**, **Open in VLC**, **Copy File Title**, vignette du confirm destructif, « Confirm all unique moves ».

## Correctifs videroid prioritaires (impact visuel élevé, coût faible)
1. **Page-size défaut → 20** (`videos_page.py:37`, `VIDEO_DEFAULT_PAGE_SIZE`). *Bug net.*
2. **Carte** : vignette en cadre fixe 180×100 ; retirer la zébrure ; ajouter les 6 états (au moins sélection+not-found+bordures, radius dépend de G18).
3. **Sidebar** : poser les fonds de sections + couleurs des boutons ⚙/✕/✙ (mode actif gras dépend de G19) ; compteur sélection `#0078d4` gras/italique.
4. **Properties** : Multiple "Yes" en vert (1 ligne) ; **Databases** : corriger les couleurs de survol (et le bug de l'expansé qui perd son bleu).
5. Centrages (titres, rangées de boutons), alignement-droite des nombres (Files), extensions avec point `.`, libellés de menu + items manquants (Find Similar/Re-encoded, Random, Playlist).

> **Cap suggéré** : d'abord les correctifs « oubli videroid » (gros gain visuel, zéro dépendance) ; puis trancher quels manques videre enrichir en priorité — les plus structurants pour le visuel sont **G18 (radius)**, **G19 (style des boutons)** et **G-DPI**, et pour l'UX **G-KBD** et **G15**.
