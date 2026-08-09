import imgui

showGUI_text = True
collapseGUI_text = True
GUItext_x = 10
GUItext_y = 100
def displayGUI_text(text:str):
    displayShortcutsGUI() # hack to ensure function is always on the main loop without calling it from the example
    global showGUI_text, collapseGUI_text
    # imgui.set_next_window_size(100.0, 200.0)
    # imgui.new_frame()
    if  showGUI_text:
        imgui.core.set_next_window_collapsed(collapseGUI_text, imgui.FIRST_USE_EVER)
        collapseGUI_text,showGUI_text = imgui.begin("Example Description", True)
        ###### do this so we can be able to move the window after it was collapsed #########
        #######                         and we re open it                           #########
        if collapseGUI_text:
            imgui.set_window_position(GUItext_x,GUItext_y,imgui.FIRST_USE_EVER)
        else:
            imgui.set_window_position(GUItext_x,GUItext_y,imgui.FIRST_USE_EVER)
        imgui.text(text)
        imgui.end()

    
show_shortcuts_window = False
shortcuts_x = 10
shortcuts_y = 140
collapseShortcutsWindow = True
def displayShortcutsGUI():
    
    global show_shortcuts_window,shortcuts_x,shortcuts_y,collapseShortcutsWindow
    if show_shortcuts_window:
        imgui.core.set_next_window_collapsed(collapseShortcutsWindow, imgui.FIRST_USE_EVER)
        collapseShortcutsWindow, show_shortcuts_window = imgui.begin("Shortcuts", True)
      
        ###### do this so we can be able to move the window after it was collapsed #########
        #######                         and we re open it                           #########
        if collapseShortcutsWindow:
            imgui.set_window_position(shortcuts_x,shortcuts_y,imgui.FIRST_USE_EVER)
        else:
            imgui.set_window_position(shortcuts_x,shortcuts_y,imgui.FIRST_USE_EVER)

        imgui.text("List of shortcuts:")

        imgui.bullet_text("Toggle Wireframe:                F")

        imgui.text("Camera -- hold RIGHT mouse button:")
        imgui.bullet_text("Drag:                            Look around (position stays put)")
        imgui.bullet_text("W / S:                           Fly forward / back along the view")
        imgui.bullet_text("A / D:                           Fly left / right")
        imgui.bullet_text("Q / E:                           Lower / raise (target stays put)")
        imgui.bullet_text("Space:                           Aim back at the origin (0,0,0)")
        imgui.bullet_text("Scroll or + / -:                 Fly speed up / down (see terminal)")
        imgui.bullet_text("Shift + Drag:                    Pan")
        imgui.bullet_text("Ctrl + Drag:                     Zoom along the view")
        imgui.text("(nothing moves the camera unless the right button is held)")
        imgui.end()