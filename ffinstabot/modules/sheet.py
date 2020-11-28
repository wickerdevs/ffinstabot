from os import replace
from gspread.client import Client
import jsonpickle
from ffinstabot import LOCALHOST
from gspread.models import Spreadsheet, Worksheet
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os, re
import json
from datetime import datetime
from ffinstabot.config import secrets



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
            print('DATABASE: Resorted to local JSON file')
            with open('ffinstabot/config/client_secret.json') as json_file:
                client_secret_dict = json.load(json_file)
        else:
            # CODE RUNNING ON SERVER
            client_secret_dict = json.loads(client_secret)

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            client_secret_dict, scope)
        creds_string = jsonpickle.encode(creds)
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
    logs = spreadsheet.get_worksheet(3)                     
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
    row = find_by_username(settings.user_id)
    if row is not None:
        sheet.delete_row(row)
    # Create new record
    sheet.append_row([settings.user_id, settings.text, str(settings.frequency), settings.account, str(settings.period)])
    log(datetime.utcnow(), settings.user_id, f'SET SETTINGS: {settings.account}')


############################### FOLLOWS SHEET ################################
def save_follows(user_id:int, account:str, scraped:list, followed:list):
    """
    Save follows onto the database.

    Args:
        user_id (int): Telegram ID of the user who requested the action
        account (str): Instagram username of the account that has been scraped
        scraped (list): List of Instagram scraped usernames
        followed (list): List of Instagram followed accounts
    """
    spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(1)
    # Format Scraped
    scraped_string = str(scraped)
    scraped_string = scraped_string.replace('[', '')
    scraped_string = scraped_string.replace(']', '')
    scraped_string = scraped_string.replace("'")
    # Format Followed
    followed_string = str(followed)
    followed_string = followed_string.replace('[', '')
    followed_string = followed_string.replace(']', '')
    followed_string = followed_string.replace("'")

    sheet.append_row([user_id, account, scraped_string, followed_string])
    log(datetime.utcnow(), user_id, f'FOLLOW: {account}')


def find_follow(user_id:int, account:str, sheet:Worksheet=None) -> None or int:
    """
    Returns the GSheet Index of the record matching the ``user_id`` and ``account`` arguments. If no record is found, None is returned.
    Each record consists of a list, reppresenting a row of the GSheet Database.

    Args:
        user_id (int): Telegram ID of the user who saved the followed list.
        account (str): Instagram account username scraped.

    Returns:
        None or int: None if no record is found, int if a record is found.
    """
    if not sheet:
        spreadsheet = auth()
        sheet:Worksheet = spreadsheet.get_worksheet(1)
    rows = sheet.get_all_values()
    selected_row = None
    for row, index in enumerate(rows):
        if row[0] == user_id and row[1] == account:
            selected_row = index+1
            break
    return selected_row


def get_follow_data(user_id:int, account:str) -> None or list:
    """
    Returns record row matching the ``user_id`` and ``account`` arguments. Returns None if no record is found.

    Args:
        user_id (int): Telegram ID of the user who saved the followed list.
        account (str): Instagram account username scraped.

    Returns:
        None or list: None if no record is found, list if a record is found.
    """
    spreadsheet = auth()
    sheet:Worksheet = spreadsheet.get_worksheet(1)
    selected_row = find_follow(user_id, account, sheet)
    if selected_row is None:
        return None
    else:
        rows = get_rows(sheet)
        return rows[selected_row-1]

    
def get_followed(user_id:int, account:str) -> None or list:
    data = get_follow_data(user_id, account)
    if data is None:
        return None
    followed_string = data[3]
    followed = followed_string.split(',')
    return followed


def get_scraped(user_id:int, account:str) -> None or list:
    data = get_follow_data(user_id, account)
    if data is None:
        return None
    scraped_string = data[2]
    scraped = scraped_string.split(',')
    return scraped

    
def delete_follow(user_id:int, account:str) -> bool:
    spreadsheet = auth()
    sheet = spreadsheet.get_worksheet(1)
    index = find_follow(user_id, account, sheet)
    if index is not None:
        sheet.delete_row(index)
        return True
    else:
        return False


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

    settings = spreadsheet.add_worksheet(title='Settings', rows=6, cols=4)
    settings.append_row(['USER ID', 'DEFAULT TEXT', 'FREQUENCY', 'ACCOUNT'])

    follows = spreadsheet.add_worksheet(title='Follows', rows=50, cols=5)
    follows.append_row(['REQUESTED BY', 'ACCOUNT TO SCRAPE', 'SCRAPED', 'FOLLOWED', 'PERIOD'])

    notifications = spreadsheet.add_worksheet(title='Notifications', rows=50, cols=5)
    notifications.append_row(['USER ID', 'LAST NOTIFICATION'])

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