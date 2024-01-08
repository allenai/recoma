import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import _jsonnet
import gradio as gr

from recoma.datasets.reader import Example, DatasetReader
from recoma.models.core.base_model import BaseModel
from recoma.search.search import SearchAlgo, ExamplePrediction
from recoma.utils.class_utils import import_module_and_submodules
from recoma.utils.env_utils import get_environment_variables
from recoma.utils.state_renderer import StateRenderer

logger = logging.getLogger(__name__)


@dataclass
class ConfigurableSystems:
    source_json: str
    reader: DatasetReader
    search: SearchAlgo
    renderer: StateRenderer

def parse_arguments():
    arg_parser = argparse.ArgumentParser(description='Run inference')
    arg_parser.add_argument('--input', type=str, required=False, help="Input file")
    arg_parser.add_argument('--output_dir', type=str, required=True, help="Output directory")
    arg_parser.add_argument('--config', type=str, required=True, help="Model and Inference config")
    arg_parser.add_argument('--debug', action='store_true', default=False,
                            help="Debug output")
    arg_parser.add_argument('--demo', action='store_true', default=False,
                            help="Demo mode")
    arg_parser.add_argument('--gradio_demo', action='store_true', default=False,
                            help="Gradio Demo mode")
    arg_parser.add_argument('--dump_prompts', action='store_true', default=False,
                            help="Dump input prompts -> output in output directory.")
    arg_parser.add_argument("--include-package", type=str, action="append", default=[],
                            help="additional packages to include")
    return arg_parser.parse_args()


def build_configurable_systems(config_file, output_dir):
    if config_file.endswith(".jsonnet"):
        ext_vars = get_environment_variables()
        logger.info("Parsing config with external variables: {}".format(ext_vars))
        config_map = json.loads(_jsonnet.evaluate_file(config_file, ext_vars=ext_vars))
    else:
        with open(config_file, "r") as input_fp:
            config_map = json.load(input_fp)

    source_json = config_map
    reader: DatasetReader = DatasetReader.from_dict(config_map["reader"])
    # TBD Make configurable
    renderer = StateRenderer.from_dict({"type": "block"})
    model_map = {}
    for k, v in config_map["models"].items():
        # initialize models
        model_map[k] = BaseModel.from_dict(v)
    Path(output_dir + "/html_dump").mkdir(parents=True, exist_ok=True)
    search = SearchAlgo.from_dict({"model_list": model_map, "renderer": renderer,
                                   "output_dir": output_dir + "/html_dump/"} |
                                  config_map["search"])

    return ConfigurableSystems(source_json=source_json, reader=reader, search=search, renderer=renderer)


def demo_mode(args, configurable_systems: ConfigurableSystems):
    qid_example_map = {}
    search_algo = configurable_systems.search
    reader = configurable_systems.reader
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
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

    reader = configurable_systems.reader
    search_algo = configurable_systems.search
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(args.output_dir + "/source_config.json", "w") as output_fp:
        output_fp.write(json.dumps(configurable_systems.source_json, indent=2))
    for example in reader.get_examples(args.input):
        example_predictions.append(search_algo.predict(example))
    dump_predictions(args, example_predictions)


def dump_predictions(args, example_predictions: List[ExamplePrediction]):
    # Path(args.output_dir + "/tree_dump").mkdir(parents=True, exist_ok=True)
    if args.dump_prompts:
        Path(args.output_dir + "/prompts_dump").mkdir(parents=True, exist_ok=True)
    # Dump trees and I/O Prompts
    for ex in example_predictions:
        if args.dump_prompts:
            with open(args.output_dir + "/prompts_dump/" + ex.example.qid + "_prompts.txt",
                      "w") as output_fp:
                if ex.final_state:
                    output_fp.write(ex.final_state.all_input_output_prompts())
    # Dump Predictions
    with open(args.output_dir + "/predictions.json", "w") as output_fp, \
            open(args.output_dir + "/all_data.jsonl", "w") as all_data_fp:
        prediction_dump = {}
        total_score = 0
        for x in example_predictions:
            metadata_json = None
            try:
                pred_json = json.loads(x.prediction)
                if not isinstance(pred_json, list) and not isinstance(pred_json, dict):
                    pred_json = x.prediction
                elif isinstance(pred_json, dict):
                    if "metadata" in pred_json:
                        metadata_json = pred_json.pop("metadata")
                    if "answer" in pred_json:
                        pred_json = pred_json["answer"]
            except Exception:
                pred_json = x.prediction
            all_data_dict = x.example.__dict__
            all_data_dict["predicted"] = pred_json
            if isinstance(x.example.gold_answer, list) and len(x.example.gold_answer) == 1:
                gold_answer = x.example.gold_answer[0]
            else:
                gold_answer = x.example.gold_answer
            score = 1 if (x.prediction == gold_answer) else 0
            all_data_dict["correct"] = str(score)
            if metadata_json:
                all_data_dict["metadata"] = metadata_json
            total_score += score
            all_data_fp.write(json.dumps(all_data_dict) + "\n")
            prediction_dump[x.example.qid] = pred_json
        print("EM Score: {} ({}/{})".format(100 * total_score / len(example_predictions),
                                            total_score, len(example_predictions)))
        json.dump(prediction_dump, output_fp)


def gradio_demo_fn(args, configurable_systems: ConfigurableSystems,
                   qid: str, question: str, context: str):
    qid_example_map = {}
    search_algo = configurable_systems.search
    reader = configurable_systems.reader
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    if args.input:
        for eg in reader.read_examples(args.input):
            qid_example_map[eg.qid] = eg

    if qid in qid_example_map:
        example = qid_example_map[qid]
        print("Using example from input file: " + str(example))
    else:
        paras = [context] if context else []
        example = Example(qid=qid, question=question, gold_answer=None, paras=paras)
    predictions = search_algo.predict(example=example)
    if args.dump_prompts and predictions.final_state:
        print(predictions.final_state.all_input_output_prompts())
    return json.dumps(predictions.prediction), \
           (configurable_systems.renderer.to_html(predictions.final_state)
            if predictions.final_state else "")


def build_gradio_interface(parsed_args, config_sys):
    gradio_fn = lambda qid, question, context: gradio_demo_fn(parsed_args, config_sys,
                                                              qid, question, context)
    with gr.Blocks(theme="monochrome") as demo:
        qid = gr.Textbox(max_lines=1, label="QID")
        question = gr.Textbox(max_lines=1, label="Question")
        context = gr.Textbox(max_lines=20, label="Context")
        button = gr.Button("Solve")

        answer_output = gr.JSON(label="Answer:")
        with gr.Accordion("More details!", open=False):
            html_output = gr.HTML(label="Inference Tree")

        button.click(gradio_fn, inputs=[qid, question, context],
                     outputs=[answer_output, html_output])

    return demo


def main():
    parsed_args = parse_arguments()
    logging.basicConfig(level=logging.ERROR)

    if parsed_args.debug:
        logging.getLogger('recoma').setLevel(level=logging.DEBUG)

    if parsed_args.include_package:
        for pkg in parsed_args.include_package:
            import_module_and_submodules(package_name=pkg)

    config_sys = build_configurable_systems(parsed_args.config, parsed_args.output_dir)

    if parsed_args.demo:
        demo_mode(args=parsed_args, configurable_systems=config_sys)
    elif parsed_args.gradio_demo:
        interface = build_gradio_interface(parsed_args=parsed_args, config_sys=config_sys)
        # DON'T SET share=True
        interface.launch(server_name="0.0.0.0")
    else:
        inference_mode(args=parsed_args, configurable_systems=config_sys)


if __name__ == "__main__":
    main()
