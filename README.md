# Trivia
Trivia game for multiple users over a network made for fun and learning purposes. 

## Usage
1. Run server.py
2. Run client.py for every user who wishes to play the game.
3. Log in with one or more of the following users:
    - user1: pass1
    - user2: pass2
    - user3: pass3
4. Play the game :)

## CLI
### Server
- `python .../server.py -r` or `python .../server.py --reset` resetting user database and loading new questions (default=10 question).
- `python .../server.py -r -q=n` or `python .../server.py -r --question=n` resetting user database and load n questions.
- `python .../server.py -p=5678` or `python .../server.py -port=5678` set up server using port 5678 (default).
- `python .../server.py --ip="0.0.0.0"` set up server listen to ip 0.0.0.0 (defalut).
- `python .../server.py -h` or `python .../server.py --help` get help

### Client
- `python .../client.py -p=5678` or `python .../client.py -port=5678` connect to server using port 5678 (default).
- `python .../client.py --ip="127.0.0.1"` connect to server at ip 127.0.0.1 (defalut).
-`python .../client.py -h` or `python .../client.py --help` get help

