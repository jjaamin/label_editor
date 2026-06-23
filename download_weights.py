"""Download EdgeSAM ONNX weights into labeler/weights/."""
import os
import sys
import shutil
import urllib.request

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "labeler", "weights")
HF_REPO = "chongzhou/EdgeSAM"

FILES = [
    ("weights/edge_sam_3x_encoder.onnx", "edge_sam_3x_encoder.onnx"),
    ("weights/edge_sam_3x_decoder.onnx", "edge_sam_3x_decoder.onnx"),
]
HF_BASE_URL = (
    "https://huggingface.co/spaces/chongzhou/EdgeSAM/resolve/main/"
)


def _progress(block_num: int, block_size: int, total_size: int) -> None:
    done = block_num * block_size
    if total_size > 0:
        pct = min(done / total_size * 100, 100)
        bar = "#" * int(pct // 2)
        print(f"\r[{bar:<50}] {pct:5.1f}%  ({done/1e6:.1f}/{total_size/1e6:.1f} MB)",
              end="", flush=True)
    else:
        print(f"\r  Downloaded {done/1e6:.1f} MB", end="", flush=True)


def _download_one(hf_file: str, dest: str) -> bool:
    """Try huggingface_hub first, fall back to urllib. Returns True on success."""
    if os.path.exists(dest):
        print(f"  Already exists: {os.path.basename(dest)}")
        return True

    # Try huggingface_hub
    try:
        from huggingface_hub import hf_hub_download
        print(f"  Downloading via huggingface_hub: {os.path.basename(dest)} …")
        cached = hf_hub_download(repo_id=HF_REPO, filename=hf_file, repo_type="space")
        shutil.copy(cached, dest)
        print(f"  Saved: {dest}")
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"  huggingface_hub failed: {e}")

    # Fallback: direct URL
    url = HF_BASE_URL + hf_file
    print(f"  Downloading via urllib:\n    {url}\n    → {dest}\n")
    try:
        urllib.request.urlretrieve(url, dest, reporthook=_progress)
        print(f"\n  Saved: {dest}")
        return True
    except Exception as e:
        if os.path.exists(dest):
            os.remove(dest)
        print(f"\n  Error: {e}")
        return False


def main() -> None:
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    failed = []
    for hf_file, filename in FILES:
        dest = os.path.join(WEIGHTS_DIR, filename)
        ok = _download_one(hf_file, dest)
        if not ok:
            failed.append(filename)

    if failed:
        print("\nFailed to download:")
        for f in failed:
            print(f"  {f}")
        print(
            "\nManual download:"
            "\n  1) https://huggingface.co/spaces/chongzhou/EdgeSAM"
            "\n     → Files → weights/"
            "\n  2) Download edge_sam_3x_encoder.onnx and edge_sam_3x_decoder.onnx"
            f"\n  3) Place them in: {WEIGHTS_DIR}"
        )
        sys.exit(1)
    else:
        print("\nAll weights ready.")


if __name__ == "__main__":
    main()
