local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "answer_only": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/answer_only.txt",
            "generator_params": generator_params
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "answer_only"
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}