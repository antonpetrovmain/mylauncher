# MyCLI

A lightweight command launcher for macOS that runs in the menu bar with global hotkey access to apps and shell commands.

## Features

- **Menu Bar App**: Runs quietly in the menu bar with a `>_` icon
- **Global Hotkey**: Press `Cmd+Ctrl+D` to instantly open the command popup
- **App Suggestions**: Running apps shown first (sorted by recent usage), then installed apps
- **Smart Sorting**: Recently used apps appear at the top of suggestions
- **Shell Commands**: Enter any shell command to execute it in your home directory
- **Command History**: Recent commands saved and accessible from the menu bar
- **Keyboard Navigation**: Full support for arrow keys to navigate suggestions
- **Focus Restoration**: Returns focus to your previous app after running a command

## Requirements

- macOS
- Python 3.14+
- Accessibility permissions (for global hotkey)

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd mycli
   ```

2. Create a virtual environment and install:
   ```bash
   python3.14 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

3. Grant Accessibility permissions:
   - Open **System Settings > Privacy & Security > Accessibility**
   - Add and enable your terminal app (e.g., Terminal, iTerm2)

## Usage

### Start the app

```bash
source venv/bin/activate
mycli
```

Or run directly:
```bash
python -m mycli
```

### Using the command launcher

1. Press `Cmd+Ctrl+D` to open the popup (or click the `>_` menu bar icon)
2. Start typing to filter apps, or enter a shell command
3. Use arrow keys to navigate suggestions
4. Press `Enter` to launch/focus the selected app or run the command

### Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Ctrl+D` | Open command popup |
| `↑` | Move up in suggestions |
| `↓` | Move down in suggestions |
| `Enter` | Select item / run command |
| `Escape` | Close popup |

### Menu bar options

Click the `>_` icon in the menu bar to:
- **Run Command...**: Open the command popup
- **Recent Commands**: Quick access to command history
- **Quit**: Exit the application

## Auto-start on Login

To have MyCLI start automatically when you log in:

1. Open **System Settings > General > Login Items**
2. Click **+** under "Open at Login"
3. Navigate to and select the MyCLI app or launch script

## Configuration

Settings are in `mycli/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `COMMAND_TIMEOUT_SECONDS` | 10 | Max time for command execution |
| `MAX_COMMAND_HISTORY` | 100 | Maximum commands to store |
| `MAX_APP_HISTORY` | 50 | Maximum app usage entries |
| `POPUP_WIDTH` | 500 | Popup window width |
| `POPUP_HEIGHT` | 300 | Popup window height |

## Data Storage

- Command history: `~/.mycli_history.json`
- App usage history: `~/.mycli_app_history.json`

## Dependencies

- `rumps`: Menu bar app framework
- `pyobjc-framework-Quartz`: For CGEventTap hotkey capture
- `pyobjc-framework-Cocoa`: For native macOS UI components
- `desktop-notifier`: Cross-platform notifications

## License

MIT
