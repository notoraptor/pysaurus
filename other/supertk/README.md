# Tkinter info and small tutorial

## Virtual events

Some widgets generate virtual events, which have syntax `<<event>>`.

It is possible to create virtual event:
```python
import tkinter
root = tkinter.Tk()
root.event_generate("<<MyOwnEvent>>")
```

## Sizes

Screen distances such as width and height are usually specified as a 
number of pixels. You can also specify them via one of several 
suffixes. For example, `350` means 350 pixels, `350c` means 350 
centimeters, `350m` means 350 millimeters, `350i` means 350 inches, 
and `350p` means 350 printer's points (1/72 inch).

## Widget class

### winfo_*() methods

`winfo_class`:
- a class identifying the type of widget, e.g., 
  TButton for a themed button

`winfo_children`:
- a list of widgets that are the direct children of a widget
  in the hierarchy

`winfo_parent`:
- parent of the widget in the hierarchy

`winfo_toplevel`:
- the toplevel window containing this widget

`winfo_width, winfo_height`:
- current width and height of the widget; 
  not accurate until it appears onscreen

`winfo_reqwidth, winfo_reqheight`:
- the width and height that the widget 
  requests of the geometry manager (more on this shortly)

`winfo_x, winfo_y`:
- the position of the top-left corner of the widget 
  relative to its parent

`winfo_rootx, winfo_rooty`:
- the position of the top-left corner of the widget 
  relative to the entire screen

`winfo_vieweable`:
- whether the widget is displayed or hidden 
  (all its ancestors in the hierarchy must be viewable 
  for it to be viewable) 

### Frame

**Padding**
```python
f['padding'] = 5           # 5 pixels on all sides
f['padding'] = (5,10)      # 5 on left and right, 10 on top and bottom
f['padding'] = (5,7,10,12) # left: 5, top: 7, right: 10, bottom: 12
```

**Borders**

- `borderwidth`: int (default 0)
- `relief`: str, enumeration: `flat` (default), `raised`, `sunken`, `solid`, `ridge`, `groove`

### Label

**`compound`**
- `none` (default, display only image or text)
- `text` (text only)
- `image` (image only)
- `center`, `top`, `left`, `bottom`, `right` (text position around image)

**`font`**

str. Some predefined fonts:
- `TkDefaultFont`: Default for all GUI items not otherwise specified.
- `TkTextFont`: Used for entry widgets, listboxes, etc.
- `TkFixedFont`: A standard fixed-width font.
- `TkMenuFont`: The font used for menu items.
- `TkHeadingFont`: A font for column headings in lists and tables.
- `TkCaptionFont`: A font for window and dialog caption bars.
- `TkSmallCaptionFont`: Smaller captions for subwindows or tool dialogs.
- `TkIconFont`: A font for icon captions.
- `TkTooltipFont`: A font for tooltips.

### Button

Buttons take the same `text`, `textvariable` (rarely used), `image`, 
and `compound` configuration options as labels. These control 
whether the button displays text and/or an image.

`invoke()`
- Invoke the button command callback.

**disabled**
```python
b.state(['disabled'])          # set the disabled flag
b.state(['!disabled'])         # clear the disabled flag
b.instate(['disabled'])        # true if disabled, else false
b.instate(['!disabled'])       # true if not disabled, else false
b.instate(['!disabled'], cmd)  # execute 'cmd' if not disabled
```


## Styles

```python
s = ttk.Style()
s.configure('Danger.TFrame', background='red', borderwidth=5, relief='raised')
ttk.Frame(root, width=200, height=200, style='Danger.TFrame').grid()
```
