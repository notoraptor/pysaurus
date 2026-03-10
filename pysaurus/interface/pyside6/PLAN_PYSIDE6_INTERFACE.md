# Plan d'implémentation de l'interface PySide6

## Vue d'ensemble

Réécriture de l'interface utilisateur de Pysaurus en utilisant PySide6 (Qt6) pour une expérience native et des interactions plus prévisibles.

## Principes d'architecture

### 1. Appels directs (pas de `__run_feature__`)

```python
# ❌ Ancienne approche (Web) - indirection via strings
result = api_bridge.__run_feature__("open_video", video_id)
data = api_bridge.backend(page_size, page_number)  # retourne dict

# ✅ Nouvelle approche (PySide6) - appels directs
self.database.ops.open_video(video_id)
context = self.database.provider.get_current_state(page_size, page_number)  # retourne VideoSearchContext
```

### 2. Objets Python natifs (pas de JSON/dict)

```python
# ❌ Ancienne approche - manipulation de dicts
video_dict = data["videos"][0]
title = video_dict.get("title", "")
duration = video_dict.get("length", "0:00:00")

# ✅ Nouvelle approche - objets typés (classes abstraites)
video: VideoPattern = context.result[0]
title = video.title                    # str
duration = video.length                # Duration (avec __str__ formaté)
size = video.size                      # FileSize (avec __str__ formaté)
props = video.properties               # dict[str, list[PropUnitType]]
```

### 3. Classes abstraites vs implémentations

**Principe** : Utiliser les classes abstraites dans les type hints pour découpler l'interface de l'implémentation de la base de données.

```python
# ❌ Mauvais - couplé à l'implémentation JSDB
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo
def display_video(video: LazyVideo): ...

# ✅ Bon - utilise l'interface abstraite
from pysaurus.video.video_pattern import VideoPattern
def display_video(video: VideoPattern): ...
```

### 4. Objets disponibles directement

| Classe abstraite | Module | Usage |
|------------------|--------|-------|
| `VideoPattern` | `video.video_pattern` | Interface vidéo avec toutes les propriétés |
| `VideoSearchContext` | `video.video_search_context` | Résultat de requête avec `.result: list[VideoPattern]` |
| `PropType` | `database.jsdb.jsdb_prop_type` | Type de propriété avec validation |
| `GroupDef` | `video_provider.view_tools` | Configuration de groupement |
| `SearchDef` | `video_provider.view_tools` | Configuration de recherche |
| `Group` | `video_provider.view_tools` | Groupe avec `.field_value` et `.videos` |
| `Duration` | `core.duration` | Durée formatée automatiquement |
| `FileSize` | `core.file_size` | Taille formatée automatiquement |
| `Date` | `core.datestring` | Date formatée automatiquement |
| `AbsolutePath` | `core.absolute_path` | Chemin avec API riche |

### 4. Accès direct aux couches

```python
# Application (gestion des bases de données)
from pysaurus.application.application import Application
app = Application(notifier)
db = app.open_database_from_name("my_db", update=True)

# Base de données
db.get_videos(where={"found": True})     # -> list[LazyVideo]
db.get_prop_types()                       # -> list[PropType]
db.prop_type_add(name, type, default, multiple)

# Provider (vue/filtrage)
provider = db.provider
context = provider.get_current_state(page_size, page_number)
provider.set_sources([["readable", "found"]])
provider.set_search("query", "and")
provider.set_groups("year", is_property=False, sorting="count")

# Opérations
ops = db.ops  # DatabaseOperations
ops.open_video(video_id)
ops.mark_as_read(video_id)
ops.delete_video(video_id)

# Algorithmes
algos = db.algos  # DatabaseAlgorithms
algos.refresh()
algos.find_similar_videos()
```

## Architecture proposée

```
pysaurus/interface/pyside6/
├── __init__.py
├── main.py                    # Point d'entrée, QApplication
├── main_window.py             # QMainWindow avec navigation
├── app_context.py             # Contexte applicatif (Application, Database, signaux Qt)
├── pages/
│   ├── __init__.py
│   ├── databases_page.py      # Sélection/création de base de données
│   ├── home_page.py           # Progression du chargement
│   ├── videos_page.py         # Navigation vidéo principale
│   └── properties_page.py     # Gestion des propriétés
├── widgets/
│   ├── __init__.py
│   ├── video_card.py          # Widget carte vidéo (reçoit VideoPattern)
│   ├── video_list_item.py     # Widget ligne vidéo (reçoit VideoPattern)
│   ├── source_tree.py         # QTreeWidget pour sélection des sources
│   ├── group_selector.py      # Dialog de configuration du groupement
│   ├── sort_editor.py         # Dialog d'édition du tri
│   └── property_editor.py     # Dialog d'édition de propriété vidéo
├── dialogs/
│   ├── __init__.py
│   ├── video_info_dialog.py   # Dialog d'information (reçoit VideoPattern)
│   ├── batch_edit_dialog.py   # Édition batch (reçoit list[VideoPattern])
│   ├── confirm_dialog.py      # Confirmation générique
│   └── move_dialog.py         # Déplacement de fichier
└── utils/
    ├── __init__.py
    ├── constants.py           # Constantes (SOURCE_TREE, GROUPABLE_FIELDS)
    ├── workers.py             # QThread workers pour opérations longues
    └── qt_utils.py            # Utilitaires Qt (styles, icônes)
```

