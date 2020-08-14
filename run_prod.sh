export $(grep -v '^#' prod.env | xargs)
./venv/bin/python3 bot.py