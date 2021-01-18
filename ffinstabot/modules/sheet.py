from ffinstabot.classes.followsession import FollowSession
from gspread.client import Client
from gspread.models import Spreadsheet, Worksheet
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os, re, json, jsonpickle 
from typing import Optional, TYPE_CHECKING
from datetime import date, datetime
from ffinstabot import applogger
from ffinstabot.config import secrets

if TYPE_CHECKING:
    from instaclient.instagram.notification import Notification



def auth():
    creds_string = secrets.get_var('GSPREAD_CREDS')
    if creds_string == None:
        # use creds to create a client to interact with the Google Drive API
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive']
        # CREDENTIALS HAVE NOT BEEN INITIALIZED BEFORE
        client_secret = os.environ.get('GCLIENT_SECRET')
        if os.environ.get('PORT') in (None, ""):
            # CODE RUNNING LOCALLY
            applogger.debug('DATABASE: Resorted to local JSON file')
            with open('ffinstabot/config/client_secret.json') as json_file:
                client_secret_dict = json.load(json_file)
        else:
            # CODE RUNNING ON SERVER
            client_secret_dict = json.loads(client_secret)

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            client_secret_dict, scope)
        creds_string = jsonpickle.encode(creds)
        if os.environ.get('PORT') in (None, ""):
            secrets.set_var('GSPREAD_CREDS', creds_string)
    creds = jsonpickle.decode(creds_string)
    client = gspread.authorize(creds)

    # IF NO SPREADSHEET ENV VARIABLE HAS BEEN SET, SET UP NEW SPREADSHEET
    if secrets.get_var('SPREADSHEET') == None:
        spreadsheet = set_sheet(client)
        return spreadsheet
    else:
        SPREADSHEET = secrets.get_var('SPREADSHEET')
        spreadsheet = client.open_by_key(SPREADSHEET)
        return spreadsheet


def log(timestamp:datetime, user_id:int or str, action:str):
    spreadsheet = auth()
    logs = spreadsheet.get_worksheet(4)                     
    logs.append_row([str(timestamp), user_id, action])


############################### SETTINGS SHEET #############################
def set_settings(settings):
    """
    set_settings Save settings to GSheet

    Args:
        settings (Settings): Settings object
    """
    spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(0)
    row = find_by_username(settings.user_id, sheet)
    if row is not None:
        sheet.delete_row(row)
    # Create new record
    sheet.append_row([settings.user_id, repr(settings)])
    log(datetime.utcnow(), settings.user_id, f'SET SETTINGS')


def get_settings(user_id:int):
    """
    Return `Setting` object corresponding to the user id.

    Args:
        user_id (int): Telegram user ID to check for

    Returns:
        Setting or None: Setting matching `user_id` attribute
    """
    spreadsheet:Spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(0)
    row = find_by_username(user_id, sheet)
    if row is None:
        return None
    values = sheet.row_values(row)
    string = values[1]
    obj = jsonpickle.decode(string)
    return obj


############################### FOLLOWS SHEET ################################
# New Methods
def get_all_follows(sheet:Worksheet=None):
    if not sheet:
        spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(1)
    rows = get_rows(sheet)[1:]
    follows = list()
    for row in rows:
        follows.append(jsonpickle.decode(row[0]))

    if len(follows) < 1:
        applogger.debug(f'All follows: {follows}')
        return None
    applogger.debug(f'All follows: {follows}')
    return follows


def get_follows(user_id:int, session:str, sheet:Worksheet=None):
    if not sheet:
        spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(1)

    follows = get_all_follows(sheet)
    if not follows:
        return None
    selected = list()
    for follow in follows:
        if follow.get_user_id() == user_id and follow.username == session:
            selected.append(follow)

    applogger.debug(f'Selected follows: {follows}')
    if len(selected) < 1:
        return None
    return selected


def get_follow(user_id:int, session:str, target:str, sheet:Worksheet=None):
    if not sheet:
        spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(1)

    follows = get_follows(user_id, session, sheet)
    applogger.debug(f'ID: {user_id} SESSION: {session}')
    if not follows:
        return None
    applogger.debug(f'Imported selected follows: {follows}')
    for follow in follows:
        if follow.get_target() == target:
            return follow
    return None


def find_follow(user_id:int, session:str, target:str, sheet:Worksheet=None):
    if not sheet:
        spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(1)
    
    follows = get_all_follows(sheet)
    if not follows:
        return None
    for index, follow in enumerate(follows):
        if follow.user_id == user_id and follow.username == session and follow.target == target:
            return index+2
    return None


def save_follows(follow:FollowSession):
    spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(1)

    previous = find_follow(follow.user_id, follow.username, follow.target, sheet)
    if previous:
        sheet.delete_row(previous)

    sheet.append_row([jsonpickle.encode(follow)])


def delete_follow(user_id:int, session:str, target:str):
    spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(1)

    previous = find_follow(user_id, session, target, sheet)
    if previous:
        sheet.delete_row(previous)
        return True
    else:
        return False


################################ NOTIFICATION #########################
def set_notification(user_id:int, notification:'Notification'):
    """
    Insert Notification inside the GSheet Database

    Args:
        user_id (int): Telegram user ID
        notification (Notification): Notification to insert
    """
    spreadsheet:Spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(2)
    row = find_by_username(str(user_id), sheet)
    notifications = dict()
    if row is not None:
        notifications = get_all_notifications(user_id, sheet)
        sheet.delete_row(row)

    # Add New Notification
    notifications[secrets.get_var(f'instasession:{user_id}')] = notification.to_dict()

    sheet.append_row([str(user_id), notifications])
    log(datetime.utcnow(), user_id, 'SET NOTIFICATION')


