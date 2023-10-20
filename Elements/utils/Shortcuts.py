import imgui,sdl2

leftAlt_Key = sdl2.SDLK_LALT
rightAlt_Key = sdl2.SDLK_RALT
leftShift_Key = sdl2.SDLK_LSHIFT
rightShift_Key = sdl2.SDLK_RSHIFT
ctrl_Key = sdl2.SDLK_LCTRL

#change this to one of the above for the shortcuts
shortcut_hotKey = leftAlt_Key

showGUI_text = True
collapseGUI_text = True
GUItext_x = 10
GUItext_y = 270
def displayGUI_text(text:str):
    displayShortcutsGUI() # hack to ensure function is always on the main loop without calling it from the example
    global showGUI_text, collapseGUI_text
    # imgui.set_next_window_size(100.0, 200.0)
    # imgui.new_frame()
    if  showGUI_text:
        imgui.core.set_next_window_collapsed(not collapseGUI_text)
        collapseGUI_text,showGUI_text = imgui.begin("Example Description", True)
        ###### do this so we can be able to move the window after it was collapsed #########
        #######                         and we re open it                           #########
        if collapseGUI_text:
            imgui.set_window_position(GUItext_x,GUItext_y,imgui.ONCE)
        else:
            imgui.set_window_position(GUItext_x,GUItext_y)
        imgui.text(text)
        imgui.end()

    
show_shortcuts_window = False
shortcuts_x = 10
shortcuts_y = 400
collapseShortcutsWindow = True
def displayShortcutsGUI():
    
    global show_shortcuts_window,shortcuts_x,shortcuts_y,collapseShortcutsWindow
    if show_shortcuts_window:
        imgui.core.set_next_window_collapsed(not collapseShortcutsWindow)
        collapseShortcutsWindow, show_shortcuts_window = imgui.begin("Shortcuts", True)
      
        ###### do this so we can be able to move the window after it was collapsed #########
        #######                         and we re open it                           #########
        if collapseShortcutsWindow:
            imgui.set_window_position(shortcuts_x,shortcuts_y,imgui.ONCE)
        else:
            imgui.set_window_position(shortcuts_x,shortcuts_y)

        imgui.text("List of shortcuts:")
        
        imgui.bullet_text("Toggle Wireframe                 Alt+F")
        imgui.bullet_text("Vertical Scroll:                 Vertical camera translate")
        imgui.bullet_text("Horizontal Scroll:               Vertical camera translate")
        
        imgui.text("When node is selected:")
        #with imgui.indent():
        imgui.bullet_text("Positive translation on x-axis   W")
        imgui.bullet_text("Negative translation on x-axis   Alt+W")
        imgui.bullet_text("Positive translation on y-axis   E")
        imgui.bullet_text("Negative translation on y-axis   Alt+E")
        imgui.bullet_text("Positive translation on z-axis   R")
        imgui.bullet_text("Negative translation on z-axis   Alt+R")

        imgui.bullet_text("Positive rotation on x-axis      T")
        imgui.bullet_text("Negative rotation on x-axis      Alt+T")
        imgui.bullet_text("Positive rotation on y-axis      Y")
        imgui.bullet_text("Negative rotation on y-axis      Alt+Y")
        imgui.bullet_text("Positive rotation on z-axis      U")
        imgui.bullet_text("Negative rotation on z-axis      Alt+U")

        imgui.bullet_text("Scale up on x-axis               I")
        imgui.bullet_text("Scale down on x-axis             Alt+I")
        imgui.bullet_text("Scale up on y-axis               O")
        imgui.bullet_text("Scale down on y-axis             Alt+O")
        imgui.bullet_text("Scale up on z-axis               P")
        imgui.bullet_text("Scale down on z-axis             Alt+P")
        imgui.end()