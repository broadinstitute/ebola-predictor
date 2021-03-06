"""
Executes a single job.

@copyright: The Broad Institute of MIT and Harvard 2015
"""

#!/usr/bin/env python

import sys, os, threading, argparse
import time, glob, time
import itertools

def get_last(name):
    mdl_folder = base_folder + "/models/" + name
    if not os.path.exists(mdl_folder): return -1
    train_files = glob.glob(mdl_folder + "/training-data-completed*.csv")
    idx = [int(fn[fn.rfind("-") + 1: fn.rfind(".")]) for fn in train_files]
    idx.sort()
    if idx: return idx[-1]
    else: return -1

def worker(name, count, first, imeth):
    print "Start"
    os.system("python init.py -B " + base_folder + " -N " + name + " -n " + str(count) + " -s " + str(first) + " -t " + str(test_prec) + " -m " + imeth + " " + impute_options[imeth])
    return

def create_var_file(mdl_id, mdl_vars):
    dir = base_folder + "/models/" + str(mdl_id)
    if not os.path.exists(dir):
        os.makedirs(dir)
    vfn = dir + "/variables.txt"
    with open(vfn, "w") as vfile:
        vfile.write(out_var + " " + var_dict[out_var] + "\n")
        for v in mdl_vars:
            vfile.write(v + " " + var_dict[v] + "\n")

def run_model(mdl_id, mdl_vars):
    print "running model", mdl_id, mdl_vars
    create_var_file(mdl_id, mdl_vars)
    
    n = get_last(mdl_id)
    if n + 1 == total_sets:
        print "Training/testing files already generated, skipping init stage..."
    else:
        imeth = impute_method
        start = n + 1
        count = total_sets - start
        nrest = 0
        while True:
            thread = threading.Thread(target=worker, args=(mdl_id, count, start, imeth))
            thread.start()
            while True:
                time.sleep(0.1)
                if not thread.isAlive(): break
            n = get_last(mdl_id)
            if n < total_sets - 1:
                # Remove core dump files, we know that (most likely) is just amelia crashing...
                core_files = glob.glob("./core.*")
                for file in core_files:
                    os.remove(file)
                if nrest < max_restarts:
                    start = n + 1
                    count = total_sets - start
                    nrest += 1
                else:
                    if impute_fallback and (not imeth == impute_fallback):
                        imeth = impute_fallback
                        count = total_sets
                        start = 0
                        nrest = 0
                        print "Primary imputation, will try fallback imputation method",imeth
                    else:
                        print "Model cannot be succesfully imputed, skipping!"
                        return
            else:
                print "Done! Number of restarts:", nrest
                break
            
    for pred_name in predictors:
        print "PREDICTOR",pred_name,"---------------"
        pred_opt = pred_options[pred_name]
        repfn = base_folder + "/models/" + mdl_id + "/report-" + pred_name + ".out"
        if os.path.exists(repfn):
            with open(repfn, "r") as report:
                lines = report.readlines()
                if lines:
                    print "Report for",pred_name,"found, skipping..."
                    continue
        os.system("python train.py -B " + base_folder + " -N " + mdl_id + " " + pred_name + " " + pred_opt)
        os.system("python eval.py -B " + base_folder + " -N " + mdl_id + " -p " + pred_name + " -m report > " + repfn)

##########################################################################################

parser = argparse.ArgumentParser()
parser.add_argument('-j', '--job_file', nargs=1, default=["./jobs/job-0"],
                    help="Job file")
parser.add_argument('-c', '--cfg_file', nargs=1, default=["./job.cfg"],
                    help="Config file")
args = parser.parse_args()

job_filename = args.job_file[0]
cfg_filename = args.cfg_file[0]

total_sets = 100
test_prec = 60
max_restarts = 5
base_folder="./"
var_file = "./data/variables-master.txt"
predictors = ["lreg", "scikit_lreg"]
pred_options = {"lreg":"", "scikit_lreg":""}
impute_method = "hmisc"
impute_fallback = "mice"
impute_options = {"hmisc":"", "mice":""}
with open(cfg_filename, "r") as cfg:
    lines = cfg.readlines()
    for line in lines:
        line = line.strip()
        if not line: continue
        key,value = line.split("=", 1)
        if key == "total_sets": total_sets = int(value)
        elif key == "test_prec": test_prec = int(value)
        elif key == "max_restarts": max_restarts = int(value)
        elif key == "base_folder": base_folder = value
        elif key == "var_file": var_file = value
        elif key == "predictors": predictors = value.split(",")
        elif "pred_options" in key:
            pred = key.split(".")[1]
            pred_options[pred] = value
        elif key == "impute_method": impute_method = value
        elif key == "impute_fallback": impute_fallback = value
        elif "impute_options" in key:
            imp = key.split(".")[1]
            impute_options[imp] = value

all_vars = []
var_dict = {}
with open(var_file, "rb") as mfile:
    for line in mfile.readlines():
        line = line.strip()
        if not line: continue
        parts = line.split()
        name = parts[0]
        type = parts[1]
        all_vars.append(name)
        var_dict[name] = type
out_var = all_vars[0]

mdl_ids = []
mdl_vars = []
with open(job_filename, "r") as cfg:
    lines = cfg.readlines()
    for line in lines:
        line = line.strip()
        if not line: continue
        id, vars = line.split(" ")
        mdl_ids.append(id)
        mdl_vars.append(vars.split(","))

for i in range(0, len(mdl_ids)):
    id = mdl_ids[i]
    vars = mdl_vars[i]
    run_model(id, vars)
