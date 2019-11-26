from piecewise.algorithm import make_xcs
from piecewise.codec import NullCodec
from piecewise.environment import DiscreteMultiplexer
from piecewise.experiment import Experiment
from piecewise.lcs import SupervisedLCS
from piecewise.monitor import (ClassifierSetStat, Monitor,
                               PopulationOperationsSubMonitor,
                               PopulationSizeSubMonitor,
                               PopulationStatisticsSubMonitor,
                               TrainingPerformanceSubMonitor)
from piecewise.rule_repr import TernaryRuleRepr


def main():
    # 6-multiplexer
    env = DiscreteMultiplexer(num_address_bits=2, shuffle_dataset=True)
    codec = NullCodec()
    rule_repr = TernaryRuleRepr()
    num_actions = len(env.action_set)
    xcs_hyperparams = {
        "N": 400,
        "beta": 0.2,
        "alpha": 0.1,
        "epsilon_nought": 0.01,
        "nu": 5,
        "gamma": 0.71,
        "theta_ga": 25,
        "chi": 0.8,
        "mu": 0.4,
        "theta_del": 20,
        "delta": 0.1,
        "theta_sub": 20,
        "p_wildcard": 0.33,
        "prediction_I": 1e-3,
        "epsilon_I": 1e-3,
        "fitness_I": 1e-3,
        "p_explore": 0.5,
        "theta_mna": num_actions,
        "do_ga_subsumption": True,
        "do_as_subsumption": True
    }
    algorithm = make_xcs(env.step_type, env.action_set, rule_repr,
                         xcs_hyperparams)
    monitor = Monitor(
        TrainingPerformanceSubMonitor(), PopulationOperationsSubMonitor(),
        PopulationSizeSubMonitor(),
        PopulationStatisticsSubMonitor([
            ClassifierSetStat("mean", "error"),
            ClassifierSetStat("max", "fitness")
        ]))
    lcs = SupervisedLCS(env, codec, algorithm)

    experiment = Experiment(lcs, monitor, num_epochs=10)
    population, monitor = experiment.run()
    monitor.report()


if __name__ == "__main__":
    main()