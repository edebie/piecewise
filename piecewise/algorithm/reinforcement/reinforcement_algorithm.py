import abc
from collections import namedtuple

from piecewise.dtype import ClassifierSet

from ..algorithm import Algorithm

ReinforcementComponents = namedtuple("ReinforcementComponents",
                                     ["action_selection", "credit_assignment"])


class ReinforcementAlgorithm(Algorithm, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, common_components, reinforcement_components, rule_repr,
                 hyperparams):
        super().__init__(common_components, rule_repr, hyperparams)
        (self._action_selection_strat,
         self._credit_assignment_strat) = reinforcement_components

    @abc.abstractmethod
    def train_query(self, situation, time_step):
        raise NotImplementedError

    @abc.abstractmethod
    def train_update(self, env_response):
        raise NotImplementedError

    @abc.abstractmethod
    def test_query(self, situation):
        raise NotImplementedError

    def _gen_action_set(self, match_set, action):
        """GENERATE ACTION SET function from 'An Algorithmic
        Description of XCS' (Butz and Wilson, 2002)."""
        action_set = ClassifierSet()
        for classifier in match_set:
            if classifier.action == action:
                action_set.add(classifier)
        return action_set

    def _select_action(self, prediction_array):
        """Returns an action to perform during training."""
        return self._action_selection_strat(prediction_array)

    def _do_credit_assignment(self, action_set, reward, use_discounting,
                              prediction_array):
        """Assigns credit to the classifiers in the action set using info from
        other params."""
        self._credit_assignment_strat(action_set, reward, use_discounting,
                                      prediction_array)
