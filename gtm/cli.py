import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parser(desc):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("input")
    p.add_argument("--approve", action="store_true", help="run the full list after reviewing the 10-row sample")
    p.add_argument("--out", default="out")
    return p
