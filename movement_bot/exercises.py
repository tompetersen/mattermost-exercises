import itertools
import json
import random
from collections import namedtuple
from enum import Enum
from functools import total_ordering


class ExerciseRegistry:
    """
    Contains all possible exercises and can create workouts from them.
    """
    STRENGTH = 'strength'
    MOBILITY = 'mobility'

    Exercise = namedtuple('Exercise', 'name min max unit')

    @total_ordering
    class Difficulty(Enum):
        EASY = (0, 'easy')
        MEDIUM = (1, 'medium')
        HARD = (2, 'hard')

        def __lt__(self, other):
            if self.__class__ is other.__class__:
                return self.value[0] < other.value[0]
            return NotImplemented

    def __init__(self, exercise_file, strength_count, mobility_count):
        self._strength_count = strength_count
        self._mobility_count = mobility_count

        self._exercises = json.loads(open(exercise_file, 'r').read())

        self.current_workout = dict()

    def _get_exercises(self, difficulty: Difficulty, type: str) -> [Exercise]:
        exercises = self._exercises[difficulty.value[1]][type]
        return list(map(lambda e: self.Exercise(**e), exercises))

    def _choose_exercises(self, exercises: [Exercise], exercise_count: int) -> [Exercise]:
        chosen_exercises = random.sample(exercises, k=exercise_count)
        return chosen_exercises

    def create_new_workout_set(self):
        """ Creates new (easy, medium, hard) workout sets. """
        for diff in self.Difficulty:
            w = self._create_workout(diff)
            self.current_workout[diff.value[1]] = w

    def _create_workout(self, difficulty: Difficulty) -> [(str, int, str)]:
        ex_str = self._choose_exercises(self._get_exercises(difficulty, self.STRENGTH), self._strength_count)
        ex_mob = self._choose_exercises(self._get_exercises(difficulty, self.MOBILITY), self._mobility_count)

        res = []
        for e in itertools.chain(ex_str, ex_mob):
            count = int(random.randint(e.min, e.max))
            res.append((e.name, count, e.unit))
        return res

    def create_training_message_for_current_workout_set(self) -> str:
        """
        Creates a mattermost table style message from the current workout.
        :return: the message
        """
        result = "### Los jetzt - beweg dich!\n"

        result += "| {} | | {} | | {} | |\n| :---- | :---- | :---- | :---- | :---- | :---- |\n".format(*map(lambda d: d.value[1], self. Difficulty))
        for i in range(self._mobility_count + self._strength_count):
            result += "|"
            for diff in sorted(self.Difficulty):
                e = self.current_workout[diff.value[1]][i]
                result += "{} | {} {} |".format(e[0], e[1], e[2])
            result += "\n"

        return result

    def create_exercise_list_message(self) -> str:
        """
        Creates a mattermost table style message for all exercises.
        :return: the message
        """
        result = "### Exercises\n\n"

        for (diff, type) in itertools.product(self.Difficulty, [self.STRENGTH, self.MOBILITY]):
            result += "**{} {}**\n\n".format(diff.value[1], type)
            result += "| Name | Time/Reps |\n| :----- | : ----- |\n"
            for e in self._get_exercises(diff, type):
                result += "| {} | {} - {} {}|\n".format(e.name, e.min, e.max, e.unit)
            result += "\n\n"

        return result
