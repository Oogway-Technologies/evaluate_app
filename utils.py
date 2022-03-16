from distutils.log import debug
import spacy
import os
from sklearn import cluster
import streamlit as st
import requests
import json
from config import hf_auth_token
NUM_CLUSTERS = 10
import pathlib
import os
debug = False
config_path  = os.path.join(pathlib.Path(__file__).parent.resolve(),'config.json')
try:
    with open(config_path,'r') as f:
        config_param = json.loads(f.read())
    eps = config_param['eps']
    min_samples = config_param['min_samples']
    # debug = config_param['debug']
except Exception as e:
    eps = 4
    min_samples = 1

# if debug:
#     st.write("eps:",eps,"min_samples:",min_samples)

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
        # if debug:
        #     st.write("Running DBSCAN",eps,min_samples)
        DBSCAN = cluster.DBSCAN(eps=eps,min_samples=min_samples)
        DBSCAN.fit(asp_vectors)    
        return DBSCAN.labels_,[]
    

def get_word_clusters(unique_aspects, nlp,algo="kmeans"):
    # print("Found {} unique aspects for this product".format(len(unique_aspects)))
    # st.write(algo)
    asp_vectors = get_word_vectors(unique_aspects, nlp)
    if algo=="kmeans" and (len(unique_aspects) <= NUM_CLUSTERS):
        return list(range(len(unique_aspects)))

    # print("Running k-means clustering...")

    labels,cluster_centers = get_cluster_labels(asp_vectors,algo)
    # st.write(labels,cluster_centers)
    # st.write(labels)
    # st.write(cluster_centers)
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
        score = sum(scores)/len(scores)
        cluster_scores[label] = round(score/20,1)
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
    # st.write(type(pros_list_1),pros_list_1)
    
    cols = st.columns(2)
    cols[0].subheader(str(item_1) + " Pros:")
    # cols[0].text(st.session_state["item_1_data"]['name'])
    # cols[0].image(st.session_state["item_1_data"]['mediumImage'], use_column_width=True)
    cols[1].subheader(str(item_2) + " Pros:")
    # cols[1].text(st.session_state["item_2_data"]['name'])
    # cols[1].image(st.session_state["item_2_data"]['mediumImage'], use_column_width=True)           

    
    
    max_pro = max(len(pros_list_1),len(pros_list_2))
    if len(pros_list_1)==0 and len(pros_list_2)==0:
        cols = st.columns(2)
        cols[0].caption("No pros found")
        cols[1].caption("No pros found")

    for i in range(max_pro):
        cols = st.columns(2)
        if i < len(pros_list_1):
            cols[0].caption(pros_list_1[i])
        if i < len(pros_list_2):
            cols[1].caption(pros_list_2[i])


             

def print_cons(cons_list_1,cons_list_2,item_1,item_2):
    cols = st.columns(2)
    cols[0].subheader(str(item_1) + " Cons:")
    cols[1].subheader(str(item_2) + " Cons:")
    max_pro = max(len(cons_list_1),len(cons_list_2))
    if len(cons_list_1)==0 and len(cons_list_2)==0:
        cols = st.columns(2)
        cols[0].caption("No cons found")
        cols[1].caption("No cons found")    
    for i in range(max_pro):
        cols = st.columns(2)
        if i < len(cons_list_1):
            cols[0].caption(cons_list_1[i])
        if i < len(cons_list_2):
            cols[1].caption(cons_list_2[i])  

def print_aspects(selected_pair,item_1,item_2,cluster_scores_1,cluster_scores_2):
    # st.write(type(selected_pair),selected_pair)
    # st.write(type(cluster_scores_1),cluster_scores_1)
    cols = st.columns(2)
    cols[0].subheader(item_1)
    cols[1].subheader(item_2)
    for i,pair in enumerate(selected_pair):
        cols = st.columns(2)
        aspect = pair[0]
        score =  cluster_scores_1[pair[0]]
        if score>0:
            cols[0].caption(aspect + ": " + str(score).rstrip('.0') + " ⭐" )
        else:
            cols[0].caption(aspect + ": " + str(int(score)) + " ⭐" )

        cols[0].progress(int(score * 20))
        aspect = pair[1]
        score =  cluster_scores_2[pair[1]]    
        if score>0:
            cols[1].caption(aspect + ": " + str(score).rstrip('.0') + " ⭐")
        else:
            cols[1].caption(aspect + ": " + str(int(score)) + " ⭐" )        
        cols[1].progress(int(score * 20))    

def list_to_text(review_list_1):
    review_list_1 = review_list_1[0:10]
    full_text = ""
    for r in review_list_1:
        full_text = full_text + r + " "
    return [full_text]

def get_summaries(review_list):
    text = "\n###\n".join(review_list[0:8])
    API_URL = "https://api-inference.huggingface.co/models/oogway-ai/autonlp-distilbart5-623717870"
    headers = {"Authorization": "Bearer "+hf_auth_token}
    payload = {
        "inputs": text,
    }   
    data = json.dumps(payload)
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()

def print_summaries(summary_1,summary_2,item_1,item_2):
    
    st.header("Reviews Summary")
    # st.write(summary_1)
    cols = st.columns(2)
    cols[0].subheader(str(item_1) )
    cols[1].subheader(str(item_2) )
    cols = st.columns(2)
    try:
        if 'generated_text' in summary_1[0]:
            cols[0].write(summary_1[0]['generated_text'])            
    except Exception as e:
        # st.write(e)
        cols[0].write("No Summary found")
    try:
        if 'generated_text' in summary_2[0]:
            cols[1].write(summary_2[0]['generated_text'])            
    except Exception as e:
        # st.write(e)
        cols[1].write("No Summary found")    


    