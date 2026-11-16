# Edit Your Videos With Claude

Install this to edit your talking-head videos with Claude in 30 styles. For how to actually use it well, see the guide that came with your purchase.

## Before you start

You need the Claude app (iPhone, Android, or desktop) with Code access. This is a paid feature, not the free plan. Look for a "Code" tab or "coding" option when you open the app. If you only see a plain chat box with no file or coding ability, you don't have the right access yet.

## Step 1: make your own copy

Click the green "Use this template" button at the top of this page, then "Create a new repository." Give it any name, such as "my-video-edits," leave everything else as-is, and create it. This makes you a personal copy. Nothing you do here affects anyone else's copy, including mine.

## Step 2: open it in Claude

Open the Claude app and start a new Code (or "coding") session. When it asks which project or repository, connect your GitHub account if you haven't already, then pick the repository you just created in Step 1. Wait for the session to open. This can take a minute the first time.

Once it's open, type /edit-video to begin, and follow your guide from there.

## If something looks stuck

Renders can take a few minutes. That's normal. If it stops responding, just say "please continue."

## One-time setup you might see

The first time you use `/edit-video cutout`, `/edit-video blur`, `/edit-video background`, or any style that cuts you out of your background, Claude runs a setup check and installs everything itself — a small, free Google tool (~40MB, Apache-2.0 licence), a tiny background-removal model (~250KB), and the free video tool ffmpeg if your computer doesn't already have it. You don't need to type anything. You'll just see one line — "Setting things up, this takes about a minute, only once." — and only the first time. If your coding environment asks you to choose a network/access level when you first create it, choosing "Trusted" or "Full" avoids a one-time prompt later. On Linux-based environments this also needs two small graphics libraries (`libegl1`, `libgles2`), installed the same way. If something can't be installed automatically (no internet, or a missing tool with no package manager available), you'll get one plain sentence saying what to do — never a raw error or technical log.

## What's been tested, and what hasn't

- **Tested on macOS** (Apple Silicon): first-run setup from a clean install, `/edit-video cutout`, `/edit-video blur` at all three strengths, and `/edit-video background` with both a photo and a drawn scene, on several real clips including a busy bookshelf background, a bright window behind the speaker, and dark-on-dark clothing.
- **Not tested on Windows or on a Linux coding environment.** The setup script is written to handle both (ffmpeg via `winget` on Windows, via `apt-get` plus the two graphics libraries on Linux), but nobody has run it there yet — if you hit a problem on either, please say so.
- **The transparent `cutout.webm` is confirmed correct at the file level**: forcing the VP9 decoder shows the alpha channel decodes properly (0 = fully see-through, 255 = fully opaque, matching what was encoded). It has **not** been confirmed playing with real transparency inside a real browser or inside Remotion in this environment, because of a sandbox restriction here that blocks starting a local test server — if you use it in Remotion and the background isn't transparent, please say so. The included `preview_transparency_check.mp4` (person composited over a grey checkerboard) is the reliable way to actually see the transparency without needing anything else installed.
