import argparse
import socket
import chatlib

ANSWER_OPTIONS = [1, 2, 3, 4]
QUESTION_COMPONENTS = {"id": 0, "question": 1, "answer1": 2, "answer2": 3, "answer3": 4, "answer4": 5}
MAX_MSG_LENGTH = 1024


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
    cmd, data = chatlib.parse_message(conn.recv(MAX_MSG_LENGTH).decode())
    return cmd, data


def build_send_recv_parse(conn, cmd, data=""):
    """
    build message, send it and return parsed message
    :param conn: socket object
    :param cmd: command matching the protocol
    :param data: content to be sent, may be empty("")
    :return: cmd (str), data (str)
    """
    build_and_send_message(conn, cmd, data)
    return recv_message_and_parse(conn)


def connect(server_ip, server_port):
    """
    connect to the server using pre-defined globals
    :return: conn (socket object)
    """
    print("connecting to server...")
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((server_ip, server_port))
        print("Connected: SERVER_IP:", server_ip, "SERVER PORT:", server_port)
        return conn
    except (ConnectionError, TimeoutError):
        error_and_exit("Connection error\nPlease make sure server is up and running and check server ip/port")


def error_and_exit(error_msg="error occurred"):
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
        cmd, data = build_send_recv_parse(conn, chatlib.login_msg, chatlib.build_login_data(username, password))
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
    build_and_send_message(conn, chatlib.logout_msg)
    print("Logged out")
    return


def get_score(conn):
    cmd, my_score = build_send_recv_parse(conn, chatlib.my_score_msg)
    if cmd == chatlib.your_score_msg:
        print("Your score is: " + my_score)
        return
    error_and_exit("Error: could not get score")


def get_highscore(conn):
    cmd, highscore = build_send_recv_parse(conn, chatlib.highscore_msg)
    if cmd == chatlib.all_score_msg:
        print(highscore)
        return
    error_and_exit("Error: could not get highscore")


def print_question(question):
    s = ""
    for i in range(1, len(question)):
        if i > 1:
            s = s + (str(i - 1) + ". " + str(question[i])) + "\n"
        else:
            s = s + str(question[i]) + "\n"
    print(s)


def play_question(conn):
    """
    Get question, send user's answer, get and print feedback
    :param conn:
    :return:
    """
    cmd, question = build_send_recv_parse(conn, chatlib.get_question_msg)
    if cmd == chatlib.no_questions_msg:
        print("GAME OVER: No more question to show.")
        return
    question = chatlib.parse_question(question)
    print_question(question)

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
    answer = chatlib.build_answer(question[QUESTION_COMPONENTS["id"]], answer)
    cmd, correct_answer = build_send_recv_parse(conn, chatlib.send_answer_msg, answer)
    if cmd == chatlib.correct_answer_msg:
        print("Correct!")
    elif cmd == chatlib.wrong_answer_msg:
        print("Wrong answer, Correct answer is: " + question[1 + int(correct_answer)])
    else:
        error_and_exit("Error playing question")


def get_logged_user(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.logged_msg)
    if cmd == chatlib.logged_answer_msg:
        print(data)
        return
    error_and_exit("Error getting logged users")


def main():

    parser = argparse.ArgumentParser(description="trivia game client")
    parser.add_argument("-p", "--port", type=int, default=5678, help="Server port to connect")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Server ip to connect. Input using apostrophes, "
                                                                    "example: --ip=\"127.0.0.1\"")
    args = parser.parse_args()

    server_ip = args.ip
    server_port = args.port

    conn = connect(server_ip, server_port)
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
