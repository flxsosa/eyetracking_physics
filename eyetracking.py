"""Utilities and classes for EyeLink interface and using mouse as gaze data."""

import hashlib
import logging
import os
import time

import pylink
from psychopy import visual, core, event, monitors
import numpy as np

from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy


def hide_dock() -> None:
    '''Function for hiding the dock on MacOS.'''
    os.system("""osascript -e '
    tell application "System Events"
      set autohide of dock preferences to true
    end tell
    '""")


def ensure_edf_filename(name:str) -> str:
    '''Ensures EDF file has reproducible unique 12-character name.
    
    Args:
        name: The file name to be ensured (hashed).
    Returns:
        MD5 hash of name argument.
    '''
    return hashlib.md5(name.encode()).hexdigest()[:8] + '.EDF'


def configure_data(tracker:pylink.EyeLink) -> None:
    '''Configures data for the EyeLink tracker.
    
    Args:
        tracker: A pylink.EyeLink tracker.
    Returns:
        None
    '''
    # pylint: disable=line-too-long
    vstr = tracker.getTrackerVersionString()
    eyelink_ver = int(vstr.split()[-1].split('.')[0])
    # Define eye events to save in the EDF file
    file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
    # Define eye events to make available over the link
    link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
    # Define sample data to save in the EDF data file and to make available
    #   over the link, include the 'HTARGET' flag to save head target sticker
    #   data for supported eye trackers.
    if eyelink_ver > 3:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
    else:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
    tracker.sendCommand(f'file_event_filter = {file_event_flags}')
    tracker.sendCommand(f'file_sample_data = {file_sample_flags}')
    tracker.sendCommand(f'link_event_filter = {link_event_flags}')
    tracker.sendCommand(f'link_sample_data = {link_sample_flags}')
    tracker.sendCommand('calibration_type = HV9')
    tracker.sendCommand('enable_automatic_calibration = NO')
    # pylint: enable=line-too-long


def pix2height(win:visual.Window, pos:list[float | int] | tuple) -> tuple:
    '''Converts pixel units to height units for a given window.
    
    Args:
        win: The display window.
        pos: The position.
    Returns:
        Adjusted position (x,y).
    '''
    assert win.units == 'height'
    w, h = win.size / 2  # eyetracker uses non-retina pixels
    x, y = pos
    y *= -1  # invert y axis
    x -= w/2
    y +=  h/2
    y /= h  # scale
    x /= h
    return x, y


def height2pix(
        win:visual.Window,
        pos:list[float | int] | tuple,
        retina=False) -> tuple:
    '''Converts height units to pixel units for a given window.
    
    Args:
        win: The display window.
        pos: The position.
    Returns:
        Adjusted position (x,y).
    '''
    assert win.units == 'height'
    if retina:
        w, h = win.size / 2  # eyetracker uses non-retina pixels
    else:
        w, h = win.size
    x, y = pos
    # scale and invert y
    y *= -h
    x *= h
    # center
    x += w/2
    y +=  h/2
    return x, y


class EyelinkError(Exception):
    '''EyeLink error wrapper.'''


