from flask import Flask, render_template, request

from recoma.datasets.reader import Example
from recoma.run_inference import build_configurable_systems

app = Flask(__name__)

# template_dir = os.path.abspath('alfworld/server/templates') + "/"
template_dir = ""

config_sys = build_configurable_systems("configs/inference/skylight/qtonl.jsonnet", "./")
search_algo = config_sys.search


def answer_question(question):
    global search_algo
    example = Example(qid='9999', question=question, gold_answer=None, paras=[])
    predictions = search_algo.predict(example=example)
    return predictions


def get_param(param_name):
    if param_name in request.args:
        print(param_name + " found in args: " + request.args[param_name])
        return request.args[param_name]
    elif param_name in request.form:
        print(param_name + " found in form: " + request.form[param_name])
        return request.form[param_name]
    else:
        print(param_name + " not found in args or form")
        return None


@app.route("/qa", methods=['POST', 'GET'])
def qa():
    answer = ""
    answer_tree = ""
    orig_question = ""
    question = get_param("question")
    if question:
        predictions = answer_question(question)
        orig_question = "Question: " + question
        answer = "Answer: " + predictions.prediction
        if predictions.final_state:
            answer_tree = "<details><summary>Details</summary>" + \
                          predictions.final_state.to_html_tree() + \
                          "</details>"
    return render_template("base.html", orig_question=orig_question,
                           answer=answer, answer_tree=answer_tree)
