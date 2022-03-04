import spacy
import os
from sklearn import cluster
import streamlit as st
NUM_CLUSTERS = 10

def init_spacy():
    print("Loading en_core_web_sm")
    nlp = spacy.load('en_core_web_sm')
    print("spaCy successfully loaded")
    return nlp

def init_spacy_lg():
    print("Loading en_core_web_lg")
    nlp = spacy.load('en_core_web_lg')
    print("spaCy successfully loaded")
    return nlp

def get_cluster_labels(asp_vectors,algo):
    if algo=="kmeans":
        n_clusters = NUM_CLUSTERS
        kmeans = cluster.KMeans(n_clusters=n_clusters,random_state=2022)
        kmeans.fit(asp_vectors)
        return kmeans.labels_,kmeans.cluster_centers_
    if algo=="DBSCAN":
        # st.write("Running DBSCAN")
        DBSCAN = cluster.DBSCAN(eps=6,min_samples=1)
        DBSCAN.fit(asp_vectors)    
        return DBSCAN.labels_,[]
    

def get_word_clusters(unique_aspects, nlp,algo="kmeans"):
    # print("Found {} unique aspects for this product".format(len(unique_aspects)))
    print(algo)
    asp_vectors = get_word_vectors(unique_aspects, nlp)
    if len(unique_aspects) <= NUM_CLUSTERS:
        # print("Too few aspects ({}) found. No clustering required...".format(len(unique_aspects)))
        return list(range(len(unique_aspects)))

    # print("Running k-means clustering...")

    labels,cluster_centers = get_cluster_labels(asp_vectors,algo)
    return labels,cluster_centers,asp_vectors

def get_word_vectors(unique_aspects, nlp):
    asp_vectors = []
    for aspect in unique_aspects:
        token = nlp(aspect)
        asp_vectors.append(token.vector)
    return asp_vectors
