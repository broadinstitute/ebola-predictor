"""
Calculates Brier score over aggregated predictions for models with F1-score above 0.9.

http://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html

Backported from 0.16.1 to work with earlier versions of scitkit-learn

@copyright: The Broad Institute of MIT and Harvard 2015

Authors of scikit-learn code:
Alexandre Gramfort <alexandre.gramfort@inria.fr>
Mathieu Blondel <mathieu@mblondel.org>
Olivier Grisel <olivier.grisel@ensta.org>
Andreas Mueller <amueller@ais.uni-bonn.de>
Joel Nothman <joel.nothman@gmail.com>
Hamzeh Alsalhi <ha258@cornell.edu>
License: BSD 3 clause
"""

import os, argparse
import pandas as pd
import numpy as np
from sklearn.utils import column_or_1d
from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_auc_score
from sklearn.metrics import precision_score, recall_score, f1_score

def _num_samples(x):
    """Return number of samples in array-like x."""
    if hasattr(x, 'fit'):
        # Don't get num_samples from an ensembles length!
        raise TypeError('Expected sequence or array-like, got '
                        'estimator %s' % x)
    if not hasattr(x, '__len__') and not hasattr(x, 'shape'):
        if hasattr(x, '__array__'):
            x = np.asarray(x)
        else:
            raise TypeError("Expected sequence or array-like, got %s" %
                            type(x))
    if hasattr(x, 'shape'):
        if len(x.shape) == 0:
            raise TypeError("Singleton array %r cannot be considered"
                            " a valid collection." % x)
        return x.shape[0]
    else:
        return len(x)

def check_consistent_length(*arrays):
    """Check that all arrays have consistent first dimensions.
    Checks whether all objects in arrays have the same shape or length.
    Parameters
    ----------
    *arrays : list or tuple of input objects.
        Objects that will be checked for consistent length.
    """

    uniques = np.unique([_num_samples(X) for X in arrays if X is not None])
    if len(uniques) > 1:
        raise ValueError("Found arrays with inconsistent numbers of samples: "
                         "%s" % str(uniques))

def _check_binary_probabilistic_predictions(y_true, y_prob):
    """Check that y_true is binary and y_prob contains valid probabilities"""
    check_consistent_length(y_true, y_prob)

    labels = np.unique(y_true)

    if len(labels) != 2:
        raise ValueError("Only binary classification is supported. "
                         "Provided labels %s." % labels)

    if y_prob.max() > 1:
        raise ValueError("y_prob contains values greater than 1.")

    if y_prob.min() < 0:
        raise ValueError("y_prob contains values less than 0.")

    return label_binarize(y_true, labels)[:, 0]

def brier_score_loss(y_true, y_prob, sample_weight=None, pos_label=None):
    """Compute the Brier score.
    The smaller the Brier score, the better, hence the naming with "loss".
    Across all items in a set N predictions, the Brier score measures the
    mean squared difference between (1) the predicted probability assigned
    to the possible outcomes for item i, and (2) the actual outcome.
    Therefore, the lower the Brier score is for a set of predictions, the
    better the predictions are calibrated. Note that the Brier score always
    takes on a value between zero and one, since this is the largest
    possible difference between a predicted probability (which must be
    between zero and one) and the actual outcome (which can take on values
    of only 0 and 1).
    The Brier score is appropriate for binary and categorical outcomes that
    can be structured as true or false, but is inappropriate for ordinal
    variables which can take on three or more values (this is because the
    Brier score assumes that all possible outcomes are equivalently
    "distant" from one another). Which label is considered to be the positive
    label is controlled via the parameter pos_label, which defaults to 1.
    Read more in the :ref:`User Guide <calibration>`.
    Parameters
    ----------
    y_true : array, shape (n_samples,)
        True targets.
    y_prob : array, shape (n_samples,)
        Probabilities of the positive class.
    sample_weight : array-like of shape = [n_samples], optional
        Sample weights.
    pos_label : int (default: None)
        Label of the positive class. If None, the maximum label is used as
        positive class
    Returns
    -------
    score : float
        Brier score
    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.metrics import brier_score_loss
    >>> y_true = np.array([0, 1, 1, 0])
    >>> y_true_categorical = np.array(["spam", "ham", "ham", "spam"])
    >>> y_prob = np.array([0.1, 0.9, 0.8, 0.3])
    >>> brier_score_loss(y_true, y_prob)  # doctest: +ELLIPSIS
    0.037...
    >>> brier_score_loss(y_true, 1-y_prob, pos_label=0)  # doctest: +ELLIPSIS
    0.037...
    >>> brier_score_loss(y_true_categorical, y_prob, \
                         pos_label="ham")  # doctest: +ELLIPSIS
    0.037...
    >>> brier_score_loss(y_true, np.array(y_prob) > 0.5)
    0.0
    References
    ----------
    http://en.wikipedia.org/wiki/Brier_score
    """
    y_true = column_or_1d(y_true)
    y_prob = column_or_1d(y_prob)
    if pos_label is None:
        pos_label = y_true.max()
    y_true = np.array(y_true == pos_label, int)
    y_true = _check_binary_probabilistic_predictions(y_true, y_prob)
    return np.average((y_true - y_prob) ** 2, weights=sample_weight)

