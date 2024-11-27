"""Main entrypoint into eyetracking experiment."""

import glob
import os
import json
import random

from psychopy import visual, monitors

import config
from eyetracking import MouseLink, EyeLink
import trial


def construct_experiment_section(
        video_paths:list[str],
        eyelink:EyeLink,
        win:visual.Window,
        red_button:str) -> list:
    """Constructs a single section of the main experiment.
    
    Each section consists of N blocks, each block consists of 3 trials. The
    structure of each experiment section is as follows:
        Task Reminder -> Fixation -> Block[Trial 1, 2, 3] -> Notifier
    where the Notifier simply states the participant response has been
    recorded.

    Args:
        video_paths: A list of paths to the stimuli used in the trials.
        eyelink: The EyeLink object used for recording eye gaze.
        win: The window upon which the experiment will be rendered.
        red_button: Whether the red button is "yes" or "no".
    
    Returns:
        experiment_trials: A list of trials that define the experiment section.
    """
    # Each experiment section begins with an instruction slide
    experiment_trials = [
        trial.ImageTrial(
            win=win,
            image_path=f'data/introduction/experiment_instruction_r{red_button}.png'
        )
    ]
    # We now construct the sequence of experiment blocks in this section
    for idx, v_path in enumerate(video_paths):
        # Path for pre- trial
        v_pre_path = v_path.replace('_intra', '_pre')
        # Path for post- trial
        v_post_path = v_path.replace('_intra', '_post')
        # The video trials that constitute a single block
        video_stimuli = [
            trial.VideoTrial(
                v_pre_path, end_keys=[config.YELLOW_BUTTON], win=win),
            trial.VideoTrial(
                v_path, end_keys=None, win=win),
            trial.VideoTrial(
                v_post_path,
                end_keys=[config.BLUE_BUTTON, config.RED_BUTTON],
                win=win),
        ]
        # Append a fixation trial that preceds the experiment block
        experiment_trials.append(trial.FixationTrial(win=win))
        # Append the video trials that constitute the experiment block
        experiment_trials.append(
            trial.ExperimentBlock(
                eyelink=eyelink, win=win, videos=video_stimuli, id=idx
            )
        )
        # If we are not finished with the section, we remind participants of
        #   the task before each block
        if idx != len(video_paths)-1:
            experiment_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path=f'data/introduction/experiment_recorded_r{red_button}.png',
                    timed=False)
            )
        # Otherwise, we notify them that their response has been recorded
        else:
            experiment_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path='data/introduction/experiment_recorded.png',
                    timed=True)
            )
    return experiment_trials


def construct_comprehension_section_easy(
        eyelink:EyeLink,
        win:visual.Window,
        video_paths:list[str],
        red_button:str) -> list:
    """Constructs a single section of comprehension blocks.
    
    Each section consists of N blocks, each block consists of 2 trials. The
    structure of each experiment section is as follows:
        Task Reminder -> Fixation -> Block[Trial 1, Trial 2] -> Notifier
    where the Notifier simply states the participant response has been
    recorded.

    Args:
        video_paths: A list of paths to the stimuli used in the trials.
        eyelink: The EyeLink object used for recording eye gaze.
        win: The window upon which the experiment will be rendered.
        red_button: Whether the red button is "yes" or "no".
    
    Returns:
        comprehension_trials: A list of trials that define the comprehension.
    """
    comprehension_trials = [
        trial.ImageTrial(
            win=win,
            image_path=f'data/introduction/easy_comp_introduction_r{red_button.lower()}.png'),
        trial.ImageTrial(
            win=win,
            image_path=f'data/introduction/comp_instruction_r{red_button.lower()}.png')
    ]
    # Construct a sequence of experiment blocks
    for idx, v_path in enumerate(video_paths):
        # Path for pre- trial stimuli
        v_pre_path = v_path.replace('_post', '_pre')
        # The video trials that define the comprehension block
        video_stimuli = [
            trial.VideoTrial(
                v_pre_path, end_keys=[config.YELLOW_BUTTON], win=win),
            trial.VideoTrial(
                v_path,
                end_keys=[config.BLUE_BUTTON, config.RED_BUTTON],
                win=win),
        ]
        # Assign the appropriate key presses for comprehension checking
        if red_button.lower() == 'yes':
            yes_button = config.RED_BUTTON
            no_button = config.BLUE_BUTTON
        else:
            yes_button = config.BLUE_BUTTON
            no_button = config.RED_BUTTON
        # The correct key press is in the file name of the stimulus
        if 'yes' in v_path:
            correct_response = yes_button
        else:
            correct_response = no_button
        # Append a fixation trial that precedes the comprehension trials
        comprehension_trials.append(trial.FixationTrial(win=win))
        # Append the comprehension block
        comprehension_trials.append(
            trial.ComprehensionBlock(
                eyelink=eyelink,
                videos=video_stimuli,
                correct_response=correct_response,
                id=idx
            )
        )
        # If we are not finished with the comprehension section, we remind
        #   participants of the task.
        if idx != len(video_paths)-1:
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path='data/introduction/experiment_recorded.png',
                    timed=True)
            )
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path=f'data/introduction/comp_instruction_r{red_button}.png',
                    timed=False)
            )
        # Otherwise we just tell them their response was recorded.
        else:
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path='data/introduction/experiment_recorded.png',
                    timed=True)
            )
    return comprehension_trials


