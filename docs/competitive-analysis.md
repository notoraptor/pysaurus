# Analyse concurrentielle : Pysaurus vs alternatives

## 1. Résumé des fonctionnalités de Pysaurus

| Domaine | Fonctionnalités |
|---|---|
| **Métadonnées vidéo** | 28+ champs extraits automatiquement : codecs (vidéo/audio), résolution, frame rate, bit depth, durée, bit rate, langues audio/sous-titres, titre, taille fichier, timestamps. Colonnes virtuelles calculées (jour, année, durée en secondes, etc.) |
| **Propriétés custom** | 4 types (bool, int, float, str), valeurs multiples, énumérations avec défaut, renommage, modifieurs de chaînes, déplacement de valeurs entre propriétés |
| **Recherche** | FTS5 (full-text search) avec 4 modes : AND, OR, exact, par ID. Recherche sur noms de fichiers, titres et propriétés string. Splitting camelCase automatique |
| **Filtrage** | Par tous les champs vidéo : codec, résolution, durée, bit rate, statut (lu/non-lu, trouvé/manquant, avec/sans miniature, écarté) |
| **Groupement** | Par n'importe quel champ ou propriété custom. Tri des groupes par valeur, nombre ou longueur. Navigation hiérarchique (classifier) |
| **Tri** | Multi-champs, ascendant/descendant par champ |
| **Similarité** | Détection par similarité d'image (NumPy, cosinus, seuil 88%) + détection de réencodages (durée, titre). Traitement parallèle |
| **Miniatures** | Extraction automatique du frame central, stockage en base (BLOB), génération parallèle |
| **Lecture** | Intégration VLC, ouverture avec lecteur système |
| **Opérations fichiers** | Renommer, déplacer, supprimer, mettre à la corbeille, ouvrir le dossier, correction mtime FAT/exFAT |
| **Multi-base** | Collections indépendantes avec métadonnées, propriétés et similarités séparées |
| **Export** | Playlist XSPF, copie chemins dans le presse-papier |
| **GUI** | PySide6 (native Qt) |
| **CLI** | Console interactive (Python Fire) : 15+ commandes (update, search, groupby, stats, repair FTS, fix_mtime, etc.) |
| **Architecture** | SQLite (via skullite), FTS5, colonnes virtuelles, traitement parallèle, profilage intégré |
| **Licence** | Non publiée (projet personnel) |
| **Prix** | Gratuit |

---

## 2. Les alternatives

### 2.1 Plex

| | |
|---|---|
| **Type** | Serveur multimédia |
| **Open source** | Non |
| **Plateformes** | Windows, macOS, Linux, NAS, Docker. Clients : web, mobile, TV, consoles |
| **Métadonnées** | Récupération automatique depuis bases en ligne (TMDb, etc.) : affiches, synopsis, casting, genres, notes, studios |
| **Recherche/filtrage** | Par genre, année, note, résolution, non-vu. Smart Collections |
| **Propriétés custom** | Limitées : labels/tags textuels uniquement. Pas de types personnalisés |
| **Similarité** | Non (script tiers `plex_dupefinder`) |
| **Lecture** | Oui, tous clients. Transcodage matériel (Plex Pass) |
| **Multi-bibliothèque** | Oui |
| **Extensibilité** | API Python (PlexAPI), webhooks (Plex Pass), pas de vrai système de plugins |
| **Forces** | UI la plus soignée, matching métadonnées ~98%, support massif d'appareils, streaming distant |
| **Faiblesses** | Fermé, free tier de plus en plus restreint, pas de propriétés custom typées, pas de détection de doublons |
| **Prix** | Freemium. Plex Pass : 7$/mois, 70$/an, 250$ à vie |

### 2.2 Jellyfin

