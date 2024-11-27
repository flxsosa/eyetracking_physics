"""Utilities for defining experimental trials for eyetracking experiment."""

import os
import random
import time

# NOTE: These packages are lazily imported
from psychopy import core, visual, event

import config
import eyetracking


class Block:
    """For type annotations."""


class Trial:
    """For type annotations."""


class ImageTrial(Trial):
    """A class wrapper for a psychopy ImageStim.
    
    Attributes:
        win: The psychopy window to render the stimulus to.
        image_path: The path to the image.
        timed: Whether the trial ends on its own (T), or by button press (F).
    """
    def __init__(
            self,
            win:visual.Window,
            image_path,
            timed=False):
        self.win = win
        self.timed = timed
        # Create the image stimulus showing the controller
        self.image_stim = visual.ImageStim(
            win=self.win,
            image=image_path,
            pos=(0,0)
        )

    def draw(self) -> None:
        """Draws the text stimuli on the window."""
        self.image_stim.draw()

    def run(self):
        """Method for running the trial."""
        if self.timed:
            self.draw()
            self.win.flip()
            time.sleep(0.5)
            return
        while True:
            self.draw()
            self.win.flip()
            keys = event.getKeys([config.YELLOW_BUTTON])
            if config.YELLOW_BUTTON in keys:
                return True  # Continue with the experiment
            event.clearEvents()


class VideoTrial(Trial):
    """A class wrapper for a psychopy MovieStim.
    
    Attributes:
        end_keys: Which keys end the trial.
        win: The psychopy window to render the stimulus to.
        path: The path to the video.
    """

    def __init__(
            self, path:str, end_keys:list[str], win:visual.Window):
        self.path = path
        self.name = path.split('/')[-1].split('.')[0]
        self.end_keys = end_keys
        self.video = None
        self.response = None
        self.rt = None
        self.win = win

    def _play_button(self, eyelink):
        event.clearEvents()
        eyelink.message('VIDEO_START')
        self.video.play()
        while True:
            # Draw video frame
            self.video.draw()
            self.video.win.flip()
            keys = event.getKeys(self.end_keys)
            for key in self.end_keys:
                if key in keys:
                    # Move to next video
                    self.video.stop()
                    eyelink.message('BUTTON_PRESS %s' % key)
                    eyelink.message('VIDEO_END')
                    return key
            event.clearEvents()

    def _play_timed(self, eyelink):
        event.clearEvents()
        eyelink.message('VIDEO_START')
        self.video.play()
        while not self.video.isFinished:
            # Draw video frame
            self.video.draw()
            self.video.win.flip()
        self.video.stop()
        eyelink.message('VIDEO_END')
        event.clearEvents()
        return

    def play(self, eyelink):
        self.video = visual.MovieStim(
            win=self.win,
            filename=self.path,
            size=(
                config.DEFAULT_WIDTH * config.STIM_SCALE,
                config.DEFAULT_HEIGHT * config.STIM_SCALE),
            pos=(0, 0),
            noAudio=True
        )
        event.clearEvents()
        if self.end_keys:
            self.response = self._play_button(eyelink)
            event.clearEvents()
        else:
            self._play_timed(eyelink)
            event.clearEvents()
        event.clearEvents()
        self.video = None


class FixationTrial(Trial):
    """A class wrapper for fixation stimuli (cross).
    
    Wraps around visual.ShapeStim.

    Attributes:
        win: The window to render the shape to.
    """

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

    def run(self):
        """Method for running trial."""
        duration = random.uniform(0.5, 2)
        self.draw()
        self.win.flip()
        core.wait(duration)
        event.clearEvents()


