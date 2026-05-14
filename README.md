# 🏏 WhatsApp Poll Bot

Automatically votes **"Yes"** on cricket match polls in your WhatsApp group — so you never miss a spot in the team because you were busy and didn't see the message in time.

When your group admin posts a poll asking who wants to play, this bot detects it and votes for you immediately. The first 11 to respond get picked — this makes sure you're always in that list.

---

## How it works

1. The bot opens WhatsApp Web in a hidden browser window on your computer
2. It watches your cricket group for new polls
3. The moment a poll appears, it votes for the first option (usually "Yes / I'm in") on your behalf
4. Your WhatsApp session stays logged in, so it works silently in the background

Your phone and the WhatsApp app are not affected — this runs entirely through WhatsApp Web.

---

## What you need

- A Windows or Mac computer that stays on when matches are scheduled
- WhatsApp installed on your phone (to scan a QR code once during setup)
- An internet connection
- That's it — **no technical knowledge required**

---

## Installation

### Windows

1. **Download** this project — click the green **Code** button on this page → **Download ZIP**

2. **Unzip** the downloaded file anywhere you like (e.g. your Desktop)

3. **Double-click `launcher.bat`**

   > If Windows shows a warning "Windows protected your PC" → click **More info** → **Run anyway**. This is normal for scripts downloaded from the internet.

4. A black terminal window will open. It will automatically:
   - Install Python (if not already installed)
   - Set up the bot's environment
   - Download the browser it needs (~300 MB, first time only)

5. Once setup is done, **your browser opens automatically** at `http://localhost:5050` — that's the bot's control panel.

