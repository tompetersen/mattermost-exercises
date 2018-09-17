import csv
import datetime
import os
import random
import re

from movement_bot.channel_bot import ChannelBot
from movement_bot.exercises import ExerciseRegistry
from movement_bot.statistics_generator import generate_stats_for_single_user, generate_stats_for_all_users


class WorkoutMessageHandler:

    CONGRATS = [
        "Great job, NAME!",
        "Well done, NAME!",
        "I like!",
        "much strength! very mobility! wow!",
        "You sir/ma'm deserve a like!",
        "NAME has just finished his/her workout - come on you other couch potatoes!",
        "Excellent, NAME!",
        "Harder, better, faster, stronger - NAME!",
        "I have just seen Arnold Schwarzenegger - Ah no, my bad - it's just NAME.",
        ":+1:",
        ":muscle:",
        "Now back to work, Mr(s). Universe!",
        ":clap:",
        "That... was... awesome, NAME! :open_mouth:",
        "Take this, NAME :beer: - you deserve it!",
        "Rocky would be proud of you, NAME! :boxing_glove:",
    ]

    def __init__(self, exercise_registry: ExerciseRegistry, csv_workout_file):
        self.exercise_registry = exercise_registry
        self.csv_workout_file = csv_workout_file
        self.completed_workouts = dict()

    def handle_message(self, sender_id: str, sender_name: str, message: str, post_id: str, channel_id: str, bot: ChannelBot):
        if re.match(r'(@' + bot.username + ')?\s*list\s*$', message):
            # list exercises
            bot.answer_message_in_channel(channel_id, post_id, self.exercise_registry.create_exercise_list_message())
        elif re.match(r'(@' + bot.username + ')?\s*stats\s*$', message):
            bot.answer_message_in_channel(channel_id, post_id, self._create_stats())
        else:
            done_match = re.match(r'(@' + bot.username + ')?\s*done (?P<diff>easy|medium|hard)\s*$', message)
            stats_match = re.match(r'(@' + bot.username + ')?\s*stats (?P<user_name>[a-zA-Z0-9]+)\s*$', message)
            if done_match:
                # store accomplished workout
                difficulty = done_match.group('diff')
                workout = self.exercise_registry.current_workout[difficulty] # [(str, int, str)]
                self.completed_workouts[sender_id] = {
                    'user_id': sender_id,
                    'user_name': sender_name,
                    'datetime': str(datetime.datetime.now()),
                    'difficulty': difficulty,
                    'workout': "|".join(map(lambda e: "{}:{}".format(e[0],e[1]), workout))
                }

                success_message = random.choice(self.CONGRATS)
                bot.answer_message_in_channel(channel_id, post_id, success_message.replace('NAME', sender_name))
            elif stats_match:
                user_name = stats_match.group('user_name')
                bot.answer_message_in_channel(channel_id, post_id, self._create_user_stats(user_name))
            else:
                # Unknown
                bot.answer_message_in_channel(channel_id, post_id, "I don't get it - try 'help' instead!")

    def _get_stats_from_file(self, user_name=None):
        """
        One result entry is of following form:
        {
            'user_id': '...',
            'user_name': '...',
            'time': '2018-07-29 09:17:13.812189',
            'difficulty': 'easy',
            'workout': 'title1:number1|...|titlen:numbern'
        }
        """
        if not os.path.exists(self.csv_workout_file):
            raise IOError('file not found')

        with open(self.csv_workout_file, 'r') as csv_file:
            fieldnames = ['user_id', 'user_name', 'datetime', 'difficulty', 'workout']
            reader = csv.DictReader(csv_file, fieldnames=fieldnames)
            lines = list(reader)[1:] # ignore header

            if user_name:
                lines = filter(lambda l: l['user_name'] == user_name, lines)

            return list(lines)

    def _create_user_stats(self, user_name) -> str:
        stats = self._get_stats_from_file(user_name)
        return generate_stats_for_single_user(stats, user_name)

    def _create_stats(self) -> str:
        stats = self._get_stats_from_file()
        return generate_stats_for_all_users(stats)

    def store_completed_workouts(self):
        file_exists = os.path.exists(self.csv_workout_file)
        with open(self.csv_workout_file, 'a') as csv_file:
            fieldnames = ['user_id', 'user_name', 'datetime', 'difficulty', 'workout']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            for w in self.completed_workouts.values():
                writer.writerow(w)

        self.completed_workouts.clear()
