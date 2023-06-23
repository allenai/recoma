local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "decomp": {
            "type": "decomp_lm",
            "prompt_file": "configs/prompts/drop/decomp.txt",
            "generator_params": generator_params,
            "use_number_format": true,
            "next_model": "router"
        },
        "textqa": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/textqa.txt",
            "generator_params": generator_params
        },
        "basic_math": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/basic_math.txt",
            "generator_params": generator_params
        },
        "router": {
            "type": "router"
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "decomp"
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}

