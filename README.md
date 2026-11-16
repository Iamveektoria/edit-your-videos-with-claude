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

The first time you use `/edit-video cutout`, `/edit-video blur`, `/edit-video background`, or any style that cuts you out of your background, Claude installs a small, free Google tool (~40MB, Apache-2.0 licence) and downloads a tiny background-removal model (~250KB) in the background. You don't need to do anything — if your coding environment asks you to choose a network/access level when you first create it, choosing "Trusted" or "Full" avoids a one-time prompt later. On Linux-based environments this also needs two small graphics libraries (`libegl1`, `libgles2`), which Claude installs the same way. If it ever can't reach the internet for this, it will tell you in one line what to allow.