| | |
|---|---|
| **Type** | Serveur multimédia open source |
| **Open source** | Oui (GPL-2.0) |
| **Plateformes** | Windows, macOS, Linux, Docker. Clients : web, Android, iOS, Roku, Fire TV, Kodi |
| **Métadonnées** | TMDb, OMDB, fichiers NFO. Affiches, synopsis, casting, genres, notes |
| **Recherche/filtrage** | Par genre, année, note, tags, statut lu/non-lu |
| **Propriétés custom** | Tags via plugins. Pas de types arbitraires |
| **Similarité** | Non |
| **Lecture** | Oui. Transcodage matériel gratuit (QSV, VA-API, NVENC, etc.) |
| **Multi-bibliothèque** | Oui |
| **Extensibilité** | Plugins C#, API REST, intégration Kodi |
| **Forces** | 100% gratuit sans restriction, pas de télémétrie, transcodage HW gratuit, communauté active |
| **Faiblesses** | UI moins soignée que Plex, matching ~95%, moins de clients natifs |
| **Prix** | Gratuit |

### 2.3 Emby

| | |
|---|---|
| **Type** | Serveur multimédia |
| **Open source** | Non (était open source, fermé depuis 2018 — Jellyfin est le fork libre) |
| **Plateformes** | Windows, macOS, Linux, Docker, NAS. Clients : web, mobile, TV, consoles |
| **Métadonnées** | Récupération automatique, fichiers NFO, tags textuels |
| **Recherche/filtrage** | Par tags, genre, année, note. Smart playlists |
| **Propriétés custom** | Tags textuels. Pas de types arbitraires |
| **Similarité** | Non (outil tiers `emby-dupe-finder`) |
| **Lecture** | Oui. Transcodage matériel (Premiere) |
| **Multi-bibliothèque** | Oui, avec contrôle d'accès par utilisateur |
| **Extensibilité** | Plugins C#/.NET, API REST |
| **Forces** | Bonne qualité métadonnées, contrôle parental solide, prix lifetime raisonnable |
| **Faiblesses** | Fermé, transcodage HW payant, communauté plus petite |
| **Prix** | Freemium. Premiere : 5$/mois, 54$/an, 119$ à vie |

### 2.4 Stash

| | |
|---|---|
| **Type** | Organisateur de collection vidéo (auto-hébergé) |
| **Open source** | Oui (AGPL-3.0) |
| **Plateformes** | Windows, macOS, Linux, Docker (binaire unique Go + React) |
| **Métadonnées** | Performers, studios, tags, films, dates, notes. Scrapers configurables |
| **Recherche/filtrage** | Filtres avancés include/exclude par performer, studio, tag. Filtres sauvegardés |
| **Propriétés custom** | Système de tags complet, hiérarchique, édition en masse |
| **Similarité** | Oui : hash perceptuel (phash) intégré. Plugin communautaire pour doublons avancés |
| **Lecture** | Oui (streaming dans le navigateur) |
| **Multi-bibliothèque** | Non (une seule, organisée par tags/studios/performers) |
| **Extensibilité** | API GraphQL, plugins JavaScript/Python, scrapers communautaires |
| **Forces** | Tagging riche, meilleure détection de doublons (phash), API GraphQL puissante, communauté active |
| **Faiblesses** | Orienté contenu adulte (même si techniquement généraliste), mono-utilisateur, pas de transcodage |
| **Prix** | Gratuit |

### 2.5 tinyMediaManager

| | |
|---|---|
| **Type** | Gestionnaire de métadonnées (outil compagnon pour Kodi/Plex/Jellyfin) |
| **Open source** | Oui (GPL) |
| **Plateformes** | Windows, macOS, Linux (Java) |
| **Métadonnées** | TMDb, IMDb, TVmaze. Génération NFO, téléchargement d'artwork, renommage par lots |
| **Recherche/filtrage** | Recherche par ID TMDb/IMDb, filtrage par métadonnées |
| **Propriétés custom** | Tags et genres (écrits en NFO). Pas de types arbitraires |
| **Similarité** | Basique (doublons par sets TMDb) |
| **Lecture** | Non |
| **Extensibilité** | Plugins scrapers, CLI |
| **Forces** | Meilleur générateur NFO, traitement par lots, multi-plateforme |
| **Faiblesses** | UI datée (Java Swing), pas de lecture, limité à la gestion de métadonnées |
| **Prix** | Freemium. PRO : ~12$/an |