def get_all_notifications(user_id, sheet=None):
    if not sheet:
        spreadsheet:Spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(2)
    row = find_by_username(str(user_id), sheet)
    if row is None:
        return None
    row = get_rows(sheet)[row-1]
    value = row[1]
    print(value)
    notifications = value
    for item in list(notifications.keys()):
        notifications[item] = Notification.de_json(notifications[item], None)
    if not isinstance(notifications, dict): 
        viewer = notifications.viewer
        notifications = {viewer: notifications}

    return notifications


def get_notification(user_id:int) -> Optional['Notification']: # TODO Change if you implement the scheduler
    """
    Retrive last notification from GSheet Database

    Args:
        user_id (int): Telegram user ID to match

    Returns:
        Notification or None: Notification object (or None if no record is found)
    """
    spreadsheet:Spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(2)
    notis = get_all_notifications(user_id, sheet)
    if not notis:
        return None

    for noti in notis.keys():
        if noti == secrets.get_var(f'instasession:{user_id}'):
            return notis.get(noti)
    return None


############################### MESSAGE #################################
def set_message(user_id, message_id):
    if os.environ.get('PORT') not in (None, ""):
        spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(3)
        row = find_by_username(user_id, sheet)
        if row:
            sheet.delete_row(row)
        sheet.append_row([user_id, message_id])
    else:
        messages = secrets.get_var('MESSAGES')
        if not messages:
            secrets.set_var('MESSAGES', {str(user_id): message_id})
        else:
            messages[str(user_id)] = message_id
            secrets.set_var('MESSAGES', messages)


def get_message(user_id):
    if os.environ.get('PORT') not in (None, ""):
        spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(3)
        row_id = find_by_username(user_id, sheet)
        if not row_id:
            return None
        row = get_rows(sheet)[row_id-1]
        message = int(row[1])
        return message
    else:
        messages = secrets.get_var('MESSAGES')
        if not messages:
            return None
        else:
            return messages.get(str(user_id))
    

############################### GENERAL ################################
def find_by_username(user_id:int, sheet:Worksheet, col:int=1) -> None or int:
    """
    Finds the Row Index within the GSheet Database, matching the ``user_id`` argument.
    Returns None if no record is found.

    Args:
        user_id (int): Telegram ID of the user.
        sheet (Worksheet): Worksheet to check.
        col (int, optional): Column to check. Defaults to 1.

    Returns:
        None or list: None if no record is found, int if the record is found.
    """
    if not sheet:
        spreadsheet = auth()
        sheet = spreadsheet.get_worksheet(0)
    column = sheet.col_values(col)
    rows = list()
    for num, cell in enumerate(column):
        if str(cell) == str(user_id):
            rows.append(num + 1)
    if rows == []:
        return None
    return rows[0]


def get_rows(sheet:Worksheet):
    """
    Get a list of the rows' content from the Google Sheets database.

    :param sheet: GSheets worksheet to get data from
    :type sheet: Worksheet

    :return: List of lists, where each sub-list contains a row's contents.
    :rtype: list
    """
    rows:list = sheet.get_all_values()
    return rows


def get_sheet_url(index:int=0):
    """
    Returns the link of a worksheet

    Args:
        index (int, optional): Index of the sheet to get. Can be either 0, 1 or 2. Defaults to 0.

    Returns:
        str: Url of the selected worksheet
    """
    spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(index)
    url = 'https://docs.google.com/spreadsheets/d/{}/edit#gid={}'.format(spreadsheet.id, sheet.id)
    return url


def set_sheet(client:Client):
    """
    Setup spreadsheet database if none exists yet.
    Will save the spreadsheet ID to Heroku Env Variables or to secrets.json file
    The service email you created throught the Google API will create the new spreadsheet and share it with the email you indicated in the GDRIVE_EMAIL enviroment variable. You will find the spreadsheet database in your google drive shared folder.
    Don't change the order of the worksheets or it will break the code.

    :param client: GSpread client to utilize
    :type client: Client
    :return: The newly created spreadsheet
    :rtype: Spreadsheet
    """
    # CREATE SPREADSHEET
    spreadsheet:Spreadsheet = client.create('FFInstaBot')
    secrets.set_var('SPREADSHEET', spreadsheet.id)

    settings = spreadsheet.add_worksheet(title='Settings', rows=6, cols=2)
    settings.append_row(['USER ID', 'SETTINGS'])

    follows = spreadsheet.add_worksheet(title='Follows', rows=50, cols=1)
    follows.append_row(['FOLLOWS'])

    notifications = spreadsheet.add_worksheet(title='Notifications', rows=50, cols=2)
    notifications.append_row(['USER ID', 'LAST NOTIFICATION'])

    messages = spreadsheet.add_worksheet(title='Messages', rows=10, cols=2)
    messages.append_row(['USER ID', 'MESSAGE ID'])

    # CREATE LOGS SHEET
    logs = spreadsheet.add_worksheet(title="Logs", rows="500", cols="3")
    logs.append_row(["TIMESTAMP", "USER ID", "ACTION"])

    # DELETE PRE-EXISTING SHEET
    sheet = spreadsheet.get_worksheet(0)
    spreadsheet.del_worksheet(sheet)

    # SHARE SPREADSHEET
    spreadsheet.share(value=secrets.get_var('GDRIVE_EMAIL'),
                      perm_type="user", role="owner")
    return spreadsheet