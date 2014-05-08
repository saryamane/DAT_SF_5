# Author: Peter Prettenhofer <peter.prettenhofer@gmail.com>
#         Olivier Grisel <olivier.grisel@ensta.org>
#         Mathieu Blondel <mathieu@mblondel.org>
#         Lars Buitinck <L.J.Buitinck@uva.nl>
# License: BSD 3 clause

# GROUP 1: start
<<<<<<< HEAD
# SETUP / INIT / OPTIONS / CONFIG
# SET Helper functions
# IO - LOADING DATA
# Feature Extractions.
=======

## Setup and initialization
>>>>>>> 53f23c52864bae93e197fba2e6841f9e12bd3ccb
from __future__ import print_function

import logging
import numpy as np
from optparse import OptionParser   #import a better library for parsing options
import sys
from time import time
import pylab as pl

from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import Perceptron
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.utils.extmath import density
from sklearn import metrics


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# Use the OptionaParser function to build both a help screen and use to parse any option flags passed in from the command line
op = OptionParser()
op.add_option("--report",
              action="store_true", dest="print_report",
              help="Print a detailed classification report.")
op.add_option("--chi2_select",
              action="store", type="int", dest="select_chi2",
              help="Select some number of features using a chi-squared test")
op.add_option("--confusion_matrix",
              action="store_true", dest="print_cm",
              help="Print the confusion matrix.")
op.add_option("--top10",
              action="store_true", dest="print_top10",
              help="Print ten most discriminative terms per class"
                   " for every classifier.")
op.add_option("--all_categories",
              action="store_true", dest="all_categories",
              help="Whether to use all categories or not.")
op.add_option("--use_hashing",
              action="store_true",
              help="Use a hashing vectorizer.")
op.add_option("--n_features",
              action="store", type=int, default=2 ** 16,
              help="n_features when using the hashing vectorizer.")
op.add_option("--filtered",
              action="store_true",
              help="Remove newsgroup information that is easily overfit: "
                   "headers, signatures, and quoting.")

(opts, args) = op.parse_args()   # pair the options possible above with any arguments passed to it from the command line
if len(args) > 0:        # but you shouldnt have any arguments, so halt the whole script
    op.error("this script takes no arguments.")
    sys.exit(1)

print(__doc__)      # print the docstring (right now it is None)
op.print_help()     # print to console the help screen
print()


if opts.all_categories:     # if the option --all_categories was used...
    categories = None       # set None
else:
    categories = [        # otherwise use the following 4 categories:
        'alt.atheism',
        'talk.religion.misc',
        'comp.graphics',
        'sci.space',
    ]

if opts.filtered:     # if the option --filtered was used
    remove = ('headers', 'footers', 'quotes')   # set a list of things to remove
else:
    remove = ()                 # otherwise, dont.

print("Loading 20 newsgroups dataset for categories:")
print(categories if categories else "all")    # print out the container of categories

## IO - Load the data


# Now grab the selected categories using the fn from sklearn.datasets  (imported at the top)
data_train = fetch_20newsgroups(subset='train', categories=categories,
                                shuffle=True, random_state=42,
                                remove=remove)
# This fn already has a concept of test vs train, so now load the test:
# This may also return some Warnings or INFO about the download and decompression
data_test = fetch_20newsgroups(subset='test', categories=categories,
                               shuffle=True, random_state=42,
                               remove=remove)
# Tell when succeeded
print('data loaded')



def size_mb(docs):
    """ Returns the sum of the data size of 'docs' in megabytes """
    return sum(len(s.encode('utf-8')) for s in docs) / 1e6

# Now remember the size_mb of train and test
data_train_size_mb = size_mb(data_train.data)
data_test_size_mb = size_mb(data_test.data)

# Print a report of the number of files, and the size_mb of each of train and test
print("%d documents - %0.3fMB (training set)" % (
    len(data_train.data), data_train_size_mb))
print("%d documents - %0.3fMB (test set)" % (
    len(data_test.data), data_test_size_mb))
print("%d categories" % len(categories))
print()

# Assign the labels for the new train/test split
y_train, y_test = data_train.target, data_test.target



## Feature Extraction


