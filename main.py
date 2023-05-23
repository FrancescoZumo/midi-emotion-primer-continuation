import pygame
import custom_generation_utils as custom_utils
import pandas as pd
from multiprocessing import Process
import os
import time
import my_utils
from mido import MidiFile


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

    gpu_scheduling = True

    while True:

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

        # DEBUG!
        #primers, maps = my_utils.import_primers(midi_reference)
        #primer_inds = [[maps["tuple2idx"][tuple(symbol)] for symbol in primer] \
        #for primer in primers]

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
        
        # move file to current directory
        os.system('move /Y ' + path + '\\' + midi_conditioned + ' ' + current_midi_folder + '\\' + midi_conditioned)
        midi_conditioned = current_midi_folder + '\\' + midi_conditioned

        # trim primer from generated midi
        print('test trim')
        midi_conditioned = my_utils.trim_primer_from_output(midi_conditioned, midi_reference)
        print("test passed!")

        print('remove all tracks except piano')
        mid = MidiFile(midi_conditioned)
        #del mid.tracks[5]
        #del mid.tracks[4]
        #del mid.tracks[3]
        del mid.tracks[1]
        mid.save(midi_conditioned)
        print('done')



        #remove unwanted tracks
        # mid = pretty_midi.PrettyMIDI(path + '\\' + midi_conditioned)
        # remove drum tracks for now NOT WORKING
        # for instr in mid.instruments:
        #    if instr.is_drum:
        #        instr.notes = []
        # mid.write(midi_conditioned)

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
        if not first_iteration:
            os.system('del /q ' + midi_conditioned_old)
        
        os.system('del /q ' + current_va_path)

        print('MUSIC GENERATION completed...')
        first_iteration = False