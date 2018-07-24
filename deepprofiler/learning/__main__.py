import json
import os

import click

import deepprofiler.dataset.image_dataset
import deepprofiler.learning.training
import deepprofiler.learning.validation
import deepprofiler.learning.optimization

# Main interaction point
@click.group()
@click.option("--config", prompt="Configuration file for learning",
              help="Configuration file, written in JSON format",
              type=click.File('r'))
@click.pass_context
def cli(context, config):
    params = json.load(config)
    params["image_set"]["index"] = os.path.join(params["image_set"]["metadata"], "index.csv")
    context.obj["config"] = params


# First learning tool: Training a network
@cli.command()
@click.option("--epoch", default=1)
@click.option("--seed", default=None)
@click.pass_context
def training(context, epoch, seed):
    metadata = deepprofiler.dataset.image_dataset.read_dataset(context.obj["config"])
    deepprofiler.learning.training.learn_model(context.obj["config"], metadata, epoch, seed)

# Optional learning tool: Optimize the hyperparameters of a model
@cli.command()
@click.option("--epoch", default=1)
@click.option("--seed", default=None)
@click.pass_context
def optimization(context, epoch, seed):
    metadata = deepprofiler.dataset.image_dataset.read_dataset(context.obj["config"])
    optim = deepprofiler.learning.optimization.Optimize(context.obj["config"], metadata, epoch, seed)
    optim.optimize()

# Second learning tool: Training a recurrent network
@cli.command()
@click.option("--epoch", default=1)
@click.pass_context
def recurrent_training(context, epoch):
    metadata = deepprofiler.dataset.image_dataset.read_dataset(context.obj["config"])
    deepprofiler.learning.recurrent_training.learn_model(context.obj["config"], metadata, epoch)

# Profile cells and extract features
@cli.command()
@click.pass_context
@click.option("--part",
              help="Part of index to process", 
              default=-1, 
              type=click.INT)
def profiling(context, part):
    import deepprofiler.learning.profiling
    config = context.obj["config"]
    if part >= 0:
        partfile = "index-{0:03d}.csv".format(part)
        config["image_set"]["index"] = os.path.join(config["image_set"]["metadata"], partfile)
    metadata = deepprofiler.dataset.image_dataset.read_dataset(context.obj["config"])
    deepprofiler.learning.profiling.profile(context.obj["config"], metadata)


if __name__ == "__main__":
    cli(obj={})
