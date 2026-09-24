.PHONY: demo manuscript validate clean
demo:
	python run_all.py --mode demo
validate:
	python validation/validate_outputs.py --mode demo
manuscript:
	python run_all.py --mode manuscript --config config.manuscript.yml
clean:
	python -c "from pathlib import Path; import shutil; [shutil.rmtree(p) for p in [Path('results'),Path('results_manuscript')] if p.exists()]"

