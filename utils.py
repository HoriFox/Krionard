import json
import sys
from hashlib import sha256

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def load_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def hash(data):
    return sha256(str(data).encode('utf-8')).hexdigest()
