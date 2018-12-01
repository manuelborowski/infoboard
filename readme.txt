#source venv/bin/activate
#export FLASK_APP=run.py
#export FLASK_CONFIG=development
#flask run --host=0.0.0.0

deployment :
------------
to make it possible for apache (www-data) to write in directories
sudo usermod -aG aboro www-data
in static-dir : chmod -R g+w *

google-calendar :
in dir infoboard, run : python app/google-calendar.py
