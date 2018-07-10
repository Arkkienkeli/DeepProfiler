import keras
from keras import backend as K
from keras import objectives
from keras.layers import *
from keras.models import Model
from keras.optimizers import Adam


def define_model(config, dset):
    def sampling(args):
        z_mean, z_log_sigma = args
        epsilon = K.random_normal(shape=(config['training']['minibatch'], config['model']['latent_dim']),
                                  mean=0., stddev=config['model']['epsilon_std'])
        return z_mean + K.exp(z_log_sigma) * epsilon

    def vae_loss(x, x_decoded_mean):
        xent_loss = objectives.binary_crossentropy(x, x_decoded_mean)
        kl_loss = - 0.5 * K.mean(1 + z_log_sigma - K.square(z_mean) - K.exp(z_log_sigma), axis=-1)
        return xent_loss + kl_loss

    input_shape = (
        config["sampling"]["box_size"],  # height
        config["sampling"]["box_size"],  # width
        len(config["image_set"]["channels"])  # channels
    )
    input_image = keras.layers.Input(input_shape)

    x = Conv2D(8, (3, 3), activation='relu', padding='same')(input_image)
    x = MaxPooling2D((2, 2), padding='same')(x)
    x = Conv2D(16, (3, 3), activation='relu', padding='same')(x)
    x = MaxPooling2D((2, 2), padding='same')(x)
    x = Conv2D(32, (3, 3), activation='relu', padding='same')(x)
    x = MaxPooling2D((2, 2), padding='same')(x)
    encoded_shape = x._keras_shape[1:]
    x = Flatten()(x)

    z_mean = Dense(config['model']['latent_dim'], name='z_mean')(x)
    z_log_sigma = Dense(config['model']['latent_dim'], name='z_log_sigma')(x)
    z = Lambda(sampling, output_shape=(config['model']['latent_dim'],), name='z')([z_mean, z_log_sigma])

    x = Reshape(encoded_shape)(z)
    x = Conv2DTranspose(32, (3, 3), activation='relu', padding='same')(x)
    x = UpSampling2D((2, 2))(x)
    x = Conv2DTranspose(16, (3, 3), activation='relu', padding='same')(x)
    x = UpSampling2D((2, 2))(x)
    x = Conv2DTranspose(8, (3, 3), activation='relu')(x)
    x = UpSampling2D((2, 2))(x)
    decoded = Conv2DTranspose(len(config["image_set"]["channels"]), (3, 3), activation='sigmoid', padding='same')(x)

    vae = Model(input_image, decoded)
    vae.compile(optimizer=Adam(lr=config['training']['learning_rate']), loss=vae_loss)
    return vae
