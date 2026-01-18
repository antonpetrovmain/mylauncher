# MyLauncher

A lightweight app launcher for macOS that runs in the menu bar with global hotkey access.

## Features

- **Menu Bar App**: Runs quietly in the menu bar with a `>_` icon
- **Global Hotkey**: Press `Cmd+Ctrl+D` to instantly open the launcher
- **App Switching**: Running apps shown first, sorted by recent usage
- **App Search**: Filter apps by typing
- **Shell Commands**: Enter any command to execute it
- **Command History**: Recent commands accessible from menu bar
- **Keyboard Navigation**: Arrow keys + Emacs bindings

## Installation

### Option 1: Download the App (Recommended)

1. Download `MyLauncher.app` from the [Releases](../../releases) page
2. Move it to your `Applications` folder
3. Open the app
4. Grant Accessibility permissions when prompted:
   - Go to **System Settings → Privacy & Security → Accessibility**
   - Enable **MyLauncher**
5. Restart the app

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/antonpetrovmain/mylauncher.git
cd mylauncher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
pip install pyinstaller pillow

# Build the app
./scripts/build_app.sh

# Install
cp -R dist/MyLauncher.app ~/Applications/
```

## Usage

### Quick Start

1. Look for `>_` in your menu bar
2. Press **Cmd+Ctrl+D** to open the launcher
3. Start typing to search apps
4. Press **Enter** to launch/focus the selected app

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Ctrl+D` | Open launcher |
| `↑` / `Ctrl+P` | Move up |
| `↓` / `Ctrl+N` | Move down |
| `Enter` | Launch app / run command |
| `Escape` | Close |
| `Ctrl+A` | Beginning of line |
| `Ctrl+E` | End of line |
| `Ctrl+K` | Delete to end |
| `Ctrl+U` | Delete to beginning |
| `Ctrl+W` | Delete word |

### Running Shell Commands

If no app matches your search, press Enter to run it as a shell command.

### Menu Bar

Click `>_` in the menu bar for:
- **Run Command...** - Open the launcher
- **Recent Commands** - Quick access to history
- **Quit** - Exit the app

## Auto-start on Login

1. Open **System Settings → General → Login Items**
2. Click **+** under "Open at Login"
3. Select **MyLauncher** from Applications

## Configuration

Edit `mylauncher/config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `POPUP_WIDTH` | 500 | Window width |
| `POPUP_HEIGHT` | 350 | Window height |
| `MAX_COMMAND_HISTORY` | 100 | Commands to remember |
| `MAX_APP_HISTORY` | 50 | App usage entries |

## Data Files

- `~/.mylauncher_history.json` - Command history
- `~/.mylauncher_app_history.json` - App usage history

## Requirements

- macOS 10.15+
- Accessibility permissions (for global hotkey)

## License

MIT
