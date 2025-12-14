import os
import sys
from collections import defaultdict
import json
import numpy as np

# Get the directory containing data_processing.py
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append('..')

import pandas as pd
from tqdm import tqdm

import config
import parser

IMG_DIR = os.path.join(MODULE_DIR, 'motion_distributions/data/train')

import warnings
warnings.filterwarnings('ignore')


def assign_path_condition(x):
    A = 11
    if 'yessp' in x:
        return 'straight_path'
    if 'nosp' in x:
        return 'no_straight_path'
    if 'scene' in x:
        scene_num = int(x.split('_')[1])
        scene_idx = int(x.split('_')[-1])
        if scene_num == 1 and scene_idx <= A:
            return 'straight_path'
        if scene_num == 1 and scene_idx > A:
            return 'no_straight_path'
        if scene_num == 2:
            return 'straight_path'
    raise ValueError


def assign_sim_time_condition(x):
    if 'high' in x:
        return 'high'
    elif 'med' in x:
        return 'med'
    elif 'low' in x:
        return 'low'
    else:
        return 'other'


def assign_experiment_label(x):
    if 'yessp' in x:
        return 'exp1'
    elif 'nosp' in x:
        return 'exp1'
    elif 'scene' in x:
        return 'exp2'
    else:
        raise ValueError(f"Unknown scene name: {x}")


def assign_ground_truth_response(scene_name:str) -> bool:
    if 'yescol' in scene_name:
        return True
    elif 'nocol' in scene_name:
        return False
    elif 'scene' in scene_name:
        return True
    else:
        raise ValueError(f"Unknown scene name: {scene_name}")


def scene_to_screen_coordinates(scene_coordinate):
    """Convert scene coordinates to screen coordinates.
    
    Args:
        scene_coordinate: Tuple of (x, y) coordinates in the scene
    
    Returns:
        Tuple of (x, y) coordinates in the screen
    """
    scene_x, scene_y = scene_coordinate
    scene_x_lim = 800
    scene_y_lim = 1000
    screen_x_lim = 1920
    screen_y_lim = 1080
    converted_x = screen_x_lim/2 - scene_x_lim/2 + scene_x
    converted_y = screen_y_lim/2 - scene_y_lim/2 + scene_y
    return [converted_x, converted_y]


def convert_to_dataframe(
    experiment_data:dict, data_type:str='gaze') -> pd.DataFrame:
    """Converts eye tracking data from dictionary format to a pandas DataFrame.
    
    Takes the raw experiment data dictionary containing trials for multiple subjects
    and converts a specified data type (gaze, fixations, or saccades) into a DataFrame
    with one row per data point. Each row includes both the eye tracking data and
    associated metadata about the trial and subject.
    
    Args:
        experiment_data: Dictionary containing subject IDs, treatments, and trial data
        data_type: Type of eye tracking data to extract - 'gaze', 'fixations', or 'saccades'

    Returns:
        DataFrame where each row is one eye tracking data point with associated metadata
        
    Raises:
        ValueError: If data_type is not one of 'gaze', 'fixations', or 'saccades'
    """
    # Initialize defaultdict to store all data fields
    all_data = defaultdict(list)
    # Get the appropriate namedtuple fields based on data type
    fields = {
        'gaze': parser.Gaze._fields,
        'fixations': parser.Fixation._fields, 
        'saccades': parser.Saccade._fields
    }.get(data_type)
    if fields is None:
        raise ValueError(f"Invalid data_type: {data_type}")
    # Pre-calculate number of subjects for iteration
    n_subjects = len(experiment_data['subject_id'])
    # Process each subject's trials
    for idx in range(n_subjects):
        trials = experiment_data['trials'][idx]
        subject_id = experiment_data['subject_id'][idx]
        subject_treatment = experiment_data['subject_treatment'][idx]
        # Process each trial for this subject
        for t in trials:
            n_points = len(t[data_type])
            if n_points == 0:
                continue
            # Create metadata dictionary - values repeated for each data point
            metadata = {
                'subject_id': [subject_id] * n_points,
                'subject_treatment': [subject_treatment] * n_points,
                'scene_name': [t['scene_name']] * n_points,
                'block_index': [t['block_idx']] * n_points,
                'button_response': [t['button_response']] * n_points,
                'response_time': [t['response_time']] * n_points,
                'block_duration': [t['block_duration']] * n_points,
                'trial_duration': [t['trial_duration']] * n_points
            }
            # Add all metadata fields to the data collection
            for key, values in metadata.items():
                all_data[key].extend(values)
            # Extract and add the eye tracking data points
            for field_idx, field in enumerate(fields):
                all_data[field].extend(point[field_idx] for point in t[data_type])
    return pd.DataFrame(all_data)


