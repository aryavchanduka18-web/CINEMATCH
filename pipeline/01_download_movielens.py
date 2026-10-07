"""Step 1: download and unzip MovieLens 32M into data/raw/ml-32m/ (cached, md5-verified)."""
import hashlib
import zipfile

import httpx

from pipeline.common import ML_DIR, RAW, get_logger

URL = "https://files.grouplens.org/datasets/movielens/ml-32m.zip"
log = get_logger("01_download")


def md5_of(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if (ML_DIR / "ratings.csv").exists() and (ML_DIR / "links.csv").exists():
        log.info("MovieLens 32M already unpacked in %s", ML_DIR)
        return
    RAW.mkdir(parents=True, exist_ok=True)
    zip_path = RAW / "ml-32m.zip"
    expected = httpx.get(URL + ".md5", timeout=30, follow_redirects=True).text.split()[0].strip()
    if not zip_path.exists() or md5_of(zip_path) != expected:
        log.info("downloading %s", URL)
        tmp = zip_path.with_suffix(".part")
        with httpx.stream("GET", URL, timeout=120, follow_redirects=True) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_bytes(1 << 20):
                    f.write(chunk)
        tmp.replace(zip_path)
    actual = md5_of(zip_path)
    if actual != expected:
        raise RuntimeError(f"MD5 mismatch for {zip_path}: {actual} != {expected}")
    log.info("md5 verified (%s)", actual)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(RAW)
    log.info("unpacked to %s", ML_DIR)


if __name__ == "__main__":
    main()