class EyeLink(object):
    """A pylink interface to the EyeLink.

    Args:
        win: psychopy.visual.Window display.
        uniqueid: A unique string identifier.
        dummy_mode: boolean flag for debugging.
    """
    def __init__(self, win:visual.Window, uniqueid:str, dummy_mode:bool=False):
        logging.info('New EyeLink object')
        self.win = win
        uniqueid = uniqueid.replace(':', '_')
        self.dummy_mode = dummy_mode
        self.uniqueid = uniqueid
        self.edf_file = ensure_edf_filename(uniqueid)
        self.disable_drift_checks = False
        if pylink.getEYELINK():
            logging.info('Using existing tracker')
            self.tracker = pylink.getEYELINK()
        else:
            logging.info('Initializing new tracker')
            if dummy_mode:
                self.tracker = pylink.EyeLink(None)
            else:
                print('Setting up EyeLink')
                self.tracker = pylink.EyeLink("100.1.1.1")
                self.tracker.openDataFile(self.edf_file)
                configure_data(self.tracker)
                self.setup_calibration()
                self.tracker.setOfflineMode()
                logging.info('Tracker initialized')

    def drift_check(self, pos:tuple[int | float]=(0,0)) -> str:
        """Perform a drift correct on the eye tracker.
        
        Args:
            pos: Origin at 0,0.
        """
        # TODO: might want to implement this myself, to make it more stringent
        if self.disable_drift_checks:
            return self.fake_drift_check(pos)
        self.win.units = 'height'
        x, y = map(int, height2pix(self.win, pos))
        try:
            self.tracker.doDriftCorrect(x, y, 1, 1)
        except RuntimeError:
            logging.info('escape in drift correct')
            self.win.showMessage(
                '''Experimenter, choose:\n(C)ontinue  (A)bort  (R)ecalibrate 
                (D)isable drift check''')
            self.win.flip()
            keys = event.waitKeys(keyList=['space', 'c', 'a', 'r', 'd'])
            logging.info('drift check keys %s', keys)
            self.win.showMessage(None)
            self.win.flip()
            if 'a' in keys:
                return 'abort'
            if 'r' in keys:
                return 'recalibrate'
            if 'd' in keys:
                self.disable_drift_checks = True
                return 'disable'
            self.drift_check(pos)
            return 'ok'
        finally:
            self.win.units = 'height'

    def fake_drift_check(self, pos:tuple[int | float]=(0,0)) -> str:
        """Perform a fake drift check."""
        self.win.units = 'height'
        x, y = map(int, height2pix(self.win, pos))
        self.genv.update_cal_target()
        self.genv.draw_cal_target(x, y)
        self.win.units = 'height'
        keys = event.waitKeys(keyList=['space', 'escape'])
        if 'space' in keys:
            return 'ok'
        self.win.showMessage(
                '''Experimenter, choose:\n(C)ontinue  (A)bort  (R)ecalibrate 
                (D)isable drift check''')
        self.win.flip()
        keys = event.waitKeys(keyList=['space', 'c', 'a', 'r', 'd'])
        logging.info('drift check keys %s', keys)
        self.win.showMessage(None)
        self.win.flip()
        if 'a' in keys:
            return 'abort'
        if 'r' in keys:
            return 'recalibrate'
        if 'd' in keys:
            self.disable_drift_checks = True
            return 'disable'
        self.drift_check(pos)
        return 'ok'

    def message(self, msg:str, log:bool=True) -> None:
        """Sends message to eye tracker.
        
        Args:
            msg: The custom message to send to eye tracker.
            log: Boolean for logging the message.
        """
        if log:
            logging.debug('EyeLink.message %s', msg)
        self.tracker.sendMessage(msg)

    def start_recording(self) -> None:
        """Starts the tracker recording."""
        logging.info('start_recording')
        self.tracker.startRecording(1, 1, 1, 1)
        pylink.pumpDelay(100)  # maybe necessary to clear out old samples??

    def stop_recording(self) -> None:
        """Stops the tracker recording."""
        logging.info('stop_recording')
        self.tracker.stopRecording()

    def set_custom_calibration_points(self) -> None:
        """Defines a set of custom calobration points for the stimuli.
        
        These points are centered on the screen with a bounding box of equal
        size to the stimuli: 800x1000 pixels.
        """
        # Screen dimensions
        scn_width, scn_height = self.win.monitor.getSizePix()
        # Stimulus dimensions
        stim_width, stim_height = 800, 1000
        # Calculate offsets to center the stimulus area
        offset_x = (scn_width - stim_width) // 2
        offset_y = (scn_height - stim_height) // 2
        # Ensure that the custom calibration settings take effect
        self.tracker.sendCommand("generate_default_targets = NO")
        # Define calibration points relative to stimulus area
        cal_points = [
            (400,500),
            (400,85),
            (400,915),
            (48,500),
            (752,500),
            (48,85),
            (752,85),
            (48,915),
            (752,915),
            (224,292),
            (576,292),
            (224,708),
            (576,708)
        ]
         # Adjust calibration points to screen coordinates
        adjusted_points = [
            (x + offset_x, y + offset_y) for x, y in cal_points
        ]
        # Convert to string format required by EyeLink
        cal_point_str = ','.join(f'{x},{y}' for x, y in adjusted_points)
        # Set calibration points
        self.tracker.sendCommand("calibration_type = HV13")
        self.tracker.sendCommand(f"calibration_targets = {cal_point_str}")
        # Set validation points (usually same as calibration)
        self.tracker.sendCommand(f"validation_targets = {cal_point_str}")

    def setup_calibration(self) -> None:
        """Method for defining tracker calibration parameters."""
        self.message('Set up calibration')
        # Get the screen resolution
        scn_width, scn_height = self.win.monitor.getSizePix()
        # Pass display pixel coordinates (left, top, right, bottom) to tracker
        el_coords = 'screen_pixel_coords = 0 0 %d %d' % (
            scn_width - 1, scn_height - 1)
        self.tracker.sendCommand(el_coords)
        # Write a DISPLAY_COORDS message to the EDF file
        dv_coords = 'DISPLAY_COORDS  0 0 %d %d' % (
            scn_width - 1, scn_height - 1)
        self.tracker.sendMessage(dv_coords)
        # Configure a graphics environment (genv) for tracker calibration
        self.genv = EyeLinkCoreGraphicsPsychoPy(self.tracker, self.win)
        foreground_color = (-1, -1, -1)
        self.genv.setCalibrationColors(foreground_color, self.win.color)
        # Set up the calibration target
        self.genv.setTargetType('circle')
        # Configure the size of the calibration target (in pixels)
        self.genv.setTargetSize(24)
        # Beeps to play during calibration, validation and drift correction
        self.genv.setCalibrationSounds('', '', '')
        pylink.closeGraphics()
        # Request Pylink to use PsychoPy window we opened above for calibration
        pylink.openGraphicsEx(self.genv)
        # Set custom calibration points
        self.set_custom_calibration_points()

    def calibrate(self) -> None:
        """Method for calibrating the tracker."""
        # Make mouse invisible so it doesn't distract from stimuli
        self.win.mouseVisible = False
        # Set up the calibration display in the graphical environment
        self.genv.setup_cal_display()
        # Clear the screen
        self.win.flip()
        # Perform calibration
        self.tracker.doTrackerSetup()
        # Clear the screen
        self.genv.exit_cal_display()
        self.win.flip()
        self.win.units = 'height'
        # Put the mouse back on the screen for future trials
        self.win.mouseVisible = True

    def save_data(self, data_dir:str=None) -> None:
        """Save data from the eye tracker.
        
        Args:
            dir: The path to store the data to.
        """
        self.tracker.closeDataFile()
        # Set up a folder to store the EDF data files and the associated
        # resources e.g., files defining the interest areas used in each trial
        if not data_dir:
            data_dir = 'data/eyelink'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        # Create a dir for the current testing session
        session_dir = os.path.join(data_dir, self.uniqueid)
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        # Download the EDF data file from the Host PC to a local data folder
        # NOTE: parameters are `source_file_on_the_host` and
        #   `destination_file_on_local_drive`
        local_edf = os.path.join(session_dir,  'raw.edf')
        logging.info('receiving eyelink data')
        # Saves the eye tracker file locally to your machine.
        self.tracker.receiveDataFile(self.edf_file, local_edf)
        logging.info('wrote %s', local_edf)
        self.tracker.close()

    def gaze_position(self) -> list[int | float]:
        """Returns the x,y position of the eye gaze at current time step.
        
        NOTE: Returns eye gaze in pixels set by the screen_pixel_coords
        command.
        """
        sample = self.tracker.getNewestSample()
        if sample is None:
            return (-100000, -100000)
        eye = sample.getLeftEye() or sample.getRightEye()
        return eye.getGaze()

    def close_connection(self) -> None:
        """Closes connection to eye tracker."""
        # TODO make sure this gets called
        if self.tracker.isConnected():
            self.tracker.close()


