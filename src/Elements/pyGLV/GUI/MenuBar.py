"""
MenuBar classes, part of the Elements.pyGLV

A small, modular ImGui application menu bar: File/Edit/View/... dropdowns full of MenuItems,
each with an optional real keyboard shortcut. A MenuItem's callback fires both when it is
clicked in the menu and when its shortcut is pressed, and the shortcut is shown next to the
label the way every native (and Dear ImGui) menu does -- purely cosmetic in ImGui itself, so
this module does the actual key polling.

Basic usage, from any example that already uses Elements' ImGui-based Scene/Viewer:

    from Elements.pyGLV.GUI.MenuBar import MenuBar, Keybinding
    import sdl2

    menu_bar = MenuBar()
    file_menu = menu_bar.add_menu("File")
    file_menu.add_item("screenshot", "Screenshot", take_screenshot, Keybinding(sdl2.SDL_SCANCODE_P))

Every frame, while the ImGui frame is active (e.g. right after ``scene.render()``):

    menu_bar.draw()
    menu_bar.poll_shortcuts()

A shortcut can be changed in code with one line:

    menu_bar.rebind("File", "screenshot", Keybinding(sdl2.SDL_SCANCODE_F, sdl2.KMOD_ALT))

or left up to whoever runs the example, via a small JSON file next to the script:

    menu_bar.save_keybindings_json(path)   # write current shortcuts out, once, if missing
    menu_bar.load_keybindings_json(path)   # apply whatever the user edited back

Adding a whole new dropdown is just:

    view_menu = menu_bar.add_menu("View")
    view_menu.add_item("wireframe", "Toggle Wireframe", gGUI.toggle_Wireframe, shortcut_label="F")
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import imgui
import sdl2

#: modifier bits this module understands, in the order they are rendered in a shortcut label
_MODIFIER_BITS = (sdl2.KMOD_CTRL, sdl2.KMOD_ALT, sdl2.KMOD_SHIFT, sdl2.KMOD_GUI)
_ALL_MODIFIERS = sdl2.KMOD_CTRL | sdl2.KMOD_ALT | sdl2.KMOD_SHIFT | sdl2.KMOD_GUI

#: how each modifier is rendered: macOS uses the familiar single glyphs, everything else a word
_MODIFIER_GLYPHS_MAC = {sdl2.KMOD_CTRL: "⌃", sdl2.KMOD_ALT: "⌥", sdl2.KMOD_SHIFT: "⇧", sdl2.KMOD_GUI: "⌘"}
_MODIFIER_GLYPHS_DEFAULT = {sdl2.KMOD_CTRL: "Ctrl+", sdl2.KMOD_ALT: "Alt+", sdl2.KMOD_SHIFT: "Shift+", sdl2.KMOD_GUI: "Cmd+"}

#: canonical name written to a keybindings JSON file for each modifier bit, e.g. "mods": "Ctrl+Alt"
_MODIFIER_JSON_NAMES = {sdl2.KMOD_CTRL: "Ctrl", sdl2.KMOD_ALT: "Alt", sdl2.KMOD_SHIFT: "Shift", sdl2.KMOD_GUI: "Cmd"}
#: names/aliases accepted when *reading* a keybindings JSON file's "mods" string (case-insensitive)
_MODIFIER_JSON_ALIASES = {
    "ctrl": sdl2.KMOD_CTRL, "control": sdl2.KMOD_CTRL,
    "alt": sdl2.KMOD_ALT, "option": sdl2.KMOD_ALT,
    "shift": sdl2.KMOD_SHIFT,
    "cmd": sdl2.KMOD_GUI, "command": sdl2.KMOD_GUI, "gui": sdl2.KMOD_GUI, "win": sdl2.KMOD_GUI, "super": sdl2.KMOD_GUI,
}


def _scancode_name(scancode: int) -> str:
    name = sdl2.SDL_GetScancodeName(scancode)
    return name.decode() if isinstance(name, bytes) else str(name)


def _parse_mods_json(mods_field) -> int:
    """Parse a keybindings JSON "mods" value: "Ctrl+Alt", "" (or missing) for none, case-insensitive.
    Also accepts a plain int, for files written by an older version of this module."""
    if isinstance(mods_field, int):
        return mods_field
    mods = 0
    for token in str(mods_field).split("+"):
        token = token.strip()
        if not token:
            continue
        bit = _MODIFIER_JSON_ALIASES.get(token.lower())
        if bit is None:
            raise ValueError(f'unknown modifier "{token}" in keybindings "mods" value "{mods_field}"')
        mods |= bit
    return mods


@dataclass(frozen=True)
class Keybinding:
    """
    A real-time keyboard shortcut: an SDL scancode plus a required modifier bitmask (0 for none).
    Used both to poll whether the shortcut is currently being pressed and to render its label.
    """

    scancode: int
    mods: int = 0

    @property
    def label(self) -> str:
        """Render as e.g. "F", "⌥P" on macOS or "Alt+P" elsewhere."""
        glyphs = _MODIFIER_GLYPHS_MAC if sys.platform == "darwin" else _MODIFIER_GLYPHS_DEFAULT
        prefix = "".join(glyphs[bit] for bit in _MODIFIER_BITS if self.mods & bit)
        return f"{prefix}{_scancode_name(self.scancode)}"

    def is_down(self, keystate, modstate: int) -> bool:
        """True while this exact key+modifier combination is held (extra modifiers make it False)."""
        return bool(keystate[self.scancode]) and (modstate & _ALL_MODIFIERS) == self.mods

    def to_json(self) -> dict:
        mods = "+".join(_MODIFIER_JSON_NAMES[bit] for bit in _MODIFIER_BITS if self.mods & bit)
        return {"key": _scancode_name(self.scancode), "mods": mods}

    @classmethod
    def from_json(cls, data: dict) -> Keybinding:
        return cls(scancode=sdl2.SDL_GetScancodeFromName(data["key"].encode()), mods=_parse_mods_json(data.get("mods", "")))


@dataclass
class MenuItem:
    """
    One entry in a Menu: a label and a callback, triggered by a mouse click and/or a Keybinding.

    ``binding`` is an actively-polled shortcut; ``shortcut_label`` alone (no binding) just displays
    text next to the item for a shortcut that's handled elsewhere in the app (e.g. a key the base
    Viewer/RenderDecorator already owns), so the menu doesn't end up polling the same key twice.
    """

    item_id: str
    label: str
    callback: Callable[[], None]
    binding: Keybinding | None = None
    shortcut_label: str | None = None
    enabled: bool = True
    _was_down: bool = field(default=False, repr=False, compare=False)

    @property
    def display_shortcut(self) -> str | None:
        return self.binding.label if self.binding is not None else self.shortcut_label

    def poll(self, keystate, modstate: int) -> None:
        """Call once per frame; fires the callback on the down-edge of a bound shortcut only."""
        if self.binding is None or not self.enabled:
            return
        is_down = self.binding.is_down(keystate, modstate)
        if is_down and not self._was_down:
            self.callback()
        self._was_down = is_down

    def draw(self) -> None:
        clicked, _ = imgui.menu_item(self.label, self.display_shortcut, False, self.enabled)
        if clicked:
            self.callback()


@dataclass
class Menu:
    """A single top-level dropdown (e.g. "File") holding an ordered list of MenuItems."""

    label: str
    items: list[MenuItem] = field(default_factory=list)

    def add_item(
        self,
        item_id: str,
        label: str,
        callback: Callable[[], None],
        binding: Keybinding | None = None,
        shortcut_label: str | None = None,
        enabled: bool = True,
    ) -> MenuItem:
        item = MenuItem(item_id, label, callback, binding, shortcut_label, enabled)
        self.items.append(item)
        return item

    def find(self, item_id: str) -> MenuItem | None:
        return next((item for item in self.items if item.item_id == item_id), None)

    def draw(self) -> None:
        if imgui.begin_menu(self.label, True).opened:
            for item in self.items:
                item.draw()
            imgui.end_menu()


class MenuBar:
    """
    A modular application menu bar: any number of Menus, each with any number of MenuItems.
    Call draw() and poll_shortcuts() once per frame while an ImGui frame is active.
    """

    def __init__(self):
        self.menus: list[Menu] = []

    def add_menu(self, label: str) -> Menu:
        menu = Menu(label)
        self.menus.append(menu)
        return menu

    def find_menu(self, label: str) -> Menu | None:
        return next((menu for menu in self.menus if menu.label == label), None)

    def find_item(self, menu_label: str, item_id: str) -> MenuItem | None:
        menu = self.find_menu(menu_label)
        return menu.find(item_id) if menu is not None else None

    def rebind(self, menu_label: str, item_id: str, binding: Keybinding | None) -> None:
        """Change a MenuItem's keyboard shortcut (or clear it with binding=None)."""
        item = self.find_item(menu_label, item_id)
        if item is None:
            raise KeyError(f'no menu item "{item_id}" in menu "{menu_label}"')
        item.binding = binding

    def draw(self) -> None:
        """Draw the menu bar. Call once per frame while an ImGui frame is active."""
        if imgui.begin_main_menu_bar().opened:
            for menu in self.menus:
                menu.draw()
            imgui.end_main_menu_bar()

    def poll_shortcuts(self) -> None:
        """Fire the callback of any bound shortcut that was just pressed. Call once per frame."""
        keystate = sdl2.SDL_GetKeyboardState(None)
        modstate = sdl2.SDL_GetModState()
        for menu in self.menus:
            for item in menu.items:
                item.poll(keystate, modstate)

    def save_keybindings_json(self, path) -> None:
        """Write the current shortcut of every bound item to a JSON file a user can hand-edit."""
        data = {
            f"{menu.label}.{item.item_id}": item.binding.to_json()
            for menu in self.menus
            for item in menu.items
            if item.binding is not None
        }
        Path(path).write_text(json.dumps(data, indent=2) + "\n")

    def load_keybindings_json(self, path) -> None:
        """Apply shortcut overrides from a JSON file previously written by save_keybindings_json()."""
        path = Path(path)
        if not path.exists():
            return
        data = json.loads(path.read_text())
        for key, value in data.items():
            menu_label, _, item_id = key.partition(".")
            item = self.find_item(menu_label, item_id)
            if item is not None:
                item.binding = Keybinding.from_json(value)
