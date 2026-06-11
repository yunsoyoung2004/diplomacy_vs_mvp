import os
import re
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RAW_KOICA = DATA / 'raw_koica'
EXTERNAL = DATA / 'external'
PROCESSED = DATA / 'processed'
OUTPUTS = ROOT / 'outputs'

for p in [RAW_KOICA, EXTERNAL, PROCESSED, OUTPUTS]:
    p.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / '.env')

def get_key(*names):
    for n in names:
        v = os.getenv(n)
        if v:
            return v.strip()
    return ''

def mask_key(k):
    if not k:
        return 'MISSING'
    if len(k) < 10:
        return '***'
    return k[:4] + '...' + k[-4:]

def clean_text(x):
    if x is None:
        return ''
    s = str(x)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_country(x):
    s = clean_text(x)
    aliases = {
        'viet nam': '베트남', 'vietnam': '베트남', '베트남': '베트남',
        'indonesia': '인도네시아', '인니': '인도네시아', '인도네시아': '인도네시아',
        'philippines': '필리핀', '필리핀': '필리핀',
        'thailand': '태국', '태국': '태국',
        'mongolia': '몽골', '몽골': '몽골',
        'uzbekistan': '우즈베키스탄', '우즈베키스탄': '우즈베키스탄',
        'kenya': '케냐', '케냐': '케냐',
        'ghana': '가나', '가나': '가나',
    }
    return aliases.get(s.lower(), s)
