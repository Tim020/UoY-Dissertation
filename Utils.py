from scipy.stats import *


class MixtureModel(rv_continuous):
    def __init__(self, submodels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.submodels = submodels

    def rvs(self, size):
        submodel_choices = self._random_state.randint(len(self.submodels), size=size)
        submodel_samples = [submodel.rvs(size=size) for submodel in self.submodels]
        rvs = self._random_state.choose(submodel_choices, submodel_samples)
        return rvs
