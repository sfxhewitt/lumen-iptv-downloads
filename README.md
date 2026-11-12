# lumen-iptv-downloads
Public downloads of LUMEN IPTV for Android TV and Fire TV. Test builds; no provider credentials included.

## Latest: LUMEN 1.0.245 beta (12 Nov 2026)

**Download:** https://raw.githubusercontent.com/sfxhewitt/lumen-iptv-downloads/main/LUMEN.apk

This link always gets the newest build, so it never needs changing. Install it over your current LUMEN and your channels, favourites and settings are kept.

- Package: com.portallive.tv, version 1.0.245
- SHA-256: `687b0ca56eb290cdce24f4ecee53a483faa478209543c9174411b0787b5699f8`
- Signed with the same key as the earlier betas, so it updates in place.

### Install with the Downloader app (Fire TV / Android TV)
1. Install **Downloader** by AFTVnews from your TV's app store.
2. Fire TV only: Settings › My Fire TV › Developer options › Install unknown apps, and turn it on for Downloader. If Developer options is missing, go to Settings › My Fire TV › About and press OK on the device name 7 times.
3. Open Downloader and type the address above in the box, then press Go.
4. Choose **Install** when it asks. You can delete the downloaded file afterwards.

### What's new since 1.0.239
- **Smart Now starts at the beginning.** Pressing Right from the menu lands on the top pick, and pressing Down goes to the first item of each row, never part-way along it.
- **Smart Now keeps your place.** When Smart Now refreshes its picks while you're browsing, the row you're in stays put, so the next press doesn't jump you back to the menu.

### Also new since 1.0.234
- **Updates in the app.** Install this build the usual way once, and after that you won't need Downloader again: each time you open LUMEN it checks this page, and when there's a newer build it downloads it straight away and your TV asks you to press **Install**. Your channels, favourites and settings are kept. If you're recording, LUMEN asks first. You can also check in Settings › About › Updates.
  - The first time, your TV may ask you to let LUMEN install apps. On Fire TV that's Settings › My Fire TV › Developer options › Install unknown apps › LUMEN. On Android TV it's Settings › Apps › Security & restrictions › Unknown sources › LUMEN (or Settings › Apps › Special app access › Install unknown apps). LUMEN shows you the way and carries on when you come back.

### Also new since 1.0.195
- **Smart Now.** A new screen in the menu that picks what's on right now worth watching: live sport, films, new episodes and more. It learns from what you watch, and leaves out SD channels.
- **Add-ons.** Settings › Add-ons takes any add-on that uses the open Stremio add-on format. Their films and series show in the new Streamio screen. LUMEN comes with none, so only add ones you trust.
- **Torrent streams, off by default.** If an add-on offers torrents, you can switch them on in Settings › Add-ons. LUMEN explains what that means first (your connection shares the file with others while it plays), and it stops sharing and deletes the files when you close the player.
- **Snooker on TV.** The Snooker page and Home's "Snooker on TV" row show one best channel for each showing, never +1 or SD.
- **Smoother menus.** Pressing Right from the menu goes straight into the screen, and Home and Smart Now reopen at the top.

### Also new since 1.0.119
- **Choose your Plex libraries.** Settings › Plex › Plex tab lists all your film and TV libraries. Pick which ones show on the Plex tab, and in what order.
- **New film and series pages.** Titles in On Demand open a Netflix-style page with the trailer playing across the top.
- **Tidier TV guide.** One row per channel, even when your provider lists it several times (HD, FHD or old names).
- **Smoother live TV.** Streams ride out provider drop-outs and reconnect without jumping back and replaying what you've already seen.
- **Safer connection.** If your provider supports HTTPS, LUMEN switches to it by itself. Settings › Providers then shows "Uses HTTPS".
- **Catch-up days.** The guide, search and the OK menu show how many days of catch-up a channel has.
- **Synopsis on OK.** Pressing OK while you watch shows a short description of the programme.
- **Voice search.** Press Speak in Search and say a channel, programme or film.
- **UK channels first.** When a programme is on several channels, LUMEN suggests the UK one.
- **Adult channels hidden.** They no longer show anywhere until they're unlocked with a remote shortcut and your PIN.
- **Snooker keeps working.** When snooker.org is down, results, draws and the calendar come from Wikipedia.
- **SHIELD extras (optional).** Turn on "LUMEN remote buttons" in the TV's Accessibility settings and the Netflix button opens LUMEN. Ask Claude lets you ask questions with the mic button; it needs your own Claude API key (Settings › Ask Claude).

## LUMEN Home
LUMEN's companion home screen (a launcher for Android TV and Fire TV): **https://raw.githubusercontent.com/sfxhewitt/lumen-iptv-downloads/main/LUMEN-Home.apk**

It updates itself the same way as LUMEN: when Home comes to the front it checks `home-version.json` here (at most every 15 minutes), downloads a newer build quietly, and your TV asks you to press **Install**. Allow it once in Install unknown apps, as for LUMEN.

## Older builds
See [Releases](https://github.com/sfxhewitt/lumen-iptv-downloads/releases) for 1.0.119 and 1.0.88.
