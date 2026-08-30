## ============================================================================
## Shaders for dynamic sprite lighting (albedo + normal map + depth map).
##
## Conventions:
##  - tex0 = albedo (with alpha), tex1 = normal map (tangent space,
##    OpenGL style: green = up). If your normal map is DirectX style
##    (green = down), pass flip_green=1.0 in the transform.
##  - tex2 = depth map (grayscale height field, white = closer to the
##    viewer). u_depth_scale says how "thick" the character is, in world
##    units where the sprite height is 1.0.
##  - u_light_dir: direction TOWARDS the light, in screen space:
##    +x = right, +y = up, +z = towards the viewer.
##  - Point light: u_light_pos in sprite UV coordinates (0,0 = top left,
##    1,1 = bottom right), z = "height" above the sprite plane.
##  - Self-shadowing: the fragment marches through the depth map towards
##    the light; if a taller feature blocks the ray, the diffuse and
##    specular terms are darkened (the skirt shadows the legs, the chin
##    shadows the neck, the front hair shadows the face...).
## ============================================================================

init python:

    renpy.register_shader("normals.spritelight", variables="""
        uniform sampler2D tex0;
        uniform sampler2D tex1;
        uniform sampler2D tex2;
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
        uniform float u_depth_scale;
        uniform float u_shadow_strength;
        uniform float u_shadow_softness;
        attribute vec2 a_tex_coord;
        varying vec2 v_tex_coord;
    """, vertex_300="""
        v_tex_coord = a_tex_coord;
    """, fragment_functions="""
        // Height-field shadow march. Walks from the fragment towards the
        // light through the depth map; returns 0.0 (fully lit) .. 1.0
        // (fully occluded). Works in an isotropic space where the sprite
        // height is 1.0 world unit (+x right, +y up, +z towards viewer).
        float sprite_shadow(sampler2D dtex, vec2 uv, vec3 L, float frag_h,
                            float aspect, float depth_scale, float softness,
                            float t_max) {

            // A frontal light has (almost) nothing to march through.
            if (length(L.xy) < 0.02) {
                return 0.0;
            }

            const int STEPS = 28;
            float soft = max(softness, 0.0005);
            float bias = 0.002 + 0.25 * soft;
            float occ = 0.0;

            for (int i = 1; i <= STEPS; i++) {
                float t = t_max * float(i) / float(STEPS);

                // World-space point on the ray, converted back to UV.
                vec2 suv = uv + vec2(L.x * t / aspect, -L.y * t);
                if (suv.x < 0.0 || suv.x > 1.0 || suv.y < 0.0 || suv.y > 1.0) {
                    break;
                }

                float h_sample = texture2D(dtex, suv).r * depth_scale;
                float ray_h = frag_h + L.z * t;

                // How far above the ray the sampled surface pokes out.
                float o = clamp((h_sample - ray_h - bias) / soft, 0.0, 1.0);

                // Distant occluders cast softer, weaker shadows.
                o *= 1.0 - 0.6 * (t / t_max);

                occ = max(occ, o);
            }

            return clamp(occ, 0.0, 1.0);
        }
    """, fragment_300="""
        vec4 albedo = texture2D(tex0, v_tex_coord);

        vec3 n = texture2D(tex1, v_tex_coord).rgb * 2.0 - 1.0;
        if (u_flip_green > 0.5) {
            n.y = -n.y;
        }
        n = normalize(n);

        float aspect = u_model_size.x / u_model_size.y;

        // Per-pixel height above the sprite plane, from the depth map.
        float frag_h = texture2D(tex2, v_tex_coord).r * u_depth_scale;

        vec3 L;
        float atten = 1.0;
        float t_max = 0.25;

        if (u_point > 0.5) {
            // Point light: vector from the fragment towards the light, in an
            // isotropic space (aspect-ratio corrected) with +y pointing up.
            // The fragment's own height comes from the depth map, so closer
            // features (nose, chest) really are closer to the light.
            vec2 d = (u_light_pos.xy - v_tex_coord) * vec2(aspect, -1.0);
            // Height relative to the character's mid-depth plane, so
            // u_light_pos.z keeps meaning "height above the character"
            // and closer features (nose, chest) tilt towards the light.
            float rel_h = frag_h - 0.5 * u_depth_scale;
            vec3 to_light = vec3(d, u_light_pos.z - rel_h);
            float dist = length(to_light);
            L = to_light / max(dist, 0.0001);
            atten = 1.0 / (1.0 + u_falloff * dist * dist);
            t_max = min(dist, 0.25);
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

        // Self-shadowing from the depth map. Only the direct terms
        // (diffuse, specular) are shadowed; ambient and rim are not.
        float shade = 1.0;
        if (u_shadow_strength > 0.001 && diff > 0.0) {
            float occ = sprite_shadow(tex2, v_tex_coord, L, frag_h, aspect,
                                      u_depth_scale, u_shadow_softness, t_max);
            shade = 1.0 - u_shadow_strength * occ;
        }

        vec3 light = u_ambient_color + u_light_color * diff * atten * shade;

        // The albedo comes with premultiplied alpha; the additive terms
        // (spec, rim) are multiplied by alpha so they don't glow outside
        // the silhouette.
        vec3 color = albedo.rgb * light + (u_light_color * spec * atten * shade + u_rim_color * rim) * albedo.a;

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
## shadow = 0.0 disables the depth-map self-shadowing entirely.
transform dirlight(direction=(0.0, 0.0, 1.0), color=(1.0, 1.0, 1.0), ambient=(0.35, 0.35, 0.40), spec=0.0, shininess=24.0, rim=(0.0, 0.0, 0.0), rim_power=3.0, flip_green=0.0, shadow=0.65, shadow_soft=0.015, depth_scale=0.32):
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
    u_depth_scale depth_scale
    u_shadow_strength shadow
    u_shadow_softness shadow_soft

## Point light (candle, campfire, nearby lamp).
transform pointlight(pos=(0.5, 0.5, 0.35), color=(1.0, 1.0, 1.0), ambient=(0.10, 0.10, 0.12), falloff=2.0, spec=0.0, shininess=24.0, rim=(0.0, 0.0, 0.0), rim_power=3.0, flip_green=0.0, shadow=0.65, shadow_soft=0.015, depth_scale=0.32):
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
    u_depth_scale depth_scale
    u_shadow_strength shadow
    u_shadow_softness shadow_soft

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
    dirlight(direction=(0.5, 0.8, 0.55), color=(1.05, 1.0, 0.92), ambient=(0.42, 0.45, 0.52), shadow=0.55)

## Sunset: low, almost horizontal orange sun, violet ambient.
transform light_sunset:
    dirlight(direction=(-0.9, 0.15, 0.35), color=(1.25, 0.62, 0.32), ambient=(0.28, 0.18, 0.30), rim=(0.5, 0.2, 0.25), rim_power=3.0, shadow=0.70)

## Night: cold moon from the upper left, minimal ambient, blue rim.
transform light_night:
    dirlight(direction=(-0.4, 0.75, 0.45), color=(0.45, 0.55, 0.85), ambient=(0.06, 0.07, 0.13), spec=0.25, shininess=32.0, rim=(0.20, 0.28, 0.50), rim_power=2.5, shadow=0.75)

## Harsh top light (interrogation): white from straight above, no ambient.
## The best showcase for the depth shadows: the chin darkens the neck,
## the skirt hem drops a shadow band onto the legs.
transform light_top:
    dirlight(direction=(0.0, 1.0, 0.30), color=(1.35, 1.32, 1.25), ambient=(0.03, 0.03, 0.04), spec=0.35, shininess=48.0, shadow=0.85, shadow_soft=0.015)

## Fixed light from below (horror flashlight): greenish, from underneath.
## Here the shadows flip: the skirt hem darkens the torso above it.
transform light_below:
    dirlight(direction=(0.0, -1.0, 0.35), color=(0.9, 1.05, 0.75), ambient=(0.04, 0.05, 0.04), shadow=0.80)

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
    u_depth_scale 0.32
    u_shadow_strength 0.65
    u_shadow_softness 0.015
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
    u_depth_scale 0.32
    u_shadow_strength 0.70
    u_shadow_softness 0.015
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
    u_depth_scale 0.32
    u_shadow_strength 0.70
    u_shadow_softness 0.015
    function _mouse_light_fn
