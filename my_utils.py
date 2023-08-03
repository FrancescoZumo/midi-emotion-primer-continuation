# Author: Francesco Zumerle
# code written for thesis: 
#   Procedural music generation for videogames conditioned through video emotion recognition


import pretty_midi
import src.data.data_processing as data_proc
from mido import MidiFile, tempo2bpm, MetaMessage
import numpy as np
from os.path import isfile, join
import os
import pygame
import signal

TRIM_BEGIN = 0
TRIM_END = 10

def play_music(midi_filename, old_p_pid):
    '''Stream music_file in a blocking manner'''

    # mixer config
    freq = 44100  # audio CD quality
    bitsize = -16  # unsigned 16 bit
    channels = 2  # 1 is mono, 2 is stereo
    buffer = 1024  # number of samples
    pygame.mixer.init(freq, bitsize, channels, buffer)

    clock = pygame.time.Clock()
    
    pygame.mixer.music.load(midi_filename)

    if old_p_pid is not None:
        os.kill(old_p_pid, signal.SIGTERM)

    pygame.mixer.music.play(-1)
    while pygame.mixer.music.get_busy():
        clock.tick(30)  # check if playback has finished

def generate_va_conditioned_midi(midi_reference, valence, arousal, gen_len):
    if valence is None and arousal is None:
        model_used = 'vanilla'
    else:
        model_used = 'continuous_concat'
    project_abs_path = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion'
    generations_rel_path = '\\output\\' + model_used + '\\generations\\inference'
    generations_abs_path = project_abs_path + generations_rel_path

    print("getting midi reference tempo")
    midi_reference_tempo = get_tempo(midi_reference)
    
    print('loop started')
    os.system('del /q ' + generations_abs_path + '\\*')
    os.chdir('src')
    tmp = os.getcwd()
    print('Current path: ', tmp)
    print('midi_reference: ', midi_reference)
    if model_used == 'vanilla':
        os.system('python generate.py --gen_len '+str(gen_len) + 
                  ' --model_dir vanilla --conditioning none --batch_size 1 --primer_path ' + midi_reference)
    else: 
        os.system('python generate.py --gen_len ' + str(gen_len) + ' --model_dir ' + model_used + ' --conditioning ' + model_used + 
              ' --batch_size 1 --valence '+ str(valence) + ' --arousal ' + str(arousal) + ' --primer_path ' + midi_reference)
    os.chdir('..')
    tmp = os.getcwd()
    print('Current path: ', tmp)

    files = [f[:] for f in os.listdir(generations_abs_path) if isfile(join(generations_abs_path, f))]

    os.chdir(generations_rel_path[1:])
    tmp = os.getcwd()
    print('Current path: ', tmp)

    midi_conditioned = ''

    for i, file in enumerate(files):

        if not file.endswith('.mid'):
            continue

        midi_conditioned = file
        print('playing ', i, ' file')
        break

    #print("setting tempo of generated midi")
    #curr_mid = set_tempo(midi_conditioned, midi_reference_tempo)
    #curr_mid.save(midi_conditioned)

    os.chdir('..\\..\\..\\..')

    return midi_conditioned, generations_abs_path

def determine_primer_duration(midi_file):
    mid = MidiFile(midi_file)
    file_duration  = mid.length
    if file_duration < 9:
        primer_duration = file_duration
    if (TRIM_END - TRIM_BEGIN) > (file_duration * 0.5):
        primer_duration = np.ceil(file_duration * 0.5)
    else:
        primer_duration = TRIM_END - TRIM_BEGIN
    
    return file_duration, primer_duration


#TODO: devo salvarmi la durata dell primer per rimuoverla dopo, deve essere la stessa non ricalcolata
def import_primers(midi_reference):
    # let's try importing a midi file and converting it to music tokens
    mid = pretty_midi.PrettyMIDI(midi_reference)

    # used to fix compatibility issues
    for i, _ in enumerate(mid.instruments):
        if mid.instruments[i].name not in ['drums', 'piano', 'strings', 'bass', 'guitar']:
            mid.instruments[i].name = 'piano'

    # determine trim length
    file_duration, primer_duration = determine_primer_duration(midi_reference)
    print("midi reference duration: ", file_duration, " seconds")

    #cut from beginning
    mid_cut = data_proc.trim_midi(mid, TRIM_BEGIN, TRIM_END, True)

    maps = data_proc.get_maps()

    # save primer as midi
    mid_cut.write(midi_reference[:len(midi_reference)-4] + '_primer' +'.mid')

    bars_primer = data_proc.mid_to_bars(mid_cut, maps['event2idx'])
    return bars_primer, maps

def trim_primer_from_output(midi_output, midi_reference, live_mode=True):
    # determine trim length
    ref_duration, primer_duration = determine_primer_duration(midi_reference)
    out_duration, _ = determine_primer_duration(midi_output)
    print("midi generated duration: ", out_duration, " seconds")

    print(ref_duration, primer_duration, out_duration)

    if out_duration - primer_duration < 9 and live_mode:
        print('keeping primer inside generated file')
        out_file = midi_output
    else:
        mid = pretty_midi.PrettyMIDI(midi_output)
        print("cutting first " + str(primer_duration) + " seconds from midi")
        mid_cut = data_proc.trim_midi(mid, primer_duration, 10000, True)

        out_file = midi_output[:-4] + "_cut.mid"
        mid_cut.write(out_file)
        #remove output file with primer
        #if not live_mode:
        #    os.system('del /q ' + midi_output)

    return out_file

