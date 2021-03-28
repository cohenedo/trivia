import select
import socket
import chatlib
import random
import json
import web_questions_loader
import argparse

logged_users = {}  # a dictionary of client hostnames to usernames
client_sockets = []  # logged users sockets
messages_to_send = []  # message = (conn, cmd, data)
users = {}  # users dictionary to be loaded on init
questions = {}  # questions dictionary to be loaded on init

QUESTIONS_JSON = "questions.json"
USERS_JSON = "users.json"
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5678
QUESTIONS_TO_LOAD = 20
MAX_MSG_LENGTH = 1024

parser = argparse.ArgumentParser(description="Play a trivia game")
parser.add_argument("-r", "--reset", action="store_true", help="reset user and questions db")
args = parser.parse_args()


def build_and_append_to_outbox(conn, cmd, data):
    """
    build message using chatlib.build_message according to the protocol and append to messages_to_send
    """
    global messages_to_send
    msg = chatlib.build_message(cmd, data)
    messages_to_send.append((conn, msg))
    return


def send_messages(ready_to_write):
    """
    Send messages to clients who are ready to write
    message = (conn, cmd, data)
    :param ready_to_write: list of ready to write clients
    :return:
    """

    global messages_to_send
    for message in messages_to_send:
        conn, content = message
        if conn in ready_to_write:
            conn.send(content.encode())
            print("[SERVER] ", conn.getpeername(), content)
            messages_to_send.remove(message)
    return


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket, then parses the message using chatlib.
    :param: conn (socket object)
    :return: cmd (str) and data (str) of the received message.
             If error occurred, will return None, None
    """
    msg = conn.recv(MAX_MSG_LENGTH).decode()
    print("[CLIENT] ", conn.getpeername(), msg)  # Debug print
    cmd, data = chatlib.parse_message(msg)
    return cmd, data


def connect_to_client(conn):
    global client_sockets
    (client_socket, client_address) = conn.accept()
    client_sockets.append(client_socket)
    print("New client joined: " + str(client_address))
    print_client_sockets()
    return client_sockets


def print_client_sockets():
    global client_sockets
    print("Current clients:")
    for c in client_sockets:
        print("\t", c.getpeername())
    return


def setup_socket():
    """
    Creates new listening socket and returns it
    :return: the socket object
    """
    print("Setting up server...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()
    print("Listening for clients...")
    return server_socket


# def load_questions_from_txt():
#     """
#     Loads questions bank from file
#     :returns: questions dictionary
#     """
#     global questions
#     with open("questions.txt", "r") as content:
#         questions = ast.literal_eval(content.read())
#     return


def load_from_json(json_name):
    with open(json_name, 'r', encoding='utf-8') as f:
        content = json.load(f)
    return content


