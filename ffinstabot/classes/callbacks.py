class Callbacks:
    """Object to store PTB conversations Callbacks"""
    CANCEL = 'CANCEL'
    NONE = 'NONE'
    DONE= 'DONE'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    LOGOUT = 'LOGOUT'
    LOGIN = 'LOGIN'
    SELECT = 'SELECT'
    UNSELECT = 'UNSELECT'
    CONFIRM = 'CONFIRM'
    REQUEST_CODE = 'REQUEST_CODE'
    TEN = 'TEN'
    TFIVE = 'TFIVE'
    FIFTY = 'FIFTY'
    SFIVE = 'SFIVE'
    RESEND_CODE = 'RESEND_CODE'


class ScrapeStates:
    """Object to store PTB Scraoe Conversation Handler states indicators"""
    SELECT_TARGET = 1
    SELECT_COUNT = 2
    CONFIRM = 3
    SELECT_NAME = 4


class InstaStates:
    """Object to store PTB InstaSession Conversation Handler states indicators"""
    INPUT_VERIFICATION_CODE = 1
    INPUT_USERNAME = 2
    INPUT_PASSWORD = 3
    INPUT_SECURITY_CODE = 4


class Objects:
    PERSISTENCE = 1
    INSTASESSION = 2
    SETTINGS = 3
    FOLLOW = 4