## Contexte applicatif (`app_context.py`)

**Principe** : Hériter de `GuiAPI` pour réutiliser le mécanisme de threading (`@process`) et de notifications existant.

```python
from PySide6.QtCore import QObject, Signal
from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.core.notifications import (
    Notification, DatabaseReady, JobToDo, JobStep, Done, Cancelled, End
)
from pysaurus.video.video_search_context import VideoSearchContext


class PySide6API(GuiAPI):
    """
    API PySide6 qui hérite de GuiAPI.

    Réutilise :
    - Le threading via @process (create_database, open_database, etc.)
    - Le système de notifications
    - Toutes les méthodes de FeatureAPI et GuiAPI

    Ajoute :
    - Conversion des notifications en signaux Qt
    """
    pass  # Voir ci-dessous pour l'implémentation


class AppContext(QObject):
    """
    Contexte applicatif partagé entre toutes les pages.

    Encapsule PySide6API et expose des signaux Qt pour les notifications.
    """

    # Signaux Qt pour les notifications backend
    notification_received = Signal(object)      # Notification (any type)
    database_ready = Signal()                   # DatabaseReady
    job_started = Signal(str, int)              # JobToDo: (channel, total)
    job_progress = Signal(str, int, int)        # JobStep: (channel, step, total)
    operation_done = Signal()                   # Done
    operation_cancelled = Signal()              # Cancelled
    operation_ended = Signal(str)               # End: (message)

    def __init__(self):
        super().__init__()
        self.api = PySide6API()
        # Connecter les notifications aux signaux Qt
        self.api.set_notification_callback(self._on_notification)

    def _on_notification(self, notification: Notification):
        """Convertit les notifications backend en signaux Qt."""
        # Signal générique
        self.notification_received.emit(notification)

        # Signaux spécifiques
        if isinstance(notification, DatabaseReady):
            self.database_ready.emit()
        elif isinstance(notification, JobToDo):
            self.job_started.emit(notification.channel, notification.total)
        elif isinstance(notification, JobStep):
            self.job_progress.emit(
                notification.channel, notification.step, notification.total
            )
        elif isinstance(notification, Done):
            self.operation_done.emit()
        elif isinstance(notification, Cancelled):
            self.operation_cancelled.emit()
        elif isinstance(notification, End):
            self.operation_ended.emit(notification.message)

    # =========================================================================
    # Accès direct aux couches (pas de sérialisation JSON)
    # =========================================================================

    @property
    def database(self):
        """AbstractDatabase ou None."""
        return self.api.database

    @property
    def provider(self):
        """VideoProvider ou None."""
        return self.database.provider if self.database else None

    @property
    def ops(self):
        """DatabaseOperations ou None."""
        return self.database.ops if self.database else None

    @property
    def algos(self):
        """DatabaseAlgorithms ou None."""
        return self.database.algos if self.database else None

    # =========================================================================
    # Opérations longues (via @process dans GuiAPI, exécutées en thread)
    # =========================================================================

    def get_database_names(self) -> list[str]:
        """Liste des noms de bases de données."""
        return self.api.application.get_database_names()

    def create_database(self, name: str, folders: list[str], update: bool = True):
        """Crée une base (thread). Émet database_ready quand terminé."""
        self.api.create_database(name, folders, update)

    def open_database(self, name: str, update: bool = True):
        """Ouvre une base (thread). Émet database_ready quand terminé."""
        self.api.open_database(name, update)

    def update_database(self):
        """Rafraîchit la base (thread). Émet database_ready quand terminé."""
        self.api.update_database()

    def find_similar_videos(self):
        """Cherche les vidéos similaires (thread). Émet database_ready quand terminé."""
        self.api.find_similar_videos()

    def move_video_file(self, video_id: int, directory: str):
        """Déplace un fichier vidéo (thread). Émet done/cancelled/ended."""
        self.api.move_video_file(video_id, directory)

    def cancel_operation(self):
        """Annule l'opération en cours."""
        self.api.cancel_copy()

    # =========================================================================
    # Opérations synchrones (accès direct, pas de thread)
    # =========================================================================

    def get_videos(self, page_size: int, page_number: int) -> VideoSearchContext:
        """Retourne le contexte avec les vidéos (list[VideoPattern])."""
        return self.provider.get_current_state(page_size, page_number)

    def close_database(self):
        """Ferme la base de données."""
        self.api.close_database()

    def delete_database(self):
        """Supprime la base de données."""
        self.api.delete_database()

    def close_app(self):
        """Ferme l'application proprement."""
        self.api.close_app()
```

## Implémentation de PySide6API