def construct_comprehension_section_med(
        eyelink:EyeLink,
        win:visual.Window,
        video_paths:list[str],
        red_button:str) -> list:
    """Constructs a single section of comprehension blocks.
    
    Each section consists of N blocks, each block consists of 2 trials. The
    structure of each experiment section is as follows:
        Task Reminder -> Fixation -> Block[Trial 1, Trial 2] -> Notifier
    where the Notifier simply states the participant response has been
    recorded.

    Args:
        video_paths: A list of paths to the stimuli used in the trials.
        eyelink: The EyeLink object used for recording eye gaze.
        win: The window upon which the experiment will be rendered.
        red_button: Whether the red button is "yes" or "no".
    
    Returns:
        comprehension_trials: A list of trials that define the comprehension.
    """
    comprehension_trials = [
        trial.ImageTrial(
            win=win,
            image_path=f'data/introduction/med_comp_introduction_r{red_button.lower()}.png'),
        trial.ImageTrial(
            win=win,
            image_path=f'data/introduction/comp_instruction_r{red_button.lower()}.png')
    ]
    # Construct a sequence of experiment blocks
    for idx, v_path in enumerate(video_paths):
        # Path for pre- trial stimuli
        v_pre_path = v_path.replace('_post', '_pre')
        # The video trials that define the comprehension block
        video_stimuli = [
            trial.VideoTrial(
                v_pre_path, end_keys=[config.YELLOW_BUTTON], win=win),
            trial.VideoTrial(
                v_path,
                end_keys=[config.BLUE_BUTTON, config.RED_BUTTON],
                win=win),
        ]
        # Assign the appropriate key presses for comprehension checking
        if red_button.lower() == 'yes':
            yes_button = config.RED_BUTTON
            no_button = config.BLUE_BUTTON
        else:
            yes_button = config.BLUE_BUTTON
            no_button = config.RED_BUTTON
        # The correct key press is in the file name of the stimulus
        if 'yes' in v_path:
            correct_response = yes_button
        else:
            correct_response = no_button
        # Append a fixation trial that precedes the comprehension trials
        comprehension_trials.append(trial.FixationTrial(win=win))
        # Append the comprehension block
        comprehension_trials.append(
            trial.ComprehensionBlock(
                eyelink=eyelink,
                videos=video_stimuli,
                correct_response=correct_response,
                id=idx
            )
        )
        # If we are not finished with the comprehension section, we remind
        #   participants of the task.
        if idx != len(video_paths)-1:
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path='data/introduction/experiment_recorded.png',
                    timed=True)
            )
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path=f'data/introduction/comp_instruction_r{red_button}.png',
                    timed=False)
            )
        # Otherwise we just tell them their response was recorded.
        else:
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path='data/introduction/experiment_recorded.png',
                    timed=True)
            )
    return comprehension_trials