class ExperimentBlock(Block):
    '''Class for an Experiment Block.

    An ExperimentBlock is a tuple of VideoTrials, usually a pre-, intra-, and
    post-video of a given scene.
    
    Args:
        eyelink: The pylink.EyeLink object (tracker).
        videos: The sequence of VideoTrials that make the block.
        win: Psychopy window object.
        id: The id of the Block.
    '''
    def __init__(
            self,
            eyelink:eyetracking.EyeLink,
            win,
            videos:list[VideoTrial],
            id:int):
        self.eyelink = eyelink
        self.videos = videos
        self.response_recorded = visual.ImageStim(
            win=win,
            image='data/introduction/experiment_recorded.png',
            pos=(0,0)
        )
        self.gaze_data = []
        self.video_start_time = None
        self.id = id
        self.responses = {}

    def stop_video_and_tracking(self, video) -> None:
        """Stop recording from eye tracker."""
        self.eyelink.stop_recording()
        # Get participant response time
        response_time = time.time() - self.video_start_time
        # Send trial variable info
        self.eyelink.message('!V TRIAL_VAR trial_index %d' % (self.id))
        self.eyelink.message('!V TRIAL_VAR scene_name %s' % (
            video.name))
        self.eyelink.message('!V TRIAL_VAR rt %f' % (response_time))
        video.rt = response_time
        event.clearEvents()

    def run(self) -> None:
        """Run forward the video trial."""
        # Send trial onset message
        self.eyelink.message('BLOCK_START')
        for trial_index, v in enumerate(self.videos):
            self.eyelink.message('TRIAL_START')
            self.eyelink.start_recording()
            self.video_start_time = time.time()
            v.play(eyelink=self.eyelink)
            self.stop_video_and_tracking(v)
            self.responses[v.name] = {'response': v.response, 'rt': v.rt}
            self.eyelink.message('!V TRIAL_VAR trial_index %d' % (trial_index))
            self.eyelink.message('TRIAL_END')
        self.eyelink.message('!V TRIAL_VAR block_index %d' % (self.id))
        self.eyelink.message('BLOCK_END')
        self.response_recorded.draw()
        self.response_recorded.win.flip()
        time.sleep(0.5)

        # Send trial offset message


class ComprehensionBlock(Block):
    '''Class for a Comprehension Block.

    A ComprehensionBlock is a tuple of VideoTrials, usually a pre-, intra-, and
    post-video of a given scene.
    
    Args:
        eyelink: The pylink.EyeLink object (tracker).
        videos: The sequence of VideoTrials that make the block.
        correct_response: The correct response to the Block.
        id: The id of the Block.
    '''
    def __init__(
            self,
            eyelink:eyetracking.EyeLink | eyetracking.MouseLink,
            videos:list[VideoTrial],
            correct_response:str,
            id:int):
        self.eyelink = eyelink
        self.videos = videos
        self.gaze_data = []
        self.video_start_time = None
        self.id = id
        self.correct_response = correct_response
        self.passed = None
        self.responses = {}

    def reset(self):
        self.passed = None
        self.responses = {}
        self.video_start_time = None
        self.gaze_data = []

    def stop_video_and_tracking(self, video) -> None:
        """Stop recording from eye tracker."""
        event.clearEvents()
        self.eyelink.stop_recording()
        # Get participant response time
        response_time = time.time() - self.video_start_time
        # Send trial variable info
        self.eyelink.message('!V TRIAL_VAR trial_index %d' % (self.id))
        self.eyelink.message('!V TRIAL_VAR scene_name %s' % (
            video.name))
        self.eyelink.message('!V TRIAL_VAR rt %f' % (response_time))
        video.rt = response_time
        event.clearEvents()

    def run(self) -> None:
        """Run forward the video trial."""
        # Send trial onset message
        self.eyelink.message('BLOCK_START')
        for v in self.videos:
            self.eyelink.message('TRIAL_START')
            self.eyelink.start_recording()
            self.video_start_time = time.time()
            v.play(eyelink=self.eyelink)
            self.stop_video_and_tracking(v)
            self.responses[v.name] = {'response': v.response, 'rt': v.rt}
            if '_post' in v.name:
                self.passed = self.correct_response == v.response
            self.eyelink.message('TRIAL_END')
        # Send trial offset message
        self.eyelink.message('BLOCK_END')


if __name__ == '__main__':
    pass
