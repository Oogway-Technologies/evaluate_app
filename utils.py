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
        DBSCAN = cluster.DBSCAN(eps=5.5,min_samples=1)
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
    # st.write(labels,cluster_centers)
    return labels,cluster_centers,asp_vectors

def get_word_vectors(unique_aspects, nlp):
    asp_vectors = []
    for aspect in unique_aspects:
        token = nlp(aspect)
        asp_vectors.append(token.vector)
    return asp_vectors

def get_cluster_score(label_aspect_list,aspect_score):
    cluster_scores = {}
    for label,cluster in label_aspect_list.items():
        scores = [aspect_score[aspect] for aspect in cluster ]
        cluster_scores[label] = round(sum(scores)/len(scores))
    return cluster_scores

def get_pro_con_list(pro_con_list):
    pros_flag = False
    cons_flag = False
    pros_list = []
    cons_list = []
    for pro_con in pro_con_list['procon']:
        for item in pro_con:
            try:
                if item:
                    if item=="Pros:":
                        pros_flag = True
                        cons_flag = False
                        continue
                    elif item=="Cons:":
                        cons_flag = True
                        pros_flag = False
                        continue
                    else:
                        item = item.split(".")[1].strip()
                        if item=='None':
                            continue
                        elif pros_flag:
                            pros_list.append(item)
                        else:
                            cons_list.append(item)
            except  Exception as e:
                print(e)
                continue
    return pros_list,cons_list

def print_pros(pros_list_1,pros_list_2,item_1,item_2):
    cols = st.columns(2)
    cols[0].header(str(item_1) + " Pros:")
    cols[1].header(str(item_2) + " Pros:")
    max_pro = max(len(pros_list_1),len(pros_list_2))
    for i in range(max_pro):
        cols = st.columns(2)
        if i < len(pros_list_1):
            cols[0].caption(pros_list_1[i])
        if i < len(pros_list_2):
            cols[1].caption(pros_list_2[i])

def print_cons(cons_list_1,cons_list_2,item_1,item_2):
    cols = st.columns(2)
    cols[0].header(str(item_1) + " Cons:")
    cols[1].header(str(item_2) + " Cons:")
    max_pro = max(len(cons_list_1),len(cons_list_2))
    for i in range(max_pro):
        cols = st.columns(2)
        if i < len(cons_list_1):
            cols[0].caption(cons_list_1[i])
        if i < len(cons_list_2):
            cols[1].caption(cons_list_2[i]) 

def print_aspects(selected_pair,item_1,item_2,cluster_scores_1,cluster_scores_2):
    cols = st.columns(2)
    cols[0].header(item_1)
    cols[1].header(item_2)
    for i,pair in enumerate(selected_pair):
        cols = st.columns(2)
        aspect = pair[0]
        score =  cluster_scores_1[pair[0]]
        cols[0].caption(aspect + ": " + str(score) + "%" )
        cols[0].progress(score)
        aspect = pair[1]
        score =  cluster_scores_2[pair[1]]
        cols[1].caption(aspect + ": " + str(score) + "%")
        cols[1].progress(score)    