class MouseLink(EyeLink):
    """A pylink interface that uses the mouse as a dummy EyeLink.
    
    Mouse positional data is interpreted as eye gaze data.

    Args:
        win: The psychopy.Visual window object.
        uniqueid: The mouselink's unique id.
        dummy_mode: Optional flag for debugging.
    """
    def __init__(self, win, uniqueid, dummy_mode=False):
        self.win = win
        self.mouse = event.Mouse()
        self.disable_drift_checks = False
        print("UNITS", self.win.units)
        self.genv = genv = EyeLinkCoreGraphicsPsychoPy(None, self.win)
        foreground_color = (-1, -1, -1)
        genv.setCalibrationColors(foreground_color, self.win.color)
        genv.setTargetType('circle')
        genv.setTargetSize(24)
        # genv.setCalibrationSounds('', '', '')
        genv.fixMacRetinaDisplay()
        self.win.units = 'height'
        print("UNITS", self.win.units)

    def drift_check(self, pos=(0,0)):
        logging.info('MouseLink drift_check')
        return super().fake_drift_check()

    def message(self, msg, log=True):
        logging.debug('MouseLink message')
        return

    def start_recording(self):
        logging.info('MouseLink start_recording')
        return

    def stop_recording(self):
        logging.info('MouseLink stop_recording')
        return

    def setup_calibration(self, full_screen=False):
        logging.info('MouseLink setup_calibration')
        return

    def calibrate(self):
        logging.info('MouseLink calibrate')
        return

    def save_data(self):
        logging.info('MouseLink save_data')
        return

    def gaze_position(self):
        return self.mouse.getPos()

    def close_connection(self):
        logging.info('MouseLink close_connection')
        return


if __name__ == '__main__':
    pass