def import_gaze_data(
    data_dir:str=os.path.join(config.DATA_DIR, 'experiment1'),
    data_type:str='gaze',
    include_fixations:bool=False
    ) -> pd.DataFrame:
    """Import the gaze data from the ASC files.
    
    Args:
        data_dir: Path to the data directory.

    Returns:
        DataFrame with the gaze data.
    """
    asc_files = [
        f
        for f
        in os.listdir(data_dir)
        if f.endswith('.asc')
    ]
    # Row structure for trial data dataframe
    experiment_data = {
        'subject_id': [],
        'subject_treatment': [],
        'trials': []
    }
    # Define process_file function outside to make it pickleable
    for fname in tqdm(asc_files, desc="Processing ASC files"):
        subject_id = fname.split('_')[0]
        subject_treatment = fname.split('_')[1].split('.')[0]
        trials = parser.parse_eyedata(
            os.path.join(data_dir, f'{fname}'))
        experiment_data['subject_id'].append(subject_id)
        experiment_data['subject_treatment'].append(subject_treatment)
        experiment_data['trials'].append(trials)
    # Convert the dictionary to a dataframe
    return convert_to_dataframe(experiment_data, data_type)


def get_intra_trial_data(gaze_data:pd.DataFrame) -> pd.DataFrame:
    """Get the intra-trial data from the gaze data.
    
    Args:
        gaze_data: The gaze data.

    Returns:
        The intra-trial data with time replaced by running count per scene/subject,
        merged with ball position data.
    """
    # Check if the scene name contains 'intra'
    intra_trial_gaze_data = gaze_data[gaze_data.scene_name.str.contains('intra')]
    # Replace '_intra' with ''
    intra_trial_gaze_data.scene_name = intra_trial_gaze_data.scene_name.apply(
        lambda x: x.replace('_intra', ''))
    # Remove the comprehension trials
    intra_trial_gaze_data = intra_trial_gaze_data[
        ~intra_trial_gaze_data.scene_name.str.contains('comprehension')]
    # Add trajectory index column
    intra_trial_gaze_data['trajectory_idx'] = intra_trial_gaze_data.groupby(
        ['scene_name', 'subject_id']).cumcount()
    return intra_trial_gaze_data


def get_participant_responses(gaze_df:pd.DataFrame) -> list[pd.DataFrame]:
    """
    Process gaze data to extract button assignments and post trial responses.
    
    Args:
        gaze_df: DataFrame containing eye gaze data
    
    Returns:
        Tuple of (button_assignments, post_trial_button_responses) DataFrames
    """
    # Process comprehension trials for button assignments
    comp_df = gaze_df[gaze_df.scene_name.str.contains('post')]
    comp_df.scene_name = comp_df.scene_name.str.replace('_post', '')
    comp_df = comp_df[comp_df.scene_name.str.contains('comprehension')]
    # Get button assignments
    button_assignments = (comp_df[['subject_id', 'scene_name', 'button_response', 'time']]
        .drop_duplicates()
        .sort_values('time')
        .groupby(['subject_id', 'scene_name'])
        .last()
        .reset_index())
    # Map yes/no values
    button_assignments['button_value'] = button_assignments.scene_name.map(
        lambda x: 'yes' if 'yes' in x else 'no' if 'no' in x else None)
    button_assignments = (button_assignments[['subject_id', 'button_response', 'button_value']]
        .drop_duplicates()
        .reset_index(drop=True))
    # Process post trial responses
    post_df = gaze_df[gaze_df.scene_name.str.contains('post')]
    post_df.scene_name = post_df.scene_name.str.replace('_post', '')
    post_df = post_df[~post_df.scene_name.str.contains('comprehension')]
    post_trial_button_responses = (post_df[['subject_id', 'scene_name', 'button_response', 'trial_duration']]
        .drop_duplicates())
    return button_assignments, post_trial_button_responses


