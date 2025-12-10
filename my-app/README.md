# FocusFlow - Productivity & Health Tracker

A cross-platform desktop application to help you stay focused and maintain healthy work habits. The app tracks your application usage, blocks distracting apps, and reminds you to take breaks and maintain good posture.

## Features

- **Focus Sessions**: Define what you're working on and track your focus time
- **App Blocking**: Blocks distracting applications during focus sessions
- **Health Reminders**:
  - 20-20-20 rule for eye strain prevention
  - Posture correction alerts
  - Hydration reminders
  - Regular break prompts
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Privacy-Focused**: All data stays on your computer

## Installation

1. Make sure you have Python 3.7 or higher installed
2. Clone this repository or download the source code
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python main.py
```

2. When prompted, enter what you're working on today
3. The app will start monitoring your active window
4. If you open an application not in your allowed list, you'll be prompted to either allow or block it
5. Health reminders will appear at regular intervals
6. Click "End Focus Session" when you're done to see your session summary

## System Tray

The app runs in the system tray. You can:
- Click the tray icon to show/hide the main window
- Right-click for options to show or quit the application

## Data Storage

- Session logs are stored in `~/.focusflow_logs/`
- Session data is saved in `~/.focusflow_sessions/` as JSON files

## Requirements

- Windows: pywin32, psutil
- macOS: pyobjc-framework-Quartz
- Linux: xdotool (install via package manager)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
