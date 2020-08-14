export $(grep -v '^#' dev.env | xargs)
venv/bin/python3 bot.py