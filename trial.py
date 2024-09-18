"""Utilities for defining experimental trials for eyetracking experiment."""

import random
import time

import numpy as np
# NOTE: These packages are lazily imported
from psychopy import core, visual, event

import config
import eyetracking


class VideoTrial:
    '''Class for playing videos and collecting eye tracking data real time.
    
    Args:
        eyelink: The pylink.EyeLink object (tracker).
        video_path: The path to the video to be played.
        win: Psychopy window object.
    '''
    def __init__(
            self,
            eyelink:eyetracking.EyeLink | eyetracking.MouseLink,
            video_path:str,
            win:visual.Window,
            id:int):
        self.eyelink = eyelink
        self.gaze_data = []
        self.video_start_time = None
        self._video_is_playing = True
        self._last_frame = None
        self.win = win
        self.id = id
        self.scene_name = video_path.split('/')[-1].split('.')[0]
        self.video_path = video_path
        width = 800*.98
        height = 1000*.98
        # Create the video stimulus with the new size
        self.video = visual.MovieStim(
            win=self.win,
            filename=video_path,
            size=(width, height),
            pos=(0, 0),  # Center the video
            noAudio=True
        )

    def play_video(self) -> None:
        '''Method for playing video stimulus to participant frame by frame.'''
        self.video_start_time = time.time()
        # Send video stimulus onset message
        self.eyelink.message('VIDEO_STIM_ONSET')
        # Play the video stimulus
        self.video.play()
        event.clearEvents()
        frame_count = 0
        while self.video.status != visual.FINISHED:
            # NOTE: Make sure this works
            # Send data viewer video frame message
            self.eyelink.message('!V VRAME %d %d %d %s' % (
                frame_count,
                self.win.size[0]/2-self.video.size[0]/2,
                self.win.size[1]/2-self.video.size[1]/2,
                self.video_path
            ))
            # Draw video frame
            self.video.draw()
            self.win.flip()
            self.update_gaze()
            keys = event.getKeys(['f','j'])
            if 'j' in keys or 'f' in keys:
                self.eyelink.message('BUTTON_PRESS')
                return keys  # Move to next trial
            if config.EXIT_KEY in keys:
                self.eyelink.message('BUTTON_PRESS')
                return False # Exit experiment
            frame_count += 1
        # Video has finished, show last frame indefinitely until response
        event.clearEvents()
        while True:
            self.video.draw()  # This will draw the last frame
            self.win.flip()
            self.update_gaze()
            keys = event.getKeys(['f','j'])
            if 'j' in keys or 'f' in keys:
                self.eyelink.message('BUTTON_PRESS')
                return keys  # Move to next trial
            if config.EXIT_KEY in keys:
                self.eyelink.message('BUTTON_PRESS')
                return False # Exit experiment

    def start_video_and_tracking(self) -> None:
        '''Method for initiating video playback and eye tracker.'''
        self.eyelink.start_recording()
        self.play_video()

    def update_gaze(self) -> None:
        """Samples current gaze position and records it in pixels."""
        if not self.eyelink:
            return
        current_time = time.time() - self.video_start_time
        gaze_sample = self.eyelink.gaze_position()
        # Convert gaze coordinates to PsychoPy coordinates
        # Return gaze data in pixel values
        gaze_x = gaze_sample[0]
        gaze_y = gaze_sample[1]
        if self.eyelink.win.units == 'height':
            gaze_x, gaze_y = eyetracking.height2pix(
                self.eyelink.win, (gaze_x, gaze_y))
        # Store gaze data with timestamp
        self.gaze_data.append((current_time, gaze_x, gaze_y))

    def stop_video_and_tracking(self) -> None:
        """Stop recording from eye tracker."""
        self.eyelink.stop_recording()
        self.video.stop()
        # Get participant response time
        response_time = time.time() - self.video_start_time
        # Send trial variable info
        self.eyelink.message('!V TRIAL_VAR trial_index %d' % (self.id))
        self.eyelink.message('!V TRIAL_VAR scene_name %s' % (
            self.scene_name))
        self.eyelink.message('!V TRIAL_VAR rt %f' % (response_time))

    def run_trial(self) -> None:
        """Run forward the video trial."""
        # Send trial onset message
        self.eyelink.message('TRIAL_START')
        self.start_video_and_tracking()
        self.stop_video_and_tracking()
        # Send trial offset message
        self.eyelink.message('TRIAL_END')