# http://stackoverflow.com/questions/19124239/scikit-learn-roc-curve-with-confidence-intervals
def score_bootstrap(score_fun, y_true, y_pred, pvalue, iter):
    n_bootstraps = iter
    bootstrapped_scores = []
#     rng_seed = 42  # control reproducibility
#     rng = np.random.RandomState(rng_seed)
    rng = np.random.RandomState()
    for i in range(n_bootstraps):
        # bootstrap by sampling with replacement on the prediction indices
        indices = rng.random_integers(0, len(y_pred) - 1, len(y_pred))
        if len(np.unique(y_true[indices])) < 2:
            # We need at least one positive and one negative sample for ROC AUC
            # to be defined: reject the sample
            continue

        score = score_fun(y_true[indices], y_pred[indices])
        bootstrapped_scores.append(score)
    
    sorted_scores = np.array(bootstrapped_scores)
    sorted_scores.sort()

    confidence_lower = sorted_scores[int(pvalue * len(sorted_scores))]
    confidence_upper = sorted_scores[int((1 - pvalue) * len(sorted_scores))]
    return [confidence_lower, confidence_upper]

def precision_bootstrap(y_true, y_pred, pvalue, iter):
    return score_bootstrap(precision_score, y_true, y_pred, pvalue, iter)

def recall_bootstrap(y_true, y_pred, pvalue, iter):
    return score_bootstrap(recall_score, y_true, y_pred, pvalue, iter)

def f1_bootstrap(y_true, y_pred, pvalue, iter):
    return score_bootstrap(f1_score, y_true, y_pred, pvalue, iter)

def brier_bootstrap(y_true, y_pred, pvalue, iter):
    return score_bootstrap(brier_score_loss, y_true, y_pred, pvalue, iter)

def roc_bootstrap(y_true, y_pred, pvalue, iter):
    return score_bootstrap(roc_auc_score, y_true, y_pred, pvalue, iter)

##########################################################################################

parser = argparse.ArgumentParser()
parser.add_argument("-mode", "--index_mode", nargs=1, default=["PRED"],
                    help="Indexing mode, either PRED or IMP")
parser.add_argument("-B", "--base_dir", nargs=1, default=["./"],
                    help="Base folder")
parser.add_argument("-rank", "--ranking_file", nargs=1, default=["./out/ranking.txt"],
                    help="Ranking file")
parser.add_argument("-out", "--output_file", nargs=1, default=["./out/scores.tsv"],
                    help="Output file")
parser.add_argument("-s", "--scores", nargs=1, default=["precision,recall,f1,brier,auc"],
                    help="Scores to compute")
parser.add_argument("-f1", "--f1_min", type=float, nargs=1, default=[0.9],
                    help="Minimum F1-score of predictors to include")
parser.add_argument("-extra", "--extra_tests", nargs=1, default=[""],
                    help="Extra tests to include a prediction in the plot, comma separated")
parser.add_argument("-x", "--exclude", nargs=1, default=["lreg,scikit_randf"],
                    help="Predictors to exclude from analysis")
parser.add_argument("-c", "--confidence", type=float, nargs=1, default=[95],
                    help="Confidence to use in the bootstrap intervals")
parser.add_argument("-i", "--iterations", type=int, nargs=1, default=[1000],
                    help="Number of bootstrap iterations")
parser.add_argument("-b", "--bootstrap", action="store_true",
                    help="Use bootstrap to generate confidence intervals")

args = parser.parse_args()
index_mode = args.index_mode[0]
base_dir = args.base_dir[0]
rank_file = args.ranking_file[0]
output_file = args.output_file[0]
scores = args.scores[0].split(",")
f1_min = args.f1_min[0]
extra_tests = args.extra_tests[0].split(",")
excluded_predictors = args.exclude[0].split(",")
bootstrap = args.bootstrap
pvalue = 1.0 - args.confidence[0] / 100.0
iter = args.iterations[0]

