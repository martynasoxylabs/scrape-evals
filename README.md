# Scrape-Evals: an evaluation framework for web scraping engines

Scrape-Evals is an evaluation framework for web scraping engines ("engines") that benchmarks quality and robustness on a fixed dataset. We focus on: (1) whether an engine successfully retrieves page content (Coverage/Success Rate); and (2) how well the retrieved content captures a human-curated core snippet while avoiding noise (Recall/Precision/F1). The F1 score measures content quality by balancing how much important content is captured (recall) against how much irrelevant content is filtered out (precision). In our results, we refer to the F1 score as "quality" for simplicity.

This framework supports APIs for Firecrawl, Apify, ScraperAPI, ScrapingBee, Zyte, and more but also some self-hosted engines like Crawl4AI, Playwright, Puppeteer, Rest, Scrapy, and Selenium. Additional APIs can be easily integrated.

## Results

Below are evaluation results across different engines.

| Engine	          | Coverage (Success Rate) (%)	| Quality (F1) |
|-------------------|-----------------------------|--------------|
| Firecrawl	        | 80.9	                      | 0.68         |
| Oxylabs AI Studio | 80.9	                      | 0.61         |
| Exa	              | 76.3	                      | 0.53         |
| Tavily	          | 67.6	                      | 0.50         |
| ScraperAPI	      | 63.5	                      | 0.45         |
| Zyte	            | 62.9	                      | 0.47         |
| ScrapingBee	      | 60.6	                      | 0.45         |
| Apify	            | 60.2	                      | 0.42         |
| Crawl4ai	        | 58.0	                      | 0.45         |
| Selenium	        | 55.0	                      | 0.40         |
| Scrapy	          | 54.0	                      | 0.43         |
| Puppeteer	        | 53.7	                      | 0.41         |
| Rest (requests)	  | 50.6	                      | 0.36         |
| Playwright	      | 39.5	                      | 0.34         |

## Install

```bash
pip install -r requirements.txt
# Optional: install Playwright browsers if using the Playwright engine
python -m playwright install chromium
```

## Datasets

The `datasets/1-0-0.csv` dataset contains 1,000 web pages with human-annotated ground truth for evaluating how well web scraping engines capture core content while avoiding noise (navigation, ads, footers, etc.). Check the dataset [README](datasets/README.md) for more details.

## How to run

### Single engine

From the `scraper_evals` directory:

```bash
python run_eval.py \
  --scrape_engine rest_scraper \
  --suite quality \
  --output-dir runs \
  --dataset datasets/1-0-0.csv \
  --resume
```

Flags:
- `--resume`: do not delete existing outputs; skip scrape if present
- `--rerun`: start fresh (deletes per-engine output dir)
- `--analysis-only`: recompute metrics only; requires existing outputs
- `--dry-run`: test with temporary directory and limited data (5 tasks); automatically cleans up
- `--max-workers N`: internal per-engine concurrency

Outputs:
- Per-engine summary: `runs/results/<engine>_<suite>.json`
- Per-URL artifacts: `runs/<engine>_<suite>/<task_id>/{task.json,scrape_output.json,grader_output.json}`

### All engines (parallel)

```bash
python run_all.py \
  --dataset datasets/1-0-0.csv \
  --suite quality \
  --output-dir runs \
  --concurrency 6 \
  --resume
```

Notes:
- Use `--rerun` for a fresh run. The runner pre-cleans per-engine dirs, then runs children with `--resume` to avoid concurrent deletes.
- `--timeout-minutes` caps each engine's total run time (default 45).
- Logs are unbuffered; each line is prefixed with the engine name.

### Dry Run Testing

The `--dry-run` option for testing your setup and verifying engines work correctly:

```bash
# Test single engine with dry run
python run_eval.py \
  --scrape_engine selenium_scraper \
  --suite quality \
  --output-dir runs \
  --dataset datasets/1-0-0.csv \
  --dry-run

# Test all engines with dry run
python run_all.py \
  --dataset datasets/1-0-0.csv \
  --dry-run
```

## Metrics

- Coverage (Success Rate): Indicates successful content retrieval when the response returns a valid HTTP status (2xx/3xx), contains substantive content (content_size>0), and represents actual page content rather than access intermediary pages. Rows requiring specific validation text are marked unsuccessful when that text is unavailable.
Snippet Quality Metrics (evaluated on the optimal content window matching the expected text length):

- Recall: Proportion of expected content successfully captured
Precision: Proportion of captured content that matches expected material
F1 Score: Balanced measure combining recall and precision for overall content quality

## Reproducibility

- Seeded dataset; fixed CSV manifest for URLs/snippets
- Engine versions pinned via `requirements.txt`

## Contributing

We welcome contributions! Please feel free to open an issue or submit a pull request.

To contribute:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## Troubleshooting

Having issues? Check out our [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide for solutions to common problems including:

- Missing dependencies and environment setup
- Selenium WebDriver and Playwright browser issues  
- Memory and permission errors
- Network/API connectivity problems
- Dataset and file path issues

**Quick tip**: Use `--dry-run` to test your setup safely with limited data and automatic cleanup.

## License

This repository is made available under the [MIT](/LICENSE) license. By contributing to this repository, you agree to make your contribution publicly available under the same license, and you represent that you have the authority to do so.
