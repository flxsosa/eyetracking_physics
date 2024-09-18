"""A basic parser for .asc files recorded from the EyeLink tracker."""

from collections import namedtuple
import re


# Parser data types
Fixation = namedtuple('Fixation', ['start', 'stop', 'x', 'y'])


Gaze = namedtuple(
    'Gaze',
    ['time', 'x', 'y', 'fixation', 'saccade', 'blink', 'event'])


Mouse = namedtuple('Mouse', ['time', 'x', 'y'])


Saccade = namedtuple(
    'Saccade',
    [
        'start',
        'stop',
        'start_x',
        'start_y',
        'end_x',
        'end_y',
        'amp',
        'peak_vel'
    ])


Blink = namedtuple('Blink', ['start', 'stop'])


def parse_eyedata(asc_file='data/pilots/test/raw.asc') -> dict:
    """Parses .asc files recorded from the EyeLink eye tracker."""
    # Trial lists
    trials = []
    trial_idx = None
    trial_time_start = None
    trial_time_end = None
    button_press_time = None
    stim_onset_time = None
    scene_name = None
    response_time = None
    # Event lists
    fixations = []
    saccades = []
    blinks = []
    gaze = []
    # Flags denoting what event the eye data is related to
    is_fixation_event = False
    is_saccade_event = False
    is_blink_event = False
    event_flag = 'None'
    trial = None
    with open(asc_file, 'r') as f:
        for line in f:
            if line.startswith("SFIX"):
                is_fixation_event = True
                event_flag = 'fixation'
            if line.startswith("SSAC"):
                is_saccade_event = True
                event_flag = 'saccade'
            if line.startswith('SBLINK'):
                is_blink_event = True
                event_flag = 'blink'
            # Parse trial start messages e.g. "MSG 314108 TRIAL_START"
            m = re.match(r'MSG\s+(\d+)\s+TRIAL_START', line)
            if m:
                trial_time_start = list(map(float, m.groups()))[0]
                trial_time_start /= 1000  # to seconds
                # trial_start_times.append(trial_time_start)
                if trial is None:
                    trial = {}
                    trial['start_time'] = trial_time_start
                else:
                    assert ValueError("Should be empty")
                continue
            # Parse trial end messages e.g. "MSG 314108 TRIAL_END"
            m = re.match(r'MSG\s+(\d+)\s+TRIAL_END', line)
            if m:
                trial_time_end = list(map(float, m.groups()))[0]
                trial_time_end /= 1000  # to seconds
                if trial is not None:
                    trial['idx'] = trial_idx
                    trial['end_time'] = trial_time_end
                    trial['gaze'] = gaze
                    trial['fixations'] = fixations
                    trial['saccades'] = saccades
                    trial['blinks'] = blinks
                    trial['response_time'] = response_time
                    trial['scene_name'] = scene_name
                    trial['button_press_time'] = button_press_time
                    trial['stimulus_onset_time'] = stim_onset_time
                    trials.append(trial)
                    trial_idx = None
                    trial_time_start = None
                    trial_time_end = None
                    button_press_time = None
                    stim_onset_time = None
                    scene_name = None
                    response_time = None
                    # Event lists
                    fixations = []
                    saccades = []
                    blinks = []
                    gaze = []
                    # Flags denoting what event the eye data is related to
                    is_fixation_event = False
                    is_saccade_event = False
                    is_blink_event = False
                    event_flag = 'None'
                    trial = None
                continue
            # Parse trial end messages e.g. "MSG 314108 BUTTON_PRESS"
            m = re.match(r'MSG\s+(\d+)\s+BUTTON_PRESS', line)
            if m:
                button_press_time = list(map(float, m.groups()))[0]
                button_press_time /= 1000  # to seconds
                continue
            # Parse trial end messages e.g. "MSG 314108 VIDEO_STIM_ONSET"
            m = re.match(r'MSG\s+(\d+)\s+VIDEO_STIM_ONSET', line)
            if m:
                stim_onset_time = list(map(float, m.groups()))[0]
                stim_onset_time /= 1000  # to seconds
                continue
            # Parse trial variable messages e.g.
            #   "MSG 314108 !V TRIAL_VAR variable value"
            m = re.match(
                r'MSG\s+(\d+)\s+!V\s+TRIAL_VAR\s+([a-z_]+)\s+([a-z0-9_.]+)',
                line)
            if m:
                mgs = list(m.groups())
                # Convert time to seconds
                onset_time = float(mgs[0]) / 1000
                for g in m.groups():
                    # RT variable
                    if g == 'rt':
                        response_time = float(mgs[-1])
                    # Scene name variable
                    if g == 'scene_name':
                        scene_name = mgs[-1]
                    # Trial index variable
                    if g == 'trial_index':
                        trial_idx = int(mgs[-1])
                continue
            # Parse fixation events "EFIX R 314120 314632 513 961.9 553.5 1170"
            # pylint: disable=line-too-long
            m = re.match(r'EFIX (L|R)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)', line)
            # pylint: enable=line-too-long
            if m:
                is_fixation_event = False
                event_flag = 'None'
                which_eye, start, stop, dur, x, y, pupil = m.groups()
                start, stop, dur, pupil = map(float, (start, stop, dur, pupil))
                # Map times to seconds
                start /= 1000
                stop /= 1000
                dur /= 1000
                x, y = map(float, (x, y))
                fixations.append(Fixation(start, stop, x, y))
                continue
            # Parse saccade events e.g.
            #   "ESACC R 344176 344200 25 973.7 575.1 965.6 440.6 2.29 134"
            # pylint: disable=line-too-long
            m = re.match(
                r'ESACC (L|R)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)',
                line)
            # pylint: enable=line-too-long
            if m:
                mgs = list(m.groups())
                is_saccade_event = False
                event_flag = 'None'
                # pylint: disable=line-too-long
                start, stop, dur, start_x, start_y, end_x, end_y, amp, peak_vel = map(float, mgs[1:])
                # pylint: enable=line-too-long
                # Map times to seconds
                start /= 1000
                stop /= 1000
                dur /= 1000
                saccades.append(
                    Saccade(
                        start,
                        stop,
                        start_x,
                        start_y,
                        end_x,
                        end_y,
                        amp,
                        peak_vel
                    ))
                continue
            # Parse blink events e.g.
            #   "EBLINK R 344176 344200 25"
            m = re.match(
                r'EBLINK (L|R)\s+(\d+)\s+(\d+)\s+(\d+)', line)
            if m:
                mgs = list(m.groups())
                is_blink_event = False
                event_flag = 'None'
                start, stop, dur = map(float, mgs[1:])
                # Map times to seconds
                start /= 1000
                stop /= 1000
                dur /= 1000
                blinks.append(Blink(start, stop))
                continue
            # Parse gaze events "314631 958.8 551.2 1183.0 ..."
            m = re.match(
                r'(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+).*\.\.\.', line)
            if m:
                onset_time, x_pos, y_pos, pupil = map(float, m.groups())
                # Convert to seconds
                onset_time /= 1000
                gaze.append(
                    Gaze(
                        onset_time,
                        x_pos,
                        y_pos,
                        is_fixation_event,
                        is_saccade_event,
                        is_blink_event,
                        event_flag))
                continue
    return trials