### 2.6 digiKam

| | |
|---|---|
| **Type** | Gestionnaire de photos/vidéos (DAM) |
| **Open source** | Oui (GPL-2.0+, projet KDE) |
| **Plateformes** | Windows, macOS, Linux |
| **Métadonnées** | Extraction via FFmpeg. Tags, notes, géolocalisation, reconnaissance faciale IA |
| **Recherche/filtrage** | Par tags, albums, dates, notes, métadonnées. Recherche par similarité d'image (Haar) |
| **Propriétés custom** | Tags hiérarchiques import/export. Notes et labels. Pas de types arbitraires |
| **Similarité** | Oui pour les images (cascades de Haar, % configurable). Non pour les vidéos |
| **Lecture** | Oui (basique, via FFmpeg) |
| **Extensibilité** | Système DPlugins, export vers services web |
| **Forces** | Extrêmement puissant pour la photo, reconnaissance faciale, similarité d'image, gère 100k+ éléments |
| **Faiblesses** | Vidéo = citoyen de seconde classe, pas de similarité vidéo, UI complexe |
| **Prix** | Gratuit |

### 2.7 Kodi

| | |
|---|---|
| **Type** | Centre multimédia / lecteur |
| **Open source** | Oui (GPL-2.0+) |
| **Plateformes** | Windows, macOS, Linux, Android, iOS, tvOS, Raspberry Pi |
| **Métadonnées** | Scraping TMDb/TVDb/IMDb via add-ons. Fichiers NFO |
| **Recherche/filtrage** | Filtrage avancé par genre, année, note, tag, acteur, réalisateur |
| **Propriétés custom** | Tags textuels. Pas de types arbitraires |
| **Similarité** | Non |
| **Lecture** | La meilleure lecture locale (supporte quasi tous les formats/codecs) |
| **Extensibilité** | Énorme écosystème d'add-ons (Python, C++), API JSON-RPC, skins personnalisables |
| **Forces** | Meilleure lecture locale, extrêmement personnalisable, communauté massive |
| **Faiblesses** | Pas de transcodage ni streaming distant, courbe d'apprentissage, pas de UI web |
| **Prix** | Gratuit |

### 2.8 MediaElch

| | |
|---|---|
| **Type** | Gestionnaire de métadonnées (outil compagnon pour Kodi/Jellyfin) |
| **Open source** | Oui (LGPL-3.0) |
| **Plateformes** | Windows, macOS, Linux (Qt/C++) |
| **Métadonnées** | TMDb, TheTVDB, TVMaze, IMDb, Fanart.tv. Génération NFO et artwork |
| **Propriétés custom** | Tags et genres. Pas de types arbitraires |
| **Similarité** | Basique (par ID IMDb ou titre) |
| **Lecture** | Non |
| **Forces** | Excellent pour NFO et artwork, gratuit, bon traitement par lots |
| **Faiblesses** | UI datée, pas de lecture, pas de système de plugins, mises à jour peu fréquentes |
| **Prix** | Gratuit |

### 2.9 FileBot

| | |
|---|---|
| **Type** | Outil de renommage/organisation de fichiers |
| **Open source** | Non (code source visible mais licence non-libre) |
| **Plateformes** | Windows, macOS, Linux (Java) |
| **Métadonnées** | TMDb, TheTVDB, AniDB. Renommage par lots avec patterns Groovy |
| **Propriétés custom** | Via scripting Groovy |
| **Similarité** | Non |
| **Lecture** | Non |
| **Forces** | Meilleur outil de renommage automatisé, scripting Groovy puissant, excellent support anime |
| **Faiblesses** | Payant, pas de gestion de bibliothèque, pas de lecture |
| **Prix** | 6$/an ou 48$ à vie |

### 2.10 Autres outils notables