def process_ball_and_gaze_data(gaze_df:pd.DataFrame) -> pd.DataFrame:
    """Process ball position data and merge with intra-trial gaze data.
    
    Args:
        gaze_df: DataFrame containing eye gaze data with columns:
            scene_name, subject_id, time, x, y, button_response, trial_duration
    
    Returns:
        DataFrame containing merged ball position and gaze data with columns:
            scene_name, subject_id, time, x, y, position
    """
    # Extract ball positions from scene description files
    ball_pos_data = defaultdict(list)
    # Get all scene description files from both experiments
    scene_desc_paths = [
        os.path.join(MODULE_DIR, '../motion_distributions/data/scene_descs/experiment1'),
        os.path.join(MODULE_DIR, '../motion_distributions/data/scene_descs/experiment2')
    ]
    scene_desc_files = []
    for path in scene_desc_paths:
        scene_desc_files.extend([
            os.path.join(path, f) 
            for f in os.listdir(path) 
            if f.endswith('.json')
        ])
    # Process each scene description file
    for sd_file in scene_desc_files:
        scene_name = os.path.splitext(os.path.basename(sd_file))[0]
        with open(sd_file, 'r') as f:
            data = json.load(f)
            for item in data:
                if item['type'] == 'Dynamic':
                    ball_pos_data['scene_name'].append(scene_name)
                    ball_pos_data['ball_start_position'].append(
                        scene_to_screen_coordinates(item['position'])
                    )
    ball_pos_df = pd.DataFrame(ball_pos_data)
    return pd.merge(gaze_df, ball_pos_df, on='scene_name')


def remove_pre_lockon(df, radius):
    """Returns eye gaze data that occurs after entering radius around a point AND being below the ball.
    
    Args:
        df: Eye gaze DataFrame with subject_id, scene_name columns
        radius: Radius around center point
    
    Returns:
        Filtered eye gaze data
    """
    filtered_data = []
    # Check if the DataFrame has the required 'ball_start_position' column
    if 'ball_start_position' not in df.columns:
        df = process_ball_and_gaze_data(df)
    for _, group_data in df.groupby(['subject_id', 'scene_name']):
        # Sort by time to ensure correct order
        group_data = group_data.sort_values('time')
        # Get center point from first position
        center_x, center_y = group_data['ball_start_position'].iloc[0]
        # Calculate distances from center point
        distances = np.sqrt(
            (group_data['x'] - center_x)**2 +
            (group_data['y'] - center_y)**2
        )
        # Create mask for points that satisfy both conditions
        valid_points = (distances <= radius) & (group_data['y'] > center_y)
        # Find first point satisfying both conditions
        first_entry = valid_points[valid_points].index.min()
        if pd.notna(first_entry):
            # Get all data after first entry
            filtered_data.append(group_data.loc[first_entry:])
    return pd.concat(filtered_data) if filtered_data else pd.DataFrame()


def remove_impossible_values(df):
    """Remove physiologically impossible gaze positions and velocities."""
    screen_bounds = {'x': (0, 1920), 'y': (0, 1080)}  # adjust as needed
    # Remove out-of-bounds gaze positions
    mask = (
        # Right of left border of screen
        (df['x'] >= screen_bounds['x'][0]) &
        # Left of right border of screen
        (df['x'] <= screen_bounds['x'][1]) &
        # Below top border of screen
        (df['y'] >= screen_bounds['y'][0]) &
        # Above bottom border of screen
        (df['y'] <= screen_bounds['y'][1]))
    return df[mask].copy()


def clean_gaze_data(df):
    """Clean eye gaze data using standard preprocessing steps.
    
    Args:
        df: Expected cols time, x, y, subject_id, scene_name
        velocity_threshold: Max vel for fixation detection (degrees/second)
        dispersion_threshold: Max dispersion for fixation detection (degrees)
        min_fixation_duration: Min duration for a valid fixation (milliseconds)
        max_gap: Max duration of gaps to interpolate (milliseconds)
    
    Returns:
        Cleaned gaze data with identified fixations and saccades
    """
    cleaned_data = df.copy()
    # 1. Remove physiologically impossible values
    cleaned_data = remove_impossible_values(cleaned_data)
    # 2. Remove pre-lock-on gaze
    cleaned_data = remove_pre_lockon(cleaned_data, 40)
    # 3. Replace time with running count for each scene_name, subject_id pair
    cleaned_data['trajectory_idx'] = cleaned_data.groupby(
        ['scene_name', 'subject_id']).cumcount()
    return cleaned_data


