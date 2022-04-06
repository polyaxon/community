import argparse
import logging
import numpy as np
from keras import optimizers
from keras.callbacks import EarlyStopping, TensorBoard, ModelCheckpoint
from keras.datasets import imdb
from keras.layers import Dense, Dropout, Embedding, LSTM, Bidirectional
from keras.models import Sequential
from keras.preprocessing import sequence

# Polyaxon
from polyaxon import tracking
from polyaxon.tracking.contrib.keras import PolyaxonCallback

logger = logging.getLogger('bidir-lstm')

OPTIMIZERS = {
    'adam': optimizers.Adam,
    'rmsprop': optimizers.RMSprop,
    'sgd': optimizers.SGD,
}


def transform_data(x_train, y_train, x_test, y_test, maxlen):
    x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
    x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
    y_train = np.array(y_train)
    y_test = np.array(y_test)
    return x_train, y_train, x_test, y_test


def train(max_features,
          maxlen,
          num_nodes,
          dropout,
          optimizer,
          log_learning_rate,
          batch_size,
          epochs):
    model = Sequential()
    model.add(Embedding(max_features, 128, input_length=maxlen))
    model.add(Bidirectional(LSTM(num_nodes)))
    model.add(Dropout(dropout))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(OPTIMIZERS[optimizer](lr=10 ** log_learning_rate),
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    model.fit(x_train,
              y_train,
              batch_size=batch_size,
              epochs=epochs,
              validation_data=[x_test, y_test],
              callbacks=[
                  EarlyStopping(
                      monitor='val_loss', min_delta=1e-4, patience=3, verbose=1, mode='auto'),
                  PolyaxonCallback(),
                  TensorBoard(log_dir=tracking.get_tensorboard_path(), histogram_freq=1),
                  ModelCheckpoint(tracking.get_outputs_path("model"))
              ])

    return model.evaluate(x_test, y_test)[1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--max_features',
        type=int,
        default=20000
    )
    parser.add_argument(
        '--skip_top',
        type=int,
        default=30,
        help='Top occurring words to skip'
    )
    parser.add_argument(
        '--maxlen',
        type=int,
        default=100
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32
    )
    parser.add_argument(
        '--num_nodes',
        type=int,
        default=8
    )
    parser.add_argument(
        '--optimizer',
        type=str,
        default='adam'
    )
    parser.add_argument(
        '--log_learning_rate',
        type=int,
        default=-3
    )
    parser.add_argument(
        '--dropout',
        type=float,
        default=0.8
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=1
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=234
    )
    args = parser.parse_args()

    # Polyaxon
    tracking.init()

    logger.info('Loading data...')
    (x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=args.max_features,
                                                          skip_top=args.skip_top,
                                                          seed=args.seed)
    logger.info('train sequences %s', len(x_train))
    logger.info('test sequences %s', len(x_test))

    # Polyaxon
    tracking.log_data_ref(content=x_train, name='x_train')
    tracking.log_data_ref(content=y_train, name='y_train')
    tracking.log_data_ref(content=x_test, name='x_test')
    tracking.log_data_ref(content=y_test, name='y_test')

    logger.info('Transforming data...')
    x_train, y_train, x_test, y_test = transform_data(x_train,
                                                      y_train,
                                                      x_test,
                                                      y_test,
                                                      args.maxlen)
    logger.info('Training...')
    accuracy = train(max_features=args.max_features,
                     maxlen=args.maxlen,
                     batch_size=args.batch_size,
                     num_nodes=args.num_nodes,
                     optimizer=args.optimizer,
                     log_learning_rate=args.log_learning_rate,
                     dropout=args.dropout,
                     epochs=args.epochs)

    # Polyaxon
    tracking.log_metrics(accuracy=accuracy)
