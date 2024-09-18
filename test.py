"""Main entrypoint into eyetracking experiment."""
import glob
import os
import random

import pandas as pd
from psychopy import visual, monitors

import config
from eyetracking import MouseLink, EyeLink
import trial

def main(mouse=True):
    '''Entrypoint.'''
    monitor_width = config.MONITOR_WIDTH
    monitor_dist = config.MONITOR_DISTANCE
    mon = monitors.Monitor(
        'dell_external', width=monitor_width, distance=monitor_dist)
    mon.setSizePix([1920, 1080])
    # Instantiate psychopy window for stimuli presentation
    win = visual.Window(
        size=[1920,1080],
        fullscr=True,
        units='pix',
        winType='pyglet',
        monitor=mon)
    # Instatiate EyeLink
    if mouse:
        el = MouseLink(win=win, uniqueid='test', dummy_mode=False)
    else:
        el = EyeLink(win=win, uniqueid='test')
    print(f'Window size: {el.win.size}')
    print(f'Window units: {el.win.units}')
    # Set up calibration trial
    # el.calibrate()
    # Grab all video stimuli
    # stimuli_path = 'data/stimuli'
    # videos = glob.glob(os.path.join(stimuli_path,'*'))
    # Shuffle order of trials for participant
    # random.shuffle(videos)
    # # Construct the introduction trial
    # intro_trial = trial.IntroductionTrial(win=win)
    # intro_keyboard_trial = trial.KeyboardIntroductionTrial(
    #     win=win, yes_key='f', no_key='j')
    # intro_final_trial = trial.FinalIntroductionTrial(win=win)
    # # Construct fixation trial (just a cross)
    # fixation_trial = trial.Fixation(win=win)
    # # Construct the instruction trial (reminds participants of key presses)
    # instruction_trial = trial.InstructionTrial(win=win)
    # Construct VideoTrial objects for each video stimulus
    # video_trials = []
    # for idx, video_path in enumerate(videos):
    #     video_trials.append(trial.VideoTrial(el, video_path, win, id=idx))
    # Main experiment loop
    # # Run introduction trials
    # intro_trial.run_trial()
    # intro_keyboard_trial.run_trial()
    # intro_final_trial.run_trial()
    # Run experimental trials
    # gaze_data = []
    # for vt in video_trials[:1]:
    #     el.win.mouseVisible = True
    #     # Instruction reminder
    #     # instruction_trial.run_trial()
        # Random fixation
        # fixation_trial.run_trial()
        # Stimulus presentation
        # vt.run_trial()
        # # Record data
        # gaze_data.append({
        #     'trial_index': vt.id,
        #     'scene_name': vt.scene_name,
        #     'gaze_data': vt.gaze_data,
        # })
    # path = 'data/pilots/'
    # gaze_data_df = pd.DataFrame(gaze_data)
    # try:
    #     el.save_data(data_dir=path)
    # except Exception as e:
    #     print(e)
    # if os.path.exists('data/pilots'):
    #     gaze_data_df.to_json('data/pilots/test_data.json')
    # else:
    #     gaze_data_df.to_json('test.json')
    el.close_connection()


if __name__ == '__main__':
    main(mouse=False)
