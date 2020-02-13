import abc
from piecewise.algorithm.rng import get_rng

from piecewise.util.classifier_set_stats import calc_summary_stat
from piecewise.algorithm.hyperparams import get_hyperparam


class DeletionStrategyABC(metaclass=abc.ABCMeta):
    def __call__(self, population):
        """DELETE FROM POPULATION function from 'An Algorithmic Description of
        XCS' (Butz and Wilson, 2002)."""
        deletion_is_required = population.num_micros > population.max_micros
        if deletion_is_required:
            self._perform_deletions(population)
        assert population.num_micros <= population.max_micros

    def _perform_deletions(self, population):
        num_deletions = population.num_micros - population.max_micros
        assert num_deletions >= 1
        for _ in range(num_deletions):
            classifier_to_delete = self._select_for_deletion(population)
            population.delete(classifier_to_delete)

    @abc.abstractmethod
    def _select_for_deletion(self, population):
        """Selects a single classifier to delete from the population.

        This method should only ever be called if the population
        is past its microclassifier capacity."""
        return NotImplementedError


class XCSRouletteWheelDeletion(DeletionStrategyABC):
    def _select_for_deletion(self, population):
        """First loop (selecting classifier to delete) of
        DELETE FROM POPULATION function from 'An Algorithmic Description of
        XCS' (Butz and Wilson, 2002)."""
        mean_fitness_in_pop = calc_summary_stat(population, "mean", "fitness")
        votes = [
            self._calc_deletion_vote(classifier, mean_fitness_in_pop)
            for classifier in population
        ]
        vote_sum = sum(votes)
        choice_point = get_rng().rand() * vote_sum

        vote_sum = 0
        for (classifier, vote) in zip(population, votes):
            vote_sum += vote
            if vote_sum > choice_point:
                return classifier

    def _calc_deletion_vote(self, classifier, mean_fitness_in_pop):
        """DELETION VOTE function from 'An Algorithmic Description of
        XCS' (Butz and Wilson, 2002)."""
        vote = classifier.action_set_size * classifier.numerosity
        fitness_numerosity_ratio = classifier.fitness / classifier.numerosity

        has_sufficient_experience = classifier.experience > \
            get_hyperparam("theta_del")
        has_low_fitness = fitness_numerosity_ratio < \
            (get_hyperparam("delta") * mean_fitness_in_pop)
        if has_sufficient_experience and has_low_fitness:
            vote *= mean_fitness_in_pop / fitness_numerosity_ratio

        return vote