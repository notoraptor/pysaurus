Database DBNAME on disk
- Folder DBNAME
  - folders list file DBNAME.txt *
  - JSON database file DBNAME.json
  - Thumbnails *.png
 
 Page Welcome
 - Button create a new database -> page Create database
 - Button open an existing database
   - Open a folder dialog to select existing database folder
   - If database folder is invalid (no list file), display an alert
   - Else -> page Open database

Page Create database
- Button back -> page Welcome
- Text input database name
- List *database_folders*: database folders. For each entry:
  - Button remove folder: remove entry from list
- Button add new folder:
  - Open a folder dialog to select an existing directory to look videos for
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
  - Open a folder dialog to select an existing directory to look videos for
  - Display an alert if selected path is not a valid existing folder
  - Else, add folder to list database_folders
- Button load database
  - load_database()


Function load_database():
  - (see current database loading code)
    - collect all potential errors
  - Display page Database with errors collected


Page Database
- Page title {database name}
- Menu bar
  - Menu File
    - Action Save database now:
      - Save database; collect potentiel errors and alert them
    - Action Close database:
      - Dialog to confirm
      - If confirmed:
        - Save database:
          - If errors occured while saving:
            - Display errors in a dialog box and ask if user still wants to close database
            - If user confirms:
              - Unload database from memory
              - Go back to page Welcome
          - else
            - Unload database from memory
            - Go back to Page Welcome
        - Unload database from memory
    - Action Delete database completely:
      - Dialog to confirm
      - If confirmed:
        - Delete database from disk
        - Go back to page Welcome
  - Menu database
    - Manage tags (add/remove/convert tags)
    - Manage a specific tag (remove/merge some tag values)
    - Manage folders (add/remove folders from database)
    - ...
- Status bas:
  - Label database name
  - Label number of folders
  - Label number of files
  - Label total size in highest unit (To, Go, Mo or Ko)
  - Label total length (hours + minutes + secondes + microseconds)
  - Label latest saved time
