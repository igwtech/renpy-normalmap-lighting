## Scripted, non-interactive run of the whole PoC, meant to be screen-recorded
## (see record_video.sh). Launch with RENPY_POC_VIDEO=1. It plays every
## lighting preset with narration on a timer, then quits.
##
## If vo/durations.json exists (see make_voiceover.py), each scene's pause is
## stretched to fit its voice-over clip, and poc_video_cues.json records the
## exact time each scene starts (relative to the start marker) so the clips
## can be mixed in at the right offsets afterwards.

init python:

    import json
    import time

    _vo_durations = {}
    _video_cues = {}
    _video_t0 = None

    def _poc_path(name):
        import os
        return os.path.join(config.gamedir, "..", name)

    def vstart():
        """Load VO durations and drop the marker that starts the recording."""
        global _video_t0
        import os
        p = _poc_path("vo/durations.json")
        if os.path.exists(p):
            with open(p) as f:
                _vo_durations.update(json.load(f))
        _video_t0 = time.time()
        with open(_poc_path("poc_video_start_marker"), "w") as f:
            f.write("go")

    def vcue(name):
        """Record when this scene started, for audio placement."""
        _video_cues[name] = round(time.time() - _video_t0, 3)
        with open(_poc_path("poc_video_cues.json"), "w") as f:
            json.dump(_video_cues, f, indent=2)

    def vdur(name, base):
        """Scene hold time: at least base, and long enough for the VO clip."""
        return max(base, _vo_durations.get(name, 0.0) + 1.5)

    def vsay(name, txt, base):
        """Show narration without waiting for a click, hold for the scene."""
        vcue(name)
        renpy.say(narrator_c, txt, interact=False)
        renpy.pause(vdur(name, base), hard=True)

    def vmark(name):
        """Drop a marker file so the recording script can sync (mouse path)."""
        with open(_poc_path(name), "w") as f:
            f.write("go")

image video_title = Text(
    "{b}Dynamic Sprite Lighting in Ren'Py{/b}\n{size=30}{color=#cde}UPDATE: depth-map self-shadows{/color}{/size}\n{size=26}{color=#9ab}one sprite  +  one normal map  +  one depth map  +  one shader{/color}{/size}",
    size=50, text_align=0.5, layout="subtitle")

image video_end = Text(
    "{b}Same PNG. Same shader.\nNow with real self-shadows.{/b}\n{size=26}{color=#9ab}Ren'Py 8.6 · Model() + register_shader() · depth-map shadow marching · lighting via ATL{/color}{/size}",
    size=44, text_align=0.5, layout="subtitle")


label poc_video:

    ## Clean frame: no quick menu, and an exact 1280x720 window (Ren'Py
    ## otherwise opens smaller than the screen).
    $ quick_menu = False
    window hide
    $ renpy.set_physical_size((1280, 720))
    $ renpy.pause(0.5, hard=True)

    $ vstart()

    ## Small black hold so the recording never misses the start.
    scene bg dark
    $ renpy.pause(2.0, hard=True)

    ## --- Title card --------------------------------------------------------

    show video_title at truecenter with dissolve
    $ vcue("title")
    $ renpy.pause(vdur("title", 5.0), hard=True)
    hide video_title with dissolve

    ## --- Comparison --------------------------------------------------------

    show girl plain at girl_stage with dissolve
    $ vsay("plain", "This is the flat sprite, straight from the PNG. Plain Ren'Py.", 5.0)

    show girl at girl_stage, dirlight() with dissolve
    $ vsay("shader", "Same sprite through the shader, neutral frontal light. Almost identical… until we move the light.", 6.0)

    ## --- Lighting scenes ---------------------------------------------------

    scene bg day with dissolve
    show girl at girl_stage, light_day with dissolve
    $ vsay("day", "{b}Daylight sun{/b} — warm light from the upper right, bluish sky ambient. Notice the volume in the skirt pleats and the hair.", 8.0)

    scene bg sunset with dissolve
    show girl at girl_stage, light_sunset with dissolve
    $ vsay("sunset", "{b}Sunset{/b} — an orange, almost horizontal sun from the left. One side lights up, the other falls into violet shadow.", 8.0)

    scene bg night with dissolve
    show girl at girl_stage, light_night with dissolve
    $ vsay("night", "{b}Night{/b} — cold, faint moonlight and a blue rim light outlining the silhouette against the dark.", 8.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_top with dissolve
    $ vsay("top", "{b}Harsh top light{/b} — a white spotlight straight overhead, no ambient. Interrogation mood.", 7.0)

    ## --- NEW: depth-map self-shadows ---------------------------------------

    scene bg dark with dissolve
    show girl at girl_stage, dirlight(direction=(0.0, 1.0, 0.35), color=(1.30, 1.26, 1.18), ambient=(0.05, 0.05, 0.06), shadow=0.0) with dissolve
    $ vsay("shadow_off", "{b}NEW — self-shadows OFF{/b} — same top light, normal map only. The legs under the skirt stay lit: nothing blocks the light.", 9.0)

    show girl at girl_stage, dirlight(direction=(0.0, 1.0, 0.35), color=(1.30, 1.26, 1.18), ambient=(0.05, 0.05, 0.06), shadow=0.9, shadow_soft=0.018) with dissolve
    $ vsay("shadow_on", "{b}Self-shadows ON{/b} — the shader marches through a depth map: the skirt shadows the thighs, the chin shadows the neck, the hair shadows the shoulders.", 11.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_below with dissolve
    $ vsay("below", "{b}Light from below{/b} — the classic horror flashlight. The shadows flip with it: the skirt hem now darkens the torso.", 8.0)

    scene bg fire with dissolve
    show girl at girl_stage, light_fire with dissolve
    $ vsay("fire", "{b}Campfire{/b} — a warm point light at her feet, with distance falloff and ATL-animated flicker. The point light reads the depth map too.", 10.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_orbit with dissolve
    $ vsay("orbit", "{b}Orbiting light{/b} — the light spins around the character and the self-shadows sweep with it. Uniforms interpolated directly in ATL.", 10.0)

    scene bg dark with dissolve
    show girl at girl_stage, light_mouse with dissolve
    $ vmark("poc_video_mouse_marker")
    $ vsay("mouse", "{b}Interactive{/b} — a point light following the mouse cursor in real time.", 13.0)

    ## --- End card ----------------------------------------------------------

    window hide
    scene bg dark with dissolve
    show video_end at truecenter with dissolve
    $ vcue("end")
    $ renpy.pause(vdur("end", 6.0), hard=True)

    scene bg dark with dissolve
    $ renpy.pause(1.5, hard=True)

    $ renpy.quit()

    return
