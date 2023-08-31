from recoma.datasets.reader import DatasetReader, Example


@DatasetReader.register("alf")
class AlfWorldReader(DatasetReader):
    """
    Simple dataset reader that reads file names (one per line) from a single text file
    """
    def read_examples(self, file: str):
        with open(file, 'r') as input_fp:
            for line in input_fp:
                qid = line.strip()
                # Answer refers to the reward from the environment. Set to "SUCCESS" to match
                # the return value from the answerer AlfRewardAnswerer
                # Question will have to be populated by loading the PDDL file specified in qid
                yield Example(qid=qid, question="", gold_answer="SUCCESS", paras=[])
