import argparse, glob, os, sys
from matplotlib import pyplot as plt
from importlib import import_module

label_file = "./data/labels.txt"
target_names = []
with open(label_file, "rb") as vfile:
    for line in vfile.readlines():
        target_names.append(line.split()[1])

def avg_cal_dis(module):
    test_files = glob.glob("./data/testing-data-*.csv")
    print "Calculating Calibration/Discrimination for " + module.title() + "..."
    count = 0
    total_cal = 0
    total_dis = 0
    for testfile in test_files:
        start_idx = testfile.find("./data/testing-data-") + len("./data/testing-data-")
        stop_idx = testfile.find('.csv')
        id = testfile[start_idx:stop_idx]
        pfile = "./data/" + module.prefix() + "-params-" + str(id)
        trainfile = "./data/training-data-completed-" + str(id) + ".csv"
        if os.path.exists(testfile) and os.path.exists(pfile) and os.path.exists(trainfile):
            count = count + 1
            print "Calibration/Discrimination for test set " + id + " ----------------------------------"
            cal, dis = module.eval(testfile, trainfile, pfile, 1)
            total_cal += cal
            total_dis += dis
    avg_cal = (total_cal)/(count)
    avg_dis = (total_dis)/(count)

    print module.title() + " Average Calibration/Discrimination ********************************************"
    print "Calibration   : " + str(avg_cal)
    print "Discrimination: " + str(avg_dis)

def cal_plots(module):
    test_files = glob.glob("./data/testing-data-*.csv")
    print "Calculating calibration plots for " + module.title() + "..."
    for testfile in test_files:
        start_idx = testfile.find("./data/testing-data-") + len("./data/testing-data-")
        stop_idx = testfile.find('.csv')
        id = testfile[start_idx:stop_idx]
        pfile = "./data/" + module.prefix() + "-params-" + str(id)
        trainfile = "./data/training-data-completed-" + str(id) + ".csv"
        if os.path.exists(testfile) and os.path.exists(pfile) and os.path.exists(trainfile):
            print "Calibration for test set " + id + " ----------------------------------"
            out_file = "./out/calstats-" + id + ".txt"
            plot_file = "./out/calplot-" + id + ".pdf"
            module.eval(testfile, trainfile, pfile, 2, test_file=testfile, out_file=out_file, plot_file=plot_file)
    print "********************************************"
    print "Saved calibration plot and Hosmer-Lemeshow goodness of fit for " + module.title() + " in out folder."

def avg_report(module):
    test_files = glob.glob("./data/testing-data-*.csv")
    print "Calculating average report for " + module.title() + "..."
    count = 0
    total_prec = 0
    total_rec = 0
    total_f1 = 0
    for testfile in test_files:
        start_idx = testfile.find("./data/testing-data-") + len("./data/testing-data-")
        stop_idx = testfile.find('.csv')
        id = testfile[start_idx:stop_idx]
        pfile = "./data/" + module.prefix() + "-params-" + str(id)
        trainfile = "./data/training-data-completed-" + str(id) + ".csv"
        if os.path.exists(testfile) and os.path.exists(pfile) and os.path.exists(trainfile):
            count = count + 1
            print "Report for test set " + id + " ----------------------------------"
            p, r, f, _ = module.eval(testfile, trainfile, pfile, 3)
            total_prec += p
            total_rec += r
            total_f1 += f

    avg_prec = (total_prec)/(count)
    avg_rec = (total_rec)/(count)
    avg_f1 = (total_f1)/(count)

    print "Average report for " + module.title() + " ********************************************"
    print "{:10s} {:10s} {:10s} {:10s}".format("", "precision", "recall", "f1-score")
    print "{:10s}      {:2.2f}    {:2.2f}        {:2.2f}".format(target_names[0], avg_prec[0], avg_rec[0], avg_f1[0])
    print "{:10s}      {:2.2f}    {:2.2f}        {:2.2f}".format(target_names[1], avg_prec[1], avg_rec[1], avg_f1[1])
    print "{:10s}      {:2.2f}    {:2.2f}        {:2.2f}".format("Total", (avg_prec[0] + avg_prec[1])/2, (avg_rec[0]+avg_rec[1])/2, (avg_f1[0]+avg_f1[1])/2)

