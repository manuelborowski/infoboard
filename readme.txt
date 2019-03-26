with ssl:
    install ssl keys (see github for more info)
    git clone git@github.com:manuelborowski/fablab-visitor-registration.git
without ssl:
    git clone https://github.com/manuelborowski/fablab-visitor-registration.git

create virtual environment
    python -m venv venv
    pip install -r requirements.txt

install nginx related files (in directory nginx) and update to the correct project-path, user and server

restart nginx
    sudo systemctl start fablab-visitor-registration
    sudo systemctl restartnginx

install certificate
    certbot --nginx
