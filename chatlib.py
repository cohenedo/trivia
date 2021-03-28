# Protocol Constants
MSG_COMPONENTS = 3  # Exact number of components in every message: (conn, cmd, data)
ANS_DATA_COMPONENTS = 2  # Exact number of components in every answer data (qid#ans)
LOGIN_DATA_COMPONENTS = 2  # Exact number of components in every login data (username#password)
QUESTION_DATA_COMPONENTS = 6  # Exact number of components in every question data (qid#question#ans1#...#ans4)
CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message
ERROR_RETURN = None  # returned in case of an error

# Protocol Client Commands
login_msg = "LOGIN"
logout_msg = "LOGOUT"
logged_msg = "LOGGED"
get_question_msg = "GET_QUESTION"
send_answer_msg = "SEND_ANSWER"
my_score_msg = "MY_SCORE"
highscore_msg = "HIGHSCORE"
CLIENT_COMMANDS = [login_msg, logout_msg, logged_msg, get_question_msg, send_answer_msg,
                   my_score_msg, my_score_msg, highscore_msg]

# Protocol Server Commands
login_ok_msg = "LOGIN_OK"
error_msg = "ERROR"
logged_answer_msg = "LOGGED_ANSWER"
your_question_msg = "YOUR_QUESTION"
correct_answer_msg = "CORRECT_ANSWER"
wrong_answer_msg = "WRONG_ANSWER"
your_score_msg = "YOUR_SCORE"
all_score_msg = "ALL_SCORE"
no_questions_msg = "NO_QUESTIONS"
SERVER_COMMANDS = [login_ok_msg, error_msg, logged_answer_msg, your_question_msg,
                   correct_answer_msg,
                   wrong_answer_msg, your_score_msg, all_score_msg, no_questions_msg]


def split_data(data, expected_fields):
    """
    Helper method. gets a string and number of expected fields in it. Splits the string
	using protocol's data field delimiter (#) and validates that there are correct number of fields.
    :param data: data (str) to split
    :param expected_fields: number of expected fields to split to
    :return: list of fields if all ok. If some error occurred, returns None
    """
    data_error = [ERROR_RETURN for _ in range(expected_fields)]
    data = data.split(DATA_DELIMITER)
    if len(data) != expected_fields:
        return data_error
    return data


def join_data(data):
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter
    :param data: list of data fields to join using data delimiter (#)
    :return: string that looks like cell1#cell2#cell3
    """
    return DATA_DELIMITER.join([str(elem) for elem in data])


def build_message(cmd, data):
    """
    build and return message matching the protocol
    :param cmd: command (str) matching the defined protocol
    :param data: content (str) to send, can be empty ("")
    :return: message matching the defined protocol
    """
    data = str(data)
    data_length = len(data)
    if data_length > MAX_DATA_LENGTH or cmd not in SERVER_COMMANDS + CLIENT_COMMANDS:
        return ERROR_RETURN
    for _ in range(CMD_FIELD_LENGTH - len(cmd)):
        cmd += ' '
    for _ in range(LENGTH_FIELD_LENGTH - len(str(data_length))):
        data_length = '0' + str(data_length)
    return DELIMITER.join([cmd, data_length, data])


def parse_message(msg):
    """
    Parses protocol message and returns command name and data field
    :param msg: message (str) to parse
    :return: cmd (str), data (str). If some error occurred, returns None, None
    """

    msg = msg.split(DELIMITER)
    if len(msg) != MSG_COMPONENTS:
        return ERROR_RETURN, ERROR_RETURN

    cmd = msg[0]
    data_length = msg[1]
    data = msg[2]

    if len(cmd) != CMD_FIELD_LENGTH or len(data_length) != LENGTH_FIELD_LENGTH \
            or len(data) > MAX_DATA_LENGTH:
        return ERROR_RETURN, ERROR_RETURN
    cmd = cmd.replace(" ", "")

    try:  # data_length may not be an integer
        data_length = int(data_length.replace(" ", ""))
    except ValueError:
        return ERROR_RETURN, ERROR_RETURN
    if data_length != len(data) or cmd not in SERVER_COMMANDS + CLIENT_COMMANDS:
        return ERROR_RETURN, ERROR_RETURN

    return cmd, data


def build_login_data(username, password):
    return username + "#" + password


def build_question(q_num, question, answers):
    return join_data([q_num] + [question] + answers), q_num


def parse_answer(data):
    return split_data(data, ANS_DATA_COMPONENTS)


def parse_login(data):
    return split_data(data, LOGIN_DATA_COMPONENTS)


def parse_question(question):
    return split_data(question, QUESTION_DATA_COMPONENTS)


def build_answer(qid, answer):
    return join_data([qid, answer])