```python
from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.core.notifications import Notification


class PySide6API(GuiAPI):
    """
    Implémentation PySide6 de GuiAPI.

    La seule différence avec GuiAPI est l'implémentation de _notify()
    qui appelle un callback configurable (pour émettre des signaux Qt).
    """

    def __init__(self):
        super().__init__()
        self._notification_callback = None

    def set_notification_callback(self, callback):
        """Configure le callback pour les notifications."""
        self._notification_callback = callback

    def _notify(self, notification: Notification) -> None:
        """Implémentation requise par GuiAPI (méthode abstraite)."""
        if self._notification_callback:
            self._notification_callback(notification)
```

## Flux des opérations longues

```
┌─────────────────────────────────────────────────────────────────┐
│ UI (MainWindow)                                                 │
│   │                                                             │
│   ├─► ctx.open_database("my_db", update=True)                   │
│   │     │                                                       │
│   │     └─► PySide6API.open_database()  [@process decorator]    │
│   │           │                                                 │
│   │           └─► _launch() → Thread                            │
│   │                 │                                           │
│   │                 ├─► JobToDo notification                    │
│   │                 │     └─► _notify() → callback              │
│   │                 │           └─► AppContext._on_notification │
│   │                 │                 └─► job_started.emit()    │
│   │                 │                       └─► HomePage.on_job │
│   │                 │                                           │
│   │                 ├─► JobStep notifications (loop)            │
│   │                 │     └─► job_progress.emit()               │
│   │                 │           └─► HomePage.update_progress()  │
│   │                 │                                           │
│   │                 └─► _finish_loading()                       │
│   │                       └─► DatabaseReady notification        │
│   │                             └─► database_ready.emit()       │
│   │                                   └─► navigate to VideosPage│
└─────────────────────────────────────────────────────────────────┘
```

## Connexion des signaux dans les pages

```python
class HomePage(QWidget):
    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx

        # Connexion des signaux
        self.ctx.job_started.connect(self._on_job_started)
        self.ctx.job_progress.connect(self._on_job_progress)
        self.ctx.database_ready.connect(self._on_database_ready)
        self.ctx.operation_cancelled.connect(self._on_cancelled)

    def _on_job_started(self, channel: str, total: int):
        """Un job démarre."""
        self.jobs[channel] = {"total": total, "current": 0}
        self._add_progress_bar(channel, total)

    def _on_job_progress(self, channel: str, step: int, total: int):
        """Progression d'un job."""
        self.progress_bars[channel].setValue(step)
        self.progress_bars[channel].setMaximum(total)

    def _on_database_ready(self):
        """Base prête → naviguer vers VideosPage."""
        self.parent().show_videos_page()

    def _on_cancelled(self):
        """Opération annulée."""
        self._show_message("Operation cancelled")
```

## Exemple : Widget VideoCard avec VideoPattern

```python
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Signal
from pysaurus.video.video_pattern import VideoPattern

class VideoCard(QFrame):
    """Carte vidéo affichant un VideoPattern (classe abstraite)."""

    clicked = Signal(int)        # video_id
    double_clicked = Signal(int)

    def __init__(self, video: VideoPattern, parent=None):
        super().__init__(parent)
        self.video = video
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Thumbnail (VideoPattern.thumbnail retourne bytes)
        thumb_label = QLabel()
        if self.video.thumbnail:
            pixmap = QPixmap()
            pixmap.loadFromData(self.video.thumbnail)
            thumb_label.setPixmap(pixmap.scaled(160, 90))
        layout.addWidget(thumb_label)

        # Titre (propriété dérivée dans VideoPattern)
        title_label = QLabel(self.video.title)
        layout.addWidget(title_label)

        # Durée (VideoPattern.length retourne Duration avec __str__)
        duration_label = QLabel(str(self.video.length))
        layout.addWidget(duration_label)

        # Résolution (propriétés abstraites implémentées)
        res_label = QLabel(f"{self.video.width}x{self.video.height}")
        layout.addWidget(res_label)

        # Taille (VideoPattern.size retourne FileSize avec __str__)
        size_label = QLabel(str(self.video.size))
        layout.addWidget(size_label)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.video.video_id)
```

## Exemple : Page Videos avec VideoSearchContext

```python
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.dbview.view_tools import GroupDef


class VideosPage(QWidget):
   def __init__(self, ctx: AppContext, parent=None):
      super().__init__(parent)
      self.ctx = ctx
      self.page_size = 20
      self.page_number = 0

   def load_videos(self):
      """Charge les vidéos via le provider."""
      # Appel direct, retourne VideoSearchContext (pas un dict!)
      context: VideoSearchContext = self.ctx.get_videos(self.page_size, self.page_number)

      # Accès direct aux objets (VideoPattern, pas l'implémentation concrète)
      videos: list[VideoPattern] = context.result
      total_count = context.view_count
      nb_pages = context.nb_pages
      total_size = context.selection_file_size  # FileSize
      total_duration = context.selection_duration  # Duration

      # Groupement actif?
      if context.grouping:
         group_def: GroupDef = context.grouping
         print(f"Groupé par: {group_def.field}")

      # Afficher les vidéos
      self._display_videos(videos)
      self._update_stats(total_count, total_size, total_duration)

   def _display_videos(self, videos: list[VideoPattern]):
      # Créer un VideoCard pour chaque vidéo (accepte VideoPattern)
      for video in videos:
         card = VideoCard(video)
         card.double_clicked.connect(self._on_open_video)
         self.grid_layout.addWidget(card)

   def _on_open_video(self, video_id: int):
      # Appel direct aux opérations
      self.ctx.ops.open_video(video_id)
```

