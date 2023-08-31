local generator_params = import "../common/default_gpt_gpt3.5.libsonnet";
{
    "models": {
        "l2m_control": {
            "type": "l2m_control",
            "l2m_decomp_model": "l2m_decomp",
            "l2m_qa_model": "l2m_qa",
            "next_model": "answer_ext",
        },
        "l2m_decomp": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/gsm8k/l2m_decomp.txt",
            "generator_params": generator_params + { "max_tokens": 200 },
        },
        "l2m_qa": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/gsm8k/l2m_qa.txt",
            "generator_params": generator_params + { "max_tokens": 300 }
        },
        "answer_ext": {
            "type": "regex_ext",
            "regex": ".* answer is (.*)\\.",
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "l2m_control"
    },
    "reader": {
      "type": "gsm8k"
    }
}