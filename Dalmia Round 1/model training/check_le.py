import pickle
import os

with open('label_encoder_event.pkl', 'rb') as f:
    le = pickle.load(f)
    print(list(le.classes_))
