import argparse
import numpy as np

# Polyaxon
from polyaxon.tracking import Run

from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score


def load_data():
    iris = datasets.load_iris()
    return iris.data, iris.target


def model(X, y, n_estimators, max_features, min_samples_leaf):
    classifier = RandomForestClassifier(
        n_estimators=n_estimators,
        max_features=max_features,
        min_samples_leaf=min_samples_leaf,
    )
    return cross_val_score(classifier, X, y, cv=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--n_estimators',
        type=int,
        default=3)
    parser.add_argument(
        '--max_features',
        type=int,
        default=3
    )
    parser.add_argument(
        '--min_samples_leaf',
        type=int,
        default=80
    )
    args = parser.parse_args()

    # Polyaxon
    experiment = Run(project='random-forest')
    experiment.create(tags=['examples', 'scikit-learn'])
    experiment.log_inputs(n_estimators=args.n_estimators,
                          max_features=args.max_features,
                          min_samples_leaf=args.min_samples_leaf)

    (X, y) = load_data()

    # Polyaxon
    experiment.log_data_ref(content=X, name='dataset_X')
    experiment.log_data_ref(content=y, name='dataset_y')

    accuracies = model(X=X,
                       y=y,
                       n_estimators=args.n_estimators,
                       max_features=args.max_features,
                       min_samples_leaf=args.min_samples_leaf)
    accuracy_mean, accuracy_std = (np.mean(accuracies), np.std(accuracies))
    print('Accuracy: {} +/- {}'.format(accuracy_mean, accuracy_std))

    # Polyaxon
    experiment.log_outputs(accuracy_mean=accuracy_mean, accuracy_std=accuracy_std)
