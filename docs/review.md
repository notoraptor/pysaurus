# Revue du cœur de pysaurus

- **Date** : 2026-07-17 (mise à jour le 2026-07-18 après une deuxième salve de correctifs)
- **Périmètre** : tout le paquet `pysaurus/` **hors** `pysaurus/interface/` (et hors `wip/`, `videroid`) —
  110 fichiers, ~10 400 lignes. Lecture intégrale du code, usages vérifiés par recherche exhaustive,
  validé par `poe check` (ruff, i18n, ty) et la suite de tests (1820 passed, 7 skipped, ~40 s en `-n auto`).

## Verdict global

Le cœur est **en bon état : compact, architecturé, et globalement fiable**. ~10 400 lignes pour un
moteur qui couvre scan de dossiers, extraction PyAV, SQLite+FTS5 avec migrations, moteur de vues
(filtres/groupes/classifier/recherche/tri), détection de similarité, propriétés typées et i18n —
c'est peu de code pour ce périmètre, et c'est une qualité : pas de sur-ingénierie. La dette existante
est **périphérique, pas structurelle** : surtout des vestiges des anciens frontends (web, backend
JSON, cysaurus) pas encore purgés. Peu de vrais bugs, aucun grave.

Le moteur est **fonctionnellement achevé** pour son périmètre : pas de demi-fonctionnalité côté
cœur ; ce qui reste relève de la consolidation post-migration.

## Points forts

- **Séparation en couches réelle**, pas cosmétique : `AbstractDatabase` (~20 méthodes abstraites) /
  `DatabaseOperations` / `DatabaseAlgorithms` ; `ViewContext` pur état ; `query_videos()` stateless.
- **Schéma SQL soigné** (`database/saurus/database.sql`) : colonnes générées VIRTUAL pour les champs
  dérivés, colonnes STORED indexées pour `extension`/`file_title` (migration m0003 avec rebuild de
  table documenté), FTS5 + triggers + fonctions Python enregistrées, contraintes CHECK, migrations
  versionnées avec bootstrap des bases pré-versioning.
- **Pas d'injection SQL trouvée** : littéraux paramétrés partout ; identifiants passés par des
  mappings contrôlés (`SqlFieldFactory`, `ATTRIBUTE_SQL_MAP`, `WRITABLE_FIELDS`, validation contre
  `F`). Le compilateur searchexp→SQL (`sql_expression_compiler.py`) est propre, y compris le XOR qui
  duplique correctement ses paramètres. Chunking `SQLITE_LIMIT_VARIABLE_NUMBER` systématique.
- **Modules de très bonne facture**, docstrings expliquant les *décisions* : `folder_scan.py`
  (un thread par point de montage, argumenté), `fs_utils.py` (correction mtime FAT/DST),
  `semantic_text.py` (tri naturel + exposants/indices Unicode, alternative natsort documentée),
  `universal_datetime/udt.py` (docstring bilingue, choix de conception), les migrations.
- **Logique métier des « moves » mûre** : détection par window functions, refus de merge en cas de
  conflit sur propriété unique, validé *avant* toute écriture
  (`database_algorithms.py::_refuse_unique_property_conflicts`).
- **Couverture de tests solide** : ~1 030 tests portent sur le cœur (sur 1 778).

## Corrigé le 2026-07-17

Traité dans la foulée de la revue (commits `ee6ed550`, `568d5bd4`, puis working tree) :

- ✅ **Bug thumbnail `avcodec_send_packet()`** : fuite de `skip_frame="NONKEY"` du codec context
  partagé entre extraction d'infos et thumbnail — reset explicite avant le seek du thumbnail
  (`video_raptor_pyav.py`).
- ✅ **Flakiness xdist** : les fixtures SQL ouvraient le fichier partagé en lecture-écriture ;
  désormais ouverture source `immutable=1` + copie in-memory (`tests/utils.py`).
- ✅ **Violation de couche core→interface** : `ConsoleNotificationPrinter` déplacé de
  `interface/api/api_utils/` vers `core/console_notification_printer.py` ; `informer.py` n'importe
  plus l'interface. C'était la *seule* violation de couche du cœur.
- ✅ **`tqdm` déclaré** dans `pyproject.toml` (n'était présent que par transitivité de `videre` ;
  `scripts/diagnose_db_folders.py` en dépend).
- ✅ **Purge de code mort** : `database/debug_database.py` (« Currently unused »), `core/native/`
  (répertoire vide, vestige backend C), `CysaurusUnavailable` (exceptions), `DecoratingMethod` et
  `Procedure` (`core/classes.py` — le `Procedure` réellement utilisé est `videre.Procedure`),
  puis dans `core/functions.py` : `fatal`, `apply_selector`, ainsi que
  `class_get_public_attributes` et `object_to_dict` (deux morts que la revue initiale avait
  manqués).
