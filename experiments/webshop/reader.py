from recoma.datasets.reader import DatasetReader, Example


@DatasetReader.register("webshop")
class WebShopReader(DatasetReader):
    """
    Simple dataset reader that returns ids
    """
    def read_examples(self, file: str):
        for i in range(10):
            yield Example(qid=str(i), question="", gold_answer="", paras=[])
