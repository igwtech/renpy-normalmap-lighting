## ============================================================================
## Shaders for dynamic sprite lighting (albedo + normal map).
##
## Conventions:
##  - tex0 = albedo (with alpha), tex1 = normal map (tangent space,
##    OpenGL style: green = up). If your normal map is DirectX style
##    (green = down), pass flip_green=1.0 in the transform.
##  - u_light_dir: direction TOWARDS the light, in screen space:
##    +x = right, +y = up, +z = towards the viewer.
##  - Point light: u_light_pos in sprite UV coordinates (0,0 = top left,
##    1,1 = bottom right), z = "height" above the sprite.
## ============================================================================

init python:

    renpy.register_shader("normals.spritelight", variables="""
        uniform sampler2D tex0;
        uniform sampler2D tex1;
        uniform vec2 u_model_size;
        uniform float u_point;
        uniform vec3 u_light_dir;
        uniform vec3 u_light_pos;
        uniform float u_falloff;
        uniform vec3 u_light_color;
        uniform vec3 u_ambient_color;
        uniform float u_spec_strength;
        uniform float u_shininess;
        uniform vec3 u_rim_color;
        uniform float u_rim_power;
        uniform float u_flip_green;
        attribute vec2 a_tex_coord;
        varying vec2 v_tex_coord;
    """, vertex_300="""
        v_tex_coord = a_tex_coord;
    """, fragment_300="""
        vec4 albedo = texture2D(tex0, v_tex_coord);

        vec3 n = texture2D(tex1, v_tex_coord).rgb * 2.0 - 1.0;
        if (u_flip_green > 0.5) {
            n.y = -n.y;
        }
        n = normalize(n);

        vec3 L;
        float atten = 1.0;

        if (u_point > 0.5) {
            // Point light: vector from the fragment towards the light, in an
            // isotropic space (aspect-ratio corrected) with +y pointing up.
            float aspect = u_model_size.x / u_model_size.y;
            vec2 d = (u_light_pos.xy - v_tex_coord) * vec2(aspect, -1.0);
            vec3 to_light = vec3(d, u_light_pos.z);
            float dist = length(to_light);
            L = to_light / max(dist, 0.0001);
            atten = 1.0 / (1.0 + u_falloff * dist * dist);
        } else {
            L = normalize(u_light_dir);
        }

        // Diffuse (Lambert).
        float diff = max(dot(n, L), 0.0);

        // Specular (Blinn-Phong, fixed view from +z).
        vec3 h = normalize(L + vec3(0.0, 0.0, 1.0));
        float spec = pow(max(dot(n, h), 0.0), max(u_shininess, 1.0)) * u_spec_strength;

        // Rim light: brightens normals that point away from the camera.
        // Useful for moonlight backlighting / night silhouettes.
        float rim = pow(clamp(1.0 - n.z, 0.0, 1.0), max(u_rim_power, 0.001));

        vec3 light = u_ambient_color + u_light_color * diff * atten;

        // The albedo comes with premultiplied alpha; the additive terms
        // (spec, rim) are multiplied by alpha so they don't glow outside
        // the silhouette.
        vec3 color = albedo.rgb * light + (u_light_color * spec * atten + u_rim_color * rim) * albedo.a;

        gl_FragColor = vec4(color, albedo.a);
    """)

    ## Simple vertical gradient, for test backgrounds.
    renpy.register_shader("normals.vgrad", variables="""
        uniform vec4 u_grad_top;
        uniform vec4 u_grad_bottom;
        attribute vec2 a_tex_coord;
        varying vec2 v_grad_coord;
    """, vertex_300="""
        v_grad_coord = a_tex_coord;
    """, fragment_300="""
        gl_FragColor = mix(u_grad_top, u_grad_bottom, clamp(v_grad_coord.y, 0.0, 1.0));
    """)


## ----------------------------------------------------------------------------
## Reusable lighting transforms.
## ----------------------------------------------------------------------------

## Directional light (sun, moon, distant spotlight).
transform dirlight(direction=(0.0, 0.0, 1.0), color=(1.0, 1.0, 1.0), ambient=(0.35, 0.35, 0.40), spec=0.0, shininess=24.0, rim=(0.0, 0.0, 0.0), rim_power=3.0, flip_green=0.0):
    u_point 0.0
    u_light_pos (0.5, 0.5, 0.3)
    u_falloff 0.0
    u_light_dir direction
    u_light_color color
    u_ambient_color ambient
    u_spec_strength spec
    u_shininess shininess
    u_rim_color rim
    u_rim_power rim_power
    u_flip_green flip_green

## Point light (candle, campfire, nearby lamp).
transform pointlight(pos=(0.5, 0.5, 0.35), color=(1.0, 1.0, 1.0), ambient=(0.10, 0.10, 0.12), falloff=2.0, spec=0.0, shininess=24.0, rim=(0.0, 0.0, 0.0), rim_power=3.0, flip_green=0.0):
    u_point 1.0
    u_light_dir (0.0, 0.0, 1.0)
    u_light_pos pos
    u_falloff falloff
    u_light_color color
    u_ambient_color ambient
    u_spec_strength spec
    u_shininess shininess
    u_rim_color rim
    u_rim_power rim_power
    u_flip_green flip_green

