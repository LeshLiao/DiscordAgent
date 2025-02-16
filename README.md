# Discord Agent

## **Set up Python3**

```bash
# On Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip

# On macOS (using Homebrew)
brew install python3
```

## Rut it!

```bash
git clone https://github.com/LeshLiao/DiscordAgent.git

cd DiscordAgent

python3 -m venv venv

# On macOS/Linux:
source venv/bin/activate

pip3 install -r requirements.txt

# setup .env file
touch .env

python3 customDiscordBot.py
```

## To exit the virtual environment, simply run

```bash
deactivate
```

## Generate requirements.txt

```bash
pip3 freeze > requirements.txt
```
