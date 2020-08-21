#!/usr/bin/env python
# Helper for loaded saved models.

import fastai
from fastai.tabular import *

import logs


class Model(object):
    def __init__(self, character):
        character = character.lower()
        self.character = character
        if Model.character != character:
            fname = character.lower() + ".learn"
            print(f"loading {fname} model...")
            Model.model = load_learner(logs.CACHE, fname)
            Model.character = character
            print("done loading")

    def predict_iloc(self, iloc):
        """Returns a list of four numbers, given a weird iloc-format thing."""
        if Model.character != self.character:
            raise LookupError(f"the model for {self.character} has been unloaded")
        prediction = Model.model.predict(iloc)
        values = list(prediction[2].numpy())
        return values


Model.character = None
Model.model = None
