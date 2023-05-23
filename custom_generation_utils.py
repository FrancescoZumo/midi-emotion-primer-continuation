from os.path import isfile, join
import os
import time
import pygame
import sys
import numpy as np
import my_utils
import itertools
import os
import signal

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

def generate_va_conditioned_midi(midi_reference, valence, arousal):
    model_used = 'continuous_token'
    project_abs_path = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion'
    generations_rel_path = '\\output\\' + model_used + '\\generations\\inference'
    generations_abs_path = project_abs_path + generations_rel_path

    gen_len = 512
    
    print('loop started')
    os.system('del /q ' + generations_abs_path + '\\*')
    os.chdir('src')
    tmp = os.getcwd()
    print('Current path: ', tmp)
    print('midi_reference: ', midi_reference)
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

    os.chdir('..\\..\\..\\..')
    return midi_conditioned, generations_abs_path

