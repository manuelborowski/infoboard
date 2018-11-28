# -*- coding: utf-8 -*-

from models import User, Registration, Series
import user.extra_filtering
from floating_menu import default_menu_config, register_runner_menu_config

tables_configuration = {
    'registration' : {
        'model' : Registration,
        'title' : 'Registraties',
        'route' : 'registration.registrations',
        'subject' :'registration',
        'delete_message' : '',
        'template' : [{'name': 'Code', 'data':'studentcode', 'order_by': Registration.studentcode, 'width': '5%'},
                      {'name': 'Voornaam', 'data':'first_name', 'order_by': Registration.first_name, 'width': '10%'},
                      {'name': 'Achternaam', 'data':'last_name', 'order_by': Registration.last_name, 'width': '10%'},
                      {'name': 'G', 'data':'gender', 'order_by': Registration.gender, 'width': '5%'},
                      {'name': 'Klas', 'data':'classgroup', 'order_by': Registration.classgroup, 'width': '5%'},
                      {'name': 'RFID', 'data':'rfidcode', 'order_by': Registration.rfidcode, 'width': '10%'},
                      {'name': 'RFID2', 'data':'rfidcode2', 'order_by': Registration.rfidcode2, 'width': '10%'},
                      {'name': 'Reeks', 'data':'series.name', 'order_by': Series.name, 'width': '10%'},
                      {'name': 'Tijd', 'data':'time_ran', 'order_by': Registration.time_ran, 'width': '20%'},
                      ],
        'filter' :  ['gender', 'series'],
        'href': [],
        'floating_menu' : register_runner_menu_config,
        'disable_add_button' : True,
        #'export' : 'asset.exportcsv',
    },
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
        'query_filter' : user.extra_filtering.filter,
    }
}

