import json

from recoma.datasets.reader import DatasetReader, QAExample


@DatasetReader.register("gsm8k")
class GSM8KReader(DatasetReader):
    """
    Dataset reader for the GSM8K dataset format:
    { "question": "<question>", "answer": "<rationale>####<answer>"
    """
    def read_examples(self, file: str):
        qid = 0
        with open(file, 'r') as input_fp:
            for line in input_fp:
                eg_json = json.loads(line.strip())
                question = eg_json["question"]
                rationale = eg_json["answer"]
                answer = rationale.split("####")[-1].strip()
                qid += 1
                yield QAExample(qid=str(qid), question=question, gold_answer=answer, paras=[])