var_labels = {}
with open("./data/alias.txt", "r") as afile:
    lines = afile.readlines()
    for line in lines:
        line = line.strip()
        parts = line.split(" ", 1)
        var_labels[parts[0]] = parts[1]

if index_mode == "PRED":
    options_file = "./data/predictors.txt"
else:
    options_file = "./data/imputation.txt"

index_names = []
index_labels = {}
index_acron = {}
with open(options_file, "r") as ofile:
    lines = ofile.readlines()
    for line in lines:
        line = line.strip()
        parts = line.split(',')
        index_names.append(parts[0])
        index_labels[parts[0]] = parts[1]
        index_acron[parts[0]] = parts[2]

print "Calculating scores..."
score_lines = []
with open(rank_file, "r") as rfile:
    lines = rfile.readlines()
    for line in lines:
        line = line.strip()
        parts = line.split(" ")

        mdl_str = parts[1]
        pred = parts[2]
        if pred in excluded_predictors:
            continue
        if index_mode == "PRED":
            idx = pred
        else:
            idx = ""
            for idx in index_names:
                if idx in mdl_str:
                    break
        if not idx in index_names:
            continue
        if extra_tests:
            missing = False
            path_pieces =  parts[1].split(os.path.sep)
            for ex in extra_tests:
                if not ex in path_pieces:
                    missing = True
            if missing: 
                 continue

        vars = parts[3]
        f1_mean = float(parts[4])
        f1_std = float(parts[5])
        vlist = vars.split(",")

        if f1_min <= f1_mean:
            id = os.path.split(mdl_str)[1]
            os.system("python utils/aggregate.py -B " + base_dir + " -N " + id + " -p " + pred)
            df = pd.read_csv("./out/predictions.csv", delimiter=",")
            y = df["Y"]
            p = df["P"]
            if len(y) == 0: continue
            pb = np.array([int(0.5 < x) for x in p])
            
            score_line = index_acron[idx] + '\t' + ', '.join([var_labels[v] for v in vlist])
            for score in scores:
                if score == "precision":
                    precision = precision_score(y, pb)
                    if bootstrap:
                        lo, hi = precision_bootstrap(y, pb, pvalue, iter)
                        scores_str = ("%.3f" % lo) + "," + ("%.3f" % precision) + "," + ("%.3f" % hi)
                    else:
                        scores_str = ("%.3f" % precision)
                    score_line = score_line + '\t' + scores_str
                elif score == "recall":
                    recall = recall_score(y, pb)
                    if bootstrap:
                        lo, hi = recall_bootstrap(y, pb, pvalue, iter)
                        scores_str = ("%.3f" % lo) + "," + ("%.3f" % recall) + "," + ("%.3f" % hi)
                    else:
                        scores_str = ("%.3f" % recall)
                    score_line = score_line + '\t' + scores_str
                elif score == "f1":
                    f1 = f1_score(y, pb)
                    if bootstrap:
                        lo, hi = f1_bootstrap(y, pb, pvalue, iter)
                        scores_str = ("%.3f" % lo) + "," + ("%.3f" % f1) + "," + ("%.3f" % hi)
                    else:
                        scores_str = ("%.3f" % f1)
                    score_line = score_line + '\t' + scores_str
                elif score == "brier":
                    brier = brier_score_loss(y, p)
                    if bootstrap:
                        lo, hi = brier_bootstrap(y, p, pvalue, iter)
                        scores_str = ("%.3f" % lo) + "," + ("%.3f" % brier) + "," + ("%.3f" % hi)
                    else:
                        scores_str = ("%.3f" % brier)
                    score_line = score_line + '\t' + scores_str
                elif score == "auc":
                    auc = roc_auc_score(y, p)
                    if bootstrap:
                        lo, hi = roc_bootstrap(y, p, pvalue, iter)
                        scores_str = ("%.3f" % lo) + "," + ("%.3f" % auc) + "," + ("%.3f" % hi)
                    else:
                        scores_str = ("%.3f" % auc)
                    score_line = score_line + '\t' + scores_str
            print score_line
            score_lines.append(score_line)

print "Done."

print ""
print "Saving list of scores to " + output_file + "..."
with open(output_file, "w") as ofile:
    ofile.write("Predictor\tVariables")
    for score in scores:
        ofile.write("\t" + score)
    ofile.write("\n")
    for line in score_lines:
        ofile.write(line + "\n")
print "Done."

