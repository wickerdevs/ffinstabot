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
    TEN = '10'
    TFIVE = '25'
    FIFTY = '50'
    SFIVE = '75'
    RESEND_CODE = 'RESEND_CODE'


class InstaStates:
    """Object to store PTB InstaSession Conversation Handler states indicators"""
    INPUT_VERIFICATION_CODE = 1
    INPUT_USERNAME = 2
    INPUT_PASSWORD = 3
    INPUT_SECURITY_CODE = 4


class FollowStates:
    """Object to store PTB Follow Conversation Handler states indicators"""
    ACCOUNT = 1
    COUNT = 2
    CONFIRM = 3

class Objects:
    PERSISTENCE = 1
    INSTASESSION = 2
    SETTINGS = 3
    FOLLOW = 4