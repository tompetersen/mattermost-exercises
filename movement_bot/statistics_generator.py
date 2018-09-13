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


def generate_stats_for_all_users(stats:[dict]) -> str:
    # TODO: Extend this one for all users
    count_dict = dict()
    for l in stats:
        user_name = l['user_name']
        if user_name not in count_dict:
            # initialize tuple
            count_dict[user_name] = {'easy': 0, 'medium': 0, 'hard': 0}
        diff = l['difficulty']
        if diff in count_dict[user_name]:
            count_dict[user_name][diff] += 1

    for c in count_dict:
        count_dict[c]['sum'] = sum(count_dict[c].values())

    return str(count_dict)


def generate_stats_for_single_user(stats:[dict], username: str) -> str:
    # TODO: Extend this one for single users
    return username + ": " + str(len(stats))