6. Continue to **[First Run — Scanning the QR Code](#first-run--scanning-the-qr-code)** below.

---

### Mac

1. **Download** this project — click the green **Code** button on this page → **Download ZIP**

2. **Unzip** the downloaded file anywhere you like (e.g. your Desktop)

3. Open **Terminal**

   > Press `Cmd + Space`, type `Terminal`, press Enter

4. Drag the `launcher.sh` file into the Terminal window and press **Enter**

   > Alternatively, right-click `launcher.sh` → **Open With** → **Terminal**

5. If prompted "cannot be opened because it is from an unidentified developer":
   - Go to **System Settings → Privacy & Security**
   - Scroll down and click **Allow Anyway** next to the launcher message

6. The terminal will automatically:
   - Install Python if needed (via Homebrew)
   - Set up the bot's environment
   - Download the browser it needs (~300 MB, first time only)

7. Once setup is done, **your browser opens automatically** at `http://localhost:5050`.

8. Continue to **[First Run — Scanning the QR Code](#first-run--scanning-the-qr-code)** below.

---

## First Run — Scanning the QR Code

This only happens once. After this, the bot remembers your login.

**Step 1 — Enter your group name**

In the bot's control panel (`http://localhost:5050`):
- Type the **exact name** of your WhatsApp cricket group in the "WhatsApp Group Name" field
- The name must match exactly as it appears in WhatsApp (including capital letters and spaces)
- Click **Save Settings**

**Step 2 — Start the bot**

Click the **▶ Start Bot** button.

A browser window will open showing WhatsApp Web with a QR code.

**Step 3 — Scan the QR code**

On your phone:
- Open **WhatsApp**
- Tap the **three dots** (⋮) menu (Android) or **Settings** (iPhone)
- Tap **Linked Devices**
- Tap **Link a Device**
- Point your phone camera at the QR code on screen

Once scanned, WhatsApp Web will load and show your chats. The browser window will then hide itself automatically — the bot is now running silently in the background.

**Step 4 — Check the Live Log**

Back in the control panel, you'll see the Live Log updating. Look for:
```
INFO     Logged in successfully
INFO     Opened group 'Your Group Name'
INFO     Monitoring 'Your Group Name' every 30s
```

That means everything is working. ✅

---

## Running the bot day-to-day

After the first setup, using the bot is simple:

1. Double-click `launcher.bat` (Windows) or run `launcher.sh` (Mac)
2. The control panel opens in your browser
3. Click **▶ Start Bot** — no QR code needed this time
4. Minimise the terminal window and leave your computer on

The bot runs quietly until you click **■ Stop Bot** or close the terminal window.

---

## Settings

| Setting | What it does | Default |
|---|---|---|
| **WhatsApp Group Name** | The exact group to monitor | *(you set this)* |
| **Check for polls every** | How often the bot looks for new polls (seconds) | 30 |
| **Vote for which option** | Which poll option to select | 1st option |

**Tip:** If your group's poll has "Yes" as the first option, leave "Vote for which option" at "1st option". If "Yes" is the second option, change it to "2nd option".

---

## Troubleshooting

### "Group not found" error in the log

- Make sure the group name is spelled **exactly** as it appears in WhatsApp
- Check for extra spaces before or after the name
- The bot saves a screenshot called `debug_group_not_found.png` in the `app_v2` folder — open it to see what the browser saw

### The bot voted on the wrong option

- Go to **Settings** in the control panel
- Change "Vote for which option" to match the "Yes / I'm in" option in your group's polls
- Click **Save Settings**, then restart the bot

### QR code expired before I could scan it

- Click **■ Stop Bot**
- Click **▶ Start Bot** again — a fresh QR code will appear

### I need to log in with a different WhatsApp account

- Click **■ Stop Bot** (if running)
- Click **🔄 Re-scan QR Code**
- Scan the QR code with the other phone

### The terminal window closed but the control panel won't load

- The terminal window must stay open while the bot runs — it's the engine
- Re-run the launcher to start it again

### "Windows protected your PC" warning

This is a standard Windows warning for downloaded scripts. The code is open source — you can read every line of it in this repository. Click **More info → Run anyway**.

### The browser window briefly appeared then closed

That's expected on the second run and beyond — the bot goes headless (invisible) after the session is saved.

### Nothing is happening / bot seems stuck

Check the Live Log in the control panel. Common messages and what they mean:

| Log message | Meaning |
|---|---|
| `Session restored -- already logged in` | Working fine, session loaded |
| `Waiting for QR code scan...` | Open your phone and scan |
| `Found 1 unvoted poll(s)` | Poll detected, voting now |
| `Vote sent` | Successfully voted ✅ |
| `Could not find search text box` | WhatsApp Web layout changed — check for a bot update |

---

## FAQ

**Does this affect my WhatsApp on my phone?**
No. WhatsApp allows one linked web session. The bot uses WhatsApp Web, the same as if you opened web.whatsapp.com in your own browser. Your phone app is unaffected.

**Will the group admin know I'm using a bot?**
Your vote appears exactly like a normal vote. There's no indication it was automated.

**What happens if a poll appears while my computer is off?**
The bot only works while it's running on your computer. If your computer is off or the bot isn't started, it won't vote. Consider leaving your computer on or using a schedule if you want it to run automatically.

**Can I use this for multiple groups?**
Currently the bot monitors one group at a time. You can change the group name in Settings and restart if needed.

**Is my WhatsApp login safe?**
Your session is stored locally in the `whatsapp_session` folder on your computer — it never leaves your machine. The `.gitignore` file ensures this folder is never accidentally uploaded to GitHub.

**The bot is running but a poll appeared and it didn't vote**
- The bot checks every 30 seconds by default — if someone clicks faster, you might miss the slot. Reduce the interval to 15 seconds in Settings.
- Scroll up in the Live Log to see if the poll was detected and what happened.

**How do I stop the bot permanently?**
Click **■ Stop Bot** in the control panel, then close the terminal window.

---

## Privacy & Security

- **No data leaves your computer.** The bot only communicates with WhatsApp Web directly.
- **No accounts or sign-ups required.** There's no backend server.
- **Open source.** Every line of code in this repository is readable. Nothing is hidden.
- Your WhatsApp session and group name are stored locally and are excluded from git via `.gitignore`.

---

## Updating the bot

1. Download the latest ZIP from this repository
2. Unzip it into a **new folder** (don't overwrite your existing install)
3. Copy your `whatsapp_session` folder from the old install into the new folder — this means you won't need to scan the QR code again
4. Run the launcher from the new folder

---

## Requirements (handled automatically by the launcher)

- Python 3.9 or later
- Flask
- Playwright (with Chromium browser)
