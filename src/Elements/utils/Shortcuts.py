import imgui

showGUI_text = True
collapseGUI_text = True
GUItext_x = 10
GUItext_y = 100
GUItext_width = 560 # wide enough for the hard-wrapped lines the descriptions already carry
def displayGUI_text(text:str):
    displayShortcutsGUI() # hack to ensure function is always on the main loop without calling it from the example
    global showGUI_text, collapseGUI_text
    # imgui.new_frame()
    if  showGUI_text:
        imgui.core.set_next_window_collapsed(collapseGUI_text, imgui.FIRST_USE_EVER)
        ###### a starting width is what gives text_wrapped() below something to wrap against; ######
        ###### left to auto-fit, the first frame has no width yet and the text ends up a       ######
        ###### narrow column. 0 height keeps the height auto-fitting to the text.              ######
        imgui.set_next_window_size(GUItext_width, 0, imgui.FIRST_USE_EVER)
        collapseGUI_text,showGUI_text = imgui.begin("Example Description", True)
        ###### do this so we can be able to move the window after it was collapsed #########
        #######                         and we re open it                           #########
        if collapseGUI_text:
            imgui.set_window_position(GUItext_x,GUItext_y,imgui.FIRST_USE_EVER)
        else:
            imgui.set_window_position(GUItext_x,GUItext_y,imgui.FIRST_USE_EVER)
        # wraps at the content edge, so narrowing the window (or the dock column it sits in) reflows
        # the description instead of clipping it
        imgui.text_wrapped(text)
        imgui.end()

    
show_shortcuts_window = False
shortcuts_x = 10
shortcuts_y = 140
shortcuts_width = 460
collapseShortcutsWindow = True

#: (keys, what they do). Kept as data rather than pre-padded strings so the two columns can be
#: laid out at runtime -- padding spaces cannot survive a window narrow enough to wrap.
general_shortcuts = [
    ("F", "Toggle Wireframe"),
]
camera_shortcuts = [
    ("Drag", "Look around (position stays put)"),
    ("W / S", "Fly forward / back along the view"),
    ("A / D", "Fly left / right"),
    ("Q / E", "Lower / raise (target stays put)"),
    ("Space", "Aim back at the origin (0,0,0)"),
    ("Scroll or + / -", "Fly speed up / down (see terminal)"),
    ("Shift + Drag", "Pan"),
    ("Ctrl + Drag", "Zoom along the view"),
]

#: how far past the longest key the descriptions start
key_column_gap = 20

def _displayShortcutRows(rows):
    """Draw `key -- description` rows, wrapping the descriptions when the window gets narrow.

    text_wrapped() continues on the x it started at, so a description that wraps stays inside its
    own column instead of running back under the keys. Once the description column gets too narrow
    to be worth aligning, the description drops to its own indented line -- still readable, where a
    squeezed two-column layout would be a stack of single words.

    Both groups measure against every row, so the general and camera keys share one column and the
    two switch to stacked together; alignment that held in one group but not the other would read
    as a broken layout.
    """
    all_rows = general_shortcuts + camera_shortcuts
    key_column = max(imgui.calc_text_size(key).x for key, _ in all_rows) + key_column_gap
    # two lines for the longest description is the point where a second column stops paying off
    min_description_width = max(imgui.calc_text_size(text).x for _, text in all_rows) / 2

    stacked = None
    for key, description in rows:
        imgui.bullet() # bullet() leaves the cursor on the same line, so the key lands next to it
        if stacked is None:
            # Decided here rather than from the window width: measured after the bullet, this is the
            # width the description itself will get -- window padding, indent and any scrollbar
            # already taken out. Guessing at those is what leaves a 70px column looking "aligned".
            stacked = imgui.get_content_region_available_width() - key_column < min_description_width
        description_x = imgui.get_cursor_pos_x() + key_column
        # wrapped too: in the stacked case the window can be narrower than a key like
        # "Scroll or + / -". In the aligned case a key always fits its column, so this never fires.
        imgui.text_wrapped(key)
        if stacked:
            imgui.indent()
            imgui.text_wrapped(description)
            imgui.unindent()
        else:
            imgui.same_line(description_x)
            imgui.text_wrapped(description)

def displayShortcutsGUI():

    global show_shortcuts_window,shortcuts_x,shortcuts_y,collapseShortcutsWindow
    if show_shortcuts_window:
        imgui.core.set_next_window_collapsed(collapseShortcutsWindow, imgui.FIRST_USE_EVER)
        # as with the description window, wrapping needs a starting width to wrap against
        imgui.set_next_window_size(shortcuts_width, 0, imgui.FIRST_USE_EVER)
        collapseShortcutsWindow, show_shortcuts_window = imgui.begin("Shortcuts", True)

        ###### do this so we can be able to move the window after it was collapsed #########
        #######                         and we re open it                           #########
        if collapseShortcutsWindow:
            imgui.set_window_position(shortcuts_x,shortcuts_y,imgui.FIRST_USE_EVER)
        else:
            imgui.set_window_position(shortcuts_x,shortcuts_y,imgui.FIRST_USE_EVER)

        imgui.text_wrapped("List of shortcuts:")
        _displayShortcutRows(general_shortcuts)

        imgui.text_wrapped("Camera -- hold RIGHT mouse button:")
        _displayShortcutRows(camera_shortcuts)
        imgui.text_wrapped("(nothing moves the camera unless the right button is held)")
        imgui.end()