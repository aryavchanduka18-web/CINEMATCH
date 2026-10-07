"""Run the pipeline steps in order.  python -m pipeline.run_all [--from N] [--only N]"""
import argparse
import importlib
import time

from pipeline.common import get_logger

STEPS = {
    1: "01_download_movielens",
    2: "02_select_catalog",
    3: "03_fetch_tmdb",
    4: "04_fetch_awards_wikidata",
    5: "05_clean",
    6: "06_ratings_prep",
    7: "07_split",
    8: "08_features_content",
    12: "12_load_db",
}
log = get_logger("run_all")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="start", type=int, default=1)
    parser.add_argument("--only", type=int)
    args = parser.parse_args()
    steps = [args.only] if args.only else [n for n in STEPS if n >= args.start]
    for n in steps:
        t0 = time.time()
        log.info("=== step %d: %s ===", n, STEPS[n])
        importlib.import_module(f"pipeline.{STEPS[n]}").main()
        log.info("step %d done in %.0fs", n, time.time() - t0)


if __name__ == "__main__":
    main()