def va_series_processing(va_dataframe, normalize=False):

    # normalize valence and arousal series:
    if normalize:
        va_dataframe, _ , _ = normalize_columns(va_dataframe, custom_min=-1, custom_max=1, feat_indexes=[1, 2], verbose=1)

    # get abs(incremental ratio)
    abs_inc_ratio_val = []
    abs_inc_ratio_ar = []
    for index, row in va_dataframe.iterrows():
        if index == 0:
            previous_val = row['valence']
            previous_ar = row['arousal']
            abs_inc_ratio_val.append(np.nan)
            abs_inc_ratio_ar.append(np.nan)
            continue
        abs_inc_ratio_val.append(np.abs((float(row['valence']) - float(previous_val))/2))
        abs_inc_ratio_ar.append(np.abs((float(row['arousal']) - float(previous_ar)/2)))
        previous_val = row['valence']
        previous_ar = row['arousal']
    if not len(abs_inc_ratio_ar) == len(va_dataframe):
        print('fix bug here please')
        quit()
    va_dataframe['abs_inc_ratio_val'] = abs_inc_ratio_val
    va_dataframe['abs_inc_ratio_ar'] = abs_inc_ratio_ar
    
    # get std
    va_dataframe['std_abs_inc_ratio_val'] = np.nanstd(abs_inc_ratio_val)
    va_dataframe['std_abs_inc_ratio_ar'] = np.nanstd(abs_inc_ratio_ar)

    # get moving average of current series
    ma_abs_inc_ratio_val = []
    ma_abs_inc_ratio_ar = []
    previous_val = []
    previous_ar = []
    window = 5
    for index, row in va_dataframe.iterrows():
        # update previous n val/ar list
        previous_val.append(row['abs_inc_ratio_val'])
        previous_ar.append(row['abs_inc_ratio_ar'])
        # if first window-1 iteration, return nan
        if index < window - 1:
            ma_abs_inc_ratio_val.append(np.nan)
            ma_abs_inc_ratio_ar.append(np.nan)
            continue
        # calculate moving average
        ma_abs_inc_ratio_val.append(np.mean(previous_val)/window)
        ma_abs_inc_ratio_ar.append(np.mean(previous_ar)/window)

        # remove old value
        previous_val.pop(0)
        previous_ar.pop(0)

    va_dataframe['ma_abs_inc_ratio_val'] = ma_abs_inc_ratio_val
    va_dataframe['ma_abs_inc_ratio_ar'] = ma_abs_inc_ratio_ar

    return va_dataframe

