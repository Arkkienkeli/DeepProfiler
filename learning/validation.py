import tensorflow as tf
import numpy as np
import pandas as pd

import dataset.utils
import learning.models
import learning.cropping
import learning.training

import keras


class Metrics():

    def __init__(self):
        self.correct = 0.0
        self.in_top5 = 0.0
        self.counts = 0.0

    def update(self, corr, top5, counts):
        self.correct += corr
        self.in_top5 += top5
        self.counts += counts
        return self.correct/self.counts, self.in_top5/self.counts

def validate(config, dset, checkpoint_file):
    config["queueing"]["min_size"] = 0
    #num_classes = dset.numberOfClasses()
    num_classes = 594
    input_vars = learning.training.input_graph(config)
    images = input_vars["labeled_crops"][0]
    labels = tf.one_hot(input_vars["labeled_crops"][1], num_classes)

    input_shape = (
        config["sampling"]["box_size"],      # height
        config["sampling"]["box_size"],      # width
        len(config["image_set"]["channels"]) # channels
    )
    model = learning.models.create_keras_resnet(input_shape, num_classes)
    true_labels = tf.placeholder(tf.float32, shape=(config["training"]["minibatch"], num_classes))
    predictions = tf.placeholder(tf.float32, shape=(config["training"]["minibatch"], num_classes))

    correct = tf.reduce_sum(
        tf.to_float(
            tf.equal(
                tf.argmax(true_labels, 1), 
                tf.argmax(predictions, 1)
            )
        )
    )
    with_k = 2
    in_top_k = tf.reduce_sum(
        tf.to_float( 
            tf.nn.in_top_k(
                predictions=predictions,
                targets=tf.argmax(true_labels, 1),
                k=with_k
            )
        )
    )

    configuration = tf.ConfigProto()
    configuration.gpu_options.allow_growth = True
    configuration.gpu_options.visible_device_list = "0"
    session = tf.Session(config = configuration)
    keras.backend.set_session(session)

    print("Checkpoint:",checkpoint_file)
    model.load_weights(checkpoint_file)
    features = model.layers[176].output
    feat_extractor = keras.backend.function( [model.input] + [keras.backend.learning_phase()], [features] )

    metrics = Metrics()

    def predict(key, image_array, meta):
        image_key, image_names, outlines = dset.getImagePaths(meta)
        batch = {"images":[], "locations":[], "labels":[]}
        batch["images"].append(image_array)
        batch["locations"].append(learning.cropping.getLocations(image_key, config, randomize=False))
        batch["labels"].append(meta[config["training"]["label_field"]])
        boxes, box_ind, labels_data, mask_ind = learning.cropping.prepareBoxes(batch, config)
        batch["images"] = np.reshape(image_array, input_vars["shapes"]["batch"])

        session.run(input_vars["enqueue_op"], {
                        input_vars["image_ph"]:batch["images"],
                        input_vars["boxes_ph"]:boxes,
                        input_vars["box_ind_ph"]:box_ind,
                        input_vars["labels_ph"]:labels_data,
                        input_vars["mask_ind_ph"]:mask_ind
        })

        items = session.run(input_vars["queue"].size())
        while items > config["training"]["minibatch"]:
            batch = session.run([images, labels])
            result = model.predict(batch[0])

            #f = feat_extractor((batch[0],0))
            #feat = pd.DataFrame(f[0])
            #feat["label"] = np.argmax(batch[1], axis=1)
            #feat.to_csv(str(np.random.randint(1000,high=9999999)) + "-features.csv")

            items, corr, intop = session.run(
                [input_vars["queue"].size(), correct, in_top_k], 
                feed_dict={true_labels:batch[1], predictions:result}
            )
            acc, topk = metrics.update(corr, intop, batch[0].shape[0])
            message = "Acc: {:0.4f} Top-{}: {:0.4f} Samples: {:0.0f}"
            print(message.format(acc, with_k, topk, metrics.counts))
           
        #print(" *",image_key, "done")

    dset.scan(predict, frame="val")
    print("Validate: done")

 
