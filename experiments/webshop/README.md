# Running WebShop


## Set up

1. Create a conda environment
2. Install the ReComA dependencies (from root directory)
3. Install additional requirements (`additional_requirements.txt`)


## Run Inference

Run following command from the root directory

```shell
python -m recoma.run_inference \
    --input /dev/null  \
    --config experiments/webshop/react.jsonnet \
    --output_dir output/ \
    --include-package experiments \
    --debug --gradio_demo
```

Enter session number (e.g. 2) as question id in the gradio demo at `http://localhost:7860/`.