# Fonctionnalités manquantes dans l'interface PySide6

Comparaison entre l'interface web (`pysaurus/interface/web/src`) et l'interface PySide6 (`pysaurus/interface/pyside6`).

---

## 1. Opérations sur les vidéos

- [x] **Copier dans le presse-papiers** :
  - Copier le meta title
  - Copier le file title
  - Copier le chemin du fichier
  - Copier le video ID
- [x] **Renommer vidéo** (changer le file title)
- [x] **Confirmer déplacement** (menu contextuel quand groupé par move_id)
- [x] **Dismiss similarity** (rejeter la similarité)
- [x] **Reset similarity** (réinitialiser la similarité)

---

## 2. Opérations sur la base de données

- [x] **Renommer la base de données** (menu Database > Rename Database)
- [x] **Éditer les dossiers sources** (menu Database > Edit Folders)
- [x] **Fermer la base de données** (menu Database > Close Database)

---

## 3. Gestion du Classifier (classification hiérarchique)

- [x] **Affichage du chemin de classification** (classifier path) - section dans sidebar
- [x] **Navigation dans le classifier** (unstack, reverse, concatenate) - boutons dans section
- [x] **Classifier focus prop val** (focus sur une valeur de propriété) - clic sur valeur dans liste

---

## 4. Opérations sur les propriétés

- [x] **Convertir valeurs en minuscules/majuscules** (pour propriétés string)
- [x] **Compter les valeurs de propriété** (affiché dans PropertyValuesDialog)
- [x] **Remplacer valeurs de propriété** (via rename dans PropertyValuesDialog)

---

## 5. Raccourcis clavier

| Raccourci Web | Action | PySide6 |
|---------------|--------|---------|
| Ctrl+Shift+T | Reset sources | Oui |
| Ctrl+Shift+G | Reset grouping | Oui |
| Ctrl+Shift+F | Reset search | Oui |
| Ctrl+P | Manage properties | Oui |
| Ctrl+L | Play list | Oui |

---

## 6. Fonctionnalités de playlist

- [x] **Générer et ouvrir une playlist** des vidéos filtrées

---

## 7. Sélection avancée

- [x] **Sélectionner/désélectionner tous** dans la vue filtrée (bouton "Select All in View")
- [x] **Afficher uniquement les sélectionnés** (bouton toggle "Show Selected")

---

## 8. Opérations de masse sur les groupes

- [x] **Confirmer tous les déplacements uniques** (bouton dans section Grouping quand groupé par move_id)
- [x] **Appliquer opération sur la vue** (apply_on_view) - utilisé par batch edit avec Selector

---

## 9. Menu/Actions manquants

- [x] **Menu Database** complet :
  - Rename database
  - Edit folders
  - Close database
- [x] **Menu Options** :
  - Sélection de la taille de page (10, 20, 50, 100)
  - Confirmation avant suppression des entrées non trouvées

---

## 10. Fonctionnalités spéciales manquantes

- [x] ~~**Historique des vidéos ouvertes**~~ - redondant : trier par "date_entry_opened DESC" affiche les dernières vidéos ouvertes
- [x] **FormPaginationGoTo** - aller à une page spécifique (clic sur "Page X/Y")
- [x] ~~**DialogSearch**~~ - redondant : la barre de recherche PySide6 intègre 4 modes (AND, OR, Exact, ID)

---

## 11. Affichage vidéo

- [x] **Affichage des moves** (sous-menu "Confirm move to" dans le menu contextuel)
- [x] ~~**Bouton settings**~~ - redondant : le menu contextuel (clic droit) offre les mêmes 16 actions

---

## Résumé par priorité

### Haute priorité (fonctionnalités importantes)

(Toutes les fonctionnalités hautes priorités ont été implémentées)

### Moyenne priorité

(Toutes les fonctionnalités moyennes priorités ont été implémentées)

### Basse priorité

(Toutes les fonctionnalités basses priorités ont été implémentées)

---

## Fonctionnalités déjà implémentées

- [x] Copier dans le presse-papiers (meta title, file title, chemin, video ID)
- [x] Renommer vidéo (changer le file title)
- [x] Dismiss similarity (rejeter la similarité)
- [x] Reset similarity (réinitialiser la similarité)
- [x] Convertir valeurs en minuscules/majuscules
- [x] Compter les valeurs de propriété
- [x] Remplacer valeurs de propriété
- [x] Générer et ouvrir une playlist (Ctrl+L)
- [x] Recherche avec 4 modes (AND, OR, Exact, ID) dans la sidebar
- [x] Menu contextuel complet (16 actions, équivalent au menu settings web)
- [x] Renommer la base de données (menu Database)
- [x] Éditer les dossiers sources (menu Database)
- [x] Fermer la base de données (menu Database)
- [x] Raccourcis clavier reset (Ctrl+Shift+T/G/F) et Ctrl+P pour les propriétés
- [x] Confirmer déplacement individuel (menu contextuel "Confirm move to")
- [x] Confirmer tous les déplacements uniques (bouton quand groupé par move_id)
- [x] Go to page dialog (clic sur "Page X/Y" dans la barre de pagination)
- [x] Menu Options avec sélection de taille de page et confirmation de suppression
- [x] Classifier path navigation (affichage, unstack, reverse, concatenate)
- [x] Bouton "+" pour ajouter un groupe au classifier (propriétés multiples)
- [x] Sélection avancée avec Selector (select all in view, show only selected)
- [x] Batch edit utilisant le Selector pour appliquer sur toute la vue
