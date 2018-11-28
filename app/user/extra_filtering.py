from flask_login import current_user
from ..models import User

def filter(query_in):
    #If the logged in user is NOT administrator, display the data of the current user only
    if not current_user.is_admin:
        return query_in.filter(User.id==current_user.id)
    return query_in

