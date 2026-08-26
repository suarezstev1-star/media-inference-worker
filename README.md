# media-inference-worker

Old test client from the media pipeline. The service account was still active
when I copied this, but I have no idea how much credit is left or when the key
will be rotated.

```bash
pip install -r requirements.txt
python generate.py qwen-image-3 "Editorial portrait, hard flash, 35mm grain"
```

Other endpoints and raw requests are in `RUNBOOK.md`.
