## Minimal options for the normal-map lighting proof of concept.

define config.name = _("RenpyNormals — PoC Shaders")
define config.version = "0.1"
define gui.about = _("Proof of concept: dynamic sprite lighting with albedo + normal map.")

define build.name = "RenpyNormals"

define config.has_sound = True
define config.has_music = True
define config.has_voice = False

define config.save_directory = "RenpyNormals-PoC"

define config.window_icon = None

## Skip the main menu and go straight to the demo.
define config.main_menu_music = None

label main_menu:
    return

init python:
    build.classify('**~', None)
    build.classify('**.bak', None)
    build.classify('**/.**', None)
    build.classify('**/#**', None)
    build.classify('**/thumbs.db', None)