def roc_plots(module):
    test_files = glob.glob("./data/testing-data-*.csv")
    print "Calculating ROC curves for " + module.title() + "..."
    count = 0
    total_roc_auc = 0
    plt.clf()
    fig = plt.figure()
    for testfile in test_files:
        start_idx = testfile.find("./data/testing-data-") + len("./data/testing-data-")
        stop_idx = testfile.find('.csv')
        id = testfile[start_idx:stop_idx]
        pfile = "./data/" + module.prefix() + "-params-" + str(id)
        trainfile = "./data/training-data-completed-" + str(id) + ".csv"
        if os.path.exists(testfile) and os.path.exists(pfile) and os.path.exists(trainfile):
            print "Report for test set " + id + " ----------------------------------"
            count = count + 1
            total_roc_auc += module.eval(testfile, trainfile, pfile, 4, pltshow=False)
    ave_roc_auc = (total_roc_auc)/(count)
    print "********************************************"
    print "Average area under the ROC curve for " + module.title() + ": " + str(ave_roc_auc)
    fig.savefig('./out/roc.pdf')
    print "Saved ROC curve to ./out/roc.pdf"
    
def avg_conf_mat(module):
    test_files = glob.glob("./data/testing-data-*.csv")
    print "Calculating average report for " + module.title() + "..."
    count = 0
    total_n_hit = 0
    total_n_false_alarm = 0
    total_n_miss = 0
    total_n_correct_rej = 0
    for testfile in test_files:
        start_idx = testfile.find("./data/testing-data-") + len("./data/testing-data-")
        stop_idx = testfile.find('.csv')
        id = testfile[start_idx:stop_idx]
        pfile = "./data/" + module.prefix() + "-params-" + str(id)
        trainfile = "./data/training-data-completed-" + str(id) + ".csv"
        if os.path.exists(testfile) and os.path.exists(pfile) and os.path.exists(trainfile):
            count = count + 1
            print "Confusion matrix for test set " + id + " ------------------------------"
            n_hit, n_false_alarm, n_miss, n_correct_rej = module.eval(testfile, trainfile, pfile, 5)
            total_n_hit += n_hit
            total_n_false_alarm += n_false_alarm
            total_n_miss += n_miss
            total_n_correct_rej += n_correct_rej

    avg_n_hit = total_n_hit/(1.0*count)
    avg_n_false_alarm = total_n_false_alarm/(1.0*count)
    avg_n_miss = total_n_miss/(1.0*count)
    avg_n_correct_rej = total_n_correct_rej/(1.0*count)
     
    print "Average confusion matrix for " + module.title() + " ********************************************"
    print "{:25s} {:20s} {:20s}".format("", "Output " + target_names[1], "Output " + target_names[0])
    print "{:25s} {:2.2f}{:17s}{:2.2f}".format("Predicted " + target_names[1], avg_n_hit,"", avg_n_false_alarm)
    print "{:25s} {:2.2f}{:17s}{:2.2f}".format("Predicted " + target_names[0], avg_n_miss,"", avg_n_correct_rej) 

def list_misses(module):
    test_files = glob.glob("./data/testing-data-*.csv")
    print "Miss-classifications for predictor " + module.title() + "..."
    count = 0
    for testfile in test_files:
        start_idx = testfile.find("./data/testing-data-") + len("./data/testing-data-")
        stop_idx = testfile.find('.csv')
        id = testfile[start_idx:stop_idx]
        pfile = "./data/" + module.prefix() + "-params-" + str(id)
        trainfile = "./data/training-data-completed-" + str(id) + ".csv"
        if os.path.exists(testfile) and os.path.exists(pfile) and os.path.exists(trainfile):
            idx = module.miss(testfile, trainfile, pfile)
            count += len(idx)
    print "********************************************"
    print "Total miss-classifications for " + module.title() + ":",count

def evaluate(predictor, method):
    module_path = os.path.abspath(predictor)
    module_filename = "eval"
    sys.path.insert(0, module_path)
    module = import_module(module_filename)

    if not os.path.exists("./out"): os.makedirs("./out")

    # Average calibrations and discriminations
    if method == "caldis":
        avg_cal_dis(module)
    # Plot each method on same calibration plot
    elif method == "calplot":
        cal_plots(module)
    # Average precision, recall, and F1 scores
    elif method == "report":
        avg_report(module)
    # Plot each method on same ROC plot
    elif method == "roc":
        roc_plots(module)
    # Average confusion matrix
    elif method == "confusion":
       avg_conf_mat(module)
    elif method == "misses":
        list_misses(module)
    # Method not defined:
    else:
        raise Exception("Invalid method given")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Evaluate the model with given method(s)
    parser.add_argument('-p', nargs=1, default=["nnet"], 
                        help="Folder containing predictor to evaluate")
    parser.add_argument('-m', nargs=1, default=["report"], 
                        help="Supported evaluation methods: caldis, calplot, report, roc, confusion, misses")
    args = parser.parse_args()
    evaluate(args.p[0], args.m[0])