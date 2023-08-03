# symbolic music generation contitioned on v-a timeseries and MIDI primer for experimental setup
Code written for my master's thesis: Procedural music generation forvideogames conditioned through video emotion recognition

This folder contains the code written for generating a continuous soundtrack conditioned on a valence and arousal timeseries and any input midi file, namely 'primer'.
In particolar the inference procedure is developed for obtaining a sequence of midi files to be synthesised with a DAW for the experimental evaluation of the proposed method.

The code is based on the pre-trained Music transformer proposed by Sulun et al. : https://github.com/serkansulun/midi-emotion

In order to run main.py you first need to download the code from that repository, in particular you need to add `src/data`, `src/models`, `src/create_datasets` to the project folder.

Then, you must adapt the paths to your own environment and provide a `primer.mid` and a `filename.csv` containing valence and arousal timeseries 

Once everything is set up, run `main.py` to generate the conditioned soundtrack, which is saved by default at `current_midi\filename\conditioned\*`.

