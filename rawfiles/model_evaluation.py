#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from flask_api import FlaskAPI
import codecs
from itertools import chain
import requests
import base64
import numpy as np
import csv

import tflearn
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.conv import conv_2d, max_pool_2d
from tflearn.layers.normalization import local_response_normalization
from tflearn.layers.estimator import regression
from tflearn.data_utils import load_csv
from tensorflow.python.framework.ops import reset_default_graph

from decimal import Decimal
from tflearn.data_utils import shuffle

class Thai_segment():
    
    file_path = './corpus/Cleaned-Masita corpus 2.csv'
    data, labels = load_csv(file_path, target_column=0, categorical_labels=True, n_classes=2)

    def preprocess_server(data):
        rlist = []
        preprocessdata = []
        for i in range(len(data)):
            x = requests.get('http://174.138.26.245:5000/preprocess/'+data[i][0])
            resu = x.json()
            preprocessdata.append(resu['result'])
        for i in range(len(preprocessdata)):
            r = requests.get('http://174.138.26.245:5000/tokenize/'+preprocessdata[i])
            result = r.json()
            rlist.append(result['result'])
        return rlist

    def get_uniquewords(listdata):
        uniquewords = []
        for line in range(len(listdata)):
            words = listdata[line]
            inner_data = []
            for word in words:
                if word not in uniquewords:
                    #w = repr(word.encode('utf-8'))
                    uniquewords.append(word)
        return uniquewords

    def preprocess_vector(listdata, uniquewords):
            sentences = []
            vectors = []
            #f = open(file_path, 'r')
            for line in range(len(listdata)):
                words = listdata[line]
                inner_data = []
                for word in words:
                    inner_data.append(word)
                sentences.append(inner_data)
            
            for sentence in sentences:
                inner_vector = []
                for word in uniquewords:
                    if word in sentence:
                        inner_vector.append(1)
                    else:
                        inner_vector.append(0)
                vectors.append(inner_vector)
            return np.array(vectors, dtype=np.float32)

    pdata = preprocess_server(data)
    unique_words = get_uniquewords(pdata)
    data = preprocess_vector(pdata, unique_words)

    neurons = len(data[0])

    # shuffle the dataset
    data, labels = shuffle(data, labels)

    reset_default_graph()
    network = input_data(shape=[None, neurons])
    network = fully_connected(network, 8, activation='relu')
    network = fully_connected(network, 8*2, activation='relu')
    network = fully_connected(network, 8, activation='relu')
    network = dropout(network, 0.5)

    network = fully_connected(network, 2, activation='softmax')
    network = regression(network, optimizer='adam', learning_rate=0.01, loss='categorical_crossentropy')

    file_path3 = './trainingdataset/Cleaned-Masita-traindataset-2.csv'
    testdata, testlabels = load_csv(file_path3, target_column=0, categorical_labels=True, n_classes=2)
    resultdata = preprocess_server(testdata)
    resultdata = preprocess_vector(resultdata, unique_words)

    model = tflearn.DNN(network)
    model.fit(data, labels, n_epoch=40, shuffle=True, validation_set=(resultdata, testlabels) , show_metric=True, batch_size=None, snapshot_epoch=True, run_id='task-classifier')
    model.save("thaitext-classifier-mashita.tfl")
    print("Network trained and saved as Pthaitext-classifier-mashita.tfl")

    result = model.evaluate(resultdata, testlabels)
    print("Evaluation result: %s" %result)

    #predict = model.predict(resultdata)