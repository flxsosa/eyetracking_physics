"""A basic parser for .asc files recorded from the EyeLink tracker."""

from collections import namedtuple
import re

# Precompile all regex patterns for better performance
BLOCK_START_RE = re.compile(r'MSG\s+(\d+)\s+BLOCK_START')
BLOCK_END_RE = re.compile(r'MSG\s+(\d+)\s+BLOCK_END') 
TRIAL_START_RE = re.compile(r'MSG\s+(\d+)\s+TRIAL_START')
TRIAL_END_RE = re.compile(r'MSG\s+(\d+)\s+TRIAL_END')
BUTTON_PRESS_RE = re.compile(r'MSG\s+(\d+)\s+BUTTON_PRESS\s+([a-z_]+)')
VIDEO_START_RE = re.compile(r'MSG\s+(\d+)\s+VIDEO_START')
TRIAL_VAR_RE = re.compile(r'MSG\s+(\d+)\s+!V\s+TRIAL_VAR\s+([a-z_]+)\s+([a-z0-9_.]+)')
FIXATION_RE = re.compile(r'EFIX (L|R)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)')
SACCADE_RE = re.compile(r'ESACC (L|R)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)')
BLINK_RE = re.compile(r'EBLINK (L|R)\s+(\d+)\s+(\d+)\s+(\d+)')
GAZE_RE = re.compile(r'(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+).*\.\.\.') 

# Parser data types
Fixation = namedtuple('Fixation', ['start', 'stop', 'x', 'y'])
Gaze = namedtuple('Gaze', ['time', 'x', 'y', 'pupil'])
Mouse = namedtuple('Mouse', ['time', 'x', 'y'])
Saccade = namedtuple('Saccade', ['start', 'stop', 'start_x', 'start_y', 'end_x', 'end_y', 'amp', 'peak_vel'])
Blink = namedtuple('Blink', ['start', 'stop'])

def parse_eyedata(asc_file='data/pilots/test/raw.asc') -> dict:
    """Parses .asc files recorded from the EyeLink eye tracker."""
    # Trial lists
    trials = []
    # Block information
    block_idx = None
    block_time_start = None
    block_time_end = None
    block_duration = None

    # Trial information
    trial_idx = None
    trial_time_start = None
    trial_time_end = None
    trial_duration = None
    button_response = None
    stim_onset_time = None
    scene_name = None
    response_time = None
    trial = {}

    # Event lists
    fixations = []
    saccades = []
    blinks = []
    gaze = []

    with open(asc_file, 'r') as f:
        for line in f:
            # Parse trial start messages e.g. "MSG 314108 BLOCK_START"
            if m := BLOCK_START_RE.match(line):
                block_time_start = float(m.group(1)) / 1000
                continue

            # Parse trial end messages e.g. "MSG 314108 BLOCK_END"
            if m := BLOCK_END_RE.match(line):
                block_time_end = float(m.group(1)) / 1000
                block_duration = block_time_end - block_time_start
                block_idx = None
                continue
            
            # Parse trial start messages e.g. "MSG 314108 TRIAL_START"
            if m := TRIAL_START_RE.match(line):
                trial_time_start = float(m.group(1)) / 1000
                assert trial == {}, ValueError("Should be empty")
                continue

            # Parse trial end messages e.g. "MSG 314108 TRIAL_END"
            if m := TRIAL_END_RE.match(line):
                trial_time_end = float(m.group(1)) / 1000
                trial_duration = trial_time_end - trial_time_start
                
                # Build trial dict all at once
                trial = {
                    'block_idx': block_idx,
                    'block_time_start': block_time_start,
                    'block_time_end': block_time_end, 
                    'block_duration': block_duration,
                    'idx': trial_idx,
                    'trial_time_start': trial_time_start,
                    'trial_time_end': trial_time_end,
                    'trial_duration': trial_duration,
                    'response_time': response_time,
                    'scene_name': scene_name,
                    'button_response': button_response,
                    'stimulus_onset_time': stim_onset_time,
                    'gaze': gaze,
                    'fixations': fixations,
                    'saccades': saccades,
                    'blinks': blinks
                }

                trials.append(trial)

                # Reset all trial variables at once
                trial_idx = trial_time_start = trial_time_end = button_response = None
                stim_onset_time = scene_name = response_time = None
                fixations, saccades, blinks, gaze = [], [], [], []
                trial = {}
                continue
            
            # Parse trial end messages e.g. "MSG 314108 BUTTON_PRESS"
            if m := BUTTON_PRESS_RE.match(line):
                button_response = m.group(2)
                continue

            # Parse trial end messages e.g. "MSG 314108 VIDEO_START"
            if m := VIDEO_START_RE.match(line):
                stim_onset_time = float(m.group(1)) / 1000
                continue

            # Parse trial variable messages
            if m := TRIAL_VAR_RE.match(line):
                onset_time = float(m.group(1)) / 1000
                var_name = m.group(2)
                value = m.group(3)
                
                if var_name == 'rt':
                    response_time = float(value)
                elif var_name == 'scene_name':
                    scene_name = value
                elif var_name == 'trial_index':
                    trial_idx = int(value)
                elif var_name == 'block_index':
                    block_idx = int(value)
                continue

            # Parse fixation events
            if m := FIXATION_RE.match(line):
                _, start, stop, dur, x, y, pupil = m.groups()
                start, stop = float(start)/1000, float(stop)/1000
                x, y = float(x), float(y)
                fixations.append(Fixation(start, stop, x, y))
                continue

            # Parse saccade events
            if m := SACCADE_RE.match(line):
                groups = m.groups()
                start = float(groups[1])/1000
                stop = float(groups[2])/1000
                start_x, start_y = float(groups[4]), float(groups[5])
                end_x, end_y = float(groups[6]), float(groups[7])
                amp, peak_vel = float(groups[8]), float(groups[9])
                saccades.append(Saccade(start, stop, start_x, start_y, end_x, end_y, amp, peak_vel))
                continue

            # Parse blink events
            if m := BLINK_RE.match(line):
                start = float(m.group(2))/1000
                stop = float(m.group(3))/1000
                blinks.append(Blink(start, stop))
                continue

            # Parse gaze events
            if m := GAZE_RE.match(line):
                onset_time = float(m.group(1))/1000
                x_pos = float(m.group(2))
                y_pos = float(m.group(3))
                pupil = float(m.group(4))
                gaze.append(Gaze(onset_time, x_pos, y_pos, pupil))
                continue

    return trials