## Phases d'implémentation

### Phase 1 : Infrastructure de base
**Durée estimée : 1 session**

1. **Structure des dossiers**
   - Créer `pysaurus/interface/pyside6/`
   - Copier et adapter `api_bridge.py` et `state.py`
   - Copier `utils/constants.py` et `utils/formatters.py`

2. **Point d'entrée (`main.py`)**
   ```python
   def main():
       app = QApplication(sys.argv)
       app.setApplicationName("Pysaurus")
       window = MainWindow()
       window.show()
       sys.exit(app.exec())
   ```

3. **Fenêtre principale (`main_window.py`)**
   - `QMainWindow` avec `QStackedWidget` central
   - Barre de menu (File, View, Help)
   - Barre d'état
   - Navigation entre pages via méthodes `show_page()`

4. **Tests de base**
   - Test de lancement de l'application
   - Test de navigation entre pages vides

### Phase 2 : Page Databases
**Durée estimée : 1 session**

1. **Layout**
   ```
   ┌─────────────────────────────────────────────┐
   │  Pysaurus - Video Collection Manager        │
   ├─────────────────────┬───────────────────────┤
   │  Existing Databases │  Create New Database  │
   │  ┌───────────────┐  │  Name: [___________]  │
   │  │ db1  [⟳][📂][✏][🗑]│  │                     │
   │  │ db2  [⟳][📂][✏][🗑]│  │  Sources:           │
   │  │ ...            │  │  📁 [folder1]    [x] │
   │  └───────────────┘  │  📁 [folder2]    [x] │
   │                     │  📄 [video.mp4]  [x] │
   │                     │  [+ Add folder]       │
   │                     │  [+ Add file]         │
   │                     │  [Create Database]    │
   └─────────────────────┴───────────────────────┘
   ```

2. **Composants Qt**
   - `QListWidget` pour la liste des bases de données
   - `QLineEdit` pour le nom
   - `QListWidget` pour les sources (dossiers ET fichiers)
   - `QPushButton` pour les actions
   - `QFileDialog.getExistingDirectory()` pour sélection de dossiers
   - `QFileDialog.getOpenFileNames()` pour sélection de fichiers vidéo
     - Filtre : `"Video files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm)"`

3. **Fonctionnalités**
   - Liste des bases existantes avec boutons d'action
   - Création de nouvelle base avec :
     - Dossiers (scannés récursivement)
     - Fichiers individuels (vidéos spécifiques)
   - Modification des sources d'une base existante
   - Dialogs de confirmation pour renommer/supprimer
   - Icônes distinctes pour dossiers (📁) et fichiers (📄)

### Phase 3 : Page Home (Progression)
**Durée estimée : 1 session**

1. **Layout**
   ```
   ┌─────────────────────────────────────────────┐
   │  Loading Database: "my_database"            │
   ├─────────────────────────────────────────────┤
   │  Job 1: Scanning files                      │
   │  [████████████░░░░░░░░] 60% (120/200)       │
   │                                             │
   │  Job 2: Generating thumbnails               │
   │  [████░░░░░░░░░░░░░░░░] 20% (40/200)        │
   ├─────────────────────────────────────────────┤
   │  Activity Log:                              │
   │  > Processing video1.mp4                    │
   │  > Processing video2.mp4                    │
   │  > ...                                      │
   ├─────────────────────────────────────────────┤
   │  [Cancel]                                   │
   └─────────────────────────────────────────────┘
   ```

2. **Composants Qt**
   - `QProgressBar` pour chaque job
   - `QTextEdit` (read-only) pour le log
   - `QTimer` pour rafraîchir l'UI (100ms)
   - Gestion des notifications du backend

3. **Fonctionnalités**
   - Affichage multi-jobs avec progression
   - Log d'activité scrollable
   - Auto-navigation vers /videos quand `DatabaseReady`

### Phase 4 : Page Videos - Structure de base
**Durée estimée : 1-2 sessions**

1. **Layout principal**
   ```
   ┌─────────────────────────────────────────────────────┐
   │ [⟳][Grid/List][🎲][📜] │ Per page: [20 ▼]          │
   ├───────────────┬─────────────────────────────────────┤
   │  FILTERS      │  Stats: 1234 videos | 500GB | 120h │
   │  ┌──────────┐ │  ┌─────────────────────────────────┐│
   │  │ Sources  │ │  │                                 ││
   │  │ [Edit]   │ │  │     VIDEO GRID / LIST           ││
   │  ├──────────┤ │  │                                 ││
   │  │ Grouping │ │  │                                 ││
   │  │ [Set]    │ │  │                                 ││
   │  ├──────────┤ │  └─────────────────────────────────┘│
   │  │ Search   │ │  [◀][◀◀] Page 1/50 [▶▶][▶]         │
   │  │ [____]   │ │                                     │
   │  │ [AND][OR]│ │                                     │
   │  ├──────────┤ │                                     │
   │  │ Sorting  │ │                                     │
   │  │ [Set]    │ │                                     │
   │  └──────────┘ │                                     │
   └───────────────┴─────────────────────────────────────┘
   ```

