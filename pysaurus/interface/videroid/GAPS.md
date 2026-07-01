# GAPS.md — insuffisances videre (backlog d'enrichissement)

Catalogue **unique** des manques de **videre** rencontrés en construisant
`videroid` (la réimplémentation de l'interface Pysaurus sur videre). Décision
fondatrice (2026-06-25) : *contourner d'abord, enrichir videre après*. Chaque
entrée donne : le **constat**, ce qu'il **impacte**, le **contournement videroid
actuel** (fichiers concernés), et la **piste videre** (le vrai widget ou
l'amélioration qui remplacerait le contournement).

> Ce fichier remplace l'ancien `PLAN.md` (phases 0–8 exécutées). La grille de
> parité kyuti↔videroid est passée dans **`PARITY.md`**. GAPS.md est désormais la
> **TODO d'enrichissement de videre**, alimentée par l'usage réel de videroid.

---

## Vue d'ensemble

| # | Manque | Statut | Contournement videroid | Piste videre |
|---|--------|--------|------------------------|--------------|
| G1 | widget Table | contourné | `widgets/table.py` (Column de Rows pondérés) | `videre.Table` |
| G2 | onglets | contourné | `widgets/tabs.py` (boutons + holder) | `videre.Tabs` |
| G3 | barre de menus | atténué | `ContextButton` ×4 + `Window.set_context` | `MenuBar` natif |
| ~~G4~~ | sélecteur de fichiers | ✅ **résolu** | `videre.Dialog` | (mineur) `filetypes`/`initialdir` |
| G5 | champ numérique (SpinBox) | contourné | `TextInput` + validation | `NumberInput` |
| G6 | tooltips | différé | libellés explicites | tooltip au survol |
| G7 | splitter ajustable | contourné | largeurs fixes (`Row`/`Column`) | `Splitter` |
| G8 | drag-drop | contourné | boutons Move Up/Down | drag-drop générique |
| G9 | virtualisation | **partiel** (côté videre) | pagination (≤100) | virtualiser le *build* |
| G10 | menus riches | atténué | `set_context` plat + glyphes ☑ | sous-menus / items cochables / icônes |
| G11 | `TextInput` multi-ligne | contourné | éditeur 1 ligne | `TextArea` |
| G12 | placeholder | contourné | label adjacent / gris manuel | placeholder natif |
| G13 | `Picture` resize | contourné | PIL en amont | `width`/`height`/fit |
| G14 | `ProgressBar` libellé % | contourné | `Text` à côté | label intégré |
| G15 | `Dropdown` sans scroll | **manque, non contourné** | aucun (la liste déborde) | ScrollView borné dans le popup d'options |
| G16 | pas de layout « flow »/wrap | **manque** | `Row` (pas de retour à la ligne) | layout flow (chips/badges qui s'enroulent) |
| G17 | `Text` mono-couleur + pas de monospace | **manque** | 1 `Text` = 1 couleur ; décomposer en `Row` de `Text` (lourd) ; pas de monospace | rich-text inline (spans colorés) + famille de police (monospace) |
| G18 | **pas de `border-radius`** | **manque** | coins carrés | `Border`/`Style` n'ont aucun rayon (`border.py` = arêtes droites). Impacte cartes (r6), sections sidebar (r3), badges (r3), vignettes (r2), items DB (r4), tous les cadres |
| G19 | `Button`/`ContextButton` n'acceptent **aucun** `style=` appelant | **manque** | ni fond, ni couleur de texte, ni bordure/hover, ni taille/gras du label | `AbstractButton.__init__` construit son propre `style` et le passe à `Div` → fournir `style=` lève `TypeError: multiple values for keyword 'style'` (`abstract_button.py:18,20`, **vérifié**) ; le label est un `Text(height_delta=0)` sans `size`/`strong` (l.19,55). Bloque : **couleurs des boutons sidebar** (⚙ bleu/✕ rouge/✙ vert), Delete/Trash-all rouge, Continue vert, Create/mode-actif gras, lien pagination souligné, taille 0.8× (cf. G-DPI) |
| G20 | `ScrollView` sans scroll-to ni pas molette | **manque** | aucun (l'enfant courant peut être hors écran) | pas d'API « défiler vers l'enfant » + `_SCROLL_STEP=120` fixe. Bloque auto-scroll de la liste de groupes, reset-au-top sur saut de page, pas molette de 20 |
| G21 | `Dropdown` sans `on_change` + `Checkbox`/`Button` sans `disabled` | **manque** | gating à la soumission seulement | impossible d'activer/désactiver des champs selon un autre (form Properties : multiple/enum/OK selon type ou validité) |
| G22 | pas d'événement double-clic | **manque** | bouton/clic explicite | double-clic (ouvrir une base d'un double-clic — kyuti databases) |
| G23 | pas de forme de curseur par widget | **manque** | aucun | curseur « main » sur les éléments cliquables |
| G24 | `TextInput` sans `on_change` | **manque** | bouton « Apply » (pas de live) | event de saisie → filtre/recherche **live** (Files, Search). Voir aussi G12 (placeholder) |
| G25 | pas de **scheduling temporisé** (timer/délai) | **manque** | aucun (statut persistant) | `Window.call_later` = tick suivant (**pas de délai**), `TaskManager` sans timer → pas de « rappeler dans N s ». Bloque les **toasts** de statut auto-effacés (3 s), et sous-tend G6 (tooltip = délai de survol) + debounce (recherche live) |
| G-KBD | raccourcis clavier | **bloquant, différé** | aucun (tout à la souris) | hook clavier fall-through |
| G-MODAL | modals empilés | contourné | prompts **inline** | pile de fancybox |
| G-TITLE | titre OS | contourné | titre **in-app** | setter `Window.title` |
| G-DPI | scaling DPI | différé | police fixe | accès DPR + police mise à l'échelle |

---

## Widgets & primitives manquants

### G1 — Pas de widget Table
- **Constat** : videre n'a pas de widget tableau (colonnes, en-tête, tri, zébrures).
- **Impacte** : page **Properties** (6 colonnes Name/Type/Default/Multiple/Enum/Actions), page **Files** (table extensions + table fichiers).
- **Contournement videroid** : `widgets/table.py` — helpers `header(columns)` et `cell(text, weight, strong)` = un `Column` de `Row`s pondérés ; chaque page garde son wrapper de ligne (zébrure / surbrillance de sélection) et ses cellules non-texte (boutons, ⚙) en inline. Utilisé par `pages/properties_page.py` et `pages/files_page.py`.
- **Piste videre** : un vrai `videre.Table` (modèle colonnes + poids/largeurs, en-tête, optionnellement tri et zébrure intégrés).

### G2 — Pas d'onglets
- **Constat** : aucun widget Tabs/TabView.
- **Impacte** : `sources_dialog` (Simple/Advanced), page **Files** (Others/Video stats), et le futur `video_properties_dialog` (Properties/Info).
- **Contournement videroid** : `widgets/tabs.py` — `Tabs(Column)` = une `Row` de boutons + un `Container` holder dont on remplace le `control` au clic ; builders **lazy** (`refresh()`/`active_index`). Utilisé par `pages/files_page.py` et `dialogs/sources_dialog.py`.
- **Piste videre** : un `videre.Tabs`/`TabView` (bandeau + contenu, état actif, builders lazy).

### G3 — Pas de barre de menus native
- **Constat** : pas de `MenuBar`.
- **Impacte** : la coquille applicative (menus Database / View / Options / Help).
- **Contournement videroid** (atténué) : `app.py` construit 4 `videre.ContextButton` (`_menu_database/_menu_view/_menu_options/_menu_help`) désactivables, ouvrant des popups via `Window.set_context`.
- **Piste videre** : un `MenuBar` dédié (ou un `ContextButton` enrichi — cf. G10).

### ~~G4~~ — Sélecteur de fichiers/dossiers ✅ RÉSOLU
- **Constat** : fourni par videre — `videre.Dialog` (`select_directory` / `select_many_files` / `select_file_to_open` / `select_file_to_save`, via `tkinter.filedialog`, natif cross-platform).
- **Contournement** : aucun — `Dialog.*` utilisé directement (page Databases, `edit_folders`).
- **Piste videre** (mineure) : exposer `filetypes`/`initialdir`, retirer un `print` parasite à la fermeture ; dépend de `tkinter` (`python3-tk` sur certaines distros).

### G5 — Pas de champ numérique (SpinBox)
- **Constat** : pas de saisie numérique bornée.
- **Impacte** : aller-à-la-page (goto), valeurs `Default` int/float des propriétés.
- **Contournement videroid** : pagination par boutons `<< < Page X/Y > >>` (`videos_page.py`, pas de dialog goto à spin) ; pour les propriétés, `TextInput` + `_parse_default` (parse/validation par type) dans `pages/properties_page.py`.
- **Piste videre** : un `NumberInput`/SpinBox (min/max/pas, validation intégrée).

### G6 — Aucun tooltip
- **Constat** : pas d'info-bulle au survol.
- **Impacte** : l'UX partout (les icônes/⚙ ne s'expliquent pas au survol).
- **Contournement videroid** : différé ; libellés explicites à la place.
- **Piste videre** : un mécanisme de tooltip au survol (timer + popup léger).

### G7 — Pas de splitter ajustable
- **Constat** : pas de séparateur redimensionnable à la souris.
- **Impacte** : la sidebar de filtres / le partage liste-détails.
- **Contournement videroid** : largeurs **fixes** — `videos_page.py` = `Row([sidebar width=240, content weight=1])`.
- **Piste videre** : un `Splitter` (poignée glissable, tailles persistées).

### G8 — Pas de drag-drop
- **Constat** : pas de réordonnancement par glisser-déposer.
- **Impacte** : `sorting_dialog` (ordre des critères de tri).
- **Contournement videroid** : boutons **Move Up/Down** (`dialogs/sorting_dialog.py` `_up`/`_down`).
- **Piste videre** : un drag-drop générique (réordonnancement de listes).

### G9 — `ScrollView`/`Column`/`Row` non virtualisés
- **Constat** : les layouts rendent **tous** leurs enfants. *Partiellement adressé depuis, côté videre* : `crop_drawer` virtualise la **rasterisation** (`ScrollView.draw` ne peint que les enfants visibles). Reste la virtualisation du **build/shaping** des items hors écran (plafond O(n), surtout le coût « shaping » de texte — cf. verdict perf).
- **Impacte** : listes longues (cartes vidéo).
- **Contournement videroid** : la **pagination** (`page_size` ≤ 100) borne le besoin → on ne construit jamais des milliers de cartes.
- **Piste videre** : virtualiser la **construction** (ne pas instancier/shaper les widgets hors viewport) ; axe perf majeur (`wip/videroid_perf/`).

### G10 — `ContextButton` plat
- **Constat** : pas de sous-menus, ni items cochables, ni icônes.
- **Impacte** : sous-menu **Copy**, **Edit Properties** (une entrée par propriété), toggle **Show Only Selected**.
- **Contournement videroid** (atténué) : menus custom via `Window.set_context` (sous-menus par composition) ; coche rendue par glyphe **☑/☐** (menu Options, show-only-selected) ; menu ⚙ par carte (`widgets/video_card.py`) et menu de sélection (`videos_page.py`) en listes plates.
- **Piste videre** : menus riches natifs (sous-menus, items cochables, icônes).

### G11 — `TextInput` mono-ligne
- **Constat** : pas de zone de texte multi-ligne.
- **Impacte** : l'éditeur d'**expression** des sources avancées.
- **Contournement videroid** : `TextInput` 1 ligne (`dialogs/sources_dialog.py`, onglet Advanced).
- **Piste videre** : un `TextArea` multi-ligne.

### G12 — `TextInput` sans placeholder
- **Constat** : pas de texte indicatif grisé.
- **Impacte** : Search (« Search… (Ctrl+F) »), divers champs.
- **Contournement videroid** : label adjacent / gris géré à la main.
- **Piste videre** : un `placeholder` natif sur `TextInput`.

### G13 — `Picture` ne redimensionne pas
- **Constat** : `Picture` affiche à la **taille native** (pas de scale).
- **Impacte** : les vignettes (cible 180×100).
- **Contournement videroid** : redimensionner via **PIL en amont** (on a les bytes JPEG) — `widgets/video_card.py::_thumbnail` fait `PIL.Image.thumbnail((180,100))` puis crée le `Picture`.
- **Piste videre** : `width`/`height`/`fit` (contain/cover) sur `Picture`. *(NB : `Gradient` vient de gagner `colors`/`__eq__` — même esprit d'enrichissement.)*

### G14 — `ProgressBar` sans libellé %
- **Constat** : pas de pourcentage intégré.
- **Impacte** : la page **Process** (barres de jobs).
- **Contournement videroid** : un `Text` « titre (X %) » à côté de la barre (`pages/process_page.py::_display`).
- **Piste videre** : un libellé % optionnel intégré au `ProgressBar`.

### G15 — `Dropdown` sans scroll sur liste longue *(découvert à la revue de parité, 2026-06-30)*
- **Constat (vérifié)** : `videre.Dropdown._open_context` (`videre/widgets/dropdown.py:104-110`) construit un `_PlainColumn` avec **tous** les `_OptionWidget`, **sans `ScrollView`** → une liste longue déborde la fenêtre (options du bas inaccessibles). kyuti (`QComboBox`) scrolle nativement (`maxVisibleItems=10` + auto-scroll vers la valeur courante).
- **Impacte** : combo de **groupement** (34 champs) et de **tri** (33 champs) ; tout `Dropdown` à options nombreuses.
- **Contournement videroid** : **aucun** (le popup est interne à `Dropdown` ; pas contournable proprement côté videroid). C'est le manque que l'utilisateur a signalé et que la première passe avait raté.
- **Piste videre** : envelopper `_PlainColumn` dans un `ScrollView` à hauteur **bornée** (≤ hauteur fenêtre), avec auto-scroll vers l'option sélectionnée à l'ouverture.

### G16 — Pas de layout « flow » / wrap *(découvert à la revue de parité, 2026-06-30)*
- **Constat (vérifié)** : videre n'a pas de layout qui passe à la ligne (`videre/layouts/` n'a ni `Flow` ni `Wrap` ; `Row` aligne sur une seule ligne, `ScrollView.wrap_horizontal` = scroll, pas flow). kyuti utilise un `FlowLayout` maison pour les badges de propriété (`video_list_item.py:418`).
- **Impacte** : badges de propriété de la **carte vidéo** (et tout ensemble de chips de largeur variable).
- **Contournement videroid** : `Row` simple → les badges **débordent** horizontalement au lieu de s'enrouler (non équivalent).
- **Piste videre** : un layout `Flow`/`Wrap` (place les enfants de gauche à droite, passe à la ligne quand la largeur est dépassée).

### G17 — `Text` mono-couleur + pas de police monospace *(découvert à la revue de parité, 2026-06-30)*
- **Constat (vérifié)** : `videre.Text` n'a qu'**un seul `color`** (`widgets/text.py:49`) → pas de spans colorés inline ; et **aucun paramètre de famille de police** (le shaper utilise les polices groupées) → pas de monospace par `Text`. kyuti compose ses lignes en **rich text HTML** (durée `#0066cc`, largeur/hauteur `#006600`, badges `#333`, codecs `#666` dans UNE ligne ; nom de fichier & dates en `<code>` monospace).
- **Impacte** : lignes de specs / format / dates / langues de la **carte vidéo** ; nom de fichier monospace ; chemins monospace (`video_confirm`).
- **Contournement videroid** : actuel = une seule couleur par ligne (les couleurs inline sont **perdues**) ; possible mais lourd = décomposer chaque ligne en `Row` de plusieurs `Text` colorés (et le monospace reste impossible).
- **Piste videre** : rich-text inline (segments colorés dans un `Text`) + sélection de famille de police (au moins une monospace groupée).

### G19 — `Button`/`ContextButton` non stylables *(constat affiné & vérifié, 2026-06-30)*
- **Constat (vérifié par exécution)** : `AbstractButton.__init__` (`abstract_button.py:18-20`) construit lui-même `style = {"default": {"square": square}}` et le passe à `Div`. Fournir son propre `style=` lève donc `TypeError: ... got multiple values for keyword argument 'style'` — confirmé pour `videre.Button` **et** `videre.ContextButton`. À l'inverse, `videre.Div(on_click=…, style=…)` fonctionne. Conséquence : un `Button` n'est **pas** colorable (ni fond, ni texte, ni bordure, ni hover) ; et son label est un `Text(height_delta=0)` créé sans `size`/`strong` (l.19,55) → ni taille ni gras/italique du libellé.
- **Impacte** : tous les boutons colorés de kyuti — sidebar `#settingsBtn` (⚙ bleu `#1976d2`), `#clearBtn` (✕ rouge `#cc3333`), `#classifierBtn` (✙ vert `#4CAF50`) ; **Delete** rouge (Databases) ; **Trash all** rouge (Files) ; **Continue** vert (Process) ; **Create** / mode de recherche actif en gras ; lien pagination souligné ; boutons sidebar à 0.8× (cf. G-DPI).
- **Contournement videroid** : possible mais imparfait = remplacer le `Button` par un `videre.Div(Text(color=…), style={…}, on_click=…)` (le chemin qui marche). Mais on perd les sémantiques natives de `Button` (`disabled`, focus) et, pour le ⚙ de sélection qui est un **`ContextButton`** (ouvre un menu), il faudrait réimplémenter l'ouverture du menu → non trivial. **Non contourné à ce jour** (boutons laissés non colorés).
- **Piste videre** : faire accepter à `AbstractButton`/`ContextButton` un `style=` appelant et le **fusionner** avec le style interne (`StyleDef.merged_with` existe déjà), plus exposer `size`/`strong`/`italic` du label. ~Quelques lignes, général, à *gater* par les tests videre.

### G25 — Pas de scheduling temporisé (timer / délai) *(découvert en portant status+process, 2026-07-01)*
- **Constat (vérifié)** : `Window.call_later(fn, *args)` poste juste un `CallbackTask` exécuté au **tick suivant** (`tasks.py::TaskManager.manage_tasks`), **sans notion de délai** ; aucun « rappeler dans N secondes ». Pas de timer/horloge exposé côté app.
- **Impacte** : les **toasts** de barre de statut (kyuti `showMessage(msg, 3000)` s'auto-efface après 3 s) ; sous-tend aussi **G6** (tooltip = popup après un délai de survol) et tout **debounce** (recherche/filtre live sans marteler le backend à chaque frappe).
- **Contournement videroid** : aucun propre. Le seul détour serait `call_async` + `time.sleep(3)` + `call_later` (un **thread par toast** — moche, non retenu). Statut laissé **persistant** (pas de toast).
- **Piste videre** : une API de callback différé (`call_after(delay, fn)` / timer), s'appuyant sur l'horloge de la boucle (`_clock`/`framing.py`).

---

## Manques transverses (sémantique d'événements & coquille)

### G-KBD — Pas de mécanisme de raccourci clavier global / de page

*Rencontré en Phase 5b (sélection), 2026-06-28.*

**Constat (vérifié dans le code videre)** :
- `windowing/event_manager.py::on_keydown` fait
  `(self._focus or self._layout).handle_keydown(entry)` → dispatch **mono-cible**
  au widget focalisé, sinon au layout racine.
- **Pas de bubbling** vers les ancêtres : l'`EventPropagator` n'a aucune méthode
  keydown (il ne gère que clic/focus/souris) ; la valeur de retour de
  `handle_keydown` (`Widget | None`) est **ignorée** par l'appelant.
- `Window` n'expose **aucun** hook clavier (pas de `add_keydown_callback`).
- `WindowLayout.handle_keydown` ne traite que `Échap` (ferme context/fancybox).

→ Une **page** ne peut pas capter un raccourci global (Ctrl+A, Suppr, Entrée,
flèches…) : il faudrait qu'elle soit elle-même le focus, ce qui n'arrive jamais
(le focus va aux boutons / champs de saisie, qui « avalent » la touche sans la
faire remonter).

**Impacte** : Phase 5b (raccourcis de sélection/navigation) **et** la convention
des dialogs (`Entrée`=OK au-delà de la simple fancybox).

**Contournement videroid** : aucun propre. Forcer le focus sur un widget-racine de
page est fragile (chaque clic sur un contrôle vole le focus). Les actions clavier
restent donc accessibles **à la souris** (menu ⚙ de sélection, boutons de dialog) ;
seuls les raccourcis-touches manquent.

**Piste videre** : exposer un handler clavier au niveau `Window`/`WindowLayout`
pour les touches **non consommées** par le focus (fall-through), en s'appuyant sur
la valeur de retour de `handle_keydown` comme signal « consommé ». Touche la
sémantique d'événements de videre → à concevoir avec soin et à *gater* par les
tests videre.

**Décision (2026-06-28)** : **différé**. Tâche dédiée à traiter (changement de
sémantique d'événements → design soigné + gated par les tests videre).

### G-MODAL — Un seul slot de fancybox (pas de modals empilés)

*Rencontré en Phase 6.4 (Manage values), 2026-06-28.*

**Constat (vérifié)** : `Window.set_fancybox` / `confirm` / `alert` partagent **un
seul** slot (`WindowLayout._fancybox`) — en ouvrir un second remplace le premier.
Et `FancyCloseButton.click()` exécute `on_click()` **puis** `clear_fancybox()` →
ouvrir un sous-modal depuis un bouton de dialog le ferait fermer aussitôt.

**Impacte** : tout dialog voulant une confirmation / une saisie
(`PropertyValuesDialog` : delete / rename / modifier ; tout « OK puis confirm »).

**Contournement videroid** : confirmations / saisies **inline** dans le dialog
(une ligne-prompt Yes/No ou TextInput, au lieu d'un sous-fancybox). Les dialogs
**passifs** (Move / Fill) évitent le problème : leur `FancyCloseButton` ferme le
dialog et l'action n'ouvre pas de sous-modal.

**Piste videre** : pile de fancyboxes (modals empilés) ou une primitive de
confirmation indépendante du slot principal.

**Décision** : contourné (inline). Pile de modals = piste videre ultérieure.

### G-TITLE / G-DPI — Coquille applicative

*Rencontrés en Phase 8, 2026-06-28.*

- **G-TITLE** : `Window.title` n'a qu'un getter (pas de setter) → titre OS figé.
  Contournement : un **label de titre in-app** mis à jour à la navigation.
- **G-DPI** : videre n'expose pas le device-pixel-ratio ; `Window(font_size=…)`
  existe mais pas de mise à l'échelle auto par densité d'écran (la version Qt
  scalait la police). Reporté ; police par défaut conservée.

À l'inverse, la **gestion d'exceptions EST fournie** par videre :
`Window(alert_on_exceptions=(…,))` affiche un dialog d'erreur au lieu de crasher.
La distinction fine warning/fatal de la version Qt est reportée.

**Piste videre** : setter de titre ; accès DPR + police mise à l'échelle.

---

## Annexe — ce que videre couvre déjà (réutilisation directe)

Pour mémoire (ne pas re-lister comme manques) :

| Besoin | Widget / API videre |
|--------|---------------------|
| Conteneurs / disposition | `Column`, `Row`, `Container`, `Div`, `ScrollView` |
| Texte / libellés | `Text`, `Label` |
| Boutons | `Button`, `SubmitButton`, `AbstractButton` |
| Cases / radios | `Checkbox`, `Radio`, `RadioGroup` |
| Listes déroulantes | `Dropdown` |
| Menus & popups | `ContextButton` (plat) + `Window.set_context()` |
| Vignettes (depuis `bytes`) | `Picture` (PIL) — resize en amont (cf. G13) |
| Champs de saisie | `TextInput` (mono-ligne — cf. G11/G12) |
| Formulaires | `Form` (`.values()`) + `SubmitButton` |
| Progression | `ProgressBar`, `Progressing` |
| Modales / dialogs | `Window.set_fancybox` / `Fancybox` / `FancyCloseButton` ; prêts : `Window.confirm()` / `alert()` / `error()` |
| Sélecteur de fichiers | `videre.Dialog` (natif, cross-platform) ✅ |
| Styles / états (hover/click) | `Div` + `Style`/`StyleDef` |
| Presse-papier | `Clipboard` |
| Notifications applicatives | `Window.notify()` + `set/add/remove_notification_callback` |
| Planification & threads | `Window.call_later/call_async/call_now` + `TaskManager` + `launch_thread` |
| Raccourcis clavier | `handle_keydown` + `KeyboardEntry` (câblage manuel — cf. G-KBD) |
| Tests headless | `StepWindow` + `FakeUser` |