- ✅ **`pgcd` déplacé dans `fraction.py`** (renommé `gcd`) : `Fraction` est désormais autosuffisant,
  et `functions.py` ne porte plus que des utilitaires réellement partagés.
- ✅ **Purge, suite** : `AbsolutePath._locate_file_old`, `PREFIX`/`get_sql_prefix`
  (`pysaurus_collection.py`), et suppression du fichier `imgsimsearch/common.py` — ce qui règle le
  doublon `SIM_LIMIT` ; `THUMBNAIL_DIMENSION` est internalisé dans `python_fine_comparator.py`,
  son unique consommateur.
- ✅ **`pythonsearchexp` déplacé dans `wip/`** (module + test, imports ajustés) : décision actée —
  hors du cœur actif, gardé pour plus tard. Nota : faute de `testpaths` dans `pyproject.toml`,
  pytest collecte aussi `wip/` (~147 tests, dont ceux-ci) — la suite « complète » n'a donc jamais
  mesuré uniquement le code actif.

## Corrigé le 2026-07-18

Poursuite du bug n°2 identifié le 2026-07-17 (tri/groupement `extension`/`file_title` n'utilisant pas
les colonnes STORED) : avant de basculer, vérification empirique de l'équivalence entre la colonne SQL
et `AbsolutePath.extension`/`.file_title` — divergence
réelle trouvée sur un motif précis (nom commençant par ≥2 points consécutifs suivis d'un segment
sans point, ex. `..backup`) : la garde de la formule SQL, et celle d'`AbsolutePath.file_title`, ne
généralisaient qu'au cas à un seul point de tête (`.gitignore`), pas à N. `AbsolutePath.extension`
(via `os.path.splitext`) généralisait déjà correctement, mais divergeait alors de son propre
`file_title` sur ce même motif.

- ✅ **Généralisation de la règle des points de tête**, désormais cohérente entre les deux implémentations :
  - `AbsolutePath.file_title`/`.extension` (`core/absolute_path.py`) dérivent maintenant d'une seule
    méthode privée commune — elles ne peuvent plus diverger entre elles.
  - Formule SQL des colonnes `extension`/`file_title` généralisée de la même façon (`database.sql` ;
    migration `m0004_generalize_leading_dots.py`, rebuild de table comme m0003).
  - Test ajouté (`tests/databases/unittests/saurus_sql/test_filename_derived_columns.py`) : insère des
    vidéos aux noms limites dans une DB in-memory et compare les colonnes lues à `AbsolutePath`.
- ✅ **Bug n°2 réglé** : `grouping_utils.py` lit désormais `v.extension`/`v.file_title` (colonnes STORED
  indexées) au lieu de rappeler une fonction Python ligne par ligne.
- ✅ **`title`/`title_numeric`** : expression SQL inline (`IIF(v.meta_title = '', v.file_title,
  v.meta_title)`) plutôt qu'un appel Python — pas de nouvelle colonne de schéma, aucun autre
  consommateur n'en avait besoin.
- ✅ **Purge** : `pysaurus_get_extension`, `pysaurus_get_file_title`, `pysaurus_get_title`
  (`sql_functions.py`) supprimées, plus aucun appelant après les changements ci-dessus.
- ✅ **`source_count` recalculé au prix fort, réglé** : nouvelle fonction `video_mega_source_count()`
  (`video_mega_search.py`) — une seule requête `COUNT(DISTINCT v.video_id)` combinant toutes les
  sources en `OR` (réutilise `_build_where_clause`/`SQLWhereBuilder.combine` déjà existants), au lieu
  de matérialiser un `SQLVideoWrapper` par vidéo de chaque source pour ne garder que son id. 7 tests
  ajoutés (`test_video_mega_source_count.py`), dont la non-double-comptabilisation des sources qui se
  chevauchent.
- ✅ **Cache de padding jamais invalidé, réglé par suppression du besoin de padding** : les clés de
  tri naturel (`*_numeric`) n'utilisent plus un padding global (largeur du plus long nombre de la
  base, scannée puis cachée par chemin de db sans invalidation — tris faux après indexation de
  nombres plus longs, clé `":memory:"` partagée entre bases in-memory) mais un encodage
  auto-délimité par valeur (`core/semantic_text.py::encode_numbers_for_sort`) : chaque suite de
  chiffres (zéros de tête retirés, exposants/indices convertis) devient ` NNNNNchiffres ` avec sa
  propre longueur padée à 5 — l'ordre lexicographique reste l'ordre naturel sans aucune connaissance
  du dataset, le bug ne peut plus exister. `pysaurus_text_with_numbers()` passe à un argument ;
  `SqlFieldFactory` perd cache, scans et paramètre de connexion ; `SemanticField`,
  `get_longest_number_in_string` et `pad_numbers_in_string` supprimés. Tests unitaires + SQL
  (`test_natural_sort.py`), dont le scénario de régression (nombre plus long inséré *après* le
  premier tri) et l'équivalence d'ordre avec `SemanticText`.
