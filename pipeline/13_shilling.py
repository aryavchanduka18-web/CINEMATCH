"""Step 13 (advanced, lab only): shilling attack and defense experiment (spec section 14.1)."""
import time

import numpy as np
import scipy.sparse as sp

from cinematch_engine.data.splits import load_split
from cinematch_engine.eval.protocol import sample_eval_users, top_k
from cinematch_engine.models.item_cf import ItemCF
from cinematch_engine.models.svd import FunkSVD
from cinematch_engine.models.user_cf import UserCF
from cinematch_engine.security.shilling import anomaly_score, detection_features, item_stats, make_attack
from pipeline.common import ARTIFACTS, PROCESSED, SEED, get_logger, write_json
from pipeline.models_io import settings

log = get_logger("13_shilling")
N_USERS, FILLER, FLAG_SHARE = 1000, 0.05, 0.06


def models_scores(train: sp.csr_matrix, users: np.ndarray, targets: np.ndarray) -> dict:
    """Predicted rating of each target for each real user, and each user's top-10, per model."""
    n_items = train.shape[1]
    means = np.asarray(train.sum(axis=1)).ravel() / np.maximum(np.diff(train.indptr), 1)
    means = means.astype(np.float32)
    out = {}
    uc, ic, sv = settings("user_cf"), settings("item_cf"), settings("svd")
    seen = [train.indices[train.indptr[u]:train.indptr[u + 1]] for u in users]

    ucf = UserCF(max_neighbors=uc["k"]).fit(train, means)
    scores = []
    for s in range(0, len(users), 250):
        ub = users[s:s + 250]
        idx, vals = ucf.neighbors(ub, uc["min_overlap"], uc["k"])
        scores.append(ucf.score_from(ub, idx, vals, uc["k"], 0.0))
    out["user_cf"] = np.vstack(scores)

    icf = ItemCF(shrinkages=(ic["shrinkage"],), max_neighbors=50).fit(train, means).configure(ic["shrinkage"], ic["neighbors"], 0.0)
    out["item_cf"] = np.vstack([icf.score(users[s:s + 500]) for s in range(0, len(users), 500)])

    svd = FunkSVD(**{k: sv[k] for k in ("n_factors", "n_epochs", "lr_all", "reg_all")}).fit(train)
    out["svd"] = svd.score(users)
    return {m: {"target_pred": sc[:, targets], "top10": top_k(sc, seen, 10)} for m, sc in out.items()}


def summarize(before: dict, after: dict, targets: np.ndarray) -> dict:
    res = {}
    for m in before:
        shift = float(np.mean(after[m]["target_pred"] - before[m]["target_pred"]))
        hit_b = float(np.mean(np.isin(before[m]["top10"], targets).any(axis=1)))
        hit_a = float(np.mean(np.isin(after[m]["top10"], targets).any(axis=1)))
        res[m] = {"prediction_shift": shift, "hit_ratio_before": hit_b, "hit_ratio_after": hit_a}
    return res


def main() -> None:
    t0 = time.time()
    data = load_split(PROCESSED, "val")
    train = data.train
    rng = np.random.default_rng(SEED)
    users = np.sort(rng.choice(sample_eval_users(data, 5000, SEED), size=N_USERS, replace=False))
    counts, _, _ = item_stats(train)
    rated = np.nonzero(counts > 0)[0]
    low = rated[(counts[rated] >= np.quantile(counts[rated], 0.10)) & (counts[rated] <= np.quantile(counts[rated], 0.30))]
    targets = np.sort(rng.choice(low, size=5, replace=False))
    log.info("targets: %s (training ratings %s)", data.item_tmdb[targets].tolist(), counts[targets].tolist())
    baseline = models_scores(train, users, targets)
    results = []
    for kind in ("average", "bandwagon"):
        for size in (0.01, 0.03, 0.05):
            n_fake = int(size * train.shape[0])
            fake = make_attack(train, kind, n_fake, targets, FILLER, rng)
            attacked = sp.vstack([train, fake]).tocsr()
            attacked_scores = models_scores(attacked, users, targets)
            # Defense: flag the most anomalous profiles, remove them, retrain.
            feats = detection_features(attacked)
            score = anomaly_score(feats)
            flagged = np.argsort(-score)[: int(FLAG_SHARE * attacked.shape[0])]
            is_fake = np.zeros(attacked.shape[0], dtype=bool)
            is_fake[train.shape[0]:] = True
            tp = int(is_fake[flagged].sum())
            keep = np.ones(attacked.shape[0], dtype=bool)
            keep[flagged] = False
            cleaned = attacked[keep]
            # real users keep their row order after removal: map evaluated users to their new rows
            new_row = np.cumsum(keep) - 1
            if not keep[users].all():
                kept_users = users[keep[users]]
            else:
                kept_users = users
            defended = models_scores(cleaned, new_row[kept_users], targets)
            base_kept = {m: {"target_pred": baseline[m]["target_pred"][keep[users]],
                             "top10": baseline[m]["top10"][keep[users]]} for m in baseline}
            entry = {
                "attack": kind, "size": size, "fake_profiles": n_fake,
                "attacked": summarize(baseline, attacked_scores, targets),
                "defended": summarize(base_kept, defended, targets),
                "detection": {"flagged": int(len(flagged)), "precision": tp / len(flagged), "recall": tp / n_fake,
                              "false_positive_rate": int((~is_fake[flagged]).sum()) / train.shape[0],
                              "real_users_removed": int((~is_fake[flagged]).sum()),
                              "evaluated_users_removed": int((~keep[users]).sum())},
            }
            results.append(entry)
            log.info("%s %.0f%%: shift %s | detection P %.2f R %.2f", kind, size * 100,
                     {m: round(v["prediction_shift"], 2) for m, v in entry["attacked"].items()},
                     entry["detection"]["precision"], entry["detection"]["recall"])
    write_json(ARTIFACTS / "lab" / "shilling.json", {
        "targets_tmdb": data.item_tmdb[targets].tolist(), "target_training_ratings": counts[targets].tolist(),
        "evaluated_users": N_USERS, "filler_share": FILLER, "flag_share": FLAG_SHARE, "results": results,
        "note": "Lab only. Prediction shift = mean change of the predicted rating for the targets (1-10 scale); "
                "hit ratio = share of real users with a target in their top 10.",
        "seconds": round(time.time() - t0, 1)})
    log.info("done in %.0fs", time.time() - t0)


if __name__ == "__main__":
    main()