class IntroductionTrial:
    """Class for introduction trials.
    
    Args:
        win: Psychopy window object.
        image_path: The path to the image displayed in the intro trial.
    """
    def __init__(
            self,
            win:visual.Window,
            image_path:str='data/introduction/scene_cp_2_arrow.jpg'):
        self.win = win
        # Index for which intro slide the trial is on
        self.slide_number = 0
        # Create text stimuli
        # pylint: disable=line-too-long
        self.text_stims = []
        intro_text = [
            "In this experiment, you will see 48 short clips of scenes like the one above.",
            "In each clip, there will be a BALL, a GOAL, and multiple SLIDES.",
            "The BALL will always be a circle.",
            "The GOAL will always be a rectangle.",
            "The SLIDES might change location and size from clip to clip.",
            "The BALL and GOAL may change colors from clip to clip.",
            "In each clip, the BALL will turn invisible, but you are to assume it's still in the scene.",
            "YOUR TASK:",
            "1. Judge whether the BALL will ever reach the GOAL.",
            "Press spacebar for further instructions."
        ]
        # pylint: enable=line-too-long
        y_positions = [
            0.025,
            0.0,
            -0.025,
            -0.05,
            -0.075,
            -0.1,
            -0.125,
            -0.15,
            -0.175,
            -0.2]
        y_positions = map(lambda x: x - .2, y_positions)
        for text, y_pos in zip(intro_text, y_positions):
            text_stim = visual.TextStim(
                win=win,
                text=text,
                font='Arial',
                pos=(0, y_pos),
                height=0.015,
                wrapWidth=1.5,
                color='black',
                alignText='center'
            )
            self.text_stims.append(text_stim)
        # Create image stimulus
        self.image_stim = visual.ImageStim(
            win=win,
            image=image_path,
            pos=(0, 0.12),
            size=(800*0.0005, 1000*0.0005)  # Adjust size as needed
        )

    def draw(self) -> None:
        """Draws the text and image stimuli onto the window."""
        self.image_stim.draw()
        for text_stim in self.text_stims:
            text_stim.draw()

    def run_trial(self) -> None:
        """Method for running the trial."""
        event.clearEvents()
        while True:
            self.draw()
            self.win.flip()
            keys = event.getKeys(['space', 'escape'])
            if 'space' in keys:
                return True  # Continue with the experiment
            if config.EXIT_KEY in keys:
                return False  # End the experiment
            core.wait(0.1)  # Small wait to prevent hammering the CPU


class KeyboardIntroductionTrial:
    """Class for keyboard introduction trials.
    
    These trials display the controls to the participant.
    
    Args:
        win: psychopy window object.
        yes_key: The assigned key for the 'yes' response in the experiment.
        no_key: The assigned key for the 'no' response in the experiment.
    """
    def __init__(self, win:visual.Window, yes_key:str, no_key:str):
        self.win = win
        image_path=f'data/introduction/keyboard_{yes_key}.jpeg'
        # Create text stimuli
        # pylint: disable=line-too-long
        # NOTE: Put this in config
        timeout = 5000
        self.text_stims = []
        intro_text = [
            f"If the Ball WILL reach the Goal: press the letter `{yes_key}` on your keyboard.",
            f"If the Ball WON'T reach the Goal: press the letter `{no_key}` on your keyboard",
            f"Each clip will only be available for `{timeout/1000}` seconds",
            "Please answer as fast and as accurately as possible!",
            "You do not have to wait for the clip to finish to answer!",
            "Press spacebar to continue."
        ]
        # pylint: enable=line-too-long
        y_positions = [
            0.025,
            0.0,
            -0.025,
            -0.05,
            -0.075,
            -0.1,]
        y_positions = map(lambda x: x - .1, y_positions)
        for text, y_pos in zip(intro_text, y_positions):
            text_stim = visual.TextStim(
                win=win,
                text=text,
                font='Arial',
                pos=(0, y_pos),
                height=0.015,
                wrapWidth=1.5,
                color='black',
                alignText='center'
            )
            self.text_stims.append(text_stim)
        # Create image stimulus
        self.image_stim = visual.ImageStim(
            win=win,
            image=image_path,
            pos=(0,0.12),
            size=(618*0.001, 262*0.001)  # Adjust size as needed
        )

    def draw(self) -> None:
        """Draws the image and text stimuli for the child on the window."""
        self.image_stim.draw()
        for text_stim in self.text_stims:
            text_stim.draw()

    def run_trial(self) -> None:
        """Method for running the trial."""
        event.clearEvents()
        while True:
            self.draw()
            self.win.flip()
            keys = event.getKeys(['space', 'escape'])
            if config.CONTINUE_KEY in keys:
                return True  # Continue with the experiment
            if config.EXIT_KEY in keys:
                return False  # End the experiment
            core.wait(0.1)  # Small wait to prevent hammering the CPU


