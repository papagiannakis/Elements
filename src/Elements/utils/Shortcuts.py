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
        
        imgui.bullet_text("Toggle Wireframe                 F")
        imgui.bullet_text("Vertical Scroll:                 Vertical camera translate")
        imgui.bullet_text("Horizontal Scroll:               Vertical camera translate")
        imgui.end()