def get_human_data(
        data_dir:str=os.path.join(MODULE_DIR, config.DATA_DIR, 'experiment1'),
        remove_outliers:bool=False,
        include:str='both'
        ) -> pd.DataFrame:
    """Get the clean human data.
    
    Args:
        gaze_data: The gaze data.

    Returns:
        The clean human data.
    """
    gaze_data = import_gaze_data(data_dir)
    human_data = get_intra_trial_data(gaze_data)
    # Get button response data
    button_assignments, button_responses = get_participant_responses(gaze_data)
    # Add button response to the intra trial data
    human_data = pd.merge(
        left=human_data,
        right=button_responses,
        on=['subject_id', 'scene_name']
    )
    human_data = pd.merge(
        left=human_data,
        right=button_assignments,
        on=['subject_id', 'button_response'])
    # Process ball position data and merge with gaze data
    human_data = process_ball_and_gaze_data(human_data)
    if remove_outliers:
        # Clean the gaze data
        human_data = clean_gaze_data(human_data)
    if include in ('behavioral', 'both'):
        print(human_data.head())
        human_data['correct_response'] = human_data.scene_name.apply(
            assign_ground_truth_response)
        # Map the key press for the button to the yes/no value of that key
        human_data['button_value'] = human_data.button_value == 'yes'
        # Determine whether the button press was correct or not
        human_data['correct'] = (
            human_data['button_value'] == human_data['correct_response']
            ).astype(int)
        # Determine mean accuracy across subjects and scenes
        mean_accuracy_subj = human_data.groupby(
            'subject_id').correct.mean().reset_index()
        mean_accuracy_scene = human_data.groupby(
            'scene_name').correct.mean().reset_index()
        mean_accuracy_subj = mean_accuracy_subj.rename(
            columns={'correct': 'mean_acc_subj'})
        mean_accuracy_scene = mean_accuracy_scene.rename(
            columns={'correct': 'mean_acc_scene'})
        # Merge accuracy results with the beahavior data
        human_data = pd.merge(
            left=human_data, right=mean_accuracy_subj, on='subject_id')
        human_data = pd.merge(
            left=human_data, right=mean_accuracy_scene, on='scene_name')
        # Assign the path condition labels to each row
        human_data['path_condition'] = human_data.scene_name.apply(assign_path_condition)
        # Assign the simulation time condition to each row
        human_data['sim_time_condition'] = human_data.scene_name.apply(assign_sim_time_condition)
        # Label the scenes according to which experiment they're from
        human_data['experiment'] = human_data.scene_name.apply(assign_experiment_label)
        # Calculate the z-score of the trial duration
        human_data['trial_duration_zscore'] = human_data.groupby(
            'subject_id')['trial_duration'].transform(
                lambda x: (x-x.mean())/x.std())
        if include == 'behavioral':
            human_data = human_data[
                [
                    'subject_id', 'scene_name', 'response_time', 'trial_duration',
                    'trial_duration_zscore', 'correct', 'mean_acc_subj', 'mean_acc_scene',
                    'path_condition', 'sim_time_condition', 'experiment'
                ]
            ]
            human_data = human_data.drop_duplicates()
            return human_data
        if include == 'both':
            return human_data[
                [
                    'subject_id', 'scene_name', 'time', 'x', 'y', 'pupil',
                    'response_time', 'trial_duration', 'trial_duration_zscore',
                    'correct', 'mean_acc_subj', 'mean_acc_scene', 'path_condition',
                    'sim_time_condition', 'experiment'
                ]
            ]
    else:
        return human_data[
            ['subject_id', 'scene_name', 'x', 'y', 'time', 'pupil']]


def get_gaze_data_from_human_data(human_data:pd.DataFrame) -> pd.DataFrame:
    """Get the gaze data from the human data.
    
    Args:
        human_data: The human data.

    Returns:
        The gaze data.
    """
    return human_data[
        ['subject_id', 'scene_name', 'x', 'y', 'time', 'pupil']
    ]


def get_behavior_data_from_human_data(human_data:pd.DataFrame) -> pd.DataFrame:
    """Get the behavioral data from the human data.
    
    Args:
        human_data: The human data.

    Returns:
        The behavioral data.
    """
    behavior_data = human_data[
        [
            'subject_id', 'scene_name', 'response_time', 'trial_duration',
            'trial_duration_zscore', 'correct', 'mean_acc_subj', 'mean_acc_scene',
            'path_condition', 'sim_time_condition', 'experiment'
        ]
    ]
    behavior_data = behavior_data.drop_duplicates()
    return behavior_data


def get_simulation_model_predictions(
        data_dir:str=os.path.join(MODULE_DIR, config.DATA_DIR, 'simulation_results.json')
        ) -> pd.DataFrame:
    """Get the simulation model predictions.
    
    Args:
        data_dir: The path to the simulation results.

    Returns:
        The simulation model predictions.
    """
    with open(data_dir, 'r') as f:
        simulation_model_predictions_dict = json.load(f)
    simulation_prediction_data = pd.DataFrame.from_dict(
        simulation_model_predictions_dict)
    return simulation_prediction_data


def main():
    # Get raw gaze data
    fixation_data = import_gaze_data(data_dir=os.path.join(MODULE_DIR, config.DATA_DIR, 'experiment1'), data_type='fixations')
    print(fixation_data.head())

if __name__ == '__main__':
    main()