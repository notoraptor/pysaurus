# Analyse concurrentielle et positionnement — Pysaurus

**État : 23 juillet 2026.** Première passe le 22 mars 2026, refondue ici avec une recherche
à jour (item « positionnement concurrentiel » de `docs/review.md`). Document unique : les
faits périmés ont été corrigés plutôt qu'annotés, et deux affirmations de mars ont été
retirées — voir § 4.1 (propriétés custom) et § 4.2 (détection de doublons).

Ce document absorbe aussi `docs/strategic-direction.md` (mars 2026, supprimé), dont la thèse
— un pivot partiel vers la curation de datasets vidéo pour le ML — est réévaluée en § 6.1.

## 1. Ce que fait Pysaurus

| Domaine | Fonctionnalités |
|---|---|
| **Métadonnées vidéo** | 28+ champs extraits automatiquement : codecs (vidéo/audio), résolution, frame rate, bit depth, durée, bit rate, langues audio/sous-titres, titre, taille fichier, timestamps. Colonnes virtuelles calculées (jour, année, durée en secondes, etc.) |
| **Propriétés custom** | 4 types (bool, int, float, str), valeurs multiples, énumérations avec défaut, renommage, modifieurs de chaînes, déplacement de valeurs entre propriétés |
| **Recherche** | FTS5 (full-text search) avec 4 modes : AND, OR, exact, par ID. Recherche sur noms de fichiers, titres et propriétés string. Splitting camelCase automatique |
| **Filtrage** | Par tous les champs vidéo : codec, résolution, durée, bit rate, statut (lu/non-lu, trouvé/manquant, avec/sans miniature, écarté) |
| **Langage d'expressions** | `searchexp` (package externe) : prédicats composables sur champs et propriétés — `width > 1080 and "eng" in audio_languages`, compilé en SQL |
| **Groupement** | Par n'importe quel champ ou propriété custom. Tri des groupes par valeur, nombre ou longueur. Navigation hiérarchique (classifier) |
| **Tri** | Multi-champs, ascendant/descendant par champ |
| **Similarité** | Détection par similarité d'image (NumPy, cosinus, seuil 88%) + détection de réencodages (durée, titre). Traitement parallèle |
| **Miniatures** | Extraction automatique du frame central, stockage en base (BLOB), génération parallèle |
| **Lecture** | Intégration VLC, ouverture avec lecteur système |
| **Opérations fichiers** | Renommer, déplacer, supprimer, mettre à la corbeille, ouvrir le dossier, correction mtime FAT/exFAT |
| **Multi-base** | Collections indépendantes avec métadonnées, propriétés et similarités séparées |
| **Export** | Playlist XSPF, copie chemins dans le presse-papier |
| **GUI** | PySide6 (native Qt) : interface `kyuti`, vue liste. Frontends legacy (web, pywebview, vue grille) archivés dans `wip/` |
| **i18n** | Anglais / français (catalogue chargé au démarrage, changement de langue à chaud) |
| **CLI** | Console interactive (Python Fire) : 22 commandes (update, search, groupby, stats, repair FTS, fix_mtime, etc.) |
| **Architecture** | SQLite (via skullite), FTS5, colonnes virtuelles, traitement parallèle, profilage intégré |
| **Licence** | Non publiée (projet personnel). `LICENSE` est un modèle MIT non édité (« Copyright (c) 2018 The Python Packaging Authority ») |
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
| **Prix** | Freemium. Plex Pass : 6,99 $/mois, 69,99 $/an, **749,99 $ à vie au 1ᵉʳ juillet 2026** (119,99 $ jusqu'en 2025, puis 249,99 $). Remote Watch Pass : 2,99 $/mois ou 29,99 $/an au 1ᵉʳ juin 2026 |

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
| **Forces** | 100% gratuit sans restriction, pas de télémétrie, transcodage HW gratuit, communauté active. 10.11 a unifié la base (refonte EF Core) ; nouvelle UI web par défaut dans la branche 10.12 |
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
| **Propriétés custom** | Système de tags complet, hiérarchique, édition en masse. **Champs custom** depuis la v0.31.0 (30 mars 2026) sur scènes, galeries, images, groupes, studios et tags : non typés, créés par entité, sans schéma global |
| **Similarité** | Oui : hash perceptuel (phash) intégré. Plugin communautaire pour doublons avancés |
| **Lecture** | Oui (streaming dans le navigateur) |
| **Multi-bibliothèque** | Non (une seule, organisée par tags/studios/performers) |
| **Extensibilité** | API GraphQL, plugins JavaScript/Python, scrapers communautaires |
| **Forces** | Tagging riche, meilleure détection de doublons (phash), API GraphQL puissante, communauté active |
| **Faiblesses** | Orienté contenu adulte (même si techniquement généraliste), mono-utilisateur, pas de transcodage |
| **Prix** | Gratuit |

### 2.5 Hydrus Network

| | |
|---|---|
| **Type** | Gestionnaire de collection de fichiers médias, style « booru de bureau » |
| **Open source** | Oui |
| **Plateformes** | Windows, macOS, Linux (Python + Qt, comme Pysaurus). Releases hebdomadaires |
| **Métadonnées** | Tags à namespaces (`creator:`, `series:`…), **ratings typés** (like/dislike, numériques à plage configurable, compteurs +/-), notes, URLs connues, timestamps. Tout est attaché au hash du fichier |
| **Recherche/filtrage** | Système de recherche par tags très riche (wildcards, OR, namespaces) + prédicats sur métadonnées de fichier |
| **Propriétés custom** | Pas de propriétés arbitraires typées, mais des services de ratings typés créés par l'utilisateur, plus les namespaces de tags |
| **Similarité** | Oui : hash perceptuel + distance de Hamming, avec **règles d'auto-résolution** (semi-auto : paires mises en file pour validation ; auto : action immédiate). Dédup vidéo via outil externe (`hydrus-video-deduplicator`, qui passe par l'API) |
| **Lecture** | Intégrée (mpv embarqué) |
| **Multi-bibliothèque** | Non (une base par instance ; plusieurs « local file domains » au sein d'une même base) |
| **Extensibilité** | Client API HTTP (opt-in), téléchargeurs/parseurs communautaires |
| **Forces** | Même pile technique que Pysaurus (Python/Qt/SQLite), local-first sans télémétrie, tient de très grosses collections, dédup mature, rythme hebdomadaire, communauté établie |
| **Faiblesses** | Courbe d'apprentissage abrupte, UI austère, pensé images d'abord (vidéo supportée mais dédup vidéo externalisée), pas de groupement dynamique, pas d'exploitation des métadonnées techniques vidéo (codec, résolution, bitrate) |
| **Prix** | Gratuit |

### 2.6 tinyMediaManager

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

### 2.7 digiKam

| | |
|---|---|
| **Type** | Gestionnaire de photos/vidéos (DAM) |
| **Open source** | Oui (GPL-2.0+, projet KDE) |
| **Plateformes** | Windows, macOS, Linux |
| **Métadonnées** | Extraction via FFmpeg. Tags, notes, géolocalisation, reconnaissance faciale IA |
| **Recherche/filtrage** | Par tags, albums, dates, notes, métadonnées. Recherche par similarité d'image (Haar) |
| **Propriétés custom** | Tags hiérarchiques import/export. Notes et labels. Pas de types arbitraires |
| **Similarité** | Oui pour les images (cascades de Haar, % configurable). Non pour les vidéos |
| **Lecture** | Oui (basique, via FFmpeg). 9.1 a amélioré la stabilité de lecture et la sélection de sortie audio |
| **Extensibilité** | Système DPlugins, export vers services web |
| **Forces** | Extrêmement puissant pour la photo, reconnaissance faciale, similarité d'image, gère 100k+ éléments |
| **Faiblesses** | Vidéo = citoyen de seconde classe, pas de similarité vidéo, UI complexe |
| **Prix** | Gratuit |

### 2.8 Kodi

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

### 2.9 MediaElch

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

### 2.10 FileBot

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

### 2.11 Autres outils notables

| Outil | Type | Remarque |
|---|---|---|
| **Infuse** | Lecteur vidéo (Apple) | Meilleur lecteur Apple, UI magnifique, pas de propriétés custom. 10$/an ou 75$ à vie |
| **Universal Media Server** | Serveur DLNA/UPnP | Streaming vers TV/consoles, pas de gestion de collection. Gratuit |
| **Fast Video Cataloger** | Catalogueur vidéo (Windows) | Propriétés custom, tagging par scène, recherche dans transcripts. ~200$ |
| **Synology Video Station** | Gestionnaire NAS | **Abandonné** (DSM 7.2.2). Remplacé par Plex/Jellyfin/Emby |
| **Immich** | Bibliothèque photo/vidéo auto-hébergée (AGPL) | v3.0.0 le 1ᵉʳ juillet 2026. **Recherche sémantique CLIP** en langage naturel sur photos *et* vidéos. Croissance très rapide. Gratuit |
| **Eagle** | DAM local (Win/macOS) | v4 (avril 2026) : AI Search, auto-tagging, recherche visuelle, 81+ formats dont vidéo. 29,95 $ une fois |
| **TagSpaces** | Tagging de fichiers locaux | Tags dans le nom de fichier ou en sidecar, sans base. Gratuit / freemium |
| **Video Hub App** | Navigateur de vidéos locales (Electron) | Vignettes + recherche rapide, pas de propriétés. 5 $ |
| **Czkawka / VideoDuplicateFinder** | Dédup pure | Similarité perceptuelle d'images et de vidéos. Czkawka 11.0.1 (février 2026). Gratuits, open source |

---

## 3. Matrice comparative

### 3.1 Fonctionnalités clés

| Fonctionnalité | Pysaurus | Plex | Jellyfin | Emby | Stash | Hydrus | tinyMM | digiKam | Kodi |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Propriétés custom typées** | **bool/int/float/str** | Non | Non | Non | Champs libres non typés | Ratings typés | Non | Non | Non |
| **Définies une fois pour la base** | **Oui** | — | — | — | Non (par entité) | Oui (services) | — | — | — |
| **Valeurs multiples par propriété** | Oui | Non | Non | Non | Oui (tags) | Oui (tags) | Non | Oui (tags) | Non |
| **Énumérations** | Oui | Non | Non | Non | Non | Non | Non | Non | Non |
| **FTS5 full-text search** | Oui (4 modes) | Basique | Basique | Basique | Filtres | Par tags | Basique | Avancé | Avancé |
| **Langage d'expressions** | **Oui (searchexp)** | Non | Non | Non | Non | Syntaxe de tags | Non | Non | Non |
| **Groupement dynamique** | **Par tout champ/propriété** | Collections | Collections | Collections | Par performer/studio | Non | Non | Par album/tag | Par genre/année |
| **Similarité visuelle** | Oui (cosinus) | Non | Non | Non | Oui (phash) | **Oui (phash + auto-résolution)** | Non | Oui (images) | Non |
| **Détection réencodages** | Oui (durée+titre) | Non | Non | Non | Via phash | Via phash | Non | Non | Non |
| **Miniatures auto** | Oui | Oui | Oui | Oui | Oui | Oui | Non | Oui | Oui |
| **Lecture vidéo** | VLC externe | Intégrée | Intégrée | Intégrée | Streaming | Intégrée (mpv) | Non | Basique | Meilleure |
| **Transcodage** | Non | Oui (HW) | Oui (HW) | Oui (HW) | Non | Non | Non | Non | Non |
| **Streaming distant** | Non | Oui (payant) | Oui | Oui | Non | Non | Non | Non | Non |
| **Multi-utilisateur** | Non | Oui | Oui | Oui | Non | Non | Non | Non | Oui |
| **Multi-base** | Oui | Oui | Oui | Oui | Non | Non | Oui | Oui | Oui |
| **CLI** | Oui (22 cmd) | Non | Non | Non | Non | Non | Oui | Non | Non |
| **API programmatique** | Non | API REST | API REST | API REST | GraphQL | Client API | Non | Non | JSON-RPC |
| **Métadonnées en ligne** | Non | Oui (TMDb) | Oui (TMDb) | Oui (TMDb) | Scrapers | Oui (boorus) | Oui (TMDb) | Non | Oui (TMDb) |
| **Recherche sémantique (IA)** | Non | Non | Non | Non | Non | Non | Non | Non | Non |
| **Plugins** | Non | Limité | Oui (C#) | Oui (C#) | Oui (JS/Py) | Via API | Oui | Oui | Oui (massif) |
| **Support appareils** | Desktop seul | Énorme | Large | Large | Web seul | Desktop seul | Desktop | Desktop | Large |

Sur la ligne « Recherche sémantique (IA) », le point de comparaison n'est aucun de ces
outils mais **Immich** (CLIP, photos et vidéos) et **Eagle v4** — voir § 4.4.

### 3.2 Informations générales

| | Pysaurus | Plex | Jellyfin | Emby | Stash | Hydrus | tinyMM | digiKam | Kodi |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Open source** | Oui* | Non | Oui | Non | Oui | Oui | Oui | Oui | Oui |
| **Prix** | Gratuit | Freemium | Gratuit | Freemium | Gratuit | Gratuit | Freemium | Gratuit | Gratuit |
| **Langage** | Python/Qt | C++/Go | C# | C# | Go | **Python/Qt** | Java | C++/Qt | C++ |
| **Maturité** | WIP | ~2012 | ~2018 | ~2014 | ~2019 | ~2013 | ~2012 | ~2001 | ~2002 |
| **Version (juillet 2026)** | — | — | 10.11.11 | — | 0.31.0 | hebdomadaire | 5.2.12 | 9.1.0 | 22 bêta |

\* Non publié à ce jour.

---

## 4. Analyse

### 4.1 Ce que Pysaurus fait mieux

1. **Propriétés custom typées, déclarées au niveau de la base** — bool/int/float/str,
   multi-valuées, énumérables avec défaut, définies une fois puis disponibles sur toute la
   collection. Deux concurrents s'en approchent sans y arriver : **Stash** a des champs
   custom depuis mars 2026, mais non typés, créés à la main entité par entité, sans schéma
   global ni valeurs suggérées (c'est l'objet de la demande d'évolution
   `stashapp/stash#6795`) ; **Hydrus** a des ratings typés, mais bornés à trois formes
   (like/dislike, numérique, compteur). Pysaurus est le seul à offrir les quatre propriétés
   ensemble : déclarées, typées, multi-valuées, énumérables.

2. **Énumérations sur propriétés** — Liste finie de valeurs autorisées avec un défaut.
   Aucun concurrent ne le propose.

3. **Groupement dynamique par n'importe quel champ** — Grouper par codec, résolution,
   année, durée, ou n'importe quelle propriété custom, avec navigation hiérarchique. Les
   concurrents offrent des groupements figés (genre, année, collection) ; Hydrus n'a pas la
   notion.

4. **Langage d'expressions (`searchexp`)** — Prédicats composables sur les champs
   techniques et les propriétés, compilés en SQL. Aucun concurrent n'expose de langage de
   requête sur les métadonnées vidéo : Stash offre des filtres UI riches, Hydrus une
   syntaxe de tags — ni l'un ni l'autre ne permet
   `width > 1080 and "eng" in audio_languages`.

5. **Recherche FTS5 multi-mode** — 4 modes (AND, OR, exact, ID) avec splitting camelCase
   sur un index full-text. Plus flexible que la plupart des concurrents.

6. **CLI interactive** — Console avec 22 commandes pour l'administration et le debug. Seul
   tinyMediaManager a un CLI comparable.

### 4.2 Ce que les concurrents font mieux

1. **Détection de doublons** — Stash et Hydrus utilisent le hash perceptuel (phash), plus
   robuste que la similarité cosinus de Pysaurus ; Hydrus y ajoute des règles
   d'auto-résolution (validation par lots, ou action automatique). digiKam utilise les
   cascades de Haar, et les utilitaires gratuits dédiés (Czkawka, VideoDuplicateFinder)
   sont sur le même terrain. **La « détection de réencodages » de Pysaurus** (heuristique
   durée + titre) relève de ce besoin, et elle est plus fragile que le phash : c'est une
   faiblesse, pas un différenciateur.

2. **Streaming et transcodage** — Plex, Jellyfin, Emby transcodent et streament vers
   n'importe quel appareil. Pysaurus ne fait que lancer VLC localement.

3. **Métadonnées en ligne** — Tous les serveurs multimédia récupèrent automatiquement
   affiches, synopsis et casting depuis TMDb/IMDb. Pysaurus n'extrait que les métadonnées
   techniques du fichier.

4. **Recherche sémantique** — Immich (CLIP, photos et vidéos) et Eagle v4 cherchent en
   langage naturel sans qu'on ait rien tagué. Aucun outil du tableau § 3.1 ne le fait,
   Pysaurus non plus.

5. **Multi-utilisateur** — Plex, Jellyfin, Emby gèrent plusieurs utilisateurs avec profils
   et contrôle parental. Pysaurus est mono-utilisateur.

6. **Écosystème de plugins** — Kodi a des milliers d'add-ons, Jellyfin/Emby des plugins C#,
   Stash des scrapers communautaires. Pysaurus n'a pas de système de plugins.

7. **Support d'appareils** — Les serveurs multimédia supportent TV, mobile, consoles.
   Pysaurus est limité au desktop.

8. **Lecture intégrée** — Kodi a la meilleure lecture locale, Plex/Jellyfin/Emby ont des
   lecteurs intégrés partout, Hydrus embarque mpv. Pysaurus dépend d'un lecteur externe.

9. **Communauté** — Tous les concurrents open source ont des communautés actives. Pysaurus
   est un projet solo non publié.

### 4.3 Les concurrents les plus proches

**Hydrus Network** est le plus proche. Même pile (Python/Qt/SQLite), même philosophie
(local-first, mono-utilisateur, aucune télémétrie, collections de dizaines de milliers de
fichiers), même refus du modèle serveur multimédia. Il a en plus : la dédup perceptuelle
avec règles d'auto-résolution, une API client, des téléchargeurs communautaires, une
communauté, et un rythme de release hebdomadaire depuis ~2013. Il a en moins : le
groupement dynamique, les métadonnées techniques vidéo, et toute notion de requête sur des
champs typés — son modèle mental est le tag, pas la colonne.

**Stash** est très proche en concept (organisateur auto-hébergé, tags riches, phash, API
GraphQL) et vient d'ajouter des champs custom (§ 4.1). Il n'a ni propriétés typées ni
groupement dynamique, et son écosystème est orienté contenu adulte.

**Fast Video Cataloger** (Windows, ~200 $, propriétaire) est l'autre concurrent proche avec
ses propriétés custom et le tagging par scène, mais il est payant et fermé.

### 4.4 Dynamique du marché

**Plex se saborde.** Le Lifetime Pass passe à 749,99 $ au 1ᵉʳ juillet 2026, après un premier
bond de 119,99 $ à 249,99 $ un an plus tôt — ×6 en deux ans. Le Remote Watch Pass,
introduit en avril 2025 quand le streaming distant est devenu payant, passe de 1,99 $ à
2,99 $/mois (19,99 $ → 29,99 $/an) au 1ᵉʳ juin 2026. C'est le plus gros mouvement du
marché, et il pousse activement les utilisateurs vers l'auto-hébergé et le local.

**Jellyfin consolide et récupère.** 10.11 a unifié la base (refonte EF Core, `library.db`
fondue dans `jellyfin.db`), 10.11.11 est sorti en mai 2026, la nouvelle UI web est activée
par défaut dans la branche 10.12. Bénéficiaire direct de l'exode Plex.

**Stash converge vers Pysaurus.** Les champs custom sont arrivés le 30 mars 2026, huit
jours après la première version de ce document. Non typés aujourd'hui, mais la trajectoire
est explicite : l'issue `#6795` demande des définitions globales, des types d'affichage et
des valeurs suggérées — c'est-à-dire, à terme, ce que Pysaurus a déjà.

**L'IA arrive sur le terrain de l'organisation.** Immich v3.0.0 (1ᵉʳ juillet 2026, AGPL)
fait de la recherche sémantique CLIP en langage naturel sur photos *et* vidéos ; Eagle v4
(avril 2026) a ajouté AI Search, auto-tagging et recherche visuelle sur plus de 80 formats
dont la vidéo. Ces outils ne visent pas la même collection que Pysaurus, mais ils changent
l'attente par défaut : « je cherche sans avoir rien tagué ».

**Le reste bouge peu.** digiKam 9.0 (mars 2026) puis 9.1 (juin 2026) : Qt6, lecteur vidéo
amélioré, mais la vidéo reste un citoyen de seconde classe ; tinyMediaManager 5.2.12
(5.3.0 en pré-version, lanceur réécrit en Rust) ; Kodi 22 « Piers » en bêta depuis juin
2026 ; Czkawka 11.0.1 (février 2026) sur l'axe dédup pure.

---

## 5. Verdict et décision

### 5.1 Le positionnement qui tient

> **Pysaurus est le seul outil qui traite une collection vidéo locale comme une base de
> données interrogeable.**

Quatre briques, et personne d'autre n'a les quatre : propriétés déclarées / typées /
multi-valuées / énumérables ; groupement dynamique sur n'importe quel champ avec navigation
hiérarchique ; langage d'expressions compilé en SQL ; FTS5 multi-mode. Les concurrents
*organisent* (tags, collections, dossiers) ; Pysaurus *interroge*. L'écart se voit sur une
question comme « les h264 1080p de plus de 2 Go, jamais lus, sans valeur pour la propriété
`état`, groupés par année » : c'est une expression dans Pysaurus, et ce n'est pas une
question qu'on peut poser à Stash ou à Hydrus.

Formuler la niche par les propriétés typées seules ne suffit plus : Stash en a depuis mars
2026 (§ 4.1). C'est la *combinaison* requête + typage + groupement qui est unique.

Pysaurus **ne rivalise pas** avec Plex/Jellyfin/Emby sur le streaming, le transcodage, le
multi-appareil ou le multi-utilisateur — et il ne devrait pas essayer.

Il est par ailleurs **structurellement à l'abri de la vague CLIP** : la recherche sémantique
répond à « une plage au coucher du soleil », pas à « débit > 8 Mb/s et pas de piste audio
anglaise ». Les deux ne se recouvrent pas. En revanche elle dévalue le tagging *descriptif*
manuel — donc la valeur des propriétés descriptives baisse, celle des propriétés de
**gestion** (état, source, à retrier, qualité vérifiée) reste intacte.

### 5.2 Ce qui reste faible

- **Similarité par cosinus** là où l'état de l'art est le phash — le point technique le
  plus exposé, y compris face à des utilitaires gratuits (§ 4.2).
- Pas d'API programmatique (`import pysaurus`).
- Pas de système de plugins.
- Pas de récupération de métadonnées en ligne.
- Pas publié, pas de communauté, pas de documentation utilisateur.
- `LICENSE` non édité : le copyright est attribué à la Python Packaging Authority.

### 5.3 Le risque réel

Ce n'est ni Plex ni Jellyfin — terrain différent, et Plex creuse sa propre tombe tarifaire.
C'est **Stash et Hydrus, qui convergent vers Pysaurus alors que Pysaurus ne converge pas
vers eux**. Stash a mis sept ans à faire des champs custom ; il ne mettra pas sept ans à
les typer, l'issue est déjà ouverte. Hydrus a déjà l'API, la dédup mature et la communauté.

Formulé autrement : les avantages de Pysaurus sont des avantages **d'implémentation**, pas
des avantages **de position**. Pas de communauté, pas d'écosystème, pas d'effet de données,
pas de coût de sortie pour un utilisateur. Un avantage d'implémentation s'érode à la
vitesse où le concurrent écrit du code. Fenêtre estimée : **12 à 24 mois**.

### 5.4 La décision qui commande tout : publier ou non

**Scénario A — outil personnel (statu quo).** Parfaitement défendable : Pysaurus fait ce
qu'il faut, pour un utilisateur qui le connaît. Mais alors la concurrence n'a d'intérêt que
comme source d'idées, et **une seule mérite d'être volée : le phash avec règles
d'auto-résolution**. Tout le reste (API, plugins, TMDb, multi-utilisateur) est du bruit, et
ce document n'a plus besoin d'être tenu à jour.

**Scénario B — publication.** Trois conditions minimales, dans l'ordre :

1. un `LICENSE` réel ;
2. une **API programmatique** (`import pysaurus`) : c'est ce qui transforme un outil en
   brique réutilisable, et c'est ce qu'ont Hydrus (Client API) et Stash (GraphQL) ;
3. une documentation utilisateur.

Le phash vient juste après. Positionnement à tenir : « requêteur de collection vidéo
locale », **pas** « gestionnaire de médias » — ce second terrain est saturé et perdu
d'avance.

Ne pas trancher revient à choisir A par défaut, tout en payant le coût de B (suivre les
concurrents, tenir cette analyse à jour) sans en avoir les bénéfices.

### 5.5 Effet sur le backlog

| Item | Vaut dans | Note |
|---|---|---|
| Hash perceptuel (+ règles d'auto-résolution) à la place du cosinus | **A et B** | Comble la faiblesse technique la plus exposée ; utile même en usage solo |
| **Serveur MCP en lecture seule** (§ 6.2) | **A et B** | Meilleur rapport valeur/coût de la liste ; à démarrer *après* le 28 juillet 2026 (spec finale + SDK Python v2) |
| Export dataset : manifeste + extraction de clips (§ 6.1) | A et B | Quelques centaines de lignes ; réhabilite `core/video_clipping.py`, resté sans consommateur |
| `LICENSE` correct | B | Une ligne, bloquant pour toute publication |
| API programmatique `import pysaurus` | B | La condition qui sépare l'outil personnel du projet réutilisable — mais elle sort en sous-produit du serveur MCP : le faire *après* lui, pas avant |
| Documentation utilisateur | B | |
| Métadonnées en ligne (TMDb/IMDb) | Ni A ni B | Terrain perdu d'avance, et hors sujet pour une collection perso non-cinéma |
| Transcodage, streaming distant, multi-utilisateur | Ni A ni B | Terrain des serveurs multimédia, explicitement abandonné |
| Système de plugins | Ni A ni B | Vient après l'API, pas avant |
| Pivot « curation ML » (formats COCO/YOLO/WebDataset, annotations, embeddings, 100k+) | Ni A ni B | Abandonné — § 6.1 : créneau pris en tenaille par NeMo Curator et FiftyOne |

---

## 6. Deux pistes d'extension, évaluées

### 6.1 Curation de datasets vidéo pour le ML — thèse abandonnée

Thèse de mars 2026 (`strategic-direction.md`) : pivoter partiellement vers la curation de
datasets vidéo pour la recherche ML, « créneau sous-exploité » face à FiftyOne, CVAT, Label
Studio et DVC. Priorités annoncées : (1) SDK Python, (2) scalabilité 100k+, (3) formats ML
(COCO, YOLO, WebDataset, Hugging Face), (4) embeddings, (5) annotations.

Trois raisons de l'abandonner.

**1. Le créneau n'est plus sous-exploité, il est pris en tenaille.** À l'échelle
industrielle, **NVIDIA NeMo Curator** (open source, versions 26.02 et 26.04 en 2026) fait
exactement le pipeline vidéo qu'il faudrait construire : découpage en clips (pas fixe ou
détection de changement de scène), filtrage, **génération d'embeddings**, déduplication, le
tout distribué (Ray, multi-GPU). À l'autre bout, **FiftyOne** (Voxel51, open source) tient
la partie interactive : inspection de dataset, visualisation d'embeddings, détection de
quasi-doublons, vues sauvegardées, support vidéo — et livre désormais des « skills » pour
agents. Les points 3, 4 et 5 de la liste de mars sont le cœur de ces outils, pas un manque
du marché.

**2. Les « briques réutilisables » transfèrent mal** (vérifié dans le code) :

- La similarité ne repose pas sur des embeddings mais sur des **miniatures RGB**
  (`core/miniature.py` : trois tableaux d'octets r/g/b d'une image réduite), stockées **hors
  SQL**, dans un `miniatures.json` chargé en bloc (`database/algorithms/miniatures.py`).
  Pour du ML on jette et on passe à CLIP/SigLIP : il n'y a pas de stockage vectoriel à
  réutiliser (il faudrait une table dédiée, avec `sqlite-vec` ou équivalent).
- FTS5 indexe noms de fichiers, titres et propriétés string — de la métadonnée de nommage,
  sans valeur sur un corpus d'entraînement.
- Ce qui transfère réellement, c'est la couche **propriétés typées + vue interrogeable**,
  c'est-à-dire la couche de sélection et d'étiquetage — précisément ce autour de quoi
  FiftyOne est construit.

**3. La scalabilité n'est pas un réglage.** La pagination récupère tous les ids triés de la
vue puis découpe en Python (`video_mega_group.py`), avec un plafond de confort autour de
100k d'après la revue. Les corpus ML commencent où ça s'arrête : le point 2 de la liste de
mars est une réécriture du chemin de requête, pas une optimisation.

**Ce qui reste, et qui vaut le coup.** Pysaurus est bon au *tri humain* d'un corpus vidéo
personnel : quels fichiers, dans quel état, avec quelles propriétés, groupés comment. Pour
en faire un fournisseur des vrais outils ML, il manque une **exportation** — un manifeste
(JSONL ou parquet : chemin, propriétés, champs techniques) et, en option, l'extraction de
clips. Ce second morceau **existe déjà et ne sert à personne** : `core/video_clipping.py`
(`video_clip()`, `video_clip_to_base64()`), que la revue laissait explicitement « en attente
de décision ». Voilà sa décision : le garder — c'est la primitive dont dépendent l'export ML
*et* la prévisualisation MCP (§ 6.2).

Autrement dit : ne pas devenir un outil de curation ML, mais savoir **passer la main** à
ceux qui le sont. Quelques centaines de lignes, pas un pivot.

### 6.2 Serveur MCP sur la base ouverte — la meilleure piste

Question : exposer la base ouverte via un serveur MCP, pour que des LLMs puissent
l'interroger et fouiller les données. Verdict : **oui, et c'est l'extension la plus alignée
avec ce que Pysaurus est**, pour quatre raisons.

**1. C'est la forme exacte du différenciateur.** Le § 5.1 dit que Pysaurus est le seul à
traiter une collection vidéo locale comme une base interrogeable ; un serveur MCP est
précisément l'interface qui rend cette propriété utile en dehors de la GUI. Des serveurs MCP
pour Plex et Jellyfin existent déjà (22 à 24 outils : sessions, scans, utilisateurs,
contrôle de lecture) : ils exposent une **surface de pilotage**, parce que leurs backends ne
savent pas répondre à une question analytique. Pysaurus sait. Ce ne serait donc pas un
énième serveur média, mais le seul auquel on peut demander « les h264 1080p de plus de 2 Go
jamais lues, groupées par année ».

**2. La plomberie est déjà de la bonne forme** (vérifié) :

- `query_videos(view, page_size, page_number, selector)` est **sans état** — exactement ce
  qu'un appel d'outil MCP exige (rien à retenir entre deux appels). `ViewContext` est un
  porteur d'état pur : il se transpose en arguments JSON sans adaptation.
- `searchexp` fournit un **langage de requête textuel** que le modèle émet directement, avec
  des erreurs structurées (`ExpressionError`) à lui renvoyer pour qu'il corrige. C'est le
  point de design qui change tout : on décrit le schéma, le modèle écrit ses requêtes — au
  lieu d'exposer deux douzaines de filtres pré-cuits.
- Les vignettes sont des BLOBs en base (`video_thumbnail`) → blocs image pour un modèle
  multimodal ; `video_clip_to_base64()` → extraits courts (§ 6.1).
- L'ouverture concurrente en lecture seule est déjà éprouvée : les fixtures de test ouvrent
  la base sur disque en `immutable=1` (`tests/utils.py`). Un serveur MCP en processus séparé
  peut donc lire pendant que la GUI tient la base.

**3. Ça règle la condition n°1 de la publication.** Le § 5.4 met l'API programmatique en tête
des prérequis. Un serveur MCP *est* une API programmatique — avec une spécification, un
transport, un mécanisme de découverte et, contrairement à un SDK maison, des clients qui
existent déjà. Il force au passage à définir proprement les opérations appelables : le SDK
Python en sort comme sous-produit. Le faire avant le SDK est plus rentable que l'inverse.

**4. Le calendrier est favorable, à une semaine près.** MCP a été donné à l'Agentic AI
Foundation (Linux Foundation) en décembre 2025 — standard neutre, plus de 10 000 serveurs
publics recensés. La spécification **2026-07-28 est en release candidate** et sort dans cinq
jours ; le **SDK Python v2**, refonte majeure, vise le 2026-07-27. Démarrer aujourd'hui sur
le v1 revient à porter la semaine suivante : attendre le 28 juillet et construire sur v2.

**Esquisse de surface** — petite, à l'inverse des 22-24 outils des serveurs Plex/Jellyfin :

| Outil | Rôle |
|---|---|
| `describe_schema()` | Champs vidéo + définitions de propriétés (types, énumérations, valeurs) — ce qui permet au modèle d'écrire des expressions valides |
| `search_videos(expression, sorting, page, page_size)` | `searchexp` → `ViewContext` → `query_videos()` |
| `group_videos(field, …)` | Le groupement dynamique, que personne d'autre ne sait exposer |
| `get_video(id)` | Fiche complète : champs techniques, propriétés, langues, erreurs |
| `get_thumbnail(id)` / `get_clip(id, start, seconds)` | Blocs image / extrait, pour modèle multimodal |
| `stats()` | Compte, durée cumulée, taille, répartitions |

**Lecture seule par défaut.** L'écriture (poser des valeurs de propriétés — « range-moi cette
collection ») est la partie intéressante, mais elle doit former un jeu d'outils **activé
explicitement** : un appel mal formé réécrit les métadonnées de milliers de fichiers. La
revue de juillet a précisément trouvé que `apply_on_view` faisait confiance aux ids reçus
sans les revalider — c'est la classe de bug qui devient coûteuse quand l'appelant est un
modèle. Transport **stdio** (sous-processus local) : aucune surface d'authentification, ce
qui cadre avec une application de bureau. En HTTP il faudrait traiter l'authentification —
que le serveur vidéo Flask existant n'a d'ailleurs toujours pas.

**Ce que ça ne règle pas** : ni la communauté, ni la publication, ni la faiblesse phash
(§ 5.2). C'est un avantage d'implémentation de plus — mais le moins cher à convertir en
usage réel par d'autres, et le seul qui transforme le différenciateur en interface.

---

## Sources (consultées le 23 juillet 2026)

- Plex : [nouveau tarif Lifetime (749,99 $)](https://9to5mac.com/2026/05/19/plex-increasing-lifetime-plex-pass-cost-to-whopping-750/), [Remote Watch Pass +50 %](https://www.androidauthority.com/plex-remote-watch-pass-price-increase-3663060/), [annonce Plex](https://www.plex.tv/blog/new-lifetime-plex-pass-pricing/)
- Jellyfin : [State of the Fin, 24 mai 2026](https://jellyfin.org/posts/state-of-the-fin-2026-05-24/)
- Stash : [release v0.31.0](https://github.com/stashapp/stash/releases/tag/v0.31.0), [issue #6795 sur les champs custom](https://github.com/stashapp/stash/issues/6795)
- Hydrus : [dépôt](https://github.com/hydrusnetwork/hydrus), [ratings](https://hydrusnetwork.github.io/hydrus/getting_started_ratings.html), [doublons](https://hydrusnetwork.github.io/hydrus/duplicates.html), [auto-résolution](https://hydrusnetwork.github.io/hydrus/advanced_duplicates_auto_resolution.html), [Client API](https://hydrusnetwork.github.io/hydrus/client_api.html)
- digiKam : [9.1.0, juin 2026](https://www.digikam.org/news/2026-06-07-9.1.0_release_announcement/), [9.0.0, mars 2026](https://www.digikam.org/news/2026-03-08-9.0.0_release_announcement/)
- tinyMediaManager : [versions](https://www.tinymediamanager.org/docs/versions) — Kodi : [22 « Piers » bêta 1](https://kodi.tv/article/kodi-22-piers-beta-1/)
- Immich : [pigsty.io/docs/app/immich](https://pigsty.io/docs/app/immich/) — Czkawka : [czkawka.net](https://czkawka.net/)
- MCP (§ 6.2) : [release candidate de la spec 2026-07-28](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/), [SDK Python officiel](https://github.com/modelcontextprotocol/python-sdk), [état de l'écosystème 2026](https://workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026)
- Serveurs MCP média existants : [jellyfin-mcp](https://github.com/sandraschi/jellyfin-mcp), [Plex MCP server](https://lobehub.com/mcp/niavasha-plex-mcp-server)
- Curation ML (§ 6.1) : [NVIDIA NeMo Curator](https://github.com/NVIDIA-NeMo/Curator) et ses [fonctionnalités vidéo](https://docs.nvidia.com/nemo/curator/v26.02/about/key-features), [FiftyOne](https://voxel51.com/fiftyone), [sqlite-vec](https://github.com/asg017/sqlite-vec)