# Based on whether the hashing option was chosen, chooses whether to use a Hashing or Tfidf Vectorizer
print("Extracting features from the training dataset using a sparse vectorizer")
t0 = time()
if opts.use_hashing:
    vectorizer = HashingVectorizer(stop_words='english', non_negative=True,
                                   n_features=opts.n_features)
    X_train = vectorizer.transform(data_train.data)
else:
    vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5,
                                 stop_words='english')
    X_train = vectorizer.fit_transform(data_train.data)
duration = time() - t0

# Measures and prints the time it takes to extract features from the training set
print("done in %fs at %0.3fMB/s" % (duration, data_train_size_mb / duration))
print("n_samples: %d, n_features: %d" % X_train.shape)
print()

print("Extracting features from the test dataset using the same vectorizer")
t0 = time()
X_test = vectorizer.transform(data_test.data)
duration = time() - t0

# Measures and prints the time it takes to extract features from the test set
print("done in %fs at %0.3fMB/s" % (duration, data_test_size_mb / duration))
print("n_samples: %d, n_features: %d" % X_test.shape)
print()

# If the Chi2 option is selected, this calculates the Chi2 and displays how long it took to complete
if opts.select_chi2:
    print("Extracting %d best features by a chi-squared test" %
          opts.select_chi2)
    t0 = time()
    ch2 = SelectKBest(chi2, k=opts.select_chi2)
    X_train = ch2.fit_transform(X_train, y_train)
    X_test = ch2.transform(X_test)
    print("done in %fs" % (time() - t0))
    print()

## Helper Functions

# Defines the trim method so our strings fit on the terminal
def trim(s):
    """Trim string to fit on terminal (assuming 80-column display)"""
    return s if len(s) <= 80 else s[:77] + "..."

# Reads the feature names if the use_hashing option is turned off
if opts.use_hashing:
    feature_names = None
else:
  # return and store the tfidf get_feature_names in a numpyarray, and pass this on to Group 2!
    feature_names = np.asarray(vectorizer.get_feature_names())

# GROUP 2: start
# functions that takes the name of the classifier model
# and returns the output of the model in terms of 4 results.
# clf_descr, score, train_time, test_time
# X_train, y_train = defined in the global namespace.
# This part does define the main function of the function. CORE Function.
def benchmark(clf):
    """ 
    Description:
    - Returns the time, score, description and relevant optional descriptive statistics/reports on how well a model runs 

    Arguments: 
    - clf: A classifier object (ie LinearSVC, MultinomialNB, SGDClassifier)

    Returns: 
    - clf_descr: The name of the model (ie LinearSVC)
    - score: The F1 score of the model, using clf.f1_score()
    - train_time: Time (in seconds) to fit the model using clf.fit()
    - test_time: Time (in seconds) to test the model using clf.predict()

    """

    print('_' * 80)
    print("Training: ")
    print(clf)
    
    # Train model, record time elapsed
    t0 = time()
    clf.fit(X_train, y_train)
    train_time = time() - t0
    print("train time: %0.3fs" % train_time)

    # Test model, record time elapsed
    t0 = time()
    pred = clf.predict(X_test)
    test_time = time() - t0
    print("test time:  %0.3fs" % test_time)

    # Calculates the f1 score, comparing between precision and recall for each model
    score = metrics.f1_score(y_test, pred)
    print("f1-score:   %0.3f" % score)

    # Grabs the description of the model by parsing the clf
    clf_descr = str(clf).split('(')[0]  
    print('clf_descr: %s' % clf_descr)


    if hasattr(clf, 'coef_'):

        #Print the dimensionality and density of a model
        print("dimensionality: %d" % clf.coef_.shape[1])
        print("density: %f" % density(clf.coef_))

        #Option to print the top 10 feature names of a model
        if opts.print_top10 and feature_names is not None:
            print("top 10 keywords per class:")
            for i, category in enumerate(categories):
                top10 = np.argsort(clf.coef_[i])[-10:]
                print(trim("%s: %s"
                      % (category, " ".join(feature_names[top10]))))
        print()

    #Option to print a classification report of a model 
    if opts.print_report:
        print("classification report:")
        print(metrics.classification_report(y_test, pred,
                                            target_names=categories))
    
    #Option to print the confusion matrix of a model
    if opts.print_cm:
        print("confusion matrix:")
        print(metrics.confusion_matrix(y_test, pred))

    print()
    

    #returns the following for every model
    return clf_descr, score, train_time, test_time

