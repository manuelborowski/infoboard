# -*- coding: utf-8 -*-

from .models import User

from .user.extra_filtering import filter
from .floating_menu import default_menu_config, register_runner_menu_config

tables_configuration = {
    'user': {
        'model': User,
        'title' : 'gebruiker',
        'route' : 'user.users',
        'subject' :'user',
        'delete_message' : '',
        'template': [
            {'name': 'Gebruikersnaam', 'data': 'username', 'order_by': User.username},
            {'name': 'Voornaam', 'data': 'first_name', 'order_by': User.first_name},
            {'name': 'Naam', 'data': 'last_name', 'order_by': User.last_name},
            {'name': 'Email', 'data': 'email', 'order_by': User.email},
            {'name': 'Is admin', 'data': 'is_admin', 'order_by': User.is_admin},],
        'filter': [],
        'href': [{'attribute': '["username"]', 'route': '"user.view"', 'id': '["id"]'},
                 ],
        'floating_menu' : default_menu_config,
        'query_filter' : filter,
    }
}