2. **Composants Qt**
   - `QSplitter` horizontal (sidebar | content)
   - `QToolBar` pour la barre d'outils
   - `QScrollArea` pour le contenu vidéo
   - `QStackedWidget` pour grid/list view

3. **Widgets personnalisés**
   - `VideoCard` - Widget pour afficher une vignette
   - `VideoListItem` - Widget pour une ligne de liste

### Phase 5 : Page Videos - Sidebar et filtres
**Durée estimée : 1-2 sessions**

1. **Source Tree Widget** (`widgets/source_tree.py`)
   ```python
   class SourceTreeWidget(QWidget):
       """
       Arbre de sélection des sources avec pattern select/develop.

       Structure:
       ▼ readable          ○ select  ● develop
         ▼ found           ○ select  ● develop
           ☑ with_thumbnails
           ☐ without_thumbnails
         ▼ not_found       ○ select  ● develop
           ...
       ▼ unreadable        ○ select  ● develop
         ☐ found
         ☐ not_found
       """
   ```
   - `QTreeWidget` avec items personnalisés
   - Radio buttons pour branches (select/develop)
   - Checkboxes pour feuilles
   - Signal `sourcesChanged(list[list[str]])`

2. **Grouping Dialog**
   - `QComboBox` pour le champ (attribut ou propriété)
   - `QRadioButton` group pour le tri
   - `QCheckBox` pour reverse et singletons

3. **Search Widget**
   - `QLineEdit` avec placeholder
   - `QPushButton` AND, OR, Clear

4. **Sorting Dialog**
   - `QListWidget` avec drag & drop
   - Boutons up/down pour réordonner
   - Toggle direction par double-clic

### Phase 6 : Page Videos - Affichage des vidéos
**Durée estimée : 1-2 sessions**

1. **Grid View**
   - `QScrollArea` avec `QWidget` interne
   - `QGridLayout` dynamique
   - `VideoCard` widgets

2. **List View**
   - `QTableWidget` ou `QListWidget` avec items personnalisés
   - Colonnes : Thumbnail, Title, Duration, Size, Resolution, etc.

3. **Video Card Widget**
   ```python
   class VideoCard(QFrame):
       clicked = Signal(int)        # video_id
       doubleClicked = Signal(int)  # video_id

       def __init__(self, video_data: dict):
           # Thumbnail (QLabel with QPixmap)
           # Duration badge
           # Status indicators
           # Title
           # Resolution

       def contextMenuEvent(self, event):
           # Menu contextuel
   ```

4. **Context Menu**
   - Open, Open in VLC, Open folder
   - Mark as watched
   - Rename, Delete entry, Delete file
   - Copy path

### Phase 7 : Page Videos - Dialogs
**Durée estimée : 1-2 sessions**

