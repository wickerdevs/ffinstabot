from datetime import datetime
from random import randrange

from instaclient.classes.instaobject import InstaBaseObject
from ffinstabot.classes.settings import Settings
from rq.job import Job
from rq.registry import DeferredJobRegistry, FailedJobRegistry, ScheduledJobRegistry, StartedJobRegistry, FinishedJobRegistry
from ffinstabot.modules import sheet
from ffinstabot import queue, applogger
from ffinstabot.classes.instasession import InstaSession
from ffinstabot.classes.followsession import FollowSession
from ffinstabot.texts import *

from telegram import ParseMode
from instaclient.errors.common import BlockedAccountError, FollowRequestSentError, InvaildPasswordError, InvalidUserError, PrivateAccountError, RestrictedAccountError, SuspisciousLoginAttemptError
from instaclient import InstaClient
from instaclient import errors
import os, time, logging, random, string


FOLLOW = 'follow'
UNFOLLOW = 'unfollow'
CHECKNOTIFS = 'checknotifs'


def random_string():
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(6)))
    return result_str


def check_job_queue():
    """
    Checks if any jobs are running in the RQ Queue. If that's the case, returns True
    """
    # Check if no other job is in queue
    registry = StartedJobRegistry(queue=queue)
    if len(registry.get_job_ids()) > 0:
        return True
    else:
        return False


def insta_error_callback(driver):
    pass


def init_client():
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)
    return client


def insta_update_calback(obj: FollowSession, message:str, message_id:int=None, timer:bool=False):
    """
    process_update_callback sends an update message to the user, to inform of the status of the current process. This method can be used as a callback in another method.

    Args:
        obj (ScraperorForwarder): Object to get the `chat_id` and `message_id` from.
        message (str): The text to send via message
        message_id (int, optional): If this argument is defined, then the method will try to edit the message matching the `message_id` of the `obj`. Defaults to None.
    """
    from ffinstabot import telegram_bot as bot
    if timer:
        message = message.format(obj.loop_timer())
    if message_id:
        try:
            bot.edit_message_text(text=message, chat_id=obj.user_id, message_id=message_id, parse_mode=ParseMode.HTML)
            return
        except: pass
    bot.send_message(obj.user_id, text=message, parse_mode=ParseMode.HTML)
    return


############################ FOLLOW JOBS ##############################
def enqueue_follow(session:FollowSession):
    if os.environ.get('PORT') not in (None, ""):
        identifier = random_string()
        scrape_id = '{}:{}:{}'.format(FOLLOW, session.target, identifier)
        job = Job.create(follow_job, kwargs={'session': session}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job)
    else:
        result = follow_job(session)
        return result