| Outil | Type | Remarque |
|---|---|---|
| **Infuse** | Lecteur vidéo (Apple) | Meilleur lecteur Apple, UI magnifique, pas de propriétés custom. 10$/an ou 75$ à vie |
| **Universal Media Server** | Serveur DLNA/UPnP | Streaming vers TV/consoles, pas de gestion de collection. Gratuit |
| **Fast Video Cataloger** | Catalogueur vidéo (Windows) | Propriétés custom, tagging par scène, recherche dans transcripts. ~200$ |
| **Synology Video Station** | Gestionnaire NAS | **Abandonné** (DSM 7.2.2). Remplacé par Plex/Jellyfin/Emby |

---

## 3. Matrice comparative

### 3.1 Fonctionnalités clés

| Fonctionnalité | Pysaurus | Plex | Jellyfin | Emby | Stash | tinyMM | digiKam | Kodi |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Propriétés custom typées** | **bool/int/float/str** | Non | Non | Non | Tags seuls | Non | Non | Non |
| **Valeurs multiples par propriété** | Oui | Non | Non | Non | Oui (tags) | Non | Oui (tags) | Non |
| **Énumérations** | Oui | Non | Non | Non | Non | Non | Non | Non |
| **FTS5 full-text search** | Oui (4 modes) | Basique | Basique | Basique | Filtres | Basique | Avancé | Avancé |
| **Groupement dynamique** | **Par tout champ/propriété** | Collections | Collections | Collections | Par performer/studio | Non | Par album/tag | Par genre/année |
| **Similarité visuelle** | Oui (images) | Non | Non | Non | Oui (phash) | Non | Oui (images) | Non |
| **Détection réencodages** | Oui | Non | Non | Non | Non | Non | Non | Non |
| **Miniatures auto** | Oui | Oui | Oui | Oui | Oui | Non | Oui | Oui |
| **Lecture vidéo** | VLC externe | Intégrée | Intégrée | Intégrée | Streaming | Non | Basique | Meilleure |
| **Transcodage** | Non | Oui (HW) | Oui (HW) | Oui (HW) | Non | Non | Non | Non |
| **Streaming distant** | Non | Oui | Oui | Oui | Non | Non | Non | Non |
| **Multi-utilisateur** | Non | Oui | Oui | Oui | Non | Non | Non | Oui |
| **Multi-base** | Oui | Oui | Oui | Oui | Non | Oui | Oui | Oui |
| **CLI** | Oui (15+ cmd) | Non | Non | Non | Non | Oui | Non | Non |
| **API programmatique** | Non | API REST | API REST | API REST | GraphQL | Non | Non | JSON-RPC |
| **Métadonnées en ligne** | Non | Oui (TMDb) | Oui (TMDb) | Oui (TMDb) | Scrapers | Oui (TMDb) | Non | Oui (TMDb) |
| **Plugins** | Non | Limité | Oui (C#) | Oui (C#) | Oui (JS/Py) | Oui | Oui | Oui (massif) |
| **Support appareils** | Desktop seul | Énorme | Large | Large | Web seul | Desktop | Desktop | Large |

### 3.2 Informations générales

| | Pysaurus | Plex | Jellyfin | Emby | Stash | tinyMM | digiKam | Kodi |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Open source** | Oui* | Non | Oui | Non | Oui | Oui | Oui | Oui |
| **Prix** | Gratuit | Freemium | Gratuit | Freemium | Gratuit | Freemium | Gratuit | Gratuit |
| **Langage** | Python | C++/Go | C# | C# | Go | Java | C++/Qt | C++ |
| **Maturité** | WIP | ~2012 | ~2018 | ~2014 | ~2019 | ~2012 | ~2001 | ~2002 |

\* Non publié à ce jour.

---

## 4. Analyse

### 4.1 Ce que Pysaurus fait mieux que tous les autres

1. **Propriétés custom typées (bool/int/float/str)** — Aucun concurrent ne propose de propriétés utilisateur avec des types distincts. Tous se limitent à des tags textuels. C'est la fonctionnalité la plus différenciante de Pysaurus. Pouvoir dire « cette vidéo a une note de qualité de 8 (int), est vérifiée (bool), et a un commentaire (str) » n'est possible nulle part ailleurs (sauf Fast Video Cataloger, propriétaire à ~200$).

2. **Énumérations sur propriétés** — Définir une liste finie de valeurs autorisées avec un défaut. Aucun concurrent ne le propose.

3. **Groupement dynamique par n'importe quel champ** — Pysaurus peut grouper par codec, résolution, année, durée, ou n'importe quelle propriété custom. Les concurrents offrent des groupements figés (genre, année, collection).

4. **Détection de réencodages** — Fonctionnalité unique : identifier qu'une vidéo est une version réencodée d'une autre (par durée et titre). Aucun concurrent ne fait ça.

5. **Recherche FTS5 multi-mode** — 4 modes de recherche (AND, OR, exact, ID) avec splitting camelCase sur un index full-text. Plus flexible que la plupart des concurrents.

6. **CLI interactive** — Console avec 15+ commandes pour l'administration et le debug. Seul tinyMediaManager a un CLI comparable.

### 4.2 Ce que les concurrents font mieux

1. **Streaming et transcodage** — Plex, Jellyfin, Emby transcodent et streament vers n'importe quel appareil. Pysaurus ne fait que lancer VLC localement.

2. **Métadonnées en ligne** — Tous les serveurs multimédia récupèrent automatiquement les métadonnées (affiches, synopsis, casting) depuis TMDb/IMDb. Pysaurus n'extrait que les métadonnées techniques du fichier.

3. **Multi-utilisateur** — Plex, Jellyfin, Emby gèrent plusieurs utilisateurs avec profils et contrôle parental. Pysaurus est mono-utilisateur.

4. **Écosystème de plugins** — Kodi a des milliers d'add-ons, Jellyfin/Emby ont des plugins C#, Stash a des scrapers communautaires. Pysaurus n'a pas de système de plugins.

5. **Support d'appareils** — Les serveurs multimédia supportent TV, mobile, consoles. Pysaurus est limité au desktop.

6. **Lecture intégrée** — Kodi a la meilleure lecture locale, Plex/Jellyfin/Emby ont des lecteurs intégrés partout. Pysaurus dépend d'un lecteur externe.

7. **Communauté** — Tous les concurrents open source ont des communautés actives. Pysaurus est un projet solo.

8. **Détection de doublons** — Stash utilise le hash perceptuel (phash), plus robuste que la similarité cosinus de Pysaurus. digiKam utilise les cascades de Haar.

### 4.3 Concurrent le plus proche

**Stash** est le plus proche de Pysaurus en concept : organisateur de vidéos auto-hébergé avec tags riches, détection de doublons, et API. Mais Stash n'a pas de propriétés typées, pas de groupement dynamique, pas de CLI, et est orienté contenu adulte.

**Fast Video Cataloger** (Windows, ~200$, propriétaire) est l'autre concurrent proche avec ses propriétés custom et le tagging par scène, mais il est payant et fermé.

---

## 5. Conclusion

### Ce que vaut Pysaurus aujourd'hui

Pysaurus occupe une **niche réelle mais étroite** : un gestionnaire de vidéos locales avec des propriétés custom typées et un groupement dynamique puissant. C'est un outil d'organisation fine, pas un serveur multimédia.

**Il ne rivalise pas** avec Plex/Jellyfin/Emby sur le terrain du streaming, du transcodage, du multi-appareil ou du multi-utilisateur — et il ne devrait pas essayer.

**Il se distingue clairement** par :
- Les propriétés typées (unique sur le marché open source)
- Le groupement dynamique (le plus flexible)
- La détection de réencodages (unique)
- La CLI interactive

**Ses faiblesses principales** pour une adoption plus large :
- Pas de récupération de métadonnées en ligne (pas de matching TMDb/IMDb)
- Pas de système de plugins
- Pas d'API programmatique (`import pysaurus`)
- Pas publié / pas de communauté
- Documentation utilisateur absente

En résumé : Pysaurus est un **outil d'organisation de vidéos puissant et unique dans sa catégorie**, mais qui reste un outil personnel tant qu'il n'offre pas une API programmatique et une publication ouverte. Sa force — les propriétés typées et le groupement dynamique — n'a pas d'équivalent open source.
