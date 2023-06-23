local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "cot": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/cot.txt",
            "generator_params": generator_params,
            "next_model": "answer_ext"
        },
        "answer_ext": {
            "type": "regex_ext",
            "regex": ".* answer is (.*)\\.",
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "cot"
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}

