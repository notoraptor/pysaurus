# Flask vs PySide6 — Analyse des fonctionnalités

Comparaison de l'interface Flask (état actuel) avec l'interface PySide6 (référence),
pour identifier ce qui est récupérable côté serveur avec un minimum de JavaScript.

## 1. Affichage des vidéos

### État actuel Flask
- [x] Vignettes 160×90 avec badge durée en overlay
- [x] Infos par vidéo : extension, taille, résolution, fps, codecs, date, état watched/introuvable
- [x] Stats de la page (taille totale, durée totale)
- [x] Affichage clair de l'état found (badge « introuvable ») et opacity réduite

### PySide6 (mode liste)
- Vignettes 180×100 avec infos détaillées (codecs, bitrate, fps, dates, langues…)
- Stats globales : « N vidéos | X Mo | HH:MM:SS »
- État found/readable clairement visible

### Reste à faire
- (rien pour l'instant)

## 2. Pagination

### État actuel Flask
- [x] Boutons first/prev/next/last (`<<` `<` `>` `>>`)
- [x] Saut à une page via `<input type="number">`
- [x] Choix page_size (10/20/50/100) via query param

### PySide6
- `<<` `<` `Page N/M` `>` `>>` (first/prev/jump/next/last)
- Choix page_size (10, 20, 50, 100)
- Dialogue « aller à la page N »

### Reste à faire
- (rien pour l'instant)

## 3. Tri

### État actuel Flask
- 8 options fixes dans un dropdown (date, titre, taille, durée × asc/desc)

### PySide6
- Tri multi-champs (ex : date puis titre)
- Tous les champs disponibles comme critère
- Direction par champ (ascendant/descendant)

### À récupérer
- [ ] Exposer plus de champs de tri
- [ ] Tri multi-champs (formulaire à N lignes : champ + direction)

## 4. Recherche

### État actuel Flask
- [x] AND/OR/Exact/ID
- [x] Bouton « effacer » visible (style bouton rouge)

### Reste à faire
- (rien pour l'instant)

## 5. Grouping

### État actuel Flask
- [x] Grouping avec navigation (first/prev/next/last + dropdown)
- [x] Affichage du nom/valeur du groupe courant + nombre de vidéos

### PySide6
- Statistiques par groupe (nombre de vidéos, taille totale)
- Bouton « confirmer tous les déplacements uniques » (pour move_id)

### Reste à faire
- (rien de bloquant)

## 6. Détail vidéo

### État actuel Flask
- ID, filename, durée, bitrate, résolution, codecs vidéo/audio, FPS, date
- Vignette 64×64
- Actions : play, rename, trash, delete, toggle watched, édition propriétés

### PySide6 (champs supplémentaires)
- Container (format conteneur)
- Taille fichier lisible (Mo/Go)
- Sample rate, channels, audio kbps
- Date d'entrée (entry date), date de dernier visionnage (opened date)
- Langues audio / sous-titres
- IDs de similarité
- État : found, readable, has_thumbnail

### État actuel Flask
- [x] Vignette 320×180 avec badge durée
- [x] Tous les champs : container, taille lisible, sample rate, channels, audio kbps, bits,
  date d'entrée, dernier visionnage, langues audio, sous-titres, similarité, état (found, readable, has_thumbnail)
- [x] Ouvrir le dossier contenant (route `/video/<id>/open-folder`)

### Reste à faire
- (rien pour l'instant)

## 7. Actions vidéo manquantes

| Action PySide6 | Faisable sans JS | Méthode | État |
|---|---|---|---|
| Ouvrir le dossier contenant | Oui | `locate_file()` | **fait** |
| Copier titre/chemin | Non (JS minimal) | `navigator.clipboard` | **fait** |
| Déplacer fichier | Oui | Formulaire texte pour le dossier cible | à faire |
| Vidéo aléatoire | Oui | Route `/videos/random` | **fait** |
| Générer playlist | Oui | Route `/videos/playlist` (XSPF) | **fait** |

## 8. Sélection multiple et opérations batch

### État actuel Flask
- Aucune sélection multiple
- Aucune opération batch

### PySide6
- Checkboxes individuelles sur chaque vidéo
- « Tout sélectionner (page) » / « Tout sélectionner (vue) »
- « Afficher uniquement la sélection »
- Édition batch des propriétés (ajouter/supprimer/remplacer des valeurs)
- Suppression batch (database, corbeille, permanent)

### À récupérer
- [x] Checkboxes HTML dans le formulaire vidéo
- [x] Tout cocher/décocher (JS minimal)
- [ ] Suppression batch (ignoré pour le moment)
- [ ] Édition batch des propriétés (formulaire dédié après sélection)

## 9. Propriétés — fonctionnalités manquantes

### État actuel Flask
- Create, rename, delete

### PySide6 (en plus)
- Gérer les valeurs d'une propriété (renommer, supprimer des valeurs)
- Convertir single ↔ multiple
- Déplacer des valeurs d'une propriété à une autre
- Remplir avec les termes des noms de fichiers

### À récupérer
- [x] Gérer les valeurs (renommer/supprimer) — formulaire POST
- [x] Convertir single ↔ multiple — bouton POST
- [ ] Déplacer des valeurs entre propriétés — formulaire POST
- [ ] Remplir avec termes — formulaire POST

## 10. Base de données — manques

### À récupérer
- [x] Renommer une base de données — formulaire POST
- [x] Trouver les vidéos similaires — opération longue (même pattern que update)
- [x] Trouver les vidéos ré-encodées — opération longue

## 11. Classifier path (navigation hiérarchique)

### PySide6
- Pour les propriétés multi-valeurs : navigation en profondeur
- Breadcrumb du chemin parcouru
- Chaque clic ajoute un filtre de valeur
- Actions : retour, inverser l'ordre, concaténer en propriété string

### À récupérer
- [ ] Navigation type breadcrumb en query params (priorité basse)

---

## Résumé par priorité

### Fait
1. ~~Vue liste améliorée (vignettes 160×90, badge durée, infos enrichies)~~
2. ~~Choix page_size + first/last page + saut à page~~
3. ~~Stats de la page (taille totale, durée totale)~~
4. ~~Recherche : bouton effacer visible~~
5. ~~Grouping : valeur du groupe courant affichée~~
6. ~~Détail vidéo enrichi (tous les champs, vignette 320×180, ouvrir dossier)~~
7. ~~Vidéo aléatoire (route `/videos/random`)~~
8. ~~Thumbnails inline (base64 data URI, 1 requête SQL au lieu de N requêtes HTTP)~~

### Prochaines étapes (priorité moyenne)
9. ~~Sélection multiple~~ (fait) — suppression batch ignorée pour le moment
10. Édition batch des propriétés
11. ~~Gestion des valeurs de propriété (renommer/supprimer)~~ (fait)
12. ~~Recherche de vidéos similaires + ré-encodées (opérations longues)~~ (fait)
13. ~~Renommer une base de données~~ (fait)
14. ~~Convertir propriété single ↔ multiple~~ (fait)

### Priorité basse (fonctionnalités avancées)
15. Tri multi-champs
16. Classifier path (navigation hiérarchique)
17. Déplacer des valeurs entre propriétés
18. Remplir avec termes des noms de fichiers
19. ~~Générer playlist~~ (fait)
20. ~~Copier titre/chemin (JS minimal)~~ (fait)
21. Déplacer fichier
