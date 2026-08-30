## Self-check: when launched with RENPY_POC_AUTOTEST=1, cycles through all
## the lighting presets, saves a screenshot of each one and quits.
## When launched with RENPY_POC_VIDEO=1, plays the scripted video demo
## (see videodemo.rpy). Neither affects the normal game.

init python:
    import os
    _poc_autotest = os.environ.get("RENPY_POC_AUTOTEST", "") == "1"
    _poc_video = os.environ.get("RENPY_POC_VIDEO", "") == "1"

label splashscreen:

    if _poc_autotest:
        jump poc_autotest

    if _poc_video:
        jump poc_video

    return

label poc_autotest:

    python:
        _poc_shots = [
            ("day", "bg day", light_day),
            ("sunset", "bg sunset", light_sunset),
            ("night", "bg night", light_night),
            ("top", "bg dark", light_top),
            ("below", "bg dark", light_below),
            ("fire", "bg fire", light_fire),
            ("orbit", "bg dark", light_orbit),
            ("mouse", "bg dark", light_mouse),
        ]

        outdir = os.path.join(config.gamedir, "..", "poc_shots")
        if not os.path.isdir(outdir):
            os.makedirs(outdir)

        for _name, _bg, _light in _poc_shots:
            renpy.scene()
            renpy.show(_bg)
            renpy.show("girl", at_list=[girl_stage, _light])
            renpy.pause(0.6, hard=True)
            renpy.screenshot(os.path.join(outdir, "poc_%s.png" % _name))

        renpy.quit()

    return
