# GAPS.md — insuffisances videre rencontrées en implémentant videroid

Journal des manques videre **rencontrés à l'usage** (décision 2026-06-25 :
*contourner d'abord, enrichir videre après*). Le catalogue prévisionnel des gaps
est dans `PLAN.md` §4.2 ; ce fichier note ce qui a **réellement** bloqué pendant
l'implémentation, le contournement choisi, et la décision.

---

## G-KBD — Pas de mécanisme de raccourci clavier global / de page

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

**Décision (2026-06-28)** : **différé**. Les chunks 4-5 de la Phase 5b se font à
la souris (menu ⚙ de sélection, boutons de dialog). Le hook clavier videre est une
**tâche dédiée** à traiter ensuite (changement de sémantique d'événements →
design soigné + gated par les tests videre).

---

## G-MODAL — Un seul slot de fancybox (pas de modals empilés)

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
dialog et l'action n'ouvre pas de sous-modal (la confirmation de Fill est omise en
v1).

**Piste videre** : pile de fancyboxes (modals empilés) ou une primitive de
confirmation indépendante du slot principal.

**Décision** : contourné (inline). Pile de modals = piste videre ultérieure.

---

## G-TITLE / G-DPI — Coquille applicative

*Rencontrés en Phase 8, 2026-06-28.*

- **G-TITLE** : `Window.title` n'a qu'un getter (pas de setter) → titre OS figé.
  Contournement : un **label de titre in-app** mis à jour à la navigation.
- **G-DPI** : videre n'expose pas le device-pixel-ratio ; `Window(font_size=…)`
  existe mais pas de mise à l'échelle auto par densité d'écran (la version Qt
  scalait la police). Reporté ; police par défaut conservée.

À l'inverse, la **gestion d'exceptions EST fournie** par videre :
`Window(alert_on_exceptions=(…,))` affiche un dialog d'erreur au lieu de crasher
(utilisé en 8.3). La distinction fine warning/fatal de la version Qt est reportée.

**Piste videre** : setter de titre ; accès DPR + police mise à l'échelle.
