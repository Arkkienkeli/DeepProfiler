import importlib
import keras.metrics


#################################################
## MAIN TRAINING ROUTINE
#################################################


def learn_model(config, dset, epoch=1, seed=None):
    model_module = importlib.import_module("plugins.models.{}".format(config['model']['name']))
    crop_module = importlib.import_module("plugins.crop_generators.{}".format(config['model']['crop_generator']))
    keras_metrics = []
    custom_metrics = 
    importlib.invalidate_caches()

    crop_generator = crop_module.GeneratorClass(config, dset)
    model = model_module.ModelClass(config, dset, crop_generator, )

    if seed:
        model.seed(seed)
    model.train(epoch)
