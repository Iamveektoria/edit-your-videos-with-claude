---
name: edit-video
description: Edit a talking-head video in one of 30 saved styles (or the user's own saved ones), or just clean up raw footage. Use for /edit-video, "/edit-video [style name]", "/edit-video styles", "/edit-video clean", "/edit-video save this style as [name]", or any request to edit a video in a style, see the styles, or cut mistakes from a video.
---

# edit-video

The user is not technical. Be brief. Never ask them to type code. Any clear yes ("yes", "approved", "go ahead", "looks good") is approval.

**Keep it light and fast:** don't read files you don't need. Files next to this one: `styles.md` (read only the section for the chosen style), `my-settings.md` (brand colours, caption spellings, saved styles), `previews/` (pictures). Install tools only when you're about to make a picture or video, and do it in the background while you talk.

## /edit-video styles (or no style named)
Publish `gallery.html` (next to this file) as an Artifact — don't read or rebuild it, just publish it as-is, titled "Video Style Library". Then say "Want your video edited in one? Upload it and paste the command:" and list each style name followed by its command alone in a code block, e.g.
Word Pop
```
/edit-video Word Pop
```
Include any saved styles from `my-settings.md`. Open a single style's picture in `previews/` only if they ask to see it up close.

## /edit-video clean
No style. Upload → transcribe → rough cut (below) → cut with ffmpeg only (no Remotion) → send back `output/clean-<date>/clean.mp4`. Then: "Want it in a style too? Just say the name."

## /edit-video [style]
**Message 1 (one message, all at once):** if no video yet, ask for it. Then ask together:
- Sizes: "9:16 (tall: TikTok/Reels/Shorts), 4:3 (box: feeds), 16:9 (wide: YouTube)? Pick one, two or all three."
- Colours: "The style's colours or your brand colours?" (use `my-settings.md`; if empty and they want brand, ask once and save there).
- Music: "Upload a track, say no, or pick a mood and I'll find one."
- If the style needs a cut-out (its "Background and light" line says to cut them out) and they sent one video, ask for the CapCut version with the background removed, or suggest a style that doesn't need one.

**Then transcribe** with faster-whisper, model "small", int8, word timestamps. Fix known words from `my-settings.md`.

**Message 2 (one message):**
- Rough cut: list filler words (um, uh), dead air over ~2s, and repeated takes (same line said 2+ times: group them, say how many, keep the last clean one; if none is clean, ask). Example: "0:18–0:31: you said this line 4 times, I'd keep take 4." End with "Remove all, keep all, or tell me which." Never cut a deliberate pause or repeat-for-effect.
- Screenshots: for anything they describe that needs a picture (an app or site, a number, a before/after), list it with its time: "At 0:40 you describe the app. Have a screenshot?" If they don't, you'll build a close, realistic mockup in code (real layout, invented content, never real people's names or photos).
- Any word you're unsure you heard right.

**Storyboard** (after their answers): at most 6 key scenes, from the cleaned video. Read the chosen style's section in `styles.md` and look at its picture in `previews/` first; match it closely. Place things relative to where the person actually is in frame. For each scene: one still in each chosen size side by side, plus the words, on-screen text and sound. Then one thumbnail per chosen size, built from the strongest moment (big readable text, face visible). Show it as a page with pictures, then ask: "Anything to change, or approved?" For changes, redo only the changed stills.

**After approval:** render only the chosen sizes, 1080p (or lower if the source is), the source's frame rate, no watermark. Short audio crossfade (<150ms) at every cut so nothing pops. Music quiet under the voice. Save to `output/<style>-<date>/` with plain names (`word-pop-916.mp4`, `thumbnail-916.jpg`). Check a frame from each scene against the rules before sending.

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
