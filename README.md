# FFInstaBot
This Telegram Bot can connect to Instagram. It can read user notifications, follow and unfollow users. The bot can be accessed through a Telegram interface.

## Bot Commands
Currently, the bot will be able to respond to the following commands:
- ```/account``` -> Returns the current connection status to the Telegram Client (if the user is logged in and with which Telegram Account)
- ```/login``` -> Asks the user to input Instagram credentials and then attempts to log in.
- ```/logout``` -> Signs out of the Telegram Client and deletes the session.
- ```/follow``` -> Follow a certain number of users who all follow a certain account.
- ```/unfollow``` -> Unfollow previously followed users (using /follow)
- ```/settings``` -> Edit bot settings
- ```/checknotifs``` -> Manually check user notifications.

## Use the Bot
- Create a Heroku Account
- Contact me (@davidwickerhf) and send me your Heroku Email (the email adress you used to create the Heroku account)
    - I will transfer the bot to your account
- Upgrade Heroku Plan
    - The bot is running on a free version of Heroku:
        - Persistence won't work for longer than 30 minutes
        - The Bot is designed to not require a paid Heroku Plan
    - By upgrading your Heroku Plan, the bot will be able to persist and the Telegram Client Sessions will be saved in a database (so you won't have to sign in multiple times)
- Start the Bot
    - Write /start to @ffinstabot to start using the bot
- Read the command reference doc: [Bot Commands]()

## Running the Bot Locally
The bot is built on a Flask Python server in order to be compatible for upload to an online server (such as Heroku)
Follow the steps below to run the bot on your local machine. (These steps don't include the steps to install Python)
1. #### Clone the Repository
    clone the master branch of this repository to your local machine
2. #### Install Ngrok
    Install ngrok from [Ngrok](https://ngrok.com/download)
3. #### Setup secrepts.json file
    Create a file named secrets.json in the [secrets](https://github.com/davidwickerhf/karim/tree/main/karim/secrets) folder. This should include:
    ```
    {
    "SERVER_APP_DOMAIN": "", # insert here the https link you will receive from Ngrok in the next steps
    "DEVS": [427293622], 
    "API_ID": , # get this from https://my.telegram.org/apps
    "API_HASH": "", # get this from https://my.telegram.org/apps
    "API_PHONE": "", # insert here your Telegram phone number
    "BOT_TOKEN": "" # insert here the BOT TOKEN
    }
    ```
4. #### Run ngrok 
    Open your command prompt and navigate to the directory where you saved the Ngrok file. Then type: ```ngrok http 5000```
5. #### Run program
    With the command prompt navigate to the directory where you cloned the git repository and run the followinf commands:
    * ```python -m venv env```
    * ```env/Scripts/activate```
    * ```pip install -r requirements.txt```
    * ```python run.py```
    The last command should launch the bot if everything went correctly.
