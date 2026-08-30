#!/bin/bash
## Records the PoC video demo (game/videodemo.rpy) into poc_video.mp4.
## Runs the game on a virtual X server (Xvfb) and captures it with ffmpeg,
## so it doesn't touch your desktop session. Requires: Xvfb, ffmpeg, xdotool.

set -e
cd "$(dirname "$0")"

DISP=:99
OUT="${1:-poc_video.mp4}"
MARKER="poc_video_mouse_marker"

rm -f "$MARKER"

## Virtual X server at the game's resolution.
Xvfb "$DISP" -screen 0 1280x720x24 -nolisten tcp &
XVFB_PID=$!
trap 'kill $XVFB_PID 2>/dev/null || true' EXIT
sleep 1

## Launch the scripted demo.
env -u WAYLAND_DISPLAY DISPLAY="$DISP" SDL_VIDEODRIVER=x11 SDL_AUDIODRIVER=dummy \
    RENPY_POC_VIDEO=1 ./renpy-sdk/renpy.sh . &
GAME_PID=$!

## Wait for the game window to exist.
for i in $(seq 1 60); do
    if DISPLAY="$DISP" xdotool search --name "RenpyNormals" >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done
sleep 1

## Park the cursor out of the way.
DISPLAY="$DISP" xdotool mousemove 1279 719

## Record.
ffmpeg -y -loglevel error -f x11grab -framerate 30 -video_size 1280x720 -i "$DISP" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart \
    "$OUT" &
FF_PID=$!

## When the interactive scene starts, sweep the cursor over the sprite so the
## point light visibly follows it.
(
    while kill -0 "$GAME_PID" 2>/dev/null; do
        if [ -f "$MARKER" ]; then
            python3 - <<'EOF'
import math, os, subprocess, time
env = dict(os.environ, DISPLAY=":99")
t0 = time.time()
while time.time() - t0 < 12.0:
    t = time.time() - t0
    x = 660 + 260 * math.sin(t * 1.1)
    y = 360 + 210 * math.sin(t * 0.7 + 1.3)
    subprocess.run(["xdotool", "mousemove", str(int(x)), str(int(y))], env=env)
    time.sleep(0.03)
# Park the cursor out of frame again before the end card.
subprocess.run(["xdotool", "mousemove", "1279", "719"], env=env)
EOF
            break
        fi
        sleep 0.4
    done
) &

## Wait for the demo to finish, then stop the recording cleanly.
wait "$GAME_PID" || true
sleep 1
kill -INT "$FF_PID" 2>/dev/null || true
wait "$FF_PID" || true
rm -f "$MARKER"

echo "Video saved to: $OUT"