def construct_comprehension_section_hard(
        video_paths:list[str],
        eyelink:EyeLink,
        win:visual.Window,
        red_button:str) -> list:
    """Constructs a single section of comprehension blocks.
    
    Each section consists of N blocks, each block consists of 3 trials. The
    structure of each experiment section is as follows:
        Task Reminder -> Fixation -> Block[Trial 1, Trial 2, 3] -> Notifier
    where the Notifier simply states the participant response has been
    recorded.

    Args:
        video_paths: A list of paths to the stimuli used in the trials.
        eyelink: The EyeLink object used for recording eye gaze.
        win: The window upon which the experiment will be rendered.
        red_button: Whether the red button is "yes" or "no".
    
    Returns:
        comprehension_trials: A list of trials that define the comprehension.
    """
    comprehension_trials = [
        trial.ImageTrial(
            win=win,
            image_path=f'data/introduction/hard_comp_introduction_r{red_button.lower()}.png'),
        trial.ImageTrial(
            win=win,
            image_path=f'data/introduction/hard_comp_instruction_r{red_button.lower()}.png')
    ]
    for idx, v_path in enumerate(video_paths):
        # Path for pre- trial
        v_pre_path = v_path.replace('_intra', '_pre')
        # Path for post- trial
        v_post_path = v_path.replace('_intra', '_post')
        # The video trials that define the comprehension block
        video_stimuli = [
            trial.VideoTrial(
                v_pre_path, end_keys=[config.YELLOW_BUTTON], win=win),
            trial.VideoTrial(
                v_path, end_keys=None, win=win),
            trial.VideoTrial(
                v_post_path,
                end_keys=[config.BLUE_BUTTON, config.RED_BUTTON],
                win=win),
        ]
        # Assign the appropriate key presses for comprehension checking
        if red_button.lower() == 'yes':
            yes_button = config.RED_BUTTON
            no_button = config.BLUE_BUTTON
        else:
            yes_button = config.BLUE_BUTTON
            no_button = config.RED_BUTTON
        # The correct key press is in the file name of the stimulus
        if 'yes' in v_path:
            correct_response = yes_button
        else:
            correct_response = no_button
        # Append a fixation trial that precedes the comprehension trials
        comprehension_trials.append(trial.FixationTrial(win=win))
        # Append the comprehension block
        comprehension_trials.append(
            trial.ComprehensionBlock(
                eyelink=eyelink,
                videos=video_stimuli,
                correct_response=correct_response,
                id=idx
            )
        )
        # If we are not finished with the comprehension section, we remind
        #   participants of the task.
        if idx != len(video_paths)-1:
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path='data/introduction/experiment_recorded.png',
                    timed=True)
            )
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path=f'data/introduction/hard_comp_instruction_r{red_button}.png',
                    timed=False)
            )
        # Otherwise we just tell them their response was recorded.
        else:
            comprehension_trials.append(
                trial.ImageTrial(
                    win=win,
                    image_path='data/introduction/experiment_recorded.png',
                    timed=True)
            )
    return comprehension_trials


def check_comprehension(trials:list[trial.Tria]) -> bool:
    """Determines whether the comprehension trials were passed.
    
    Args:
        trials: The block (list of trials) to check.
    Returns:
        True/False"""
    _trials = [ct for ct in trials if isinstance(ct, trial.ComprehensionBlock)]
    return all(ct.passed for ct in _trials)


def run_introduction_block(intro_trials:list[trial.Trial]) -> None:
    """Runs the introduction blocks.
    
    Args:
        intro_trials: A list of trials (block) to be run.
    
    Returns:
        None
    """
    for it in intro_trials:
        it.run()


def run_comprehension_blocks(
        comprehension_blocks:list[trial.Trial | trial.Block],
        win:visual.Window,
        idx:int=0) -> None:
    """Runs the comprehension blocks and handles decision logic.
    
    Args:
        comprehension_blocks: The list of trials (block) to run.
        win: The window to render the pass/fail trials to.
        idx: Index for easy (0) medium (1) or hard (2) pass/fail trials.
        
    Returns:
        None
    """
    while True:
        for ct in comprehension_blocks:
            ct.run()
        if check_comprehension(comprehension_blocks):
            pass_trial = trial.ImageTrial(
                win=win, image_path=f'data/introduction/pass_comp_{idx}')
            pass_trial.run()
            break
        else:
            fail_trial = trial.ImageTrial(
                win=win, image_path=f'data/introduction/error_comp_{idx}')
            fail_trial.run()


