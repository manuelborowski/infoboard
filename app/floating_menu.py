# -*- coding: utf-8 -*-

fmi_edit = {"menu_id": "edit_menu_item", "menu_text": "Pas aan", "route": "edit", "flags": ["id_required"]}
fmi_delete = {"menu_id": "delete_menu_item", "menu_text": "Verwijder", "route": "delete","flags": ["id_required", "confirm_before_delete"]}
fmi_copy = {"menu_id": "copy_menu_item", "menu_text": "Kopieer van", "route": "add", "flags": ["id_required"]}
fmi_add = {"menu_id": "add_menu_item", "menu_text": "Voeg toe", "route": "add", "flags": []}
fmi_view = {"menu_id": "view_menu_item", "menu_text": "Details", "route": "view", "flags": ["id_required"]}
fmi_change_pwd = {"menu_id": "change_pwd_menu_item", "menu_text": "Verander paswoord", "route": "change_pwd","flags": ["id_required"]}
fmi_update_rfid = {"menu_id": "update_rfid_menu_item", "menu_text": "Nieuwe code", "route": "new_rfid","flags": ["bootbox_single"]}
fmi_delete_rfid = {"menu_id": "delete_rfid_item", "menu_text": "Verwijder code", "route": "delete_rfid", \
                   "message" : "Zeker dat u deze rfid code wil verwijderen?", "flags": ["confirm_before_delete"]}
fmi_delete_time_ran = {"menu_id": "delete_time_ran_menu_item", "menu_text": "verwijder gelopen tijd", "route": "delete_time_ran", \
                    "message" : "Zeker dat u deze tijd wil verwijderen?","flags": ["confirm_before_delete"]}

default_menu_config = [
    fmi_edit,
    fmi_copy,
    fmi_add,
    fmi_view,
    fmi_delete
]

user_menu_config = [
    fmi_edit,
    fmi_change_pwd
]

admin_menu_config = [
    fmi_edit,
    fmi_copy,
    fmi_add,
    fmi_view,
    fmi_delete,
    fmi_change_pwd
]

offence_menu_config = [
    fmi_delete
]

register_runner_menu_config = [
    fmi_update_rfid,
    fmi_delete_rfid,
    fmi_delete_time_ran
]