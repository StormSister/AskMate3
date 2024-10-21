from datetime import datetime


def get_current_timestamp():
    current_time = datetime.now()
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


def underline_phrase(list_of_dics, phrase):
    for dict in list_of_dics:
        for key in dict:
            if type(dict[key]) is str:
                if phrase in dict[key]:
                    dict.update({key: dict[key].replace(phrase, f"<mark class='search'>{phrase}</mark>")})
    return list_of_dics


def format_submission_time(epoch_time):
    formatted_time = datetime.fromtimestamp(int(epoch_time)).strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


# list_of_dics = [{'text1': 'Hello World!'}, {'text2': 'Hello Ood!'}, {'text3': 'Hello Gold'}]
# phrase = 'Hello'
#
# print(underline_phrase(list_of_dics, phrase))
