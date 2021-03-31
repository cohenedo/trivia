import random
import requests
import json


def load(amount):
    """
    load amount of random question from opentdb.com
    :param amount: amount of questions to be loaded
    :return: question (dict)
    """
    if amount < 1:
        print("number of questions to load must be a positive integer")
        print("using 10 as default value instead")
        amount = 10

    questions = dict()
    print("Loading questions from web... This might take a few seconds")
    print("number of questions to load:", amount)
    i = 0
    while len(questions) < amount:
        url = "https://opentdb.com/api.php?type=multiple&amount=1&difficulty=easy"
        r = requests.get(url)
        question_raw = r.json()["results"][0]
        # first make sure there are no special character caused by mis-encoding of html in source
        if "#" in question_raw["question"] or "&" in question_raw["question"]:
            continue
        elif any(["#" in a for a in question_raw["incorrect_answers"]] + ["&" in a for a in
                                                                          question_raw["incorrect_answers"]]):
            continue
        else:
            questions[i] = dict()
            questions[i]["question"] = question_raw["question"]
            questions[i]["answers"] = question_raw["incorrect_answers"]
            questions[i]["answers"].append(question_raw["correct_answer"])
            random.shuffle(questions[i]["answers"])
            questions[i]["correct"] = questions[i]["answers"].index(question_raw["correct_answer"]) + 1
            i = i + 1

    print("Loading questions complete")
    with open('questions.json', 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)