def generate_final_midi(videogame_choice, video_name,  output_final_midis_path, gen_min_interval, start_t, end_t):

    path_to_midis = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\current_midi\\' + video_name
    available_midis = os.listdir(path_to_midis)
    output_final_midis_path += '\\'

    try:
        os.mkdir(output_final_midis_path)
    except FileExistsError:
        print('directory already existing')

    os.system('del /q ' + output_final_midis_path + '*')

    prev_midi_file = ''
    prev_t = -np.inf
    prev_mid = []
    prev_mid_duration = np.nan
    final_mid_files_path = []
    
    for midi_file in available_midis:
        
        # keep only files with primer trimmed
        if midi_file.find('cut') < 0:
            continue
        
        curr_t = int(midi_file[2:5])

        print('current_midi: ', midi_file)

        # if curr_t is acceptable and satisfies gen_min_interval
        if curr_t == 0 or (curr_t >= start_t and curr_t <= end_t and (curr_t - prev_t) > gen_min_interval):

            print('current_midi: ', midi_file)

            print("getting midi reference tempo")
            midi_reference_tempo = get_tempo(path_to_midis + '\\' + midi_file)
            curr_mid = pretty_midi.PrettyMIDI(path_to_midis + '\\' + midi_file)
            curr_mid_duration  = curr_mid.get_end_time()

            # doesn't count as iteration, just loading beginning mid
            if curr_t == 0:
                path_to_beginning_mid = path_to_midis + '\\' + midi_file
                continue
            
            # if first iteration
            if prev_t == -np.inf:
                # trim beginning midi until first generation starts
                beginning_mid = pretty_midi.PrettyMIDI(path_to_beginning_mid)
                beginning_mid = data_proc.trim_midi(beginning_mid, 0, curr_t, False)
                beginning_mid.write(output_final_midis_path + 't_000_beginning.mid')
                # update prev variables
                final_mid_files_path.append(output_final_midis_path + 't_000_beginning.mid')
                prev_midi_file, prev_t, prev_mid, prev_mid_duration = midi_file, curr_t, curr_mid, curr_mid_duration
                continue
            
            # determine prev mid desired duration
            prev_mid_desired_duration = np.float(curr_t - prev_t)
            final_midi_name = prev_midi_file[:len(prev_midi_file)-8] + '_final.mid'

            if prev_mid_duration < prev_mid_desired_duration:
                #TODO: loop prev midi n times
                n_iterations = int(np.ceil(prev_mid_desired_duration / prev_mid_duration))
                for iter in range(n_iterations, 0, -1):
                    part = len(range(n_iterations, 0, -1)) - iter
                    # bug da sistemare
                    final_midi_name_part = output_final_midis_path + 'part' + str(part) + '_' + final_midi_name
                    if iter != 1:
                        # save a copy of current midi
                        prev_mid.write(final_midi_name_part)
                        final_mid_files_path.append(final_midi_name_part)
                        print(get_tempo(final_midi_name_part))

                    else:
                        # last iteration, generare remaining seconds
                        remaining_seconds = prev_mid_desired_duration - (prev_mid_duration * (n_iterations -1))
                        prev_mid = data_proc.trim_midi(prev_mid, 0, remaining_seconds, False)
                        print(prev_midi_file, ' desired_duration: ', remaining_seconds, ' real duration ', prev_mid.get_end_time())
                        prev_mid.write(final_midi_name_part)
                        print(get_tempo(final_midi_name_part))

                        final_mid_files_path.append(final_midi_name_part)

            else:
                # trim prev midi to desired duration
                prev_mid = data_proc.trim_midi(prev_mid, 0, prev_mid_desired_duration, False)
                print(prev_midi_file, ' desired_duration: ', prev_mid_desired_duration, ' real duration ', prev_mid.get_end_time())
                prev_mid.write(output_final_midis_path + final_midi_name)
                print(get_tempo(output_final_midis_path + final_midi_name))
            
                # update final midi
                #final_mid = concatenate_midis(final_mid, prev_mid)
                final_mid_files_path.append(output_final_midis_path + final_midi_name)

            # update prev variables
            prev_midi_file, prev_t, prev_mid, prev_mid_duration = midi_file, curr_t, curr_mid, curr_mid_duration
    
    # concatenate last file
    final_midi_name = prev_midi_file[:len(prev_midi_file)-9] + '_final.mid'
    prev_mid.write(output_final_midis_path + final_midi_name)
    final_mid_files_path.append(output_final_midis_path + final_midi_name)

    print('synthesizing midi files to wav')
    for i, file in enumerate(final_mid_files_path):
        os.system('C:\\tools\\fluidsynth\\bin\\fluidsynth.exe ' + file + ' -F ' + output_final_midis_path + str(i) + '.wav')



def get_tempo(path_to_midi):

    mid = MidiFile(path_to_midi)

    for msg in mid:     # Search for tempo
        if msg.type == 'set_tempo':
            return msg.tempo
    return 500000       # If not found return default tempo

def set_tempo(midi_conditioned, tempo):
    curr_mid = MidiFile(midi_conditioned)
    for index, metamessage in enumerate(curr_mid.tracks[0]):
        if metamessage.type == 'set_tempo':
            curr_mid.tracks[0][index].tempo = tempo
            break


def normalize_columns(va_dataframe, custom_min=None, custom_max=None, feat_indexes=[0, 1], verbose=0):
    """
    Normalize valence and arousal predictions in 0-1 range

    Args:
        va_dataframe: input dataframe
        feat_dict: dict containing indexes inside df
        feat_indexes: columns to normalize, default are valence and arousal
        custom_min: used for custom range
        custom_max: used for custom range
        verbose: if 1, prints min and max values before and after normalization

    Return:
      dataframe with normalized columns
    """
    curr_min_value = None
    curr_max_value = None

    # normalization formula: (x - min) / (max - min)
    for feat in feat_indexes:  # columns
        if verbose:
            print("min and max values before normalization:",
                  va_dataframe.iloc[:, feat].min(), va_dataframe.iloc[:, feat].max())

        va_dataframe.iloc[:, feat] = (va_dataframe.iloc[:, feat] - va_dataframe.iloc[:, feat].min()) / (
                va_dataframe.iloc[:, feat].max() - va_dataframe.iloc[:, feat].min())
        # linear conversion: NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
        if custom_min is not None and custom_max is not None and (custom_min != 0 or custom_max != 1):
            va_dataframe, curr_min_value, curr_max_value = linear_conversion(va_dataframe, feat, 0, 1, custom_min, custom_max)
        if verbose:
            print("min and max values after normalization:", curr_min_value, curr_max_value)

    if curr_max_value is None or curr_min_value is None:
        raise Exception("no min or max values were determined, check function usage")
    return va_dataframe, curr_min_value, curr_max_value

def linear_conversion(df, df_column, old_min, old_max, custom_min, custom_max):
    old_range = (old_max - old_min)
    if old_range == 0:
        df.iloc[:, df_column] = custom_min
    else:
        custom_range = (custom_max - custom_min)
        df.iloc[:, df_column] = (((df.iloc[:,
                                     df_column] - old_min) * custom_range) / old_range) + custom_min
    curr_min_value = df.iloc[:, df_column].min()
    curr_max_value = df.iloc[:, df_column].max()
    return df, curr_min_value, curr_max_value