class FinalIntroductionTrial:
    """Class for the final introduction trial.
    
    Args:
        win: psychopy window object."""
    def __init__(self, win:visual.Window):
        self.win = win
        # Create text stimuli
        # pylint: disable=line-too-long
        self.text_stims = []
        intro_text = [
            "We are almost ready for the study.",
            "Before we start, we have a few comprehension questions,",
            "to make sure you understand the task.",
            "The first few clips you will see will be full clips of a Ball falling in a scene.",
            "After the first few clips, the Ball will begin to disappear after the first few frames of each clip, just like it will in the experiment.",
            "Press spacebar to continue."
        ]
        # pylint: enable=line-too-long
        y_positions = [
            0.025,
            0.0,
            -0.025,
            -0.05,
            -0.075,
            -0.1,]
        y_positions = map(lambda x: x + .025, y_positions)
        for text, y_pos in zip(intro_text, y_positions):
            text_stim = visual.TextStim(
                win=win,
                text=text,
                font='Arial',
                pos=(0, y_pos),
                height=0.015,
                wrapWidth=1.5,
                color='black',
                alignText='center'
            )
            self.text_stims.append(text_stim)

    def draw(self) -> None:
        """Draws the text stimuli on the window."""
        for text_stim in self.text_stims:
            text_stim.draw()

    def run_trial(self) -> None:
        """Method for running the trial."""
        event.clearEvents()
        while True:
            self.draw()
            self.win.flip()
            keys = event.getKeys(['space', 'escape'])
            if config.CONTINUE_KEY in keys:
                return True  # Continue with the experiment
            if config.EXIT_KEY in keys:
                return False  # End the experiment
            core.wait(0.1)  # Small wait to prevent hammering the CPU


class InstructionTrial:
    """Class for the instruction trial.
    
    Gives participant instructions for the experiment.
    
    Args:
        win: Pyshopy window object.
        f_key: Flag for whether the f key is 'yes' or 'no'.
        j_key: Flag for whether the j key is 'yes' or 'no'.
        text_color: Color of the text on the window.
    """

    def __init__(
            self,
            win:visual.Window,
            f_key:str='Yes',
            j_key:str='No',
            text_color:str='black'):
        self.win = win
        self.f_key = f_key
        self.j_key = j_key
        # Create the instruction text
        instruction_text = (
            f"In the next scene: Will the ball reach the goal?\n\n"
            f"F: {self.f_key}, J: {self.j_key}\n\n"
            "(Press spacebar to begin)"
        )
        self.text_stim = visual.TextStim(
            win=win,
            text=instruction_text,
            pos=(0, 0),
            height=0.02,
            color=text_color,
            colorSpace='rgb',
            alignText='center'
        )

    def draw(self) -> None:
        """Draws the text stimuli on the window."""
        self.text_stim.draw()

    def run_trial(self):
        """Method for running the trial."""
        event.clearEvents()
        while True:
            self.draw()
            self.win.flip()
            keys = event.getKeys(['space', 'q'])
            if config.CONTINUE_KEY in keys:
                return True  # Continue with the experiment
            elif config.EXIT_KEY in keys:
                return False  # End the experiment
            core.wait(0.1)  # Small wait to prevent hammering the CPU


class Fixation:
    '''Class for fixation stimuli (crosses).
    
    Wraps around visual.ShapeStim.
    '''

    def __init__(self, win):
        self.win = win
        self.shape = visual.ShapeStim(
            win=win,
            vertices=((0, -0.05), (0, 0.05), (0, 0), (-0.05, 0), (0.05, 0)),
            lineWidth=6,
            lineColor='black',
            closeShape=False,
            colorSpace='rgb'
        )

    def draw(self):
        '''This method overrides psychopy's weird lazy importing issues.
        
        If you don't do it this way, you'll get some weird type errors.
        '''
        self.shape.draw()

    def run_trial(self):
        duration = random.uniform(0.5, 2)
        self.draw()
        self.win.flip()
        core.wait(duration)


if __name__ == '__main__':
    pass
