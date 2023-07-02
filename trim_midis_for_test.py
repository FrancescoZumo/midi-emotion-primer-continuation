import my_utils
import pygame
import os
from mido import MidiFile

folder = 'minecraft'

my_utils.import_primers('C:\\Users\\franc\\PycharmProjects\\videogame-procedural-music\\midi-emotion\\data_files\\minecraft.mid')

my_utils.generate_final_midi(folder, 5, 0, 60)