# GROUP 3: start
<<<<<<< HEAD
results = [] #initialize the results array to empty lists.
=======
results = [] # Initialize result in an empty list
>>>>>>> 53f23c52864bae93e197fba2e6841f9e12bd3ccb
for clf, name in (
        (RidgeClassifier(tol=1e-2, solver="lsqr"), "Ridge Classifier"),
        (Perceptron(n_iter=50), "Perceptron"),
        (PassiveAggressiveClassifier(n_iter=50), "Passive-Aggressive"),
<<<<<<< HEAD
        (KNeighborsClassifier(n_neighbors=10), "kNN")): # Initialize the classifiers
    print('=' * 80) # Print the equal sign 80 times.
    print(name) # 
    results.append(benchmark(clf))
=======
        (KNeighborsClassifier(n_neighbors=10), "kNN")): #Looping through each classifier result
    print('=' * 80) # printing equal sign 80 times on the terminal
    print(name) # printing each name on terminal
    results.append(benchmark(clf)) # Calling benchmark on the classifier result and appending the result to the list
>>>>>>> 53f23c52864bae93e197fba2e6841f9e12bd3ccb

for penalty in ["l2", "l1"]: # Initializing and looping through the penalties L1 and L2
    print('=' * 80)
    print("%s penalty" % penalty.upper()) # Prinitng the uppercase on L1 and L2
    results.append(benchmark(LinearSVC(loss='l2', penalty=penalty,
                                            dual=False, tol=1e-3))) # Appending the result of the linear SVC with the assigned penalty

    results.append(benchmark(SGDClassifier(alpha=.0001, n_iter=50,
                                           penalty=penalty))) # Appending the result of the SGDC classifier with the assigned penalty

print('=' * 80)
print("Elastic-Net penalty")
results.append(benchmark(SGDClassifier(alpha=.0001, n_iter=50,
                                       penalty="elasticnet"))) # Appending the result of the SGDC classifier with the elasticnet penalty

print('=' * 80)
print("NearestCentroid (aka Rocchio classifier)")
results.append(benchmark(NearestCentroid())) # Appending the result of Nearest Centroid to benchmark

print('=' * 80)
print("Naive Bayes")
results.append(benchmark(MultinomialNB(alpha=.01))) # Appending the result of MultinomiaNB to benchmark
results.append(benchmark(BernoulliNB(alpha=.01))) # Appending the result of BernoulliNB to benchmark


class L1LinearSVC(LinearSVC): # Creating new class L1LinearSVC with two methods, fit and predict

    def fit(self, X, y): # This method acts on itself with X and y
        self.transformer_ = LinearSVC(penalty="l1",
                                      dual=False, tol=1e-3) # This is changing all the defaults for LinearSVC
        X = self.transformer_.fit_transform(X, y) # Assigning X with the new parameters for LinearSVC performing fit_transform operation
        return LinearSVC.fit(self, X, y) # Returns the fit with the new X with the default LinearSVC parameters

    def predict(self, X): # Predicts the outcome based on the test dataset X
        X = self.transformer_.transform(X) # Perform a transform on X using the updated defaults for LinearSVC
        return LinearSVC.predict(self, X) # returns the predicted score on the transformed data X

print('=' * 80)
print("LinearSVC with L1-based feature selection")
results.append(benchmark(L1LinearSVC())) # Append the results of the linearSVC to the exisiting list



indices = np.arange(len(results)) # Length of the results

results = [[x[i] for x in results] for i in range(4)] # Iterating through the classifier output results

clf_names, score, training_time, test_time = results # Assigns order of classifier output with these names
training_time = np.array(training_time) / np.max(training_time) # Normalizing the training time
test_time = np.array(test_time) / np.max(test_time) # Normalizing the test time

# Plotting the graph with the following configs
pl.figure(figsize=(12,8))
pl.title("Score")
pl.barh(indices, score, .2, label="score", color='r')
pl.barh(indices + .3, training_time, .2, label="training time", color='g')
pl.barh(indices + .6, test_time, .2, label="test time", color='b')
pl.yticks(())
pl.legend(loc='best')
pl.subplots_adjust(left=.25)
pl.subplots_adjust(top=.95)
pl.subplots_adjust(bottom=.05)

for i, c in zip(indices, clf_names): # Looping through the indicies with clf_names
    pl.text(-.3, i, c)

pl.show()