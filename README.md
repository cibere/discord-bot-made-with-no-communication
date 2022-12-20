This is a project that I want to see how it turns out. Basically like 7 discord bot developers spend time working on the bot.
One at a time, but with no communication.

## Running the discord bot
1. **Make sure to get Python 3.8 or higher.**
This is the minimum version that will run the bot.

2. **Setup venv**
Do `python -m venv venv`

3. **Install dependencies**
Run `pip install -U -r requirements.txt`

4. **Configure the bot**

Create a `config.py` file in the root directory. 
You can paste the following template and fill in necessary information.

```py
token = '' # bot token from discord developer portal
```

The bot also requires `members` and `message_content` intents to function.
