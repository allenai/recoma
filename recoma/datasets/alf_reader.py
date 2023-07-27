from recoma.datasets.reader import DatasetReader, Example


@DatasetReader.register("drop")
class AlfWorldReader(DatasetReader):

    def read_examples(self, file: str):
        with open(file, 'r') as input_fp:
            for line in input_fp:
                qid = line.strip()
                # answer refers to the reward from the environment
                yield Example(qid=qid, question="", gold_answer="SUCCESS", paras=[])
