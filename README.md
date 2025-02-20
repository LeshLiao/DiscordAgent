# Discord Agent

## **Set up Python3**

```bash
# On macOS (using Homebrew)
brew install python3

# On Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip
sudo apt-get install -y scrot python3-tk python3-dev python3-xlib
```

## Rut it!

```bash
# Clone
git clone https://github.com/LeshLiao/DiscordAgent.git
cd DiscordAgent
python3 -m venv venv

# On macOS:
source venv/bin/activate
pip3 install -r mac_os/requirements.txt

# On Ubuntu/Debian
source venv/bin/activate
pip3 install -r linux/requirements.txt

# setup .env file
touch .env

# find Discord Message field position,
python3 find_position.py

# Update message box position in utility.py
    pyautogui.click(x=571, y=653) # Click on Discord message box

# Let's Go!
python3 customDiscordBot.py
```

## To exit the virtual environment, simply run

```bash
deactivate
```

## Generate requirements.txt

```bash
# On Ubuntu/Debian:
pip3 freeze > python_requirements/linux/requirements.txt
    # remove mac dependencies
    -pyobjc-core==11.0
    -pyobjc-framework-Cocoa==11.0
    -pyobjc-framework-Quartz==11.0

# On macOS:
pip3 freeze > python_requirements/mac_os/requirements.txt
```
