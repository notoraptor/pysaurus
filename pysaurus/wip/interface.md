Database DBNAME on disk
- Folder DBNAME
  - Folders list file DBNAME.txt
  - JSON database file DBNAME.json
    - videos: array of videos
    - tags: array of tags
    - user_queries: array of user-defined queries
  - Thumbnails *.png

Tags
- Définition
  - Name: string
  - Dimension: one | many
  - Type: bool | int | unsigned | float | string
  - Values: null | [allowed values]
    - If empty, any value is accapted.
  - default null | value
    - If dimension is one, value must be null or one value
    - If dimension is many, value must be null or a list of values
- Default tags
  - Category (many string null null)
- Special tags
  - Note (one unsigned [(0, 1, 2, 3, 4, 5] 0)

Page Welcome
 - Button create a new database -> page **Create database**
 - Button open an existing database
   - Open a folder dialog to select existing database folder
   - If database folder is invalid (no list file), display an alert
   - Else -> page **Open database**

Page Create database
- Button back -> page **Welcome**
- Input database name
- **FolderList** (empty)
- Button create database
  - Create database structure on disk. If an error occurs:
    - try to delete database structure, collect any new errors during deletion
    - display errors with an alert
  - Else: **load_database()**

Page Open database
- Button back -> page **Welcome**
- Label database name
- **FolderList** (filled with folder of loaded database)
- Button load database -> **load_database()**

Page Database
- Page title: database name
- Menu bar
  - Menu Database
    - Action Refresh database now: -> **load_database()**
    - Action **Save database now**
    - Action **Close database**
    - Action **Delete database completely**
  - Menu database
    - Action **Manage tags** -> ...
    - Action **Manage tag values** (remove/merge some tag values) -> ...
    - Action **Manage folders** (add/remove folders from database) -> ...
    - Menu Display videos with:
      - Action a same property ... -> **classify for a property**
      - Action a same tag ... -> **classify for a tag**
      - Action **same properties** -> ...
      - Action **same tags** -> ...
      - Action **same properties and tags** -> ...
      - Action same specific properties and tags ... -> **classify for selected properties and tags**
      - Action **same name** (shortcut)
      - Action **same size** (shortcut)
      - Action **same duration** (shortcut)
    - Action **Display potential similar videos**
    - ...
- Search bar
  - Input search
  - Radio buttons:
    - exact expression
    - any word
    - all words (default)
  - Option case sensitive (default insensitive)
  - Button search ...
  - Button advanced search ...
- Tab errors (if errors)
  - errors report
    - Display a report about errors occured while loading database or videos, 
      from oldest (top) to newest errors.
  - Button clear:
    - clear errors report
- Tab display: display videos for a selection
  - display title bar
    - Label display description
    - Button manage display columns ...
  - list of videos for current diplay.
  - View for currently selected video(s).
    - (if 0 videos selected): informations about videos of current selection
      - Label number of folders
      - Label number of files
      - Label total size
      - Label total duration
    - (if 1 video selected)
      - Button open video
      - Button delete video from disk
      - Label filename
      - Label title
      - Label $size, $container ($videoCodec, $audioCodec)
      - Label $width X $height, $frameRate / sec
      - Label $duration, $sampleRate Hz, $bitrate / sec
      - Section tags
          - button add a tag ...
          - for each defined tag:
            - tag name, tag values
            - button modify ...
            - button delete ...
      - (if wwarnings) list of warnings
      - diaplay thumbnail
    - (if many videos selected)
      - Label number of selected videos
      - Label total size
      - Label containers
      - Label video codecs
      - Label audio codecs
      - Label total duration, min duration, max duration
      - Label min width, max width
      - Label min height, max height
      - Label min framerate, max framerate
      - Label min samplerate, max samplerate
      - Label min bitrate, max bitrate
      - Section tag
        - Button add common tag ...
        - For each tag present in any selected video:
          - tag name, all tags values in selected videos
          - button modify ...
          - button delete ...
- Status bas:
  - Label database name
  - Label number of folders
  - Label number of files
  - Label total size in highest unit (To, Go, Mo or Ko)
  - Label total diration (hours + minutes + secondes + microseconds)
  - Label latest saved time

FolderList
- entries. For each entry:
  - Button remove: remove entry from list
- Button add new:
  - Open a folder dialog to select an existing videos directory
  - Display an alert if selected path is not a valid existing folder
  - Else, add folder to list database_folders

Function load_database():
  - (see current database loading code)
    - collect all potential errors
  - -> page **Database** (with errors collected)

Action Save database now:
- Save database
- Collect potential errors and write them into errors report
- If errors occured, display errors report

Action Close database:
- Dialog to confirm
- If confirmed:
- Save database:
  - If errors occured while saving:
    - Write errors in errors report
    - Ask user if he still wants to close database
    - If user confirms:
      - Unload database from memory
      - -> page **Welcome**
  - Else
    - Unload database from memory
    - -> Page **Welcome**
- Unload database from memory

Action Delete database completely:
- Dialog to confirm
- If confirmed:
  - Unload database from memory (do not save it)
  - Delete database from disk
    - If errors occur, display a dialog box, and tell user he can manually 
      delete database folder to remove database
  - -> page **Welcome**

Feature Manage tags
- Button **Add new tag** -> ...
- List of tags. For each tag:
  - Labels: tag name, tag dimension, tag type, tag values, tag default value
  - Button remove:
    - Dialog to confirm. If confirmed:
      - Delete tag values from database
      - Delete tag from databse
      - Delete tag from this list
  - Button modify -> feature **Modify tag**

Feature Manage tag values
- Select tag to manage
- Sort bar
  - (if tag type is string) Checkbox sort values by string length
  - Select sort direction:
    - ascending
    - descending
- List of values for selected tag. For each value:
  - Checkbox to select it
  - Label value
  - Label to telle if it's a current default value
  - Label number of videos with this value
  - Button rename:
    - Dialog box:
      - Label tag name
      - Label current value to rename
      - Input new name
      - Button cancel: close dialog
      - Button rename:
        - Change current value name with new given name everywhere current value appears in videos
        - Close dialog
- Button delete selected values:
  - Dialog to confirm
  - If confirmed, delete selected values from database and from list


Feature Add new tag
- Input tag name
- Radio buttons: tag dimensions: one, many
- Radio buttons: tag type: bool, int, unsigned, float, string
- Section allowed values (leave empty to allow any value)
  - List of allowed values. For each value:
    - Button remove: remove value from list
    - (if dimension is one) radio button: default value: set as default value
    - (if dimension is many) checkbox: default value: add to default values
  - Form add an allowed value
    - Input value
    - Button add: add value to list of allowed values
- (if no allowed values)
  - (if dimension is one) Input default value (optional)
  - (if dimension is many) List of default values
    - Default values list. For each value:
      - Button remove: remove value from list
    - Input new default value + button add: add value to list
- Button cancel: close feature
- Button add:
  - If tag settings are invalid, alert
  - Else, add tag to database

Feature Modify tag
- Bar
  - Label "Name: {current name}"
  - Input tag name (default: current tag name)
- Bar
  - Label "Dimension: {current dimension}"
  - Select [one, many] (default: current tag dimension)
- Section "Allowed values: {current allowed values separated by commas, or all}"
  - List of allowed values. For each value:
    - Button remove: remove value from list
    - (if dimension is one) radio button: default value: set as default value
    - (if dimension is many) checkbox: default value: add to default values
  - Form Add an allowed value
    - Input value
    - Button add: add value to list of allowed values
- (if no allowed values)
  - (if dimension is one) Bar
    - Label "default value: {current default value, or none}"
    - Input default value (default: current tag default value)
  - (if dimension is many) Section "default values: {current default values, or none}"
    - List of default values. For each value:
      - Button remove: remove value from list
    - Input new default value + button add: add value to list
- Select "current type: {current type}" (default: current tag type)
- (if new type requires a default value for conversion) Input "Replace unconvertible old values with:"
- Button cancel: close feature
- Button reset: reload feature will current tag properties
- Button update:
  - name
    - If new name matchs existing tag name:
      - Either both tags must have exactly same other properties (dimension, allowed values, default values, type)
        - Ask user to confirm tags will be merged
        - If confirmed, merge tags
      - Else, unable to rename:
        - Tell user he must either choose another new name or make sure both tags have exactly same properties before
          merging
  - dimension
    - many -> one: tag must have only 1 value per video where he appears, otherwise unable to change dimension
  - allowed values
    - null -> allowed values
      - if some videos have disallowed values based on new given allowed values, ask user if he wants to remove
        disallowed values from videos
      - if confirmed, remove disallowed values and update tag
      - otherwise, cannot set allowed values
  - default value
  - type
    - bool
      - int, unsigned, float: false -> 0, true -> 1
      - string: false -> "0", true -> "1"
    - int
      - bool: 0 -> false, else true
      - unsigned:
        - required default_value (= 0) for negative values
        - if value < 0, then default_value, else value
      - float: same
      - string: string representation
    - unsigned
      - bool: 0 -> false, else true
      - int, float: same
      - string: string representation
    - float
      - bool: 0 -> false, else true
      - int: int(value) (decimal part is truncated)
      - unsigned:
        - required default_value (= 0) for negative values
        - if value < 0, then default_value, else int(value)
      - string: string representation
    - string
      - bool: "" -> false, else true
      - int, unsigned, float:
        - required default_value (= 0) for un-parsable strings
        - (for int and unsigned) parse_fn = parseInt
        - (for float) parse_fn = parseFloat
        - parse_fn(value) or default_value
  
Feature Manage folders
- **FolderList**
- Checkbox refresh database on update
- Button cancel: close feature
- Button update
  - Update database folders list
  - If refresh databse on update: -> **load_database()**


NB:
- `a in {x, y, z} <=> a == x OR a == y OR a == Z`
- `a not in {x, y z} <=> a != x AND a != y AND a != z`

DatabaseQueryBuilder
- List of query parts. For each part:
  - Button remove: remove part from query
  - Button modify:
    - (if query piece) -> **Query piece** (modify)
    - (if query group) -> **Query group** (modify) 
- Button add a query piece -> **Query piece** (add)
- Button add a query group -> **Query group** (add)

Database Query Group (action=add|modify)
- Select query group type: AND | OR | XOR
- Section query pieces:
- List of query pieces. For each piece:
  - Button remove: remove piece from group
  - Button modify: -> **Query piece** (modify)
- Button add a query piece: -> **Query piece** (add)
- Button {action}
  - (if action == add) add query group to given list
  - (if add modify) Return modified query group

Database Query Piece (action=add|modify)
- Select tag or property
- Select test type: 
  * ==
  * !=
  * <
  * <=
  * \>
  * \>=
  * "is defined"
  * "is undefined"
  * (if field type is string) contains exactly
  * (if field type is string) contains any of
  * (if field type is string) contains all of
  * (if field type is string) does not contains exactly
  * (if field type is string) contains none of
  * (if field type is string) does not contains any of
- Section test values
  - (if "contains" in test type)
    - Input text to search, words separated with spaces
  - (else if "defined" not in test type) Bar:
    - Select value to check: {set of all current field values used in videos}
- Button {action}:
  - (if action == add) Add query piece to given list
  - (if action == modify) Return modified query piece
 
Function classify_videos(properties=None, tags=None):
- NB: database classifier, keywords:
  - none: None
  - all: []
  - some: [...]
- if properties is None and tags is None:
  - return []
- if properties is None and tags is []:
  - same values for all tags
- if properties is None and tags is [...]:
  - same values for given tags
- if properties is [] and tags is None:
  - same values for all properties
- if properties is [] and tags is []:
  - same values for all properties and tags
- if properties is [] and tags is [...]:
  - same values for all properties and given tags
- if properties is [...] and tags is None:
  - same values for given properties
- if properties is [...] and tags is []:
  - same values for given properties and all tags
- if properties is [...] and tags is [...]:
  - same values for given properties and tags
- return classified videos: list of dictionaries, for each dictionary:
  - properties: dictionary mapping a property name to property value common for these videos
  - tags: dictionary mapping a tag name to tag value(s) common for these videos
  - videos: list of videos

Function display_classification(params)
- results = classify_videos(**params)
- Set display with results

Feature classify for a property
- Select property_name
- Button cancel: close feature
- Button search: -> display_classification(properties=[property_name])

Feature classify for a tag
- Select tag_name
- Button cancel: close feature
- Button search: -> display_classification(taga=[tag_name])

Action same properties
- display_classification(properties=[])

Action same tags
- display_classification(tags=[])

Action same properties and tags
- display_classification(properties=[], tags=[])

Feature classify for selected properties and tags:
- List of properties. For each property:
  - Checkbox to select it
  - Property name
- List of tag. For each tag:
  - Checkbox to select if
  - Tag name
- Button cancel: close feature
- Button search: display_classification(properties=[selected properties], tags=[selected tags])

Action same name:
- display_classification(properties=[title])

Action same size:
- display_classification(properties=[size])

Action same duration:
- display_classification(properties=[duration])

Action Display potential similar videos (TODO)
- results_name = classify_videos(properties=[title])
- results_size = classify_videos(properties=[size])
- results_duration = classify_videos(properties=[duration])
- TODO merge ...