import json
import pprint

def parse_questions(file_path="Questions.txt"):
    """Parse questions and answers from a text file where answers are indented.
       Supports multiple correct answers (prefixed with '>')."""
    QuestionsAnswers = {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f if line.strip()]  # keep indentation, drop blanks

    question = None
    correct = []
    wrong = []

    for line in lines:
        if line.startswith(" ") or line.startswith("\t"):  # indented = answer
            answer = line.strip()
            if answer.startswith(">"):
                correct.append(answer[1:].strip())  # remove ">"
            else:
                wrong.append(answer)
        else:
            # save previous question if any
            if question is not None:
                QuestionsAnswers[question] = {
                    "correct": correct,
                    "wrong": wrong
                }
            # start new question
            question = line.strip()
            correct = []
            wrong = []

    # save last one
    if question is not None:
        QuestionsAnswers[question] = {
            "correct": correct,
            "wrong": wrong
        }

    return QuestionsAnswers


def save_to_json(data, file_path="Questions.json"):
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    print(f"✅ Questions saved to {file_path}")


def load_from_json(file_path="Questions.json"):
    with open(file_path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


if __name__ == "__main__":
    qa_dict = parse_questions("Questions.txt")
    save_to_json(qa_dict, "Questions.json")

    loaded_dict = load_from_json("Questions.json")
    print("\n🔄 Loaded back from JSON:")
    pprint.pprint(loaded_dict)
    print(len(loaded_dict))