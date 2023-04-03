import pretty_midi
import src.data.data_processing as data_proc

def import_primers():
        # let's try importing a midi file and converting it to muysic tkens
        midi_reference = 'C:\\Users\\franc\\Documents\\GitHub\\POP909-Dataset\\POP909\\001\\001.mid'
        mid = pretty_midi.PrettyMIDI(midi_reference)

        mid_cut = data_proc.trim_midi(mid, 0, 13, 23)

        maps = data_proc.get_maps()

        # just for debugging
        mid_cut.instruments[1].name = 'STRINGS'
        mid_cut.instruments[0].name = 'GUITAR'
        # note_events = data_proc.mid_to_timed_tuples(mid, maps['event2idx'])

        bars_primer = data_proc.mid_to_bars(mid_cut, maps['event2idx'])
        return bars_primer, maps