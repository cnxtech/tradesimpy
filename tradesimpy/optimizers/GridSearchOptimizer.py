from Optimizer import Optimizer
import Backtester as b
from OptimizationResults import OptimizationResults
import itertools
import numpy as np
import multiprocessing as mp


def _backtest(backtest_args):
    # Extract backtest arguments
    backtest_id, parameters, trading_algorithm, commission, ticker_spreads, data, start_date, end_date = backtest_args

    # Setup the trading algorithm and backtester
    trading_algorithm.set_parameters(parameters)
    backtester = b.Backtester(backtest_id, trading_algorithm, 10000, commission, ticker_spreads)

    return backtester.run(data, start_date, end_date)

class GridSearchOptimizer(Optimizer):

    def __init__(self, num_processors, trading_algorithm, commission, ticker_spreads, optimization_metric,
        optimization_metric_ascending, optimization_parameters, frequency):
        super(GridSearchOptimizer, self).__init__(num_processors, trading_algorithm, optimization_metric,
            optimization_metric_ascending, optimization_parameters, frequency)

        # Data members
        self.commission = commission
        self.ticker_spreads = ticker_spreads
        self.optimization_parameter_sets = self.get_param_sets(self.optimization_parameters)
        self.num_paramameter_sets = len(self.optimization_parameter_sets)

    def run(self, data, start_date, end_date):
        # Prepare input data for running parallel backtests
        backtest_args = itertools.izip(
            range(len(self.optimization_parameter_sets)),
            self.optimization_parameter_sets,
            itertools.repeat(self.trading_algorithm),
            itertools.repeat(self.commission),
            itertools.repeat(self.ticker_spreads),
            itertools.repeat(data),
            itertools.repeat(start_date),
            itertools.repeat(end_date)
        )

        # Run all backtest scenarios in parallel
        pool = mp.Pool(processes=self.num_processors)
        backtest_results = pool.map(func=_backtest, iterable=backtest_args)

        # Find optimal parameters
        optimal_parameters = Optimizer.get_optimal_parameters(backtest_results, self.optimization_metric, \
            self.optimization_parameter_sets, self.optimization_metric_ascending, self.frequency)

        # Save results
        self.results = OptimizationResults(backtest_results, optimal_parameters, self.optimization_parameter_sets)

        return self.results

    # Generate parameter sets for each scenario
    @staticmethod
    def get_param_sets(parameter_spaces):
        discrete_param_spaces = []
        param_names = []
        param_sets = []

        # Discretize each parameter space
        for key, value in parameter_spaces.iteritems():
            # Skip unused parameters
            if len(value) == 0:
                continue

            discrete_param_spaces.append(list(np.linspace(value[0], value[1], value[2])))
            param_names.append(key)

        # Generate all unique parameter sets
        temp_param_sets = list(itertools.product(*discrete_param_spaces))

        # Build proper output structure
        for p in temp_param_sets:
            params = {}
            for i in range(0, len(p)):
                params[param_names[i]] = p[i]

            param_sets.append(params)

        return param_sets
