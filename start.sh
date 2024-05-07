python=venv/bin/python
$python -m http.server -port $PORT &
$python get_config.py && $python bot.py