- ✅ **Sélections fantômes** (bug découvert à l'usage, hors findings de la revue) : une écriture de
  données qui retire des vidéos de la vue sans changer ses paramètres (ex. retirer la valeur de
  propriété sur laquelle la vue est groupée) laissait leurs ids dans le `Selector` — l'invalidation
  par génération ne couvre que les changements de paramètres, et les purges ponctuelles que les
  suppressions connues de l'UI. Compte de sélection faux dans les deux modes, et surtout
  `apply_on_view` faisait confiance aux ids inclus sans les revalider : les actions batch pouvaient
  toucher des vidéos hors vue. Corrigé à trois niveaux : `Selector.has_marks()`/`restrict_to()`
  (`core/classes.py`), réconciliation de la sélection avec les ids réels de la vue à chaque
  refresh (kyuti + videroid, via `get_all_view_ids()` — requête émise seulement si des ids sont
  marqués), et `FeatureAPI.apply_on_view` résout désormais les *deux* modes du selector contre la
  vue courante. 10 tests (unitaires `Selector`, FeatureAPI, kyuti, videroid — dont le scénario
  complet rejoué sur base SQL réelle).

## Problèmes d'architecture (restants)

1. **Deux bus de notifications coexistent** : `Notifier` (`core/notifying.py`, porté par la db) et
   `Information` (`core/informer.py`, singleton process-global avec `multiprocessing.Manager`).
   Les algorithmes lourds (`database/algorithms/videos.py`, `miniatures.py`, `imgsimsearch`,
   `Profiler` par défaut) court-circuitent `db.notifier` et passent par `Information.notifier()` ;
   `GuiAPI` doit se brancher aux deux. Ça fonctionne, mais c'est le point le plus embrouillé du
   cœur — premier candidat à une unification.
2. **Circularité ops ↔ algos** contournée par 3 imports locaux commentés
   (`database_operations.py`, `database_algorithms.py`) — la frontière operations/algorithms n'est
   pas naturelle partout.
3. `informer.py` fait des `print("NEW INFORMATION", file=sys.stderr)` de debug en production, et
   `NotificationCollector.views` (`core/job_notifications.py`) accumule chaque notification à vie —
   fuite mémoire lente sur une longue session.
4. `core/classes.py` reste un fourre-tout ; `FileSize`/`BitSize` sont des copies structurelles
   l'une de l'autre.

## Bugs et risques concrets (restants)

1. **Incohérences dans les erreurs de propriétés** : `prop_type_del` lève `ValueError` (pas une
   `PysaurusError`), `prop_type_set_name` échoue *silencieusement* si la propriété n'existe pas,
   `prop_type_set_multiple` lève `PropertyAlreadyMultiple` même pour unique→unique.
2. **`videos_tag_set` mute le dict de l'appelant** (`pysaurus_collection.py`, boucle
   `updates[video_id] = pt.instantiate(...)`).
3. **Comparateurs sans garde de type** : `Date.__eq__`, `Text.__eq__`, `VideoPattern.__eq__`
   crashent face à `None` ou un autre type au lieu de retourner `NotImplemented`.
   `FileSize`/`BitSize`/`Duration` le font correctement — c'est inégal.
4. **RuntimeWarning NumPy connu** : `imgsimsearch/backend_numpy.py::moderate` fait inf/inf → nan,
   rattrapé après coup par `nan_to_num` mais en émettant le warning visible dans les runs de tests.
   Un `np.errstate(invalid="ignore")` l'assumerait proprement.
5. **`_get_video_moves`** (`video_mega_utils.py`) : générateur qui ouvre `with db:` — si l'appelant
   n'épuise pas l'itération, la connexion reste tenue jusqu'au GC.
