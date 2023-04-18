import pretty_midi
import src.data.data_processing as data_proc
from mido import MidiFile
import numpy as np



TRIM_BEGIN = 0
TRIM_END = 10


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

    # determine trim length
    file_duration, primer_duration = determine_primer_duration(midi_reference)
    print("midi reference duration: ", file_duration, " seconds")

    mid_cut = data_proc.trim_midi(mid, file_duration - primer_duration, file_duration, True)

    maps = data_proc.get_maps()

    # used to fix compatibility issues
    for i, _ in enumerate(mid_cut.instruments):
        mid_cut.instruments[i].name = 'PIANO'
    # note_events = data_proc.mid_to_timed_tuples(mid, maps['event2idx'])

    bars_primer = data_proc.mid_to_bars(mid_cut, maps['event2idx'])
    return bars_primer, maps

def trim_primer_from_output(midi_output, midi_reference):
    # determine trim length
    ref_duration, primer_duration = determine_primer_duration(midi_reference)
    out_duration, _ = determine_primer_duration(midi_output)
    print("midi generated duration: ", out_duration, " seconds")

    print(ref_duration, primer_duration, out_duration)

    if out_duration - primer_duration < 9:
        print('keeping primer inside generated file')
        out_file = midi_output
    else:
        mid = pretty_midi.PrettyMIDI(midi_output)
        print("cutting first " + str(primer_duration) + " seconds from midi")
        mid_cut = data_proc.trim_midi(mid, primer_duration, 10000, True)

        out_file = midi_output[:-4] + "_cut.mid"
        mid_cut.write(out_file)
    return out_file
