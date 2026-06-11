import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

def load_func(filename, func):
    path = SRC / filename
    spec = importlib.util.spec_from_file_location(filename.replace('.py',''), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func)

collect_koica = load_func('01_collect_koica.py', 'collect_koica')
ingest_external = load_func('02_ingest_external.py', 'ingest_external')
build_index = load_func('03_build_index.py', 'build_index')
make_report = load_func('04_dealproof_report.py', 'make_report')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--country', default='베트남')
    ap.add_argument('--item', default='스마트팜 농산물 식품 유통')
    ap.add_argument('--collect-koica', action='store_true')
    ap.add_argument('--pages', type=int, default=3)
    ap.add_argument('--topk', type=int, default=15)
    args = ap.parse_args()

    print('\n[1] ingest external files')
    ingest_external()

    if args.collect_koica:
        print('\n[2] collect KOICA API')
        collect_koica(max_pages=args.pages)
    else:
        print('\n[2] KOICA collect skipped. Use --collect-koica to collect API data.')

    print('\n[3] build unified index')
    build_index()

    print('\n[4] generate DealProof report')
    make_report(args.country, args.item, args.topk)

if __name__ == '__main__':
    main()
