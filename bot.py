import datetime
import sys
import time
import random
import configparser
from enum import Enum

from requests import HTTPError
from movement_bot.channel_bot import ChannelBot
from movement_bot.exercises import ExerciseRegistry
from movement_bot.workout_handler import WorkoutMessageHandler


CONFIG_FILE = 'bot.conf'
C_SEC = 'bot'


class ConfigKey(Enum):
    SERVER = "server"
    PORT = "port"
    USERNAME = "username"
    TOKEN = "token"
    TEAM_NAME = "team_name"
    CHANNEL_NAME = "channel_name"
    EXERCISE_FILE = "exercise_file"
    BOT_ACTIVE_FROM = "bot_active_from"
    BOT_ACTIVE_TO = "bot_active_to"
    BOT_ACTIVE_ON_WEEKEND = "bot_active_on_weekend"
    EXERCISE_BETWEEN_MIN = "exercise_between_min"
    EXERCISE_BETWEEN_MAX = "exercise_between_max"
    EXERCISE_STRENGTH_COUNT = "exercise_strength_count"
    EXERCISE_MOBILITY_COUNT = "exercise_mobility_count"
    CSV_WORKOUTS = "csv_workouts"


def conf_get(conf: configparser.ConfigParser, key: ConfigKey):
    return conf.get(C_SEC, key.value)


def conf_getint(conf: configparser.ConfigParser, key: ConfigKey):
    return conf.getint(C_SEC, key.value)


def conf_getboolean(conf: configparser.ConfigParser, key: ConfigKey):
    return conf.getboolean(C_SEC, key.value)


HELP_TEXT = """
| Command | Description |
| : ----- | :------ |
| **help** | I think you know what this one does... |
| **list** | List currently available exercises the workouts are created from. |
| **done** (**easy**,**medium**,**hard**) | Tell the bot about your accomplished workout. Currently just one workout per "session" is remembered - final one wins.|
| **stats** [*username*] | Show all-workout statistics (in progress). If a valid username is given, show stats for the particular user.|
"""


if __name__ == '__main__':
    c = configparser.ConfigParser()
    c.read(CONFIG_FILE)
    for k in ConfigKey:
        assert conf_get(c, k)
    
    exercise_reg = ExerciseRegistry(
        conf_get(c, ConfigKey.EXERCISE_FILE),
        conf_getint(c, ConfigKey.EXERCISE_STRENGTH_COUNT),
        conf_getint(c, ConfigKey.EXERCISE_MOBILITY_COUNT)
    )

    workout_message_handler = WorkoutMessageHandler(
        exercise_reg,
        conf_get(c, ConfigKey.CSV_WORKOUTS)
    )

    bot = None
    try:
        bot = ChannelBot(
            url=conf_get(c, ConfigKey.SERVER),
            port=conf_getint(c, ConfigKey.PORT),
            username=conf_get(c, ConfigKey.USERNAME),
            token=conf_get(c, ConfigKey.TOKEN),
            team_name=conf_get(c, ConfigKey.TEAM_NAME),
            channel_name=conf_get(c, ConfigKey.CHANNEL_NAME),
            help_text=HELP_TEXT,
            message_handler=workout_message_handler,
            debug=False
        )
        bot.start_listening()
    except HTTPError as e:
        print("An error occured during bot initialisation:")
        print(e)
        sys.exit()

    active_from = conf_getint(c, ConfigKey.BOT_ACTIVE_FROM)
    active_to = conf_getint(c, ConfigKey.BOT_ACTIVE_TO)
    active_on_weekend = conf_getboolean(c, ConfigKey.BOT_ACTIVE_ON_WEEKEND)

    wait_min = conf_getint(c, ConfigKey.EXERCISE_BETWEEN_MIN)
    wait_max = conf_getint(c, ConfigKey.EXERCISE_BETWEEN_MAX)

    while True:
        try:
            current_hour = int(time.strftime("%H"))
            is_week_day = (datetime.datetime.today().weekday() < 5)  # mon = 0, ..., sat = 5, sun = 6
            if (active_from <= current_hour <= active_to) and (is_week_day or active_on_weekend):
                workout_message_handler.store_completed_workouts()
                exercise_reg.create_new_workout_set()

                w_message = exercise_reg.create_training_message_for_current_workout_set()
                bot.send_message_to_channel(w_message)

            wait_minutes = random.randint(wait_min, wait_max)
            print("{} - Next workout in {} minutes...".format(time.strftime("%H:%M"), wait_minutes))
            time.sleep(wait_minutes * 60)
        except KeyboardInterrupt as i:
            print("Stopping bot...")
            sys.exit()
