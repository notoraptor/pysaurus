Database DBNAME on disk
- Folder DBNAME
  - Folders list file DBNAME.txt
  - JSON database file DBNAME.json
  - Thumbnails *.png
 
Tags definition
- Tag name
- Tag dimension: 1 | multiple
- Tag type: bool | int | unsigned | float | string
- Values: any | enum
  - For enum, specify list of allowed values
- default value

- Default tags
  - Category (multiple string any)

- Special tags
  - Note (1 unsigned enum(0, 1, 2, 3, 4, 5))

Page Welcome
 - Button create a new database -> page Create database
 - Button open an existing database
   - Open a folder dialog to select existing database folder
   - If database folder is invalid (no list file), display an alert
   - Else -> page Open database

Page Create database
- Button back -> page Welcome
- Input database name
- List *database_folders*: database folders. For each entry:
  - Button remove folder: remove entry from list
- Button add new folder:
  - Open a folder dialog to select an existing videos directory
  - Display an alert if selected path is not a valid existing folder
  - Else, add folder to list database_folders
- Button create database
  - Create database structure on disk. If an error occurs:
    - try to delete database structure, collect any new errors
    - display errors with an alert
  - Else: load_database()

Page Open database
- Button back -> page Welcome
- Label {database name}
- List *database_folders*: database folders. 
  - Fill list with database folders
  - For each entry:
    - Button remove folder: remove entry from list
- Button add new folder:
  - Open a folder dialog to select an existing videos directory
  - Display an alert if selected path is not a valid existing folder
  - Else, add folder to list database_folders
- Button load database
  - load_database()

Function load_database():
  - (see current database loading code)
    - collect all potential errors
  - Display page Database with errors collected

Action Save database now:
- Save database
- Collect potential errors and write them into errors report

Action Close database:
- Dialog to confirm
- If confirmed:
- Save database:
  - If errors occured while saving:
    - Write errors in errors report
    - Ask user if he still wants to close database
    - If user does not confirm, do nothing
    - Else:
      - Unload database from memory
      - Go back to page Welcome
  - Else
    - Unload database from memory
    - Go back to Page Welcome
- Unload database from memory

Action Delete database completely:
- Dialog to confirm
- If confirmed:
- Unload database from memory (do not save it)
- Delete database from disk
  - If errors occur, display a dialog box, and tell user he can manually 
    delete database folder to remove database
- Go back to page Welcome

Feature Add new tag
- Input tag name
- Radio buttons: tag dimensions: one, many
- Radio buttons: tag type: bool, int, unsigned, float, string
- Form add an allowed value
  - Input value
  - Button add: add value to list of allowed values
- List of allowed values (let empty to allow all values). For each value:
  - Button remove: remove value from list
- Default value (optional)
  - (if allowed values) selection with options = allowed values
  - (else) input
- Button cancel: close feature
- Button add:
  - If tag settings are invalid, alert
  - Else, add tag to database

Feature Remove tag
- Dialog to confirm
- If confirmed, delete tag values from database and delete tag
Feature Modify tag
- bool
  - int, unsigned, float: true -> 1, false -> 0
  - string: true -> "1", false -> "0"
- int
  - bool: 0 -> false, else true
  - unsigned: < 0 -> 0, else value
  - float: value
  - string: string representation
- unsigned
  - bool: 0 -> false, else true
  - int, float: value
  - string: string representation
- float
  - bool: 0 -> false, else true
  - int: ceil(value)
  - unsigned: < 0 -> 0, else ceil(value)
  - string: string representation
- string
  - bool: "" -> false, else true
  - int: int(value) else 0
  - unsigned: unsigned(value) else 0
  - float: float(value) else 0

Action Manage tags
- Button Add new tag -> feature Add new tag
- List of tags. For each tag:
  - Label tag name, tag dimension, tag type, tag values
  - Button remove -> feature Remove tag
  - Button modify -> feature Modify tag

Action manage a specific tag
- Select tag to manage
- (if tag type is string) Checkbox sort values by string length
- Select sort direction:
  - ascending
  - descending
- List of values for selected tag. For each tag:
  - Checkbox to select it
  - value
  - Number of videos with this value
  - Button rename:
    - Dialog box
      - Input new name
      - Button cancel: close dialog
      - Button rename:
        - If new name matches existing value, merge them
        - Else, rename it
        - Close dialog
- Button delete selected values:
  - Dialog to confirm
  - If confirmed, delete selected values from database

Page Database
- Page title {database name}
- Menu bar
  - Menu File
    - Action Save database now
    - Action Close database
    - Action Delete database completely
  - Menu database
    - Action Manage tags -> ...
    - Action Manage a specific tag (remove/merge some tag values)
    - Action Manage folders (add/remove folders from database)
    - Menu Display videos with:
      - Action same name
      - Action same size
      - Action same duration
      - Action same tags values
      - Action same values for specific tags
    - Action Display potential similar videos
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
