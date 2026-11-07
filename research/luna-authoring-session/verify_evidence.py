#!/usr/bin/env python3
"""Verify every selected lossless frame's bytes and decoded pixels."""
import hashlib,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
count=0
for rec in manifest['frames']:
 p=root/rec['lossless_webp_path']
 assert p.is_file(),f'missing {p}'
 data=p.read_bytes()
 assert len(data)==rec['lossless_webp_bytes'],f'length mismatch {p}'
 assert hashlib.sha256(data).hexdigest()==rec['lossless_webp_sha256'],f'file sha mismatch {p}'
 with Image.open(p) as im:
  rgb=im.convert('RGB')
  assert [rgb.width,rgb.height]==rec['resolution'],f'dimensions mismatch {p}'
  assert hashlib.sha256(rgb.tobytes()).hexdigest()==rec['decoded_rgb_sha256'],f'pixel hash mismatch {p}'
 count+=1
print(f'OK: {count} lossless WebP source-frame images matched manifest file and pixel hashes')