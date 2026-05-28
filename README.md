# InkyPi Spoolman Active Spools

A custom InkyPi plugin that shows recently active Spoolman spools on an e-paper display with a clean, glanceable layout and configurable display fields.

## Install

Use the InkyPi plugin installer with the plugin ID and this repository URL, following the install pattern shown by the official InkyPi plugin template.

```bash
inkypi plugin install spoolman_active_spools https://github.com/shadal18/inkypi-spoolman-active-spools
```

## Update

If the plugin was installed from GitHub as its own repository, update it from inside the plugin folder and then restart InkyPi.

```bash
cd ~/InkyPi/src/plugins/spoolman_active_spools
git pull origin main
sudo systemctl restart inkypi.service
```

If `git pull` says `Already up to date` but the changes are not showing in the web UI, check that:

- You are in the correct plugin folder
- The updated files were committed and pushed to GitHub
- The files were not accidentally added to a nested subfolder
- InkyPi was restarted after the update
- Your browser cache was refreshed

You can verify the currently installed plugin files with commands like:

```bash
cd ~/InkyPi/src/plugins/spoolman_active_spools
git status
git remote -v
find . -name "settings.html"
```

If a file was accidentally added to a nested folder, move it into the plugin root so InkyPi can use it. For example:

```bash
cd ~/InkyPi/src/plugins/spoolman_active_spools
cp spoolman_active_spools/settings.html settings.html
sudo systemctl restart inkypi.service
```

After restarting the service, reload the settings page in the browser.

## Requirements

- A working InkyPi installation with plugin support.
- A reachable Spoolman instance with its API available over HTTP.
- Network access from the InkyPi device to the Spoolman host.

This plugin is an extension for the InkyPi e-paper display frame and includes the following features.

**Features**

- Shows recently active Spoolman spools.
- Configurable active time window.
- Color-focused spool display for quick identification.
- Optional material display.
- Optional brand display.
- Optional spool ID display.
- Optional remaining grams display.
- Optional last used display.
- Optional location display.
- Clean layout optimized for quick glance reading on e-paper.
- Human-readable active window labels such as minutes, hours, and days.

**Settings**

- Spoolman URL.
- Active window in minutes.
- Header text.
- Show or hide color.
- Show or hide material.
- Show or hide brand.
- Show or hide spool ID.
- Show or hide remaining grams.
- Show or hide last used.
- Show or hide location.

**Screenshots**

- Main plugin display showing active spools.
- Plugin settings screen.

<p align="center">
  <img src="screenshots/example.png" width="45%" />
  <img src="screenshots/settings.png" width="45%" />
</p>
