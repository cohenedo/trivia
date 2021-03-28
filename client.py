import socket
import chatlib

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678
ANSWER_OPTIONS = [1, 2, 3, 4]
QUESTION_COMPONENTS = {"id": 0, "question": 1, "answer1": 2, "answer2": 3,
                       "answer3": 4, "answer4": 5}


def build_and_send_message(conn, cmd, data=""):
    """
    Builds a new message using chatlib and sends it.
    :param conn: message destination (socket object)
    :param cmd: command (str) matching the protocol
    :param data: content (str) to be sent, may be empty ("")
    :return:
    """
    msg = chatlib.build_message(cmd, data)
    conn.send(msg.encode())
    return


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket, then parses the message using chatlib.
    :param conn: (socket object)
    :return: cmd (str) and data (str) of the received message.
             If error occurred, will return None, None
    """
    cmd, data = chatlib.parse_message(conn.recv(1024).decode())
    return cmd, data


def connect():
    """
    connect to the server using pre-defined globals
    :return: conn (socket object)
    """
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((SERVER_IP, SERVER_PORT))
    return conn


def error_and_exit(error_msg):
    print(error_msg)
    exit()


def login(conn):
    """
    Asks for a username and password to login, keep asking until connected successfully
    :param conn: socket object
    :return:
    """
    cmd = ""
    while cmd != "LOGIN_OK":
        username = input("Please enter username: \n")
        password = input("Please enter password: \n")
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], username + "#" + password)
        # conn.send(build_login
        cmd, data = recv_message_and_parse(conn)
        if cmd != "LOGIN_OK":
            print(data)
    print("Logged in!")
    return


def logout(conn):
    """
    logout user from connection
    :param conn: socket object
    :return:
    """
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"])
    print("Logged out")
    return


def build_send_recv_parse(conn, cmd, data):
    """
    build message, send it and return parsed message
    :param conn: socket object
    :param cmd: command matching the protocol
    :param data: content to be sent, may be empty("")
    :return: cmd (str), data (str)
    """
    build_and_send_message(conn, cmd, data)
    return recv_message_and_parse(conn)


def get_score(conn):
    cmd, my_score = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["my_score_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["your_score_msg"]:
        print("Your score is: " + my_score)
        return
    error_and_exit("Error: could not get score")


def get_highscore(conn):
    cmd, highscore = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["highscore_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["all_score_msg"]:
        print(highscore)
        return
    error_and_exit("Error: could not get highscore")


# noinspection DuplicatedCode
def play_question(conn):
    """
    Get question, send user's answer, get and print feedback
    :param conn:
    :return:
    """
    cmd, question = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["no_questions_msg"]:
        print("GAME OVER: No more question to show.")
        return

    question = chatlib.split_data(question, 6)  # print question
    for i in range(1, len(question)):
        if i > 1:
            print(str(i - 1) + ". " + str(question[i]))
        else:
            print(question[i])

    while True:  # get answer from user
        answer = input("Please choose the correct answer (1-4)\n")
        try:
            answer = int(answer)
            if answer in ANSWER_OPTIONS:
                break
            print("Invalid answer, Please choose again")
            continue
        except ValueError:
            print("Invalid answer, Please choose again")
            continue

    # send answer and get feedback (correct / wrong)
    answer = [question[QUESTION_COMPONENTS["id"]], answer]
    answer = chatlib.join_data(answer)
    cmd, correct_answer = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer_msg"], answer)
    if cmd == chatlib.PROTOCOL_SERVER["correct_answer_msg"]:
        print("Correct!")
    elif cmd == chatlib.PROTOCOL_SERVER["wrong_answer_msg"]:
        print("Wrong answer, Correct answer is: " + question[1 + int(correct_answer)])
    else:
        error_and_exit("error occurred")


# noinspection DuplicatedCode
def play_question2(conn):
    """
    Get question, send user's answer, get and print feedback
    :param conn:
    :return:
    """
    cmd, question = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["no_questions_msg"]:
        print("GAME OVER: No more question to show.")
        return

    question = chatlib.split_data(question, 6)  # print question
    for i in range(1, len(question)):
        if i > 1:
            print(str(i - 1) + ". " + str(question[i]))
        else:
            print(question[i])

    # send answer and get feedback (correct / wrong)
    for i in range(100):
        for j in range(1, 5):
            answer = j
            answer = [question[QUESTION_COMPONENTS["id"]], answer]
            answer = chatlib.join_data(answer)
            cmd, correct_answer = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer_msg"], answer)
            if cmd == chatlib.PROTOCOL_SERVER["correct_answer_msg"]:
                print("Correct!")
            elif cmd == chatlib.PROTOCOL_SERVER["wrong_answer_msg"]:
                print("Wrong answer, Correct answer is: " + question[1 + int(correct_answer)])
            else:
                error_and_exit("error occurred")


def get_logged_user(conn):
    cmd, logged = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["logged_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["logged_answer_msg"]:
        print(logged)
        return
    print("Error occurred")
    return


def main():
    conn = connect()
    login(conn)
    while True:
        c = input("Please select an action:\n1 - Play a trivia question\n2 - Show My Score\n"
                  "3 - Show Highscore\n4 - Show Logged Users\n5 - Logout\n")
        if c == "1":
            play_question(conn)
        elif c == "2":
            get_score(conn)
        elif c == "3":
            get_highscore(conn)
        elif c == "4":
            get_logged_user(conn)
        elif c == "5":
            logout(conn)
            return
        else:
            print("Invalid option")


if __name__ == '__main__':
    main()
