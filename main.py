import pygame
import pandas as pd
from multiprocessing import Process
import os
import time
import my_utils
import pretty_midi
import numpy as np
import my_utils
import math

if __name__ == '__main__':

    old_p = None
    first_iteration = True

    # parameters
    gen_len = 512
    video_max_length = np.inf
    inference_modes = {
        0: 'live',
        1: 'from_file',
    }
    inference_choice = inference_modes[1]

    gpu_scheduling = True   # only for live mode

    videogame_choice = 'no_mans_sky'
    normalize_va_predictions = False
    threshold_percentile = 80

    files_in_video_folder = os.listdir('C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\VA_real_time\\videos\\' + videogame_choice)
    available_videos = []
    for file in files_in_video_folder:
        if file[len(file)-4:len(file)] == '.mp4':
            available_videos.append(file)
    print("the following videos will be used:", available_videos)

    # mixer config
    freq = 44100  # audio CD quality
    bitsize = -16  # unsigned 16 bit
    channels = 2  # 1 is mono, 2 is stereo
    buffer = 1024  # number of samples
    pygame.mixer.init(freq, bitsize, channels, buffer)

    # optional volume 0 to 1.0
    pygame.mixer.music.set_volume(0.8)

    for video in available_videos:

        #if not ("na3" in video):
        #    print("skipping: ", video)
        #    continue
        
        video_filename = video[:len(video)-4]   # remove .mp4 from name
        print("processing video: ", video_filename)
        
        midi_reference = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\data_files\\' + videogame_choice + '.mid'
        # these two paths are specific for each video
        current_va_path = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\VA_real_time\\output\\' + video_filename + '.csv'
        output_midi_folder = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\current_midi\\' + video_filename

        output_midi_folder_cond = output_midi_folder + '\\' + 'conditioned'
        output_midi_folder_uncond = output_midi_folder + '\\' + 'unconditioned'

        my_utils.import_primers(midi_reference)

        # if the  directory is not present then create it.
        if not os.path.exists(output_midi_folder):
            os.makedirs(output_midi_folder)
        if not os.path.exists(output_midi_folder_cond):
            os.makedirs(output_midi_folder_cond)
        if not os.path.exists(output_midi_folder_uncond):
            os.makedirs(output_midi_folder_uncond)

        if len(os.listdir(output_midi_folder)) != 0:
            os.system('del /q ' + output_midi_folder + '\\*')
            os.system('del /q ' + output_midi_folder_cond + '\\*')
            os.system('del /q ' + output_midi_folder_uncond + '\\*')

        generation_counter = 0
        # for real time
        while inference_choice == inference_modes[0]:

            if first_iteration:
                # clear generated files
                os.system('del /q ' + current_va_path)
                os.system('del /q ' + output_midi_folder + '\\*')
                try:
                    # use the midi reference for beginning
                    p = Process(target=my_utils.play_music, args=(midi_reference, old_p.pid if old_p is not None else None))
                    p.start()
                    # p.join()
                    # my_utils.play_music(path + '\\' + midi_conditioned)
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
            midi_conditioned, path = my_utils.generate_va_conditioned_midi(midi_reference, valence, arousal, gen_len)
            generation_counter+=1
            # move file to current directory
            os.system('move /Y ' + path + '\\' + midi_conditioned + ' ' + output_midi_folder + '\\' + midi_conditioned)
            midi_conditioned = output_midi_folder + '\\' + midi_conditioned

            # rename file accordingly
            new_name = output_midi_folder + '\\' + str(valence) + str(arousal) + '_' + str(generation_counter) + '.mid'
            os.system('move /Y ' + midi_conditioned + ' ' + new_name)
            midi_conditioned = new_name

            # trim primer from generated midi
            print('test trim')
            midi_conditioned = my_utils.trim_primer_from_output(midi_conditioned, midi_reference)
            print("test passed!")

            # sett current p as old_p, so it is stopped
            old_p = p

            # listen for interruptions
            try:
                # use the midi file you just saved

                p = Process(target=my_utils.play_music, args=(midi_conditioned, old_p.pid if old_p is not None else None))
                p.start()
                # p.join()
                # my_utils.play_music(path + '\\' + midi_conditioned)
            except KeyboardInterrupt:
                # if user hits Ctrl/C then exit
                # (works only in console mode)
                pygame.mixer.music.fadeout(1000)
                pygame.mixer.music.stop()
                raise SystemExit
            
            #removing old midi
            #if not first_iteration:
            #    os.system('del /q ' + midi_conditioned_old)

            # delete va_file for gpu scheduling
            os.system('del /q ' + current_va_path)

            print('MUSIC GENERATION completed...')
            first_iteration = False
        
        print('MODE 1: generating conditioned midi soundtrack\n')
        if inference_choice == inference_modes[1]:

            # MODE 1: generating conditioned procedural music
            if not os.path.isfile(current_va_path):
                print('file not found: breaking loop')
                quit()
            else:
                va_dataframe = pd.read_csv(current_va_path, names=['time', 'valence', 'arousal'])
                while math.isnan(va_dataframe.loc[0]['time']):
                    va_dataframe = va_dataframe.drop(0).reset_index(drop=True)

            # since we cannot predict the future, pad beginning of dataframe first prediction according to frames time window
            # TODO: test everything works fine
            va_dataframe['time'] += 1
            padding_row = pd.DataFrame({
                'time': va_dataframe['time'][0] - 1, 
                'valence': va_dataframe['valence'][0], 
                'arousal': va_dataframe['arousal'][0]
                }, index=[0])
            va_dataframe = pd.concat([padding_row,va_dataframe.loc[:]]).reset_index(drop=True)
            va_dataframe = va_dataframe.drop(va_dataframe.shape[0] - 1).reset_index(drop=True)

            # process dataframe
            va_dataframe = my_utils.va_series_processing(va_dataframe, normalize=normalize_va_predictions)

            # setting threshold:
            threshold_abs_inc_ratio_val = np.nanpercentile(va_dataframe['abs_inc_ratio_val'], threshold_percentile)
            threshold_abs_inc_ratio_ar = np.nanpercentile(va_dataframe['abs_inc_ratio_ar'], threshold_percentile)

            generation_interval = 3
            last_gen_index = 0

            for index, row in va_dataframe.iterrows():

                if index > video_max_length:
                    print("maximum length reached, stopping")
                    break

                # check threshold
                if not (row['abs_inc_ratio_val'] > threshold_abs_inc_ratio_val or 
                        row['abs_inc_ratio_ar'] > threshold_abs_inc_ratio_ar) and index != 0:
                    continue
                # do not generate if last generation happened in previous generation_interval samples
                if (index - last_gen_index) < generation_interval and index != 0:
                    print("last generation too close, continuing")
                    continue
                valence = row['valence']
                arousal = row['arousal']
                print("valence: ", valence, " arousal: ", arousal)
                midi_conditioned, path = my_utils.generate_va_conditioned_midi(midi_reference, valence, arousal, gen_len=gen_len)
                generation_counter+=1
                last_gen_index = index

                # move file to current directory
                os.system('move /Y ' + path + '\\' + midi_conditioned + ' ' + output_midi_folder + '\\' + midi_conditioned)
                midi_conditioned = output_midi_folder + '\\' + midi_conditioned

                # rename file accordingly
                new_name = output_midi_folder + '\\'  + 't_' + "{:03d}".format(index) + '__' + "{:.2f}_{:.2f}_".format(valence, arousal) + '.mid'
                os.system('move /Y ' + midi_conditioned + ' ' + new_name)
                midi_conditioned = new_name

                # trim primer from generated midi and save final file
                midi_conditioned = my_utils.trim_primer_from_output(midi_conditioned, midi_reference, live_mode=False)

            end_t = min(video_max_length, va_dataframe.shape[0])
            print("generating final midi files for " + video[:len(video)-4] + " until t = " + str(end_t))
            my_utils.generate_final_midi(videogame_choice, video_filename, output_midi_folder_cond, gen_min_interval=5, start_t=0, end_t=end_t)


            # MODE 2: generating unconditioned procedural music
            midi_total_length = 0.0
            print('MODE 2: generating unconditioned midi soundtrack\n')
            continue
            for index in range(1000):
                midi_conditioned, path = my_utils.generate_va_conditioned_midi(midi_reference, valence=None, arousal=None, gen_len=gen_len)
                # move file to current directory
                os.system('move /Y ' + path + '\\' + midi_conditioned + ' ' + output_midi_folder_uncond + '\\' + midi_conditioned)
                midi_conditioned = output_midi_folder_uncond + '\\' + midi_conditioned

                # rename file accordingly
                new_name = output_midi_folder_uncond + '\\'  + 'unconditioned_' + "{:02d}".format(index) + '.mid'
                os.system('move /Y ' + midi_conditioned + ' ' + new_name)
                midi_conditioned = new_name

                # trim primer from generated midi and save final file
                midi_conditioned = my_utils.trim_primer_from_output(midi_conditioned, midi_reference, live_mode=False)

                # check current length
                curr_mid = pretty_midi.PrettyMIDI(midi_conditioned)
                curr_mid_duration  = curr_mid.get_end_time()

                midi_total_length += curr_mid_duration

                if midi_total_length >= end_t:
                    break