1. **Video Info Dialog** (`dialogs/video_info_dialog.py`)

   Dialog complet affichant **tous les attributs publics de VideoPattern**.

   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │  Video Information                                    [X]       │
   ├─────────────────────────────────────────────────────────────────┤
   │  ┌─────────────────┐  IDENTIFICATION                           │
   │  │                 │  Title: My Video Title                     │
   │  │   [Thumbnail]   │  File title: my_video.mp4                  │
   │  │                 │  Video ID: 12345                           │
   │  │   1920x1080     │  Filename: /path/to/my_video.mp4           │
   │  └─────────────────┘  Extension: mp4                            │
   │                                                                 │
   │  ┌─── FILE ────────────────────────────────────────────────────┐│
   │  │ Size: 1.5 GiB (1,610,612,736 bytes)                         ││
   │  │ Date modified: 2024-01-15 14:30:22                          ││
   │  │ Entry modified: 2024-01-15 14:35:00                         ││
   │  │ Entry opened: 2024-01-16 10:00:00                           ││
   │  │ Disk: C:                                                    ││
   │  │ Device: Samsung SSD                                         ││
   │  └─────────────────────────────────────────────────────────────┘│
   │  ┌─── VIDEO ───────────────────────────────────────────────────┐│
   │  │ Duration: 1:23:45 (raw: 5025000000 µs)                      ││
   │  │ Resolution: 1920 x 1080                                     ││
   │  │ Frame rate: 23.976 fps (24000/1001)                         ││
   │  │ Bit rate: 8.5 MiB/s                                         ││
   │  │ Bit depth: 8                                                ││
   │  │ Codec: h264 (H.264 / AVC / MPEG-4 AVC)                      ││
   │  │ Container: mp4 (MPEG-4)                                     ││
   │  └─────────────────────────────────────────────────────────────┘│
   │  ┌─── AUDIO ───────────────────────────────────────────────────┐│
   │  │ Codec: aac (AAC - Advanced Audio Coding)                    ││
   │  │ Bit rate: 320 kbps                                          ││
   │  │ Sample rate: 48000 Hz                                       ││
   │  │ Channels: 2                                                 ││
   │  │ Bits: 16                                                    ││
   │  │ Languages: eng, fra                                         ││
   │  └─────────────────────────────────────────────────────────────┘│
   │  ┌─── STATUS ──────────────────────────────────────────────────┐│
   │  │ Found: ✓  Readable: ✓  Watched: ✗  Thumbnails: ✓            ││
   │  │ Discarded: ✗                                                ││
   │  │ Similarity: 42 (group ID)                                   ││
   │  │ Subtitle languages: eng                                     ││
   │  └─────────────────────────────────────────────────────────────┘│
   │  ┌─── PROPERTIES ──────────────────────────────────────────────┐│
   │  │ genre: Action, Adventure                                    ││
   │  │ rating: 8                                                   ││
   │  │ year: 2024                                                  ││
   │  └─────────────────────────────────────────────────────────────┘│
   │  ┌─── ERRORS ──────────────────────────────────────────────────┐│
   │  │ (none)                                                      ││
   │  └─────────────────────────────────────────────────────────────┘│
   │  ┌─── MOVES ───────────────────────────────────────────────────┐│
   │  │ Potential moves: (none)                                     ││
   │  └─────────────────────────────────────────────────────────────┘│
   ├─────────────────────────────────────────────────────────────────┤
   │  [Open] [Open in VLC] [Open Folder] [Toggle Watched] [Close]   │
   └─────────────────────────────────────────────────────────────────┘
   ```

   **Tous les attributs de VideoPattern affichés :**

   | Section | Attributs |
   |---------|-----------|
   | **Identification** | `title`, `file_title`, `meta_title`, `video_id`, `filename`, `extension` |
   | **File** | `size`/`file_size`, `date`/`mtime`, `date_entry_modified`, `date_entry_opened`, `disk`, `device_name`, `driver_id` |
   | **Video** | `length`/`duration`, `width`, `height`, `frame_rate`, `frame_rate_num`, `frame_rate_den`, `bit_rate`, `bit_depth`, `video_codec`, `video_codec_description`, `container_format`, `duration_time_base` |
   | **Audio** | `audio_codec`, `audio_codec_description`, `audio_bit_rate`, `audio_bit_rate_kbps`, `sample_rate`, `channels`, `audio_bits`, `audio_languages` |
   | **Status** | `found`, `readable`/`unreadable`, `watched`, `with_thumbnails`/`without_thumbnails`, `discarded`, `similarity_id`, `similarity`, `subtitle_languages` |
   | **Properties** | `properties` (dict) |
   | **Errors** | `errors` (list) |
   | **Moves** | `moves`, `move_id` |

   **Implémentation :**
   ```python
   class VideoInfoDialog(QDialog):
       def __init__(self, video: VideoPattern, parent=None):
           super().__init__(parent)
           self.video = video
           self._setup_ui()

       def _setup_ui(self):
           layout = QVBoxLayout(self)

           # Scroll area pour tout le contenu
           scroll = QScrollArea()
           scroll.setWidgetResizable(True)
           content = QWidget()
           content_layout = QVBoxLayout(content)

           # Sections
           content_layout.addWidget(self._create_header_section())
           content_layout.addWidget(self._create_file_section())
           content_layout.addWidget(self._create_video_section())
           content_layout.addWidget(self._create_audio_section())
           content_layout.addWidget(self._create_status_section())
           content_layout.addWidget(self._create_properties_section())
           content_layout.addWidget(self._create_errors_section())
           content_layout.addWidget(self._create_moves_section())

           scroll.setWidget(content)
           layout.addWidget(scroll)
           layout.addWidget(self._create_buttons())

       def _create_file_section(self) -> QGroupBox:
           group = QGroupBox("File")
           layout = QFormLayout(group)

           layout.addRow("Size:", QLabel(f"{self.video.size} ({self.video.file_size:,} bytes)"))
           layout.addRow("Date modified:", QLabel(str(self.video.date)))
           layout.addRow("Entry modified:", QLabel(str(self.video.date_entry_modified)))
           layout.addRow("Entry opened:", QLabel(str(self.video.date_entry_opened)))
           layout.addRow("Disk:", QLabel(str(self.video.disk)))
           layout.addRow("Device:", QLabel(self.video.device_name))

           return group
   ```

2. **Rename Dialog**
   - `QInputDialog` ou dialog personnalisé

3. **Confirm Dialogs**
   - `QMessageBox` pour confirmations simples
   - Dialog personnalisé pour actions dangereuses

### Phase 8 : Page Properties
**Durée estimée : 1 session**

1. **Layout**
   ```
   ┌─────────────────────────────────────────────────────┐
   │ [←] Properties Management                           │
   ├─────────────────────────┬───────────────────────────┤
   │  Current Properties     │  Add New Property         │
   │  ┌─────────────────────┐│  Name: [___________]      │
   │  │ Name  │Type│Default ││  Type: [bool ▼]           │
   │  │───────┼────┼────────││  ☐ Multiple values        │
   │  │ genre │str │ ""     ││  ☐ Enumeration            │
   │  │   [✏][⟳][🗑]        ││  Default: [___________]   │
   │  │ rating│int │ 0      ││                           │
   │  │   [✏][⟳][🗑]        ││  [Reset] [Create]         │
   │  └─────────────────────┘│                           │
   └─────────────────────────┴───────────────────────────┘
   ```

2. **Composants Qt**
   - `QTableWidget` pour la liste des propriétés
   - Formulaire avec validation
   - Dialogs pour renommer/supprimer/convertir

### Phase 9 : Tests et polish
**Durée estimée : 1-2 sessions**

1. **Tests unitaires**
   - Tests des widgets isolés
   - Tests des dialogs
   - Tests de l'API bridge

2. **Tests d'intégration**
   - Navigation entre pages
   - Opérations CRUD complètes

3. **Polish**
   - Icônes cohérentes (Material Icons ou Qt icons)
   - Raccourcis clavier
   - Styles et thème

## Composants Qt à utiliser

| Fonctionnalité | Widget Qt |
|----------------|-----------|
| Navigation | `QStackedWidget` |
| Listes | `QListWidget`, `QTableWidget` |
| Arbres | `QTreeWidget` |
| Formulaires | `QLineEdit`, `QComboBox`, `QCheckBox`, `QSpinBox` |
| Boutons | `QPushButton`, `QToolButton` |
| Dialogues | `QDialog`, `QMessageBox`, `QInputDialog`, `QFileDialog` |
| Layout | `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QSplitter` |
| Progression | `QProgressBar` |
| Images | `QLabel` avec `QPixmap` |
| Scroll | `QScrollArea` |
| Menus | `QMenu`, `QMenuBar` |
| Toolbar | `QToolBar` |

## Signaux et slots clés

```python
# Navigation
main_window.page_changed.connect(on_page_changed)