def follow_job(session:FollowSession) -> bool:
    insta_update_calback(session, logging_in_text, session.get_message_id())
    # Define client
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    # Scrape followers
    try:
        # LOGIN
        session.get_creds()
        client.login(session.username, session.password)
        # SCRAPE
        session.start_timer()
        if session.count == 10:
            wait = 25
        elif session.count == 25:
            wait = 50
        elif session.count == 50:
            wait = 100
        else:
            wait = 150
        followers = client.scrape_followers(session.target, max_wait_time=wait, callback=insta_update_calback, obj=session, message=waiting_scrape_text, message_id=session.get_message_id(), timer=True)
        # Initiating Follow
        insta_update_calback(session, starting_follows_text.format(session.target, session.count), session.get_message_id())
        # FOLLOW
        for index, follower in enumerate(followers):
            if index > session.count-1:
                break
            try:
                applogger.info(f'Following user <{follower}>')
                client.follow_user(follower)
                applogger.debug('Followed a user.')
                insta_update_calback(session, followed_user_text.format(index+1, session.count), session.get_message_id())
                session.add_followed(follower)
            except (PrivateAccountError, FollowRequestSentError):
                applogger.debug('Followed a user.')
                insta_update_calback(session, followed_user_text.format(index+1, session.count), session.get_message_id())
                session.add_followed(follower)
            except (RestrictedAccountError, BlockedAccountError) as error:
                applogger.warning('ACCOUNT HAS BEEN RESTRICTED')   
                session.add_failed(followers[index:])
                insta_update_calback(session, restricted_account_text, session.get_message_id())
                break
            except Exception as error:
                applogger.warning(f'An error occured when following a user <{follower}>: ', error)
                session.add_failed(follower)
            if index < len(followers)-1:
                applogger.info('Followed user <{}>... Waiting...'.format(follower))
                time.sleep(randrange(10, 30))
        client.discard_driver()
        # Save followed list onto GSheet Database
        sheet.save_follows(session.user_id, session.target, followers, session.get_followed())
        insta_update_calback(session, follow_successful_text.format(len(session.get_followed()), session.target), session.get_message_id())
        applogger.info('Done following {} users.'.format(len(session.get_followed())))
        return True

    except (InvalidUserError, InvaildPasswordError):
        session.delete_creds()
        insta_update_calback(session, invalid_credentials_text, session.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        insta_update_calback(session, verification_code_necessary, session.get_message_id())
        return False
    except errors.PrivateAccountError as error:
        insta_update_calback(session, private_account_error_text, session.get_message_id())
        return False
    except Exception as error:
        from ffinstabot import telegram_bot as bot
        applogger.error('An error occured: {}'.format(error))
        bot.report_error(error)
        insta_update_calback(session, operation_error_text, session.get_message_id())
        return False


############################ UNFOLLOW JOBS ##############################
def enqueue_unfollow(session:FollowSession) -> bool:
    if os.environ.get('PORT') not in (None, ""):
        applogger.info('Enqueueing Unfollow Job')
        identifier = random_string()
        scrape_id = '{}:{}:{}'.format(UNFOLLOW, session.target, identifier)
        job = Job.create(follow_job, kwargs={'session': session}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job)
        return True
    else:
        applogger.info('Running Enqueueing Job Locally')
        result = unfollow_job(session)
        return result


def unfollow_job(session:FollowSession) -> bool:
    # Define Client & Log In
    insta_update_calback(session, logging_in_text, session.get_message_id())
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    try:
        client.login(session.username, session.password)
    except (InvalidUserError, InvaildPasswordError):
        session.delete_creds()
        insta_update_calback(session, invalid_credentials_text, session.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        insta_update_calback(session, verification_code_necessary, session.get_message_id())
        return False
    except Exception as error:
        from ffinstabot import telegram_bot as bot
        bot.report_error(error)
        insta_update_calback(session, operation_error_text, session.get_message_id())
        return False

    insta_update_calback(session, retriving_follows_text, session.get_message_id())
    # Get Followed from GSheet Database
    session.set_scraped(sheet.get_scraped(session.get_user_id(), session.get_account()))
    session.set_followed(sheet.get_followed(session.get_user_id(), session.get_account()))
    
    
    # Unfollow Loop
    insta_update_calback(session, initiating_unfollow_text, session.get_message_id())
    session.set_failed(list())
    for index, follower in enumerate(session.get_followed()):
        try:
            client.unfollow_user(follower)
            session.add_unfollowed(follower)
            applogger.info(f'Unfollowed user <{follower}>')
            insta_update_calback(session, unfollowed_user_text.format(len(session.get_unfollowed()), len(session.get_followed())), session.get_message_id())
        except (RestrictedAccountError, BlockedAccountError):
            session.add_failed(session.get_followed()[index:])
            applogger.warning(f'ACCOUNT HAS BEEN RESTRICTED')
        except:
            session.add_failed(follower)
            applogger.warning(f'Failed unfollowing user <{follower}>')

    # Discard driver
    client.discard_driver()

    # Delete record from Database
    sheet.delete_follow(session.get_user_id(), session.get_account())

    text = unfollow_successful_text.format(len(session.get_unfollowed()), len(session.get_followed()))
    if len(session.get_failed()) > 0:
        text += '\n<b>Failed:</b>'
        for user in session.get_failed():
            text += f'\n- <a href="https://www.instagram.com/{user}">{user}</a>'

    insta_update_calback(session, text, session.get_message_id())
    return True


############################ NOTIFICATIONS JOBS ##############################
def enqueue_checknotifs(settings:Settings, instasession:InstaSession) -> bool:
    if os.environ.get('PORT') not in (None, ""):
        applogger.info('Enqueueing CheckNotifs Job')
        identifier = random_string()
        scrape_id = '{}:{}:{}'.format(CHECKNOTIFS, settings.account, identifier)
        job = Job.create(follow_job, kwargs={'settings': settings, 'instasession': instasession}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job)
        return True
    else:
        applogger.info('Running CheckNotifs Job Locally')
        result = checknotifs_job(settings, instasession)
        return result


def schedule_checknotifs(settings:Settings, instasession:InstaSession) -> bool:
    pass


def checknotifs_job(settings:Settings, instasession:InstaSession) -> bool:
    # Get Notifs from Database
    last_notification = sheet.get_notification(settings.get_user_id())
    # Init & Login 
    insta_update_calback(settings, logging_in_text, settings.get_message_id())
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    from ffinstabot import telegram_bot as bot

    try:
        client.login(instasession.username, instasession.password)
    except (InvalidUserError, InvaildPasswordError):
        instasession.delete_creds()
        insta_update_calback(settings, invalid_credentials_text, settings.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        insta_update_calback(settings, verification_code_necessary, settings.get_message_id())
        return False
    except Exception as error:
        bot.report_error(error)
        insta_update_calback(settings, operation_error_text, settings.get_message_id())
        return False
    # Scrape New Notifications
    try:
        notifications = client.check_notifications([InstaBaseObject.GRAPH_FOLLOW], 50)
        if len(notifications) < 1:
            # No notifications found
            return False
    except Exception as error:
        bot.report_error(error)
        insta_update_calback(settings, operation_error_text, settings.get_message_id())
        return False

    # Confront notifications
    new_notifs = list()
    notifications = sorted(notifications)
    if last_notification is None:
        # No last notification found
        pass
    elif notifications == []:
        # No New notifications
        insta_update_calback(settings, no_new_notifications_found_text, settings.get_message_id())
        return True
    else:
        for notification, index in enumerate(notifications):
            if notification == last_notification:
                new_notifs = notifications[index:]
                break

    # Follow new users & send message
    insta_update_calback(settings, operation_error_text, settings.get_message_id())
    failed = list()
    for notification, index in enumerate(new_notifs):
        try:
            client.send_dm(notification.from_user.username, settings.get_text())
            time.sleep(randrange(25-45))
        except PrivateAccountError:
            failed.append(notification.from_user.username)
            continue
        except (RestrictedAccountError, BlockedAccountError):
            # Cancel Schedules for 24 hours
            """ registry = ScheduledJobRegistry(queue=queue)
            now = datetime.utcnow()
            ids = registry.get_job_ids()
            for id in ids:
                job = queue.fetch_job(id)
                enqueue_time = job.enqueued_at
                
                # Check if job is within 24 hour range to cancel
                job.cancel() """
            # Add failed
            failed.append(new_notifs[index:])
            # Set last notification to last successful processed notification
            if index != 0:
                last = new_notifs[index-1]
                sheet.set_notification(settings.get_user_id(), last)
            return False
        except Exception as error:
            # Add failed
            failed.append(notification.from_user.username)
            bot.report_error(error)
            continue

    # Save Last Notification
    last_notification = notifications[len(notifications)-1]
    sheet.set_notification(settings.get_user_id(), last_notification)