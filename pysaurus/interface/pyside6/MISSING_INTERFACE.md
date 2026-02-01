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

- [ ] **Convertir valeurs en minuscules/majuscules** (pour propriétés string)
- [ ] **Compter les valeurs de propriété** (count_property_values)
- [ ] **Remplacer valeurs de propriété** (replace_property_values)

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
- [ ] **DialogSearch** - recherche dans les groupes/pages

---

## 11. Affichage vidéo

- [ ] **Affichage des moves** (confirmations de déplacement potentielles)
- [ ] **Bouton settings** (gear icon) sur chaque vidéo pour le menu contextuel rapide

---

## Résumé par priorité

### Haute priorité (fonctionnalités importantes)

1. Copier dans le presse-papiers (file path, title, ID)
2. Renommer vidéo
3. Renommer/éditer dossiers de la base de données
4. Classifier path navigation

### Moyenne priorité

6. Dismiss/Reset similarity
7. Confirmer déplacements (move_id grouping)
8. Convertir valeurs en min/majuscules
9. Sélection avancée (tout sélectionner dans la vue)
10. Raccourcis clavier reset (Ctrl+Shift+...)

### Basse priorité

11. Go to page dialog
12. Options menu (confirmation dialogs)
13. Historique des vidéos
