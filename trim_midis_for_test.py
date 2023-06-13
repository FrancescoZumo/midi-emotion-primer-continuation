import my_utils
import pygame
import os
from mido import MidiFile

folder = 'dark_souls'


my_utils.generate_final_midi(folder, 5, 0, 60)

#TODO: fixare problema bpm perso, ora va fino a trimming, roba final no purtroppo


'''
# mixer config
freq = 44100  # audio CD quality
bitsize = -16  # unsigned 16 bit
channels = 2  # 1 is mono, 2 is stereo
buffer = 1024  # number of samples
pygame.mixer.init(freq, bitsize, channels, buffer)
pygame.mixer.music.set_volume(0.8)

path_to_midis = 'C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\current_midi\\' + folder + '\\final'
list_of_files = os.listdir(path_to_midis)

for file in list_of_files:
    clock = pygame.time.Clock()

    pygame.mixer.music.load(path_to_midis +'\\'+ file)

    pygame.mixer.music.play(1)

    while pygame.mixer.music.get_busy():
        clock.tick(30)  # check if playback has finished
'''