def update_json(json_name, content):
    with open(json_name, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    return


def reset_users_json():
    update_json(USERS_JSON, load_from_json("users_backup.json"))


# def load_user_database_from_txt():
#     """
#     :returns: user dictionary from file
#     """
#     global users
#     with open("users.txt", "r") as content:
#         users = ast.literal_eval(content.read())
#     return users


# def update_user_database():
#     """
#     update the changes made to the users dictionary (score and questions asked)
#     :return:
#     """
#     global users
#     with open('users.txt', 'w') as content:
#         content.write(str(users))
#     return


def get_username(conn):
    """
    return username matching the conn
    :param conn: socket object
    :return: username
    """
    global logged_users
    return logged_users[conn.getpeername()]


def create_random_question(username):
    """
    choose a random question from questions (dict) which the user hasn't been asked before
    :return: question (str), q_num(int) or None, None if no more questions left
    """
    global users
    global questions
    if set(users[username]["questions_asked"]) == set(questions.keys()):  # check user has unanswered questions
        return None, None
    while True:
        q_num, value = random.choice(list(questions.items()))
        if q_num not in users[username]["questions_asked"]:
            question = value["question"]
            answers = value["answers"]
            return chatlib.build_question(q_num, question, answers)


def handle_question_message(conn):
    """
    Send question to client using create_random_question()
    :param conn: socket object
    :return:
    """
    global questions
    username = get_username(conn)
    (question, q_num) = create_random_question(username)
    if question is None:
        build_and_append_to_outbox(conn, chatlib.no_questions_msg, "")
    else:
        build_and_append_to_outbox(conn, chatlib.your_question_msg, question)
        users[username]["questions_asked"].append(q_num)
    return


def handle_answer_message(conn, data):
    """
    return feedback for user answer: correct / wrong
    :param conn: socket object
    :param data: qid#choice
    :return:
    """
    global logged_users
    global users
    global questions
    username = get_username(conn)

    qid, choice = chatlib.parse_answer(data)
    choice = int(choice)
    print("correct is", questions[qid]["correct"])
    if qid in users[username]["questions_answered"]:  # ensure user is only submitting one answer for each question
        handle_error(conn, "You may only answer question once")
    elif questions[qid]["correct"] == choice:  # correct answer
        users[username]["score"] += 1
        build_and_append_to_outbox(conn, chatlib.correct_answer_msg, "")
    else:  # wrong answer
        build_and_append_to_outbox(conn, chatlib.wrong_answer_msg,
                                   questions[qid]["correct"])
    users[username]["questions_answered"].append(qid)
    return


def handle_getscore_message(conn):
    """
    Send score to user
    :param conn: socket object
    :return:
    """
    global users
    username = get_username(conn)
    build_and_append_to_outbox(conn, chatlib.your_score_msg, users[username]["score"])


def handle_highscore_message(conn):
    """
    Send highscore to user
    :param conn: socket object
    :return:
    """
    global users
    scores = sorted([(user, value["score"]) for user, value in users.items()], key=lambda x: x[1],
                    reverse=True)
    s = ''
    for tup in scores:
        s = s + str(tup[0]) + ": " + str(tup[1]) + "\n"
    build_and_append_to_outbox(conn, chatlib.all_score_msg, s)


def handle_error(conn, error_msg):
    """
    Handle error using messages_to_send
    :param: socket, message error string from called function, messages_to_send
    :return: messages_to_send
    """
    global messages_to_send
    build_and_append_to_outbox(conn, chatliberror_msg, error_msg)
    return


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    :param: socket and data
    :returns:
    """
    global logged_users
    global messages_to_send
    global users

    username, password = chatlib.parse_login(data)
    if username is None or password is None:
        handle_error(conn, "invalid input")
    elif username not in users or password != users[username]["password"]:
        handle_error(conn, "incorrect username or password")
    elif username in logged_users.values():
        handle_error(conn, "user already logged in")
    else:
        build_and_append_to_outbox(conn, chatlib.login_ok_msg, "")
        logged_users[conn.getpeername()] = username
    return


def handle_logout_message(conn):
    """
    Closes the given socket (in later chapters, also remove user from logged_users dictionary)
    :param: socket
    :returns:
    """
    global logged_users
    global client_sockets
    global messages_to_send

    print("closing connection with client: ", conn.getpeername())
    logged_users.pop(conn.getpeername())
    client_sockets.remove(conn)
    conn.close()
    print_client_sockets()
    return


def handle_logged_message(conn):
    """
    Send logged users to user
    :param conn: socket
    :return:
    """
    global logged_users
    users_list = [value for value in logged_users.values()]
    s = ", ".join(users_list)
    build_and_append_to_outbox(conn, chatlib.logged_answer_msg, s)


def handle_client_message(conn, cmd, data):
    """
    Gets command and data and calls the matching function to handle
    :param: socket, cmd and data
    :returns:
    """
    global logged_users
    global client_sockets
    global messages_to_send
    global users
    global questions

    if cmd == chatlib.login_msg and conn.getpeername() not in logged_users.keys():  # log in user
        handle_login_message(conn, data)
    elif conn.getpeername() in logged_users:  # user is logged in
        if cmd == chatlib.get_question_msg:
            handle_question_message(conn)
        elif cmd == chatlib.send_answer_msg:
            handle_answer_message(conn, data)
        elif cmd == chatlib.logged_msg:
            handle_logged_message(conn)
        elif cmd == chatlib.my_score_msg:
            handle_getscore_message(conn)
        elif cmd == chatlib.highscore_msg:
            handle_highscore_message(conn)
        else:  # (cmd is None and data is None) or (cmd == chatlib.logout_msg):
            handle_logout_message(conn)

    else:
        handle_error(conn, "Error: undefined command")
    return


def main(reset=False):

    global client_sockets
    global messages_to_send
    global users
    global questions

    print("Welcome to Trivia Server!")
    if reset:
        reset_users_json()
        web_questions_loader.load(QUESTIONS_TO_LOAD)
    server_socket = setup_socket()
    questions = load_from_json(QUESTIONS_JSON)
    users = load_from_json(USERS_JSON)

    while True:
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets,
                                                                client_sockets, [])
        for current_socket in ready_to_read:
            if current_socket is server_socket:  # connect to a new client
                connect_to_client(current_socket)
            else:  # read data from existing client
                try:
                    cmd, data = recv_message_and_parse(current_socket)
                    handle_client_message(current_socket, cmd, data)
                except ConnectionError:
                    print("client ", current_socket.getpeername(), "forced disconnect")
                    handle_logout_message(current_socket)
        send_messages(ready_to_write)
        update_json(USERS_JSON, users)


if __name__ == '__main__':
    main(args.reset)
