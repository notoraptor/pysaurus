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

## 1. Coquille & navigation *(kyuti: main.py, main_window.py)*

| Fonction | Statut | Note |
|---|---|---|
| Fenêtre 1200×800 | ❓ | videroid : taille Window par défaut |
| Titre dynamique selon page/base | 🟡 | titre **in-app**, pas le titre OS (G-TITLE) |
| Démarrage page Databases | ✅ | |
| Mise à l'échelle DPI de la police | ❌ | G-DPI |
| 4 pages permanentes + Process dynamique | ✅ | |
| Sélecteur radio (Videos/Properties/Files) | ❓ | présent ; **rendu visuel à vérifier** |
| Radios + menus désactivés pendant opération / cachés sans base | ✅ | |
| Barre de statut (message, clic=effacer, horodatage) | 🟡 | clic=effacer OK ; journal horodaté à vérifier |
| Confirmation de fermeture → `close_app()` | ✅ | |
| Exceptions non gérées → dialog (warning/fatal + traceback) | 🟡 | `alert_on_exceptions` ; distinction warning/fatal reportée |

## 2. Barre de menus *(kyuti: main_window.py)*

| Menu / entrée | Statut | Note |
|---|---|---|
| **Database** : Rename, Edit Folders, Update | ✅ | |
| **Database** : Find Similar Videos | ❌ | niche, différé |
| **Database** : Find Re-encoded Videos | ❌ | niche, différé |
| **Database** : Close Database, Quit | ✅ | |
| **Database** : Session Log… | ❌ | différé |
| **View** : Random Video (Ctrl+O) | ❌ | + raccourci (G-KBD) |
| **View** : Generate Playlist (Ctrl+L) | ❌ | + raccourci (G-KBD) |
| **View** : Refresh View (Ctrl+R) | 🟡 | Refresh présent ; raccourci absent (G-KBD) |
| **Options** : Page Size (10/20/50/100, défaut 20) | ✅ | |
| **Options** : toggle « Confirm deletion not found » | ✅ | |
| **Help** : About | ✅ | |
| Rendu visuel de la barre (vs menus Qt natifs) | 🟡 | barre de `ContextButton` plats (G3/G10) — **à auditer** |

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

### 4a. Carte vidéo
| Élément | Statut | Note |
|---|---|---|
| Vignette 180×100 (placeholder si absente) | ✅ | resize PIL (G13) |
| Titre fichier (checkbox + gras souligné) | 🟡 | **diff caractère** en groupe de similarité = ❓/❌ |
| Meta-titre (italique gris), chemin (couleur selon vu) | ✅ | |
| Badges EXT/taille/conteneur/codecs/débit | ✅ | |
| Durée/résolution @ fps/profondeur/échantillonnage/audio | ✅ | |
| Dates, langues audio & sous-titres | ✅ | |
| Statuts NOT FOUND / Unreadable / Watched | ✅ | |
| Similarity ID / Re-encoded ID | 🟡 | Similarity affiché ; Re-encoded ❓ |
| Messages d'erreur | ✅ | |
| Propriétés custom (nom : valeur) **cliquables** (clic=filtrer) | 🟡 | badges présents ; **clic-pour-filtrer** ❓/❌ |
| **États visuels** (neutre/survol/sélection/not-found jaune) — fonds+bordures, soulignement au survol | ❓ | **à auditer en priorité (visuel)** |

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
