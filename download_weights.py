"""Download EdgeSAM weights into labeler/weights/."""
import os
import sys
import urllib.request

DEST = os.path.join(os.path.dirname(__file__), "labeler", "weights",
                    "edge_sam_3x_vi_t_sam.pth")
URL  = ("https://huggingface.co/chongzhou/EdgeSAM/resolve/main/weights/"
        "edge_sam_3x_vi_t_sam.pth")


def _progress(block_num: int, block_size: int, total_size: int) -> None:
    done = block_num * block_size
    if total_size > 0:
        pct = min(done / total_size * 100, 100)
        bar = "#" * int(pct // 2)
        print(f"\r[{bar:<50}] {pct:5.1f}%  ({done/1e6:.1f}/{total_size/1e6:.1f} MB)",
              end="", flush=True)


def main() -> None:
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    if os.path.exists(DEST):
        print(f"Already downloaded: {DEST}")
        return
    print(f"Downloading EdgeSAM weights...\n  {URL}\n  → {DEST}\n")
    try:
        urllib.request.urlretrieve(URL, DEST, reporthook=_progress)
        print("\nDone!")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