## Gradient background: apply it to a Solid with a mesh.
transform vgrad(top="#000000", bottom="#000000"):
    mesh True
    shader "normals.vgrad"
    u_grad_top Color(top).rgba
    u_grad_bottom Color(bottom).rgba
    xysize (config.screen_width, config.screen_height)


## ----------------------------------------------------------------------------
## Scene presets.
## ----------------------------------------------------------------------------

## Daylight sun: warm light from the upper right, high bluish ambient.
transform light_day:
    dirlight(direction=(0.5, 0.8, 0.55), color=(1.05, 1.0, 0.92), ambient=(0.42, 0.45, 0.52))

## Sunset: low, almost horizontal orange sun, violet ambient.
transform light_sunset:
    dirlight(direction=(-0.9, 0.15, 0.35), color=(1.25, 0.62, 0.32), ambient=(0.28, 0.18, 0.30), rim=(0.5, 0.2, 0.25), rim_power=3.0)

## Night: cold moon from the upper left, minimal ambient, blue rim.
transform light_night:
    dirlight(direction=(-0.4, 0.75, 0.45), color=(0.45, 0.55, 0.85), ambient=(0.06, 0.07, 0.13), spec=0.25, shininess=32.0, rim=(0.20, 0.28, 0.50), rim_power=2.5)

## Harsh top light (interrogation): white from straight above, no ambient.
transform light_top:
    dirlight(direction=(0.0, 1.0, 0.30), color=(1.35, 1.32, 1.25), ambient=(0.03, 0.03, 0.04), spec=0.35, shininess=48.0)

## Fixed light from below (horror flashlight): greenish, from underneath.
transform light_below:
    dirlight(direction=(0.0, -1.0, 0.35), color=(0.9, 1.05, 0.75), ambient=(0.04, 0.05, 0.04))

## Campfire: warm point light below the character, with animated flicker.
transform light_fire:
    u_point 1.0
    u_light_dir (0.0, 0.0, 1.0)
    u_ambient_color (0.05, 0.03, 0.04)
    u_spec_strength 0.2
    u_shininess 16.0
    u_rim_color (0.0, 0.0, 0.0)
    u_rim_power 3.0
    u_flip_green 0.0
    u_falloff 1.6
    u_light_pos (0.5, 0.95, 0.30)
    u_light_color (1.30, 0.62, 0.25)
    block:
        linear 0.09 u_light_color (1.10, 0.50, 0.20) u_light_pos (0.485, 0.96, 0.28)
        linear 0.13 u_light_color (1.40, 0.68, 0.28) u_light_pos (0.515, 0.94, 0.33)
        linear 0.07 u_light_color (1.22, 0.58, 0.22) u_light_pos (0.495, 0.95, 0.29)
        linear 0.11 u_light_color (1.35, 0.66, 0.27) u_light_pos (0.508, 0.96, 0.31)
        linear 0.10 u_light_color (1.15, 0.52, 0.20) u_light_pos (0.490, 0.94, 0.30)
        repeat

## Orbiting light (demo): the light direction rotates around the character.
transform light_orbit:
    u_point 0.0
    u_light_pos (0.5, 0.5, 0.3)
    u_falloff 0.0
    u_light_color (1.0, 0.95, 0.9)
    u_ambient_color (0.10, 0.10, 0.14)
    u_spec_strength 0.3
    u_shininess 32.0
    u_rim_color (0.0, 0.0, 0.0)
    u_rim_power 3.0
    u_flip_green 0.0
    u_light_dir (1.0, 0.0, 0.45)
    block:
        linear 1.25 u_light_dir (0.0, 1.0, 0.45)
        linear 1.25 u_light_dir (-1.0, 0.0, 0.45)
        linear 1.25 u_light_dir (0.0, -1.0, 0.45)
        linear 1.25 u_light_dir (1.0, 0.0, 0.45)
        repeat


## ----------------------------------------------------------------------------
## Light that follows the mouse (interactive point light).
## ----------------------------------------------------------------------------

init python:

    def _mouse_light_fn(trans, st, at):
        # Converts the mouse position (screen) to sprite UV coordinates,
        # knowing how the girl_stage transform places it (centered zoom,
        # bottom aligned).
        mx, my = renpy.get_mouse_pos()

        sw, sh = config.screen_width, config.screen_height
        iw, ih = 1408.0, 768.0
        zoom = sh / ih

        x0 = (sw - iw * zoom) / 2.0
        y0 = sh - ih * zoom

        u = (mx - x0) / (iw * zoom)
        v = (my - y0) / (ih * zoom)

        trans.u_light_pos = (u, v, 0.22)

        # Returning 0 makes this get called every frame.
        return 0

transform light_mouse:
    u_point 1.0
    u_light_dir (0.0, 0.0, 1.0)
    u_light_pos (0.5, 0.5, 0.22)
    u_falloff 2.5
    u_light_color (1.15, 1.05, 0.85)
    u_ambient_color (0.06, 0.06, 0.09)
    u_spec_strength 0.35
    u_shininess 32.0
    u_rim_color (0.0, 0.0, 0.0)
    u_rim_power 3.0
    u_flip_green 0.0
    function _mouse_light_fn