6. Mineurs : serveur Flask localhost sans authentification (acceptable pour un outil desktop, mais
   tout processus local peut streamer les vidéos par id) ; `assert` utilisés comme validation
   d'entrée (`application.py::open_database_from_name`) ; `AbsolutePath.__eq__` sensible à la casse
   sous Windows (deux casses d'un même fichier = deux entrées, `UNIQUE(filename)` ne protège pas).

## Code mort et vestiges (restants)

Usages vérifiés par recherche exhaustive (tout le repo, y compris interface et tests).
Reste ~300-450 lignes purgeables :

| Vestige | Emplacement | Note |
|---|---|---|
| `Text` | `core/classes.py` | comparaison locale-aware, plus aucun consommateur |
| `Group`, `GroupArray`, `GroupDef.sorted`/`sort_inplace`/`_generate_sort_key` | `dbview/view_tools.py` | tri Python des groupes, remplacé par le SQL ; les consommateurs n'importent que `GroupDef`/`SearchDef` |
| `NegativeComparator` | `core/compare.py` | instancié par `GroupDef.__init__` mais exploité uniquement par la machinerie ci-dessus — à supprimer *avec* elle |
| `HTMLStripper` (TODO « Unused »), `System.is_case_insensitive`/`get_identifier`/`get_lib_basename`/`get_exe_basename`, `ImageUtils.get_near_front_pixels` (~84 l.), `ImageUtils.thumbnail_to_base64` | `core/modules.py` | vestiges natif/web |
| `Miniature.global_intensity`, `Graph.__remove` | divers | |
| `_CompareAllProvider` + chemin `compare_all=True` | `database/features/db_similar_videos.py` | personne ne passe `True` |
| `custom_json_parse_string` | `core/custom_json_parser.py` | seul le fallback fichier (`parse_json`) sert encore, pour d'anciens fichiers non-UTF-8 |

Un cas reste une **décision**, pas une suppression mécanique :

- `core/video_clipping.py` (~55 l., avec des `print` de debug) : testé mais aucun consommateur
  applicatif — garder si une fonction « extrait/preview » est prévue, sinon supprimer.

Vérification notable : `Selector.parse_dict` avait été classé mort par erreur lors de la première
passe (grep paginé) — il est **vivant** (`feature_api.py`, entrée des sélections du frontend).

## Performance

Rien d'alarmant pour l'échelle visée (dizaines de milliers de vidéos) :

- La pagination récupère tous les ids triés de la vue puis découpe en Python au lieu de
  LIMIT/OFFSET (`video_mega_group.py::_compute_results_and_stats`) — acceptable, à revoir si une
  collection dépasse ~100k entrées.
- `_query_property_groups_with_classifier` exécute deux fois la même sous-requête (une pour
  compter via `len(query_all)`, une dans la super-requête).
- 3 `deepcopy` de `QueryMaker` par affichage de page.
- `prop_type_search` : N+1 sur `property_enumeration` — négligeable (peu de propriétés).
- FTS5 : table à contenu dupliqué (le texte est stocké deux fois) — un `content=`/contentless
  économiserait de l'espace mais complexifie ; choix défendable.
- L'extraction vidéo (le coût dominant réel) est bien parallélisée par processus, un seul container
  par fichier.

## Recommandations restantes, par priorité

Plus aucun item P1 : les trois correctifs à fort ratio de la revue initiale (colonnes STORED,
`source_count`, cache de padding) sont tous réglés.

**P2 — hygiène**

1. Purger le code mort restant (tableau ci-dessus).
2. Harmoniser les exceptions propriétés (bug n°1).
3. `np.errstate` autour de `moderate()` (bug n°4).
4. Retirer les `print` de debug d'`informer.py` ; borner `NotificationCollector.views`.

**P3 — fond, sans urgence**

5. Unifier `Notifier`/`Information` en un seul bus de notifications.
6. Fusionner `FileSize`/`BitSize` via une base commune.
7. Statuer sur `video_clipping` (`pythonsearchexp` : tranché, déplacé dans `wip/`).

## Suite envisagée

- Même revue pour l'interface **kyuti**.
- ✅ **Positionnement concurrentiel** — fait le 2026-07-23, dans `docs/competitive-analysis.md`
  (document refondu en une seule analyse à jour ; verdict et décision en § 5). En résumé : la niche
  tient mais change de nom — non plus « le seul avec des propriétés typées » (Stash 0.31.0 a
  ajouté des champs custom le 30 mars 2026) mais « le seul qui traite une collection vidéo
  locale comme une base interrogeable » (propriétés typées + groupement dynamique +
  `searchexp` + FTS5). Le concurrent le plus proche n'est pas Stash mais **Hydrus Network**
  (même pile Python/Qt/SQLite, phash mature, API, communauté), que la première analyse avait
  manqué. Faiblesse la plus exposée : la similarité par cosinus face au phash. Décision en
  suspens, qui commande le backlog : publier ou rester un outil personnel.
