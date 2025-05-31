Python 3.8, Windows, Linux.

Run with default GUI (CEF on Windows, Qt web view elsewhere)

`python -m pysaurus`

Run with Qt web view QUI

`python -m pysaurus qt`

Run with CEF GUI (on Windows only)

`python -m pysaurus cef`

Find used flet classes:
```bash
# -o, --only-matching
$ grep -E "ft\.[A-Z][a-zA-Z0-9_]+" -owr `find -type f | egrep "\.py$"`| cut -d":" -f 2 | sort -u > out.log
```

Used flet classes:
```
ft.AlertDialog
ft.AppView
ft.ButtonStyle
ft.Checkbox
ft.Column
ft.Container
ft.Control
ft.ControlEvent
ft.CrossAxisAlignment
ft.ElevatedButton
ft.FilePicker
ft.FilePickerResultEvent
ft.FontWeight
ft.IconButton
ft.Image
ft.KeyboardEvent
ft.ListView
ft.MainAxisAlignment
ft.Markdown
ft.MarkdownExtensionSet
ft.MenuBar
ft.MenuItemButton
ft.MenuStyle
ft.Page
ft.ProgressBar
ft.ProgressRing
ft.Radio
ft.RadioGroup
ft.RoundedRectangleBorder
ft.Row
ft.ScrollMode
ft.SubmenuButton
ft.Text
ft.TextField
ft.TextStyle
```

Coverage for videre:

```
pytest --cov=videre --cov-report=term-missing --cov-report=html videre_tests
```
