from recoma.datasets.reader import DatasetReader, Example


@DatasetReader.register("webshop")
class WebShopReader(DatasetReader):
    """
    Simple dataset reader that returns ids
    """
    def __init__(self, start_num: int = 0, end_num: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.start_num = start_num
        self.end_num = end_num

    def read_examples(self, file: str):
        for i in range(self.start_num, self.end_num):
            yield Example(qid=str(i), question="",
                          gold_answer="Your score (min 0.0, max 1.0): 1.0", paras=[])
