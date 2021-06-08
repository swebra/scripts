# Scripts
A collection of quick and dirty QOL scripts which automate some of my daily workflow. They are generally built for me and me only, expect some messy code and poor documentation.

## `fix-stylus.sh`
Bash script to reset my stylus + touch screen mapping when I connect my laptop to an external display.

## `import-notes.py`
Python script to take downloaded PDFs and PowerPoint files, convert them as needed to a target format (`.svgz` for use in [Stylus Labs Write](http://www.styluslabs.com) in my case), and move them to an appropriate folder. Calls other CLI programs/scripts for most of the conversion, and uses [inquirer](https://pypi.org/project/inquirer/) for pretty user input.

## `manage-minecraft.py`
Python script for managing systemd-based Minecraft servers in a nice to use menu. Primarily provides a world switcher which can load world-specific settings into [`server.properties`](https://minecraft.fandom.com/wiki/Server.properties). World settings files are expected to be saved in the same directory as the world and with the same name:
```bash
saves
├── world1
│   └── # Contents of the world (level.dat, playerdata, etc.)
├── world1.properties
├── world2
│   └── # Contents of the world (level.dat, playerdata, etc.)
├── world2.properties
# ...
```
They also follow the same format as the `server.properties` file, only settings you wish to override need to be included. For example, `world1.properties` and `world2.properties` could just respectively contain `difficulty=easy` and `difficulty=hard`, so that the server's difficulty changes when loading the respective worlds.

The script also provides menu options to run common commands:
- Connect to RCON terminal using [mcrcon](https://github.com/Tiiffi/mcrcon)
- View or follow server logs (using `journalctl`)
- Start/stop the server (using `systemctl`), with logs followed afterwards
- Safely restart the server, letting the user wait until the server has completely shutdown before starting back up again
