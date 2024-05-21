import json

from recoma.datasets.reader import DatasetReader, QAExample


@DatasetReader.register("bbh")
class BBHReader(DatasetReader):
    """
    Dataset reader for the BBH-formatted data from https://github.com/suzgunmirac/BIG-Bench-Hard/
    with the format:
        ```
            "examples": [
                {
                "input": "..."
                "target": "..."
                }
            ...
            ]
        ```
    """

    def read_examples(self, file: str):
        with open(file, 'r') as input_fp:
            input_json = json.load(input_fp)
        qid = 0
        for example in input_json["examples"]:
            question = example["input"]
            qid += 1
            answer = example["target"]
            yield QAExample(qid=str(qid), question=question, gold_answer=answer, paras=[])