def main(mouse=True):
    '''Entrypoint.'''
    # Instantiate psychopy window for stimuli presentation
    monitor_width = config.MONITOR_WIDTH
    monitor_dist = config.MONITOR_DISTANCE
    mon = monitors.Monitor(
        'dell_external', width=monitor_width, distance=monitor_dist)
    mon.setSizePix([1920, 1080])
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
    # Set up calibration trial
    # el.calibrate()
    red_button = random.choice(['yes', 'no'])
    # Construct introduction phase
    introduction_block = [
        trial.ImageTrial(win=win, image_path='data/introduction/introduction_1.png'),
        trial.ImageTrial(win=win, image_path='data/introduction/introduction_2.png')
    ]
    # Construct comprehension phase
    easy_comprehension_section = construct_comprehension_section_easy(
        video_paths=glob.glob(
            os.path.join('data/comprehension','*_easy_*_post.mp4')),
        eyelink=el,
        win=win,
        red_button=red_button,
    )
    medium_comprehension_section = construct_comprehension_section_med(
        video_paths=glob.glob(
            os.path.join('data/comprehension','*_med_*_post.mp4')),
        eyelink=el,
        win=win,
        red_button=red_button,
    )
    hard_comprehension_section = construct_comprehension_section_hard(
        video_paths=glob.glob(
            os.path.join('data/comprehension','*_hard_*_intra.mp4')),
        eyelink=el,
        win=win,
        red_button=red_button,
    )
    # Construct main experiment phase. Gather stimuli
    with open('data/latin_square_stimuli.json', 'r') as f:
        latin_square_stimuli = json.load(f)
        latin_square_stimuli = {
            int(k):v for k,v in latin_square_stimuli.items()}
    # Shuffle within groups
    for key in latin_square_stimuli:
        random.shuffle(latin_square_stimuli[key])
    experiment_section_0 = construct_experiment_section(
        video_paths=latin_square_stimuli[0][:2],
        eyelink=el,
        win=win,
        red_button=red_button)
    experiment_section_0.append(
        trial.ImageTrial(
            win=win, image_path='data/introduction/experiment_section_end_0')
    )
    experiment_section_1 = construct_experiment_section(
        video_paths=latin_square_stimuli[1][:2],
        eyelink=el,
        win=win,
        red_button=red_button)
    experiment_section_1.append(
        trial.ImageTrial(
            win=win, image_path='data/introduction/experiment_section_end_1')
    )
    experiment_section_2 = construct_experiment_section(
        video_paths=latin_square_stimuli[2][:2],
        eyelink=el,
        win=win,
        red_button=red_button)
    experiment_section_2.append(
        trial.ImageTrial(
            win=win, image_path='data/introduction/experiment_section_end_2')
    )
    experiment_section_3 = construct_experiment_section(
        video_paths=latin_square_stimuli[3][:2],
        eyelink=el,
        win=win,
        red_button=red_button)
    experiment_section_3.append(
        trial.ImageTrial(
            win=win, image_path='data/introduction/experiment_section_end_3')
    )

    # Introduction phase
    run_introduction_block(introduction_block)
    # Comprehension phase
    run_comprehension_blocks(easy_comprehension_section, win, 0)
    run_comprehension_blocks(medium_comprehension_section, win, 1)
    run_comprehension_blocks(hard_comprehension_section, win, 2)
    # Main experiment phase
    for experiment_block in experiment_section_0:
        experiment_block.run()
    for experiment_block in experiment_section_1:
        experiment_block.run()
    for experiment_block in experiment_section_2:
        experiment_block.run()
    for experiment_block in experiment_section_3:
        experiment_block.run()


if __name__ == '__main__':
    main(mouse=True)
