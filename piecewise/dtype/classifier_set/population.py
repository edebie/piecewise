import functools

from piecewise.error.population_error import InvalidSizeError

from .classifier_set_base import ClassifierSetBase, verify_membership
from .population_operation_recorder import PopulationOperationRecorder


def record_operation(atomic_method):
    """Decorator to record operations types (in units of number of
    microclassifiers) when performing atomic operations on the population.
    """
    @functools.wraps(atomic_method)
    def _record_operation(self, *args, operation_label=None):
        micros_before = self.num_micros
        result = atomic_method(self, *args, operation_label=operation_label)
        micros_after = self.num_micros
        micros_delta = micros_after - micros_before
        num_micros_altered = abs(micros_delta)

        if operation_label is not None:
            self._operation_recorder[operation_label] += num_micros_altered
        return result

    return _record_operation


class Population(ClassifierSetBase):
    """Container used to hold classifiers that make up the predictive model of
    the LCS: the population.

    Public methods use the operation_label kwarg to give a label for the type
    of operation performed: these labels are forwarded to the private atomic
    methods of the class which use them to record the number of different types
    of operations performed (see record_operation decorator).

    Notably this class continually updates and caches the num_micros property
    when operations are performed on it. This is possible (and maintains an
    accurate state) because all mutations of classifier numerosities is done
    by calling public methods on the population, which internally take care
    of numerosity incermenting/decrementing.
    """
    def __init__(self, max_micros):
        self._max_micros = self._validate_and_return_max_micros(max_micros)
        self._num_micros = 0
        self._operation_recorder = \
            PopulationOperationRecorder()
        super().__init__()

    def _validate_and_return_max_micros(self, max_micros):
        max_micros = int(max_micros)
        if not max_micros > 0:
            raise InvalidSizeError("Invalid max micros for population size: "
                                   f"{max_micros}, must be positive integer")
        return max_micros

    @property
    def num_micros(self):
        return self._num_micros

    @property
    def max_micros(self):
        return self._max_micros

    @property
    def operations_record(self):
        return self._operation_recorder

    def _inc_num_micros(self, added_numerosity):
        self._num_micros += added_numerosity

    def _dec_num_micros(self, removed_numerosity):
        self._num_micros -= removed_numerosity
        assert self._num_micros >= 0

    def add(self, classifier, *, operation_label=None):
        """Adds the given classifier to the population.

        Adding implies the classifier is newly discovered and cannot be
        'absorbed' into the population via an existing classifier - see
        insert() for that functionality.
        """
        self._atomic_add_new(classifier, operation_label=operation_label)

    def insert(self, classifier, *, operation_label=None):
        """Inserts the given classifier into the population.

        Insertion implies that the classifier may be a duplicate of an existing
        classifier, and so part of the insertion process is checking for
        classifiers with duplicate rules. In the case of a duplicate, the
        numerosity of the existing rule is incremented appropriately.

        INSERT IN POPULATION function from 'An Algorithmic Description of
        XCS' (Butz and Wilson, 2002)."""
        was_absorbed = self._try_to_absorb(classifier)
        if not was_absorbed:
            self._atomic_add_new(classifier, operation_label=operation_label)

    def _try_to_absorb(self, classifier):
        for member in self._members:
            if member.rule == classifier.rule:
                self._absorb(absorbee=classifier, absorber=member)
                return True
        return False

    def _absorb(self, absorbee, absorber):
        num_absorber_copies = absorbee.numerosity
        self._atomic_copy_existing(absorber,
                                   num_absorber_copies,
                                   operation_label="absorption")

    @verify_membership
    def duplicate(self, classifier, num_copies=1, *, operation_label=None):
        """Duplicate the given classifier num_copies times in the population.

        Throws:
            MemberNotFoundError: if the classifier is not in the population.
        """
        assert num_copies >= 1
        self._atomic_copy_existing(classifier,
                                   num_copies,
                                   operation_label=operation_label)

    @verify_membership
    def replace(self, replacee, replacer, *, operation_label=None):
        """Replace the first classifier (replacee) with the second classifier
        (replacer) in the population.

        This involves completely removing all copies of the replacee and
        incrementing the numerosity of the replacer by the same number of
        copies - therefore there is no overall diff in population size as a
        result of this operation.

        Both replacee and replacer *must* already exist in the population.

        Throws:
            MemberNotFoundError: if either replacee or replacer are not in the
                population.
        """
        num_replacer_copies = replacee.numerosity
        self._atomic_remove_whole(replacee)
        self._atomic_copy_existing(replacer,
                                   num_replacer_copies,
                                   operation_label=operation_label)

    @verify_membership
    def delete(self, classifier):
        """Deletes (removes a single copy) of the given classifier in the
        population.

        Throws:
            MemberNotFoundError: if the classifier is not in the population.
        """
        self._atomic_remove_single_copy(classifier, operation_label="deletion")

    @verify_membership
    def remove(self, classifier, *, operation_label=None):
        """Removes the given classifier from the population, i.e. removes all
        copies / the whole macroclassifier.

        Throws:
            MemberNotFoundError: if the classifier is not in the population.
        """
        self._atomic_remove_whole(classifier, operation_label=operation_label)

    # Atomic operations - wrapped with operation recording

    @record_operation
    def _atomic_add_new(self, new_classifier, *, operation_label=None):
        self._members.append(new_classifier)
        self._inc_num_micros(new_classifier.numerosity)

    @record_operation
    def _atomic_copy_existing(self,
                              existing_classifier,
                              num_copies,
                              *,
                              operation_label=None):
        assert num_copies >= 1
        existing_classifier.numerosity += num_copies
        self._inc_num_micros(num_copies)

    @record_operation
    def _atomic_remove_whole(self, classifier, *, operation_label=None):
        self._members.remove(classifier)
        self._dec_num_micros(classifier.numerosity)

    @record_operation
    def _atomic_remove_single_copy(self,
                                   existing_classifier,
                                   *,
                                   operation_label=None):
        """Lines 11-14 in body of second loop of
        DELETE FROM POPULATION function from 'An Algorithmic Description of
        XCS' (Butz and Wilson, 2002)."""
        if existing_classifier.numerosity > 1:
            existing_classifier.numerosity -= 1
        else:
            # can't have 0 numerosity, so remove completely
            self._members.remove(existing_classifier)
        self._dec_num_micros(1)
