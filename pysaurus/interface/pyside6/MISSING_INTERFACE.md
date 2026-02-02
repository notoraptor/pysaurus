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
- [ ] **Confirmer déplacement** (quand groupé par move_id)
- [x] **Dismiss similarity** (rejeter la similarité)
- [x] **Reset similarity** (réinitialiser la similarité)

---

## 2. Opérations sur la base de données

- [ ] **Renommer la base de données**
- [ ] **Éditer les dossiers sources** de la base de données
- [ ] **Fermer la base de données** (retour à la page databases sans supprimer)

---

## 3. Gestion du Classifier (classification hiérarchique)

- [ ] **Affichage du chemin de classification** (classifier path)
- [ ] **Navigation dans le classifier** (unstack, reverse, concatenate)
- [ ] **Classifier focus prop val** (focus sur une valeur de propriété)

---

## 4. Opérations sur les propriétés

- [x] **Convertir valeurs en minuscules/majuscules** (pour propriétés string)
- [x] **Compter les valeurs de propriété** (affiché dans PropertyValuesDialog)
- [x] **Remplacer valeurs de propriété** (via rename dans PropertyValuesDialog)

---

## 5. Raccourcis clavier manquants

| Raccourci Web | Action | PySide6 |
|---------------|--------|---------|
| Ctrl+Shift+T | Reset sources | Non |
| Ctrl+Shift+G | Reset grouping | Non |
| Ctrl+Shift+F | Reset search | Non |
| Ctrl+P | Manage properties | Non |
| Ctrl+L | Play list | Oui |

---

## 6. Fonctionnalités de playlist

- [x] **Générer et ouvrir une playlist** des vidéos filtrées

---

## 7. Sélection avancée

- [ ] **Sélectionner/désélectionner tous** dans la vue filtrée (pas juste la page courante)
- [ ] **Afficher uniquement les sélectionnés** (toggle)

---

## 8. Opérations de masse sur les groupes

- [ ] **Confirmer tous les déplacements uniques** (confirm_unique_moves)
- [ ] **Appliquer opération sur la vue** (apply_on_view)

---

## 9. Menu/Actions manquants

- [ ] **Menu Database** complet :
  - Rename database
  - Edit folders
  - Close database
- [ ] **Menu Options** :
  - Confirmation avant suppression des entrées non trouvées

---

## 10. Fonctionnalités spéciales manquantes

- [ ] **Historique des vidéos ouvertes**
- [ ] **FormPaginationGoTo** - aller à une page spécifique
- [x] ~~**DialogSearch**~~ - redondant : la barre de recherche PySide6 intègre 4 modes (AND, OR, Exact, ID)

---

## 11. Affichage vidéo

- [ ] **Affichage des moves** (confirmations de déplacement potentielles)
- [x] ~~**Bouton settings**~~ - redondant : le menu contextuel (clic droit) offre les mêmes 16 actions

---

## Résumé par priorité

### Haute priorité (fonctionnalités importantes)

1. Renommer/éditer dossiers de la base de données
2. Fermer la base de données
3. Classifier path navigation

### Moyenne priorité

4. Confirmer déplacements (move_id grouping)
5. Sélection avancée (tout sélectionner dans la vue)
6. Raccourcis clavier reset (Ctrl+Shift+T/G/F, Ctrl+P)
7. Confirmer tous les déplacements uniques

### Basse priorité

8. Go to page dialog (FormPaginationGoTo)
9. Options menu (confirmation dialogs)
10. Historique des vidéos ouvertes

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
