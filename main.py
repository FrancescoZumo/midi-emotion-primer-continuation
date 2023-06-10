import pygame
import custom_generation_utils as custom_utils
import pandas as pd
from multiprocessing import Process
import os
import time
import my_utils
from mido import MidiFile
import numpy as np


if __name__ == '__main__':

    # mixer config
    freq = 44100  # audio CD quality
    bitsize = -16  # unsigned 16 bit
    channels = 2  # 1 is mono, 2 is stereo
    buffer = 1024  # number of samples
    pygame.mixer.init(freq, bitsize, channels, buffer)

    # optional volume 0 to 1.0
    pygame.mixer.music.set_volume(0.8)
    old_p = None
    first_iteration = True

    midi_reference = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\data_files\\BreathoftheWildCave.mid'
    #midi_reference = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\data_files\\2023_04_13_10_39_53_0_V-035_A004_cut2.mid'
    current_va_path = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\VA_real_time\\output\\current_va.csv'
    current_midi_folder = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\current_midi'
    va_history_path = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\VA_real_time\\output\\DarkSouls3Midir.csv'

    inference_modes = {
        0: 'live',
        1: 'from_file',
    }
    inference_choice = inference_modes[1]

    gpu_scheduling = True
    generation_counter = 0

    while inference_choice == inference_modes[0]:

        if first_iteration:
            # clear generated files
            os.system('del /q ' + current_va_path)
            os.system('del /q ' + current_midi_folder + '\\*')
            try:
                # use the midi reference for beginning
                p = Process(target=custom_utils.play_music, args=(midi_reference, old_p.pid if old_p is not None else None))
                p.start()
                # p.join()
                # custom_utils.play_music(path + '\\' + midi_conditioned)
            except KeyboardInterrupt:
                # if user hits Ctrl/C then exit
                # (works only in console mode)
                pygame.mixer.music.fadeout(1000)
                pygame.mixer.music.stop()
                raise SystemExit

        # SCHEDULING: wait until current_va.csv is generated:
        print('waiting for valence arousal estimation...')
        while not os.path.isfile(current_va_path) and gpu_scheduling:
            time.sleep(1)
        print('MUSIC GENERATION started!')

        if not first_iteration:
            #midi_reference = midi_conditioned
            midi_conditioned_old = midi_conditioned
        current_va = pd.read_csv(current_va_path)

        valence = current_va['valence'][len(current_va)-1]
        arousal = current_va['arousal'][len(current_va)-1]
        print("valence: ", valence, " arousal: ", arousal)
        midi_conditioned, path = custom_utils.generate_va_conditioned_midi(midi_reference, valence, arousal)
        generation_counter+=1
        # move file to current directory
        os.system('move /Y ' + path + '\\' + midi_conditioned + ' ' + current_midi_folder + '\\' + midi_conditioned)
        midi_conditioned = current_midi_folder + '\\' + midi_conditioned

        # rename file accordingly
        new_name = current_midi_folder + '\\' + str(valence) + str(arousal) + '_' + str(generation_counter) + '.mid'
        os.system('move /Y ' + midi_conditioned + ' ' + new_name)
        midi_conditioned = new_name

        # trim primer from generated midi
        print('test trim')
        midi_conditioned = my_utils.trim_primer_from_output(midi_conditioned, midi_reference)
        print("test passed!")

        '''
        print('remove all tracks except piano')
        mid = MidiFile(midi_conditioned)
        #del mid.tracks[5]
        #del mid.tracks[4]
        #del mid.tracks[3]
        del mid.tracks[1]
        mid.save(midi_conditioned)
        print('done')
        '''
        # sett current p as old_p, so it is stopped
        old_p = p

        # listen for interruptions
        try:
            # use the midi file you just saved

            p = Process(target=custom_utils.play_music, args=(midi_conditioned, old_p.pid if old_p is not None else None))
            p.start()
            # p.join()
            # custom_utils.play_music(path + '\\' + midi_conditioned)
        except KeyboardInterrupt:
            # if user hits Ctrl/C then exit
            # (works only in console mode)
            pygame.mixer.music.fadeout(1000)
            pygame.mixer.music.stop()
            raise SystemExit
        
        #removing old midi
        #if not first_iteration:
        #    os.system('del /q ' + midi_conditioned_old)
        
        os.system('del /q ' + current_va_path)

        print('MUSIC GENERATION completed...')
        first_iteration = False
    
    if inference_choice == inference_modes[1]:

        if not os.path.isfile(va_history_path):
            print('file not found: breaking loop')
            quit()
        else:
            va_dataframe = pd.read_csv(va_history_path)

        # process dataframe
        va_dataframe = my_utils.va_series_processing(va_dataframe)

        # setting threshold:
        threshold_abs_inc_ratio_val = np.nanpercentile(va_dataframe['abs_inc_ratio_val'], 80)
        threshold_abs_inc_ratio_ar = np.nanpercentile(va_dataframe['abs_inc_ratio_ar'], 80)

        for index, row in va_dataframe.iterrows():

            if not (row['abs_inc_ratio_val'] > threshold_abs_inc_ratio_val or 
                    row['abs_inc_ratio_ar'] > threshold_abs_inc_ratio_ar):
                continue
            valence = row['valence']
            arousal = row['arousal']
            print("valence: ", valence, " arousal: ", arousal)
            midi_conditioned, path = custom_utils.generate_va_conditioned_midi(midi_reference, valence, arousal)
            generation_counter+=1
            # move file to current directory
            os.system('move /Y ' + path + '\\' + midi_conditioned + ' ' + current_midi_folder + '\\' + midi_conditioned)
            midi_conditioned = current_midi_folder + '\\' + midi_conditioned

            # rename file accordingly
            new_name = current_midi_folder + '\\' + str(valence) + str(arousal) + '_' + str(index) + '.mid'
            os.system('move /Y ' + midi_conditioned + ' ' + new_name)
            midi_conditioned = new_name

            # trim primer from generated midi
            print('test trim')
            midi_conditioned = my_utils.trim_primer_from_output(midi_conditioned, midi_reference)
            print("test passed!")
