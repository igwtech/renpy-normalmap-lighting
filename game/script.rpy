## ============================================================================
## PoC: dynamic sprite lighting with albedo + normal map.
##
## The sprite is defined as a Model with two textures (tex0 = albedo,
## tex1 = normal map) and the "normals.spritelight" shader. The light_*
## transforms (in shaders.rpy) only change the uniforms, so the same
## image is re-lit without touching the PNG.
## ============================================================================

define narrator_c = Character(None, what_italic=True)

## Lightable sprite: albedo + normal map + shader.
image girl = Model().texture("images/girl_albedo.png", fit=True).texture("images/girl_normal.png").shader("normals.spritelight")

## Flat reference sprite (no shader).
image girl plain = "images/girl_albedo.png"

## Character placement on screen (the mouse-light math in shaders.rpy
## assumes this placement: zoomed to screen height, centered).
transform girl_stage:
    zoom (config.screen_height / 768.0)
    xalign 0.5
    yalign 1.0

## Test backgrounds (shader gradients, no PNGs).
image bg day = At(Solid("#ffffff"), vgrad("#6fb3ef", "#dcefff"))
image bg sunset = At(Solid("#ffffff"), vgrad("#43286b", "#ff8f3a"))
image bg night = At(Solid("#ffffff"), vgrad("#04070f", "#15203d"))
image bg dark = At(Solid("#ffffff"), vgrad("#000000", "#17171a"))
image bg fire = At(Solid("#ffffff"), vgrad("#0a0302", "#3a1305"))


label start:

    scene bg dark with dissolve

    narrator_c "Proof of concept: sprite lighting with {b}albedo + normal map{/b} in Ren'Py."

    ## --- Quick comparison -------------------------------------------------

    show girl plain at girl_stage with dissolve
    narrator_c "This is the flat sprite, straight from the PNG. Plain Ren'Py."

    show girl at girl_stage, dirlight() with dissolve
    narrator_c "And this is the same sprite going through the shader, with a neutral frontal light. Almost identical… until we move the light."

    jump hub


label hub:

    menu:
        narrator_c "Which lighting should we try?"

        "Daylight sun":
            jump scene_day

        "Sunset":
            jump scene_sunset

        "Night (moonlight)":
            jump scene_night

        "Harsh top light (interrogation)":
            jump scene_top

        "Light from below (horror)":
            jump scene_below

        "Campfire (flickering point light)":
            jump scene_fire

        "Orbiting light (animated uniforms)":
            jump scene_orbit

        "Light follows the mouse (interactive)":
            jump scene_mouse

        "Quit":
            return


label scene_day:
    scene bg day with dissolve
    show girl at girl_stage, light_day with dissolve
    narrator_c "{b}Daylight sun{/b}: warm light from the upper right, with plenty of bluish ambient from the sky. Notice the volume in the skirt pleats and the hair."
    jump hub


label scene_sunset:
    scene bg sunset with dissolve
    show girl at girl_stage, light_sunset with dissolve
    narrator_c "{b}Sunset{/b}: an orange, almost horizontal sun from the left. One side of the body lights up while the other falls into violet shadow, with a touch of backlight."
    jump hub


label scene_night:
    scene bg night with dissolve
    show girl at girl_stage, light_night with dissolve
    narrator_c "{b}Night{/b}: cold, faint moonlight, minimal ambient, and a blue {i}rim light{/i} that outlines the silhouette against the dark."
    jump hub


label scene_top:
    scene bg dark with dissolve
    show girl at girl_stage, light_top with dissolve
    narrator_c "{b}Harsh top light{/b}: a white spotlight straight overhead, no ambient. Upward-facing surfaces blow out and everything else sinks into black."
    jump hub


label scene_below:
    scene bg dark with dissolve
    show girl at girl_stage, light_below with dissolve
    narrator_c "{b}Light from below{/b}: the classic horror-story flashlight. Same normal map, direction flipped: now the downward-facing planes light up."
    jump hub


label scene_fire:
    scene bg fire with dissolve
    show girl at girl_stage, light_fire with dissolve
    narrator_c "{b}Campfire{/b}: a warm {i}point{/i} light at the character's feet, with distance falloff and ATL-animated flicker (the light's position and color loop over time)."
    jump hub


label scene_orbit:
    scene bg dark with dissolve
    show girl at girl_stage, light_orbit with dissolve
    narrator_c "{b}Orbiting light{/b}: the light direction spins around the character. The shader uniforms are interpolated directly in ATL, no per-frame Python."
    jump hub


label scene_mouse:
    scene bg dark with dissolve
    show girl at girl_stage, light_mouse with dissolve
    narrator_c "{b}Interactive light{/b}: move the mouse and the point light follows it in real time. (Dismiss this dialogue box and sweep the cursor over the sprite.)"
    pause
    jump hub
