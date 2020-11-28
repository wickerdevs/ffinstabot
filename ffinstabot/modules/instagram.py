import logging
from instaclient.errors.common import InvaildPasswordError, InvalidUserError, PrivateAccountError
from ffinstabot.classes.instasession import InstaSession
from instaclient import InstaClient
from instaclient import errors
import os, time


def insta_error_callback(driver):
    pass


def insta_update_calback():
    pass


def enqueue_follow():
    pass


def follow(username:str, count:int, instasession:InstaSession):
    # Define client
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    # Scrape followers
    try:
        client.login(instasession.username, instasession.password)
        followers = client.scrape_followers(username, max_wait_time=350, callback=insta_update_calback)
        followed = list()
        failed = 0
        for follower in followers:
            try:
                logging.info(f'Following user <{follower}>')
                client.follow_user(follower)
                logging.info('Followed a user.')
                followed.append()
            except PrivateAccountError:
                logging.info('Followed a user.')
                followed.append()
                pass
            except Exception as error:
                logging.info(f'An error occured when following a user <{follower}>: ', error)
                failed += 0
                pass
            time.sleep(30)

    except (InvalidUserError, InvaildPasswordError):
        pass
    except errors.SuspisciousLoginAttemptError as error:
        pass
    except errors.VerificationCodeNecessary as error:
        pass
    except errors.NotLoggedInError as error:
        pass
    except Exception as error:
        pass

    # Save followed list onto GSheet Database
    


    # Return results or errors