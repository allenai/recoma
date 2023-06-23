import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import _jsonnet

from recoma.control.controller import Controller
from recoma.datasets.reader import Example, DatasetReader
from recoma.models.base_models import BaseModel
from recoma.search.search import SearchAlgo
from recoma.utils.env_utils import get_environment_variables

logger = logging.getLogger(__name__)


@dataclass
class ConfigurableSystems:
    source_json: str
    reader: DatasetReader
    controller: Controller
    search: SearchAlgo


def parse_arguments():
    arg_parser = argparse.ArgumentParser(description='Run inference')
    arg_parser.add_argument('--input', type=str, required=False, help="Input file")
    arg_parser.add_argument('--output_dir', type=str, required=False, help="Output directory")
    arg_parser.add_argument('--config', type=str, required=True, help="Model and Inference config")
    arg_parser.add_argument('--debug', action='store_true', default=False,
                            help="Debug output")
    arg_parser.add_argument('--demo', action='store_true', default=False,
                            help="Demo mode")
    arg_parser.add_argument('--dump_prompts', action='store_true', default=False,
                            help="Dump input prompts -> output in output directory.")
    arg_parser.add_argument('--threads', default=1, type=int,
                            help="Number of threads (use MP if set to >1)")
    return arg_parser.parse_args()


def build_configurable_systems(config_file):
    if config_file.endswith(".jsonnet"):
        ext_vars = get_environment_variables()
        logger.info("Parsing config with external variables: {}".format(ext_vars))
        config_map = json.loads(_jsonnet.evaluate_file(config_file, ext_vars=ext_vars))
    else:
        with open(config_file, "r") as input_fp:
            config_map = json.load(input_fp)

    source_json = config_map
    reader: DatasetReader = DatasetReader.from_dict(config_map["reader"])

    model_map = {}
    for k, v in config_map["models"].items():
        # initialize models
        model_map[k] = BaseModel.from_dict(v)
    controller = Controller(model_list=model_map)

    search = SearchAlgo.from_dict({"controller": controller} | config_map["search"])
    return ConfigurableSystems(source_json=source_json, reader=reader, controller=controller,
                               search=search)


def demo_mode(args, configurable_systems: ConfigurableSystems):
    qid_example_map = {}
    search_algo = configurable_systems.search
    reader = configurable_systems.reader
    if args.input:
        for eg in reader.read_examples(args.input):
            qid_example_map[eg.qid] = eg
    while True:
        qid = input("QID: ")
        if qid in qid_example_map:
            example = qid_example_map[qid]
            print("Using example from input file: " + str(example))
        else:
            question = input("Question: ")
            context = input("Context?:")
            if context.strip():
                paras = [context]
            else:
                paras = []
            example = Example(qid=qid, question=question, gold_answer=None, paras=paras)
        predictions = search_algo.predict(example=example)
        if args.dump_prompts:
            print(predictions.final_state.all_input_output_prompts())
        print(predictions.example.question)
        print(predictions.prediction)
        print(predictions.final_state.to_str_tree())


def inference_mode(args, configurable_systems: ConfigurableSystems):
    print("Running inference on examples")
    example_predictions = []

    if not args.input:
        raise ValueError("Input file must be specified when run in non-demo mode")

    reader = configurable_systems.reader
    search_algo = configurable_systems.search
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(args.output_dir + "/source_config.json", "w") as output_fp:
        output_fp.write(json.dumps(configurable_systems.source_json, indent=2))
    if args.threads > 1:
        import multiprocessing as mp
        mp.set_start_method("spawn")
        with mp.Pool(args.threads) as p:
            example_predictions = p.map(search_algo.predict,
                                        reader.read_examples(args.input))
    else:
        for example in reader.read_examples(args.input):
            example_predictions.append(search_algo.predict(example))
    Path(args.output_dir + "/tree_dump").mkdir(parents=True, exist_ok=True)
    if args.dump_prompts:
        Path(args.output_dir + "/prompts_dump").mkdir(parents=True, exist_ok=True)
    for ex in example_predictions:
        with open(args.output_dir + "/tree_dump/" + ex.example.qid + ".json", "w") as output_fp:
            output_fp.write(ex.final_state.to_json_tree())
        if args.dump_prompts:
            with open(args.output_dir + "/prompts_dump/" + ex.example.qid + "_prompts.txt",
                      "w") as output_fp:
                output_fp.write(ex.final_state.all_input_output_prompts())
    with open(args.output_dir + "/predictions.json", "w") as output_fp:
        prediction_dump = {}
        for x in example_predictions:
            try:
                pred_json = json.loads(x.prediction)
                if not isinstance(pred_json, list):
                    pred_json = x.prediction
            except Exception:
                pred_json = x.prediction
            prediction_dump[x.example.qid] = pred_json
        json.dump(prediction_dump, output_fp)


if __name__ == "__main__":

    parsed_args = parse_arguments()
    logging.basicConfig(level=logging.ERROR)
    if parsed_args.debug:
        logging.getLogger('recoma').setLevel(level=logging.DEBUG)

    config_sys = build_configurable_systems(parsed_args.config)

    if parsed_args.demo:
        demo_mode(args=parsed_args, configurable_systems=config_sys)
    else:
        inference_mode(args=parsed_args, configurable_systems=config_sys)
