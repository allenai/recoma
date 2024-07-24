import argparse
from copy import deepcopy
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import _jsonnet
import gradio as gr

from recoma.datasets.reader import DatasetReader, QAExample
from recoma.models.core.base_model import BaseModel
from recoma.search.search import SearchAlgo, ExamplePrediction
from recoma.utils.class_utils import import_module_and_submodules
from recoma.utils.env_utils import get_environment_variables
from recoma.utils.state_renderer import StateRenderer

logger = logging.getLogger(__name__)

# import litellm
# litellm.set_verbose=True

@dataclass
class ConfigurableSystems:
    source_json: dict
    reader: DatasetReader
    search: SearchAlgo
    renderers: List[StateRenderer]

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
    return build_configurable_systems_from_json(config_map, output_dir)

def build_configurable_systems_from_json(config_map, output_dir):
    source_json = deepcopy(config_map)
    reader: DatasetReader = DatasetReader.from_dict(config_map["reader"])
    if "renderers" in config_map:
        renderers = [StateRenderer.from_dict(x)
                     for x in config_map["renderers"]]
    else:
        renderers = [StateRenderer.from_dict({"type": "block"}),
                     StateRenderer.from_dict({"type": "simple_json"})]
    model_map = {}
    for k, v in config_map["models"].items():
        # initialize models
        model_map[k] = BaseModel.from_dict(v)
    Path(output_dir + "/files").mkdir(parents=True, exist_ok=True)
    search = SearchAlgo.from_dict({"model_list": model_map, "renderers": renderers,
                                   "output_dir": output_dir + "/files/"} |
                                  config_map["search"])

    return ConfigurableSystems(source_json=source_json, reader=reader, search=search, renderers=renderers)


def demo_mode(args, configurable_systems: ConfigurableSystems):
    qid_example_map = {}
    search_algo = configurable_systems.search
    reader = configurable_systems.reader
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    if args.input:
        for eg in reader.read_examples(args.input):
            qid_example_map[eg.unique_id] = eg
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
            example = QAExample(qid=qid, question=question, gold_answer=None, paras=paras)
        predictions = search_algo.predict(example=example)
        if args.dump_prompts:
            print(predictions.final_state.all_input_output_prompts())
        print(predictions.example.task)
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
            metadata_json = {}
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
            if x.final_state and x.final_state.data:
                metadata_json = x.final_state.data | metadata_json
            if isinstance(x.example.label, list) and len(x.example.label) == 1:
                gold_answer = x.example.label[0]
            else:
                gold_answer = x.example.label
            score = 1 if (x.prediction == gold_answer) else 0
            all_data_dict["correct"] = str(score)
            if metadata_json:
                all_data_dict["metadata"] = metadata_json
            total_score += score
            all_data_fp.write(json.dumps(all_data_dict) + "\n")
            prediction_dump[x.example.unique_id] = pred_json
        print("EM Score: {} ({}/{})".format(100 * total_score / len(example_predictions),
                                            total_score, len(example_predictions)))
        json.dump(prediction_dump, output_fp)


def gradio_demo_fn(args, configurable_systems: ConfigurableSystems,
                   field_values):
    qid_example_map = {}
    search_algo = configurable_systems.search
    reader = configurable_systems.reader
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    if args.input:
        for eg in reader.read_examples(args.input):
            qid_example_map[eg.unique_id] = eg
    kwargs = {}
    idx = 0
    for idx, k in enumerate(QAExample.fields()):
        if k == "paras":
            kwargs[k] = [field_values[idx]]
        else:
            kwargs[k] = field_values[idx]
    example = QAExample(**kwargs)
    if example.unique_id in qid_example_map:
        example = qid_example_map[example.unique_id]
        print("Using example from input file: " + str(example))

    predictions = search_algo.predict(example=example)
    if args.dump_prompts and predictions.final_state:
        print(predictions.final_state.all_input_output_prompts())
    html_renderer = None
    for renderer in configurable_systems.renderers:
        if renderer.output_format == "html":
            html_renderer = renderer
    if html_renderer is None:
        raise ValueError("HTML renderer not found in renderers")
    return json.dumps(predictions.prediction), \
           (html_renderer.output(predictions.final_state)
            if predictions.final_state else "")


def build_gradio_interface(parsed_args, config_sys):

    gradio_fn = lambda *field_values: gradio_demo_fn(parsed_args, config_sys, field_values)

    with gr.Blocks(theme="monochrome") as demo:
        field_values = []
        for field in QAExample.fields():
            field_values.append(gr.Textbox(max_lines=1, label=field))
        # qid = gr.Textbox(max_lines=1, label="QID")
        # question = gr.Textbox(max_lines=1, label="Question")
        # context = gr.Textbox(max_lines=20, label="Context")
        button = gr.Button("Solve")

        answer_output = gr.JSON(label="Answer:")
        with gr.Accordion("More details!", open=False):
            html_output = gr.HTML(label="Inference Tree")

        button.click(gradio_fn, inputs=field_values,
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