# Database operations
databases_page.database_opened.connect(main_window.show_home_page)
home_page.database_ready.connect(main_window.show_videos_page)

# Video operations
video_card.clicked.connect(videos_page.show_video_info)
video_card.doubleClicked.connect(videos_page.open_video)

# Filters
source_tree.sources_changed.connect(videos_page.apply_sources)
search_widget.search_requested.connect(videos_page.apply_search)
```

## Estimation totale

| Phase | Description | Sessions |
|-------|-------------|----------|
| 1 | Infrastructure | 1 |
| 2 | Page Databases | 1 |
| 3 | Page Home | 1 |
| 4 | Videos - Structure | 1-2 |
| 5 | Videos - Sidebar | 1-2 |
| 6 | Videos - Affichage | 1-2 |
| 7 | Videos - Dialogs | 1 |
| 8 | Page Properties | 1 |
| 9 | Tests et polish | 1-2 |
| **Total** | | **9-13 sessions** |

## Points d'attention

1. **Threading** : Les opérations longues (chargement thumbnails) doivent être dans des `QThread`
2. **Mémoire** : Libérer les `QPixmap` non utilisés pour les grandes collections
3. **Responsive** : Utiliser `QTimer.singleShot()` pour ne pas bloquer l'UI
4. **Cross-platform** : Tester sur Windows et Linux
5. **Styles** : Utiliser `QSS` (Qt Style Sheets) pour un look cohérent

## Dépendances

Déjà présentes dans `pyproject.toml` :
```toml
"pyside6>=6.9.0"
```

### Phase 10 : Sélection multiple et édition batch
**Durée estimée : 1-2 sessions**

1. **Sélection multiple**
   - `QRubberBand` pour sélection par rectangle
   - `Ctrl+Click` pour sélection individuelle
   - `Shift+Click` pour sélection de plage
   - Indicateur de sélection (count badge)

2. **Actions batch**
   - `apply_on_view` - Appliquer sur toute la vue
   - Toolbar avec actions batch quand sélection active

3. **Dialog Batch Edit** (interface 3-colonnes)
   ```
   ┌─────────────────────────────────────────────────────┐
   │  Edit properties for 15 videos                      │
   ├─────────────────┬─────────────────┬─────────────────┤
   │  REMOVE         │  CURRENT        │  ADD            │
   │  ┌───────────┐  │  ┌───────────┐  │  ┌───────────┐  │
   │  │ genre: A  │  │  │ genre: A  │  │  │ [+] genre │  │
   │  │ genre: B  │  │  │ genre: B  │  │  │           │  │
   │  │           │  │  │ rating: 5 │  │  │           │  │
   │  └───────────┘  │  └───────────┘  │  └───────────┘  │
   │  Click to remove│  Current values │  Click to add   │
   └─────────────────┴─────────────────┴─────────────────┘
   ```
   - `QListWidget` pour chaque colonne
   - Drag & drop entre colonnes
   - API : `delete_property_values`, `replace_property_values`

### Phase 11 : Déplacement de fichiers
**Durée estimée : 1 session**

1. **Move Dialog**
   ```
   ┌─────────────────────────────────────────────┐
   │  Move video file                            │
   ├─────────────────────────────────────────────┤
   │  Current: /path/to/video.mp4               │
   │                                             │
   │  Destination folder:                        │
   │  [/new/path/_______________] [Browse...]    │
   │                                             │
   │  ☐ Keep original (copy instead of move)    │
   ├─────────────────────────────────────────────┤
   │  [Cancel]                      [Move]       │
   └─────────────────────────────────────────────┘
   ```

2. **Fonctionnalités**
   - `move_video_file(video_id, directory)`
   - `set_video_moved`, `confirm_move`
   - `confirm_unique_moves` pour batch
   - `QFileDialog.getExistingDirectory()`

### Phase 12 : Similarités
**Durée estimée : 1 session**

1. **Toolbar button** - Trouver vidéos similaires
2. **API**
   - `find_similar_videos()` - Lance la recherche
   - `set_similarities()` - Configure les paramètres

3. **Affichage**
   - Groupement automatique par `similarity_id`
   - Indicateur visuel des vidéos similaires

### Phase 13 : Propriétés avancées
**Durée estimée : 1 session**

1. **Opérations sur valeurs**
   - `fill_property_with_terms` - Extraire termes du titre
   - `apply_on_prop_value` - Actions sur une valeur spécifique
   - `move_property_values` - Déplacer valeurs entre propriétés

2. **Dialog Property Value Editor**
   - Liste toutes les valeurs d'une propriété
   - Actions : renommer, fusionner, supprimer

### Phase 14 : Groupement avancé
**Durée estimée : 1 session**

1. **Classifier avancé**
   - `classifier_focus_prop_val` - Focus sur une valeur
   - `classifier_concatenate_path` - Concaténer chemins
   - `classifier_reverse` - Inverser l'ordre

2. **Sources avancées**
   - `set_video_folders` - Filtrer par dossiers spécifiques
   - Dialog de sélection de dossiers

### Phase 15 : Raccourcis clavier
**Durée estimée : 1 session**

1. **Implémentation**
   - `QShortcut` pour chaque raccourci
   - Affichage dans les tooltips des boutons

2. **Table des raccourcis**
   | Raccourci | Action |
   |-----------|--------|
   | `Ctrl+T` | Sélectionner sources |
   | `Ctrl+G` | Grouper vidéos |
   | `Ctrl+F` | Rechercher |
   | `Ctrl+S` | Trier |
   | `Ctrl+P` | Gérer propriétés |
   | `Ctrl+O` | Ouvrir vidéo aléatoire |
   | `Ctrl+L` | Créer playlist |
   | `Ctrl+R` | Recharger base de données |
   | `←/→` | Page précédente/suivante |
   | `↑/↓` | Groupe précédent/suivant |
   | `Ctrl+A` | Sélectionner tout |
   | `Escape` | Annuler sélection |
   | `Delete` | Supprimer sélection |
   | `Enter` | Ouvrir vidéo sélectionnée |

3. **Dialog Aide raccourcis**
   - `QDialog` listant tous les raccourcis
   - Accessible via `F1` ou menu Help

---

## Estimation totale mise à jour

| Phase | Description | Sessions |
|-------|-------------|----------|
| 1 | Infrastructure | 1 |
| 2 | Page Databases | 1 |
| 3 | Page Home | 1 |
| 4 | Videos - Structure | 1-2 |
| 5 | Videos - Sidebar | 1-2 |
| 6 | Videos - Affichage | 1-2 |
| 7 | Videos - Dialogs | 1 |
| 8 | Page Properties | 1 |
| 9 | Tests et polish (intermédiaire) | 1 |
| 10 | Sélection multiple et batch | 1-2 |
| 11 | Déplacement de fichiers | 1 |
| 12 | Similarités | 1 |
| 13 | Propriétés avancées | 1 |
| 14 | Groupement avancé | 1 |
| 15 | Raccourcis clavier | 1 |
| 16 | Tests finaux et polish | 1-2 |
| **Total** | | **15-20 sessions** |

---

## Points d'attention

1. **Threading** : Les opérations longues (chargement thumbnails) doivent être dans des `QThread`
2. **Mémoire** : Libérer les `QPixmap` non utilisés pour les grandes collections
3. **Responsive** : Utiliser `QTimer.singleShot()` pour ne pas bloquer l'UI
4. **Cross-platform** : Tester sur Windows et Linux
5. **Styles** : Utiliser `QSS` (Qt Style Sheets) pour un look cohérent

## Dépendances

Déjà présentes dans `pyproject.toml` :
```toml
"pyside6>=6.9.0"
```

## Point d'entrée

Ajouter dans `pysaurus/__main__.py` :
```python
if args.interface == "pyside6":
    from pysaurus.interface.pyside6.main import main
    main()
```
