"""Utilities for partitioning stimuli according to a pseudo latin square."""

import json
import glob
import os
import random

import config


def partition_list(items, num_groups=4):
    n = len(items)
    base_size = n // num_groups
    groups = []
    # Create first three groups of equal size
    for i in range(num_groups-1):
        start = i * base_size
        end = (i + 1) * base_size
        groups.append(items[start:end])
    # Last group gets remaining elements
    groups.append(items[(num_groups-1) * base_size:])
    return groups


def main():
    # Grab all stimuli
    video_paths = glob.glob(os.path.join(config.TRIAL_STIM_DIR,'*_intra.mp4'))
    # Shuffle stimuli
    random.shuffle(video_paths)
    # Partition into four groups
    stimuli_groups = {
        idx:group for idx, group in enumerate(partition_list(video_paths))
    }
    with open('data/latin_square_stimuli.json', 'w') as f:
        json.dump(stimuli_groups, f)
    with open('data/latin_square_stimuli.json', 'r') as f:
        latin_square_stimuli = json.load(f)
        latin_square_stimuli = {
            int(k):v for k,v in latin_square_stimuli.items()}
    print(latin_square_stimuli[0])
    for key in latin_square_stimuli:
        random.shuffle(latin_square_stimuli[key])
    print(latin_square_stimuli[0])


if __name__ == '__main__':
    main()