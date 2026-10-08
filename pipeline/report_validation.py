"""Readable validation tables: docs/phase-3-results.md (baselines) and docs/phase-4-results.md (MF)."""
import json

from pipeline.common import ARTIFACTS, ROOT

NAMES = {"bias": "Bias baseline", "popularity": "Popularity", "content": "Content-based",
         "user_cf": "User CF", "item_cf": "Item CF", "svd": "Funk SVD", "als": "Implicit ALS"}


def ci(m: dict, digits: int = 4) -> str:
    return f"{m['mean']:.{digits}f} [{m['ci_low']:.{digits}f}, {m['ci_high']:.{digits}f}]"


def table(models: dict) -> list[str]:
    lines = ["| Model | P@10 | R@10 | MAP@10 | NDCG@10 | MAE | RMSE |", "|---|---|---|---|---|---|---|"]
    for key, r in models.items():
        rk, rt = r.get("ranking"), r.get("ratings")
        cells = [ci(rk[m]) if rk else "n/a" for m in ("precision", "recall", "map", "ndcg")]
        cells += [ci(rt[m], 3) if rt else "n/a" for m in ("mae", "rmse")]
        lines.append(f"| {NAMES[key]} | " + " | ".join(cells) + " |")
    lines += ["", "| Model | Coverage | Intra-list diversity | Novelty (bits) | Long-tail share | Mean popularity percentile |",
              "|---|---|---|---|---|---|"]
    for key, r in models.items():
        rk = r.get("ranking")
        if rk:
            lines.append(f"| {NAMES[key]} | {100 * rk['coverage']:.1f}% | {rk['diversity']['mean']:.3f} | "
                         f"{rk['novelty']['mean']:.2f} | {rk['long_tail_share']:.1f}% | {rk['mean_popularity_percentile']:.1f} |")
    lines += ["", "| Model | Tuned settings | Runtime (s) |", "|---|---|---|"]
    for key, r in models.items():
        settings = ", ".join(f"{k}={v}" for k, v in r["settings"].items() if not isinstance(v, dict))
        lines.append(f"| {NAMES[key]} | {settings} | {r.get('runtime_seconds', '')} |")
    return lines


def write(src: str, dest: str, title: str, intro: list[str]) -> None:
    path = ARTIFACTS / "metrics" / src
    if not path.exists():
        return
    data = json.loads(path.read_text())
    lines = [f"# {title}", "", *intro, "",
             f"Validation split, {data['evaluated_users']:,} evaluated users (fixed sample, seed 42), full ranking over "
             f"{data['universe_films']:,} part-A films, relevant = rating >= {data['relevant_threshold']}/10. "
             "Brackets are 95% bootstrap confidence intervals over users. The test split is not used yet.", "",
             *table(data["models"]), "",
             f"Peak memory of the run: {data['peak_memory_mb']:,} MB.", ""]
    checks = {k: v["fold_in_check"] for k, v in data["models"].items() if "fold_in_check" in v}
    if checks:
        lines += ["## Fold-in check", "",
                  "A few users are removed from training, the model is retrained, and the users are folded back in "
                  "from their own ratings. Compared with the model that saw them in training:", "",
                  "| Model | Users | Top-10 overlap | NDCG@10 full training | NDCG@10 fold-in | RMSE full | RMSE fold-in |",
                  "|---|---|---|---|---|---|---|"]
        for k, c in checks.items():
            lines.append(f"| {NAMES[k]} | {c['users']} | {100 * c['top10_overlap']:.0f}% | {c['ndcg_full_training']:.4f} | "
                         f"{c['ndcg_fold_in']:.4f} | {c.get('rmse_full_training', 'n/a') if isinstance(c.get('rmse_full_training'), str) else format(c.get('rmse_full_training', float('nan')), '.3f')} | "
                         f"{format(c.get('rmse_fold_in', float('nan')), '.3f') if 'rmse_fold_in' in c else 'n/a'} |")
        lines.append("")
    (ROOT / "docs" / dest).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    write("validation_baselines.json", "phase-3-results.md", "Phase 3 results: baseline models",
          ["Generated from `artifacts/metrics/validation_baselines.json` by `pipeline/report_validation.py`."])
    write("validation_mf.json", "phase-4-results.md", "Phase 4 results: matrix factorization",
          ["Generated from `artifacts/metrics/validation_mf.json` by `pipeline/report_validation.py`."])


if __name__ == "__main__":
    main()