local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "decomp_control": {
            "type": "decomp_control",
            "use_number_format": true,
            "decomp_model": "decomp",
            "qa_model": "router",
        },
        "decomp": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/decompv2.txt",
            "generator_params": generator_params,
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
        "start_model": "decomp_control",
        "answerer": {
            "type": "root"
        }
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}

