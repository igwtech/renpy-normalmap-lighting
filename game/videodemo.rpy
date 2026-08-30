## Scripted, non-interactive run of the whole PoC, meant to be screen-recorded
## (see record_video.sh). Launch with RENPY_POC_VIDEO=1. It plays every
## lighting preset with narration on a timer, then quits.

init python:

    def vsay(txt, t=6.0):
        """Show narration without waiting for a click, hold for t seconds."""
        renpy.say(narrator_c, txt, interact=False)
        renpy.pause(t, hard=True)

    def vmark(name):
        """Drop a marker file so the recording script can sync (mouse path)."""
        import os
        with open(os.path.join(config.gamedir, "..", name), "w") as f:
            f.write("go")

image video_title = Text(
    "{b}Dynamic Sprite Lighting in Ren'Py{/b}\n{size=26}{color=#9ab}one sprite  +  one normal map  +  one shader{/color}{/size}",
    size=50, text_align=0.5, layout="subtitle")

image video_end = Text(
    "{b}Same PNG. Same shader.\nOnly the light changes.{/b}\n{size=26}{color=#9ab}Ren'Py 8.6 · Model() + register_shader() · lighting via ATL transforms{/color}{/size}",
    size=44, text_align=0.5, layout="subtitle")


label poc_video:

    ## Clean frame: no quick menu.
    $ quick_menu = False
    window hide

    ## Small black hold so the recording never misses the start.
    scene bg dark
    $ renpy.pause(2.0, hard=True)

    ## --- Title card --------------------------------------------------------

    show video_title at truecenter with dissolve
    $ renpy.pause(5.0, hard=True)
    hide video_title with dissolve

    ## --- Comparison --------------------------------------------------------

    show girl plain at girl_stage with dissolve
    $ vsay("This is the flat sprite, straight from the PNG. Plain Ren'Py.", 5.0)

    show girl at girl_stage, dirlight() with dissolve
    $ vsay("Same sprite through the shader, neutral frontal light. Almost identical… until we move the light.", 6.0)

    ## --- Lighting scenes ---------------------------------------------------

    scene bg day with dissolve
    show girl at girl_stage, light_day with dissolve
    $ vsay("{b}Daylight sun{/b} — warm light from the upper right, bluish sky ambient. Notice the volume in the skirt pleats and the hair.", 8.0)

    scene bg sunset with dissolve
    show girl at girl_stage, light_sunset with dissolve
    $ vsay("{b}Sunset{/b} — an orange, almost horizontal sun from the left. One side lights up, the other falls into violet shadow.", 8.0)

    scene bg night with dissolve
    show girl at girl_stage, light_night with dissolve
    $ vsay("{b}Night{/b} — cold, faint moonlight and a blue rim light outlining the silhouette against the dark.", 8.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_top with dissolve
    $ vsay("{b}Harsh top light{/b} — a white spotlight straight overhead, no ambient. Interrogation mood.", 7.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_below with dissolve
    $ vsay("{b}Light from below{/b} — the classic horror flashlight. Same normal map, direction flipped.", 7.0)

    scene bg fire with dissolve
    show girl at girl_stage, light_fire with dissolve
    $ vsay("{b}Campfire{/b} — a warm point light at her feet, with distance falloff and ATL-animated flicker.", 10.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_orbit with dissolve
    $ vsay("{b}Orbiting light{/b} — the light direction spins around the character. Uniforms interpolated directly in ATL.", 10.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_mouse with dissolve
    $ vmark("poc_video_mouse_marker")
    $ vsay("{b}Interactive{/b} — a point light following the mouse cursor in real time.", 13.0)

    ## --- End card ----------------------------------------------------------

    window hide
    scene bg dark with dissolve
    show video_end at truecenter with dissolve
    $ renpy.pause(6.0, hard=True)

    scene bg dark with dissolve
    $ renpy.pause(1.5, hard=True)

    $ renpy.quit()

    return
