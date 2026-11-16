---
name: edit-video
description: Edit a talking-head video in one of 30 saved styles (or the user's own saved ones), cut it out onto a transparent background, blur the background, swap the background, or just clean up raw footage. Use for /edit-video, "/edit-video [style name]", "/edit-video styles", "/edit-video clean", "/edit-video cutout", "/edit-video blur", "/edit-video background", "/edit-video save this style as [name]", or any request to edit a video in a style, see the styles, remove/blur/change a background, or cut mistakes from a video.
---

# edit-video

The user is not technical. Be brief. Never ask them to type code. Any clear yes ("yes", "approved", "go ahead", "looks good") is approval.

**Keep it light and fast:** don't read files you don't need. Files next to this one: `styles.md` (read only the section for the chosen style), `my-settings.md` (brand colours, caption spellings, saved styles), `previews/` (pictures), `scripts/` (cutout/blur/background code, used only by those three commands). Install tools only when you're about to make a picture or video, and do it in the background while you talk.

## Experience rules (apply to EVERY command below, now and later)
- **Silent setup.** Installing packages (`pip install -r scripts/requirements.txt`), downloading the segmentation model, fetching a video: never narrate it, never ask the user to install anything themselves. It happens in the background while you talk to them.
- **One grouped permission question, only when truly needed.** If you must ask permission for something (e.g. network access to download a file), ask ONE short yes/no question in plain words, grouped with anything else you need at that moment. Never ask permissions one at a time.
- **No process chatter.** Never show intermediate frames, test renders, progress logs, or explain your steps, unless asked.
- **Finished result = one line.** "Your video is ready." plus the file(s) (and thumbnail where relevant). Nothing else unless they ask.
- **Storyboard stage:** build everything silently, then show ONLY the final storyboard sheet and thumbnail(s). Say only: "Your storyboard is ready. Anything to change, or is it approved?"
- **Feedback:** apply it silently, reply with ONLY the updated storyboard/thumbnail plus "Anything to change, or is it approved?" No before/after, no commentary.
- **Approval:** render everything silently. Reply with ONLY the finished file(s) and "Your video is ready."
- **Cut-out is automatic.** If a style needs the person cut out, just do it (`scripts/cutout_core.py`) — never send the user anywhere else to do it, never ask what to cut out.
- Keep every question short, one message, tap-friendly. Put commands in their own fenced code block.
- Never claim you checked audio you cannot hear. Never state a timestamp you did not verify.

## /edit-video styles (or no style named)
Publish `gallery.html` (next to this file) as an Artifact, titled "Video Style Library" — don't read or rebuild it, just publish it as-is. Say ONLY: "Pick a style from the library and paste its command." Nothing else — no command list repeated in chat. The gallery itself has each style's command in a tap-to-copy block, which styles need a cutout, and a "More commands" section (clean/cutout/blur/background/save-as). Include any saved styles from `my-settings.md` by republishing the artifact with them added. Open a single style's picture in `previews/` only if they ask to see it up close.

## Step 0 — before the style flow (video from Drive, or otherwise ambiguous)
Ask exactly: **"Is this video ready to edit as it is, or is it still rough and needs trimming (filler words, mistakes)?"**
- "Ready" → go straight to the style flow below.
- "Rough" → run `/edit-video clean` silently first, then the style flow on the cleaned video.

## /edit-video clean
No style. Upload → transcribe → rough cut (below) → cut with ffmpeg only (no Remotion) → send back `output/clean-<date>/clean.mp4`. Then: "Want it in a style too? Just say the name."

## /edit-video [style]
**Message 1 (one message, all at once):** if no video yet, ask for it. Then ask together:
- Sizes: "9:16 (tall: TikTok/Reels/Shorts), 4:3 (box: feeds), 16:9 (wide: YouTube)? Pick one, two or all three."
- Colours: "The style's own colours, or your brand colours?" (use `my-settings.md`; if empty and they want brand, ask once and save there).
- Music: "Background music? Say no, upload a track, or pick a mood: Upbeat / energetic, Calm / chill, Cinematic / emotional, Trendy / pop, Minimal / tech, Motivational / corporate."
- **If the style needs a cut-out** (its "Background and light" line in `styles.md` says to cut them out): do NOT mention CapCut or ask them to prepare anything — the cut-out is automatic (`scripts/cutout_core.py`, silent). Only say this once, as information, not a question: *"This style changes your background to the style's own background. If you'd like to keep your real background instead, these styles don't need a cutout: Tutorial Split, Podcast Clip, App World, Bento Grid, Inside the Post, Signature Pink — or upload a reference video with a style you like and I'll use that."*

**Then transcribe** with faster-whisper, model "small", int8, word timestamps. Fix known words from `my-settings.md`.

**Message 2 (one message):**
- Rough cut: list filler words (um, uh), dead air over ~2s, and repeated takes (same line said 2+ times: group them, say how many, keep the last clean one; if none is clean, ask). Example: "0:18–0:31: you said this line 4 times, I'd keep take 4." End with "Remove all, keep all, or tell me which." Never cut a deliberate pause or repeat-for-effect.
- Screenshots: for anything they describe that needs a picture (an app or site, a number, a before/after), list it with its time: "At 0:40 you describe the app. Have a screenshot?" If they don't, you'll build a close, realistic mockup in code (real layout, invented content, never real people's names or photos).
- Any word you're unsure you heard right.

**Storyboard** (after their answers): at most 6 key scenes, from the cleaned video. Read the chosen style's section in `styles.md` and look at its picture in `previews/` first; match it closely. Place things relative to where the person actually is in frame. If the style needs a cutout, run `scripts/cutout_core.py` silently first and composite onto the style's own background. For each scene: one still in each chosen size side by side, plus the words, on-screen text and sound. Then one thumbnail per chosen size, built from the strongest moment (big readable text, face visible). Show it as a page with pictures, then ask: "Anything to change, or approved?" For changes, redo only the changed stills.

**After approval:** render only the chosen sizes, 1080p (or lower if the source is), the source's frame rate, no watermark. Short audio crossfade (<150ms) at every cut so nothing pops. Music quiet under the voice. Save to `output/<style>-<date>/` with plain names (`word-pop-916.mp4`, `thumbnail-916.jpg`). Check a frame from each scene against the rules before sending.

## /edit-video cutout
Cuts the person out onto a transparent background. No questions. Silently:
1. `pip install -r scripts/requirements.txt` if not already installed (background, silent). On a Linux environment, also silently `apt-get install -y libegl1 libgles2` if mediapipe fails to import for a missing-library reason — this is a one-time thing.
2. `python3 scripts/cutout_core.py <input_video> output/cutout-<date>/` — this downloads the official Google model on first use (~250KB, silent) and writes `cutout.webm` (transparent VP9, colour = original frame) plus `preview_transparency_check.mp4` (the same thing over a grey checkerboard, so the user can actually SEE the transparency — many players show empty space as solid black or white instead).
3. Before replying, open `output/cutout-<date>/alpha_report.txt` and confirm alpha min is 0 and max is 255 and a meaningful share of pixels are transparent. Don't just assume the cutout worked.
4. Reply with only: "Your video is ready." plus `cutout.webm` and the checkerboard preview, labelled as a preview.
Best results: plain background, steady camera, one person, close/medium shot. Curly/loose hair can leave thin gaps or a faint light halo at the top, especially on fast head turns — if you notice this on a specific video, say so plainly in one short line rather than hiding it.

## /edit-video blur
Same cutout under the hood, but blurs the real background (disc-kernel "lens" blur with a soft highlight boost, not a flat gaussian) and keeps the person sharp on top of it — no background swap. Ask ONE question: **"How blurry? Light, medium or strong."** Then silently run `scripts/blur_core.py <input_video> output/blur-<date>/ <light|medium|strong>` and reply "Your video is ready." with `blur.mp4`.

## /edit-video background
**Talking-head videos only** (plain background, steady camera, one person, close/medium shot). If the uploaded video is clearly not that, say so kindly and point to a cutout-free style instead (see the list in the "Background" question above).
1. Ask: **"Want me to use a photo you upload, or should I draw a background for this video?"**
2. If they have a photo: ask them to upload a photo of a room (not a screenshot with app buttons), and optionally a brand colour and/or a short name/logo text for the wall.
3. If they want one drawn: **there is no preset list to choose from.** Look at what the video is actually about (and the talking-head framing: close-up gets walls/shelves/window light; only mid/wide shots can show desks/sofas; floors only on wide shots) and compose ONE scene that fits, using `scripts/bg_toolkit.py`'s drawing primitives (`canvas`, `glow`, `leaf_cluster`, `bokeh_dots`, `shelf_grid`, `window_light`) directly in a short script — don't reuse a fixed scene from a past job. Keep it simple, warm, uncluttered; these read as soft illustrations, not photos, so don't oversell them. Save the result as a PNG.
4. Ask: **"How blurry should the background be? None / Light / Medium / Strong."** (default Medium if they don't say).
5. Ask (optional, one message): "Any colour you want in the background, or a name/logo on the wall?" A brand colour is never a flat painted wall — it's added as a soft coloured glow; render a name/logo as a code overlay for exact spelling, not drawn by you as part of the scene.
6. Silently run `scripts/background_core.py <input_video> output/background-<date>/ <bg_image.png> <blur> [brand R,G,B]`. Show ONE frame preview (two options, Natural vs With your brand colour, if a brand colour was given), ask "Which one, or any changes?", then render the full video silently on approval. Reply "Your video is ready." with `background.mp4`.

## Rules for every frame
- Nothing covers the face. Captions sit under the chin, never near the mouth, easy to read.
- 9:16: keep text out of the top 250px, bottom 420px and right 160px.
- Graphics land on the word they illustrate.
- Camera: at most one or two slow, small zoom-ins (4–6%) on the single biggest moments, unless the style has its own camera move. Never zoom captions or graphics.
- Never real people's posts, names or photos.

## Music (when they pick a mood)
Open the matching Pixabay page, take one fitting track, use it, delete it after rendering (never keep a library of them). Moods: upbeat https://pixabay.com/music/search/upbeat/ · calm https://pixabay.com/music/search/calm/ · cinematic https://pixabay.com/music/search/cinematic/ · pop https://pixabay.com/music/search/pop/ · tech https://pixabay.com/music/search/minimal%20technology/ · motivational https://pixabay.com/music/search/motivational/. If there's no internet access, give them the link to download it themselves and upload it.

## /edit-video save this style as [name]
Study the uploaded video (story, cuts, text, graphics, colours, sound, pacing). Say in 3 sentences what makes it work. Add it to `my-settings.md` under saved styles, written like the entries in `styles.md`. Reply "Saved. Next time upload your video and paste:" with `/edit-video [name]` in a code block.

## Saving (phone/cloud sessions)
Save any change to `my-settings.md` to the main branch so it's there next time.

## If it's slow or stuck
Tell them a render can take a few minutes; if it stops, say "please continue". If their folder gets big, suggest deleting old videos on github.com.
