from __future__ import division, print_function
import os
import argparse
import json
import numpy as np
import torch
from pydoc import locate
from data_loader import MnistLoader
from utils import init_dir, show_config, setup_logger

parser = argparse.ArgumentParser(description="MNIST classifiers")
parser.add_argument("--method", type=str, default="mlp")

parser.add_argument("--resume", action="store_true")
parser.add_argument("--test", action="store_true")
parser.add_argument("--config-dir", type=str, default="config")
parser.add_argument("--data-dir", type=str, default="data")
parser.add_argument("--model-dir", type=str, default="trained_models")
parser.add_argument("--log-dir", type=str, default="logs")
parser.add_argument("--output-dir", type=str, default="outputs")
parser.add_argument("--last-epoch", type=int, default=-1)
parser.add_argument("--cuda", type=bool, default=True)

if __name__ == "__main__":
    args = parser.parse_args()
    with open(os.path.join(args.config_dir, "%s.json" % args.method)) as f:
        config = json.load(f)
    for arg in vars(args):
        if arg not in config.keys():
            config[arg] = getattr(args, arg)
    show_config(config)
    
    init_dir(args.model_dir)
    init_dir(args.log_dir)
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.set_default_tensor_type('torch.FloatTensor')

    data = MnistLoader(flatten=config["flatten"], data_path=args.data_dir)
    model = locate("models.%s.%s" % (args.method, config["model_name"]))()
    if args.resume or args.test:
        model_path = os.path.join(config["model_dir"], "%s_model.pth" % config["method"])
        if os.path.exists(model_path):
            print("Loading latest model from %s" % model_path)
            model.load_state_dict(torch.load(model_path))
    if args.cuda and torch.cuda.is_available():
        model = model.cuda()
    model.train()
    optimizer = locate("torch.optim.%s" % config["optimizer_type"])(model.parameters(), **config["optimizer"])
    logger = setup_logger(args.method, os.path.join(args.log_dir, "%s.log" % args.method), resume=args.resume)

    if args.test:
        f = locate("trainers.%s.test" % config["trainer"])
    else:
        f = locate("trainers.%s.train" % config["trainer"])
    f(data, model, optimizer, logger, config)
    