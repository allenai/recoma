import json
from typing import Iterable

from recoma.datasets.reader import DatasetReader, QAExample


def format_drop_answer(answer_json):
    if answer_json["number"]:
        return answer_json["number"]
    if len(answer_json["spans"]):
        return answer_json["spans"]
    # only date possible
    date_json = answer_json["date"]
    if not (date_json["day"] or date_json["month"] or date_json["year"]):
        print("Number, Span or Date not set in {}".format(answer_json))
        return None
    return date_json["day"] + "-" + date_json["month"] + "-" + date_json["year"]


@DatasetReader.register("drop")
class DropReader(DatasetReader):

    def read_examples(self, file: str):
        with open(file, 'r') as input_fp:
            input_json = json.load(input_fp)

        for paraid, item in input_json.items():
            para = item["passage"].strip()
            for qa_pair in item["qa_pairs"]:
                question = qa_pair["question"]
                qid = qa_pair["query_id"]
                answer = format_drop_answer(qa_pair["answer"])
                paras = [para]
                yield QAExample(qid=qid, question=question, gold_answer=answer, paras=paras)
