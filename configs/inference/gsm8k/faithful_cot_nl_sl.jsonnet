local generator_params = import "../common/default_gpt_gpt3.5.libsonnet";
{
    "models": {
        "program_cot": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/gsm8k/faithful_cot_nl_sl.txt",
            "generator_params": generator_params + {"stop": ["\n\n"], "max_tokens": 500},
            "next_model": "program_exec",
        },
        "program_exec": {
            "type": "math_exec",
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "program_cot"
    },
    "reader": {
      "type": "gsm8k"
    }
}