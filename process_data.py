import os
import sys
import json
import pandas as pd
import subprocess
version = sys.argv[1]
# wid = 'fred'


trials = []
for file in os.listdir(f"data/exp/{version}/"):
    wid = file.replace('.json', '')
    print(wid)
    # wid = uid.rsplit('-', 1)[1]

    # experimental data
    with open(f"data/exp/{version}/{file}") as f:
        data = json.load(f)
    for i, t in enumerate(data["trial_data"]):
        t["wid"] = wid
        t["trial_index"] = i
        trials.append(t)

    # eyelink data
    edf = f'data/eyelink/{wid}/raw.edf'
    assert os.path.isfile(edf)
    dest = f'data/eyelink/{wid}/samples.asc'
    if os.path.isfile(edf) and not os.path.isfile(dest):
        cmd = f'edf2asc {edf} {dest}'
        output = subprocess.getoutput(cmd)
        if 'Converted successfully' not in output:
            print(f'Error parsing {edf}', '-'*80, output, '-'*80, sep='\n')


os.makedirs(f'data/processed/{version}/', exist_ok=True)
with open(f'data/processed/{version}/trials.json', 'w') as f:
    json.dump(trials, f)


