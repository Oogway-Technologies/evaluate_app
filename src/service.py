import requests
import json
import time
import pandas as pd
import streamlit as st
SERVICE_URL = "http://3.22.185.47:8001/aspect"
from pyabsa import APCCheckpointManager,ATEPCCheckpointManager
from utils import *
from sklearn.metrics import pairwise_distances_argmin_min
@st.cache(allow_output_mutation=True)
def get_models():
    # gdown.download(url1,output1, quiet=True)
    # gdown.download(url2,output2, quiet=True)
    aspect_extractor = ATEPCCheckpointManager.get_aspect_extractor(checkpoint='fast_lcf_atepc_English_cdw_apcacc_80.16_apcf1_78.34_atef1_75.39.zip',auto_device=False)  # False means load model on CPU 
    sent_classifier = APCCheckpointManager.get_sentiment_classifier(checkpoint='fast_lsa_t_acc_84.84_f1_82.36.zip',auto_device=False)  # Use CUDA if available
    return aspect_extractor,sent_classifier
def tokens_to_aspect(tokens,position):
  j = 0
  i = 0
  final_string = ''
  while(j<len(position) and i < len(tokens)):
    if i==position[j][0] and len(position[j])>1:
      aspect = " ".join(tokens[position[j][0] : position[j][-1]+1])
      term = "[ASP] "+aspect+" [ASP]"
    elif(i==position[j][0] and len(position[j])==1):
      term = "[ASP] "+tokens[position[j][0]]+" [ASP]"
    else:
      term = tokens[i]
    final_string = final_string + " " +term
    # print(final_string)
    i+=1
    if i > position[j][0]:
      j+=1
  return final_string

def aspect_polarity_extractor(inference_source):
  atepc_result = aspect_extractor.extract_aspect(inference_source=inference_source,  #
                                               save_result=True,
                                               print_result=False,  # print the result
                                               pred_sentiment=True,  # Predict the sentiment of extracted aspect terms
                                               )
  examples = [ tokens_to_aspect(d['tokens'],d['position']) for d in atepc_result if d['aspect'] ]
  result= []
  for example in examples:
    try:
      r = sent_classifier.infer(example)
      result.append(r)
    except Exception as e:
      print(e)
      continue
  return result

def get_aspect_score(aspect,sentiments):
  num_entries = len(sentiments)
  # Sum of sentiments [1, 5] about that topic 
  ctr_value = sum(sentiments)

  # This is how much if every review was negative for that topic
  min_val = -1 * num_entries

  # This is how much if every review was positive for that topic
  max_val = 1 * num_entries

  # Normalize counters
  ctr_value -= min_val
  max_val -= min_val
  # Calculate percentage
  perc = round((ctr_value / max_val) * 100.0)
  return perc

def get_highest_count_aspect(aspects,aspect_review_count):
  return sorted(aspects, key=lambda x: aspect_review_count[x], reverse=True)[0]

def get_similar_clusters(product1_clusters,product2_clusters):
  st.write(product1_clusters,product2_clusters)
  similarity_matrix = {}
  #find similiarity score for each cluster of product 1 with each cluster of product 2
  for token1 in product1_clusters:
    for token2 in product2_clusters:
      score = nlp(token1).similarity(nlp(token2))
      if score > 0.45:
        similarity_matrix[(token1,token2)] = score
  similarity_matrix = sorted(similarity_matrix.items(), key=lambda t: t[1], reverse=True)
  product1_selected = {}
  product2_selected = {}
  selected_pair = []
  st.write(similarity_matrix)
  #find best matching for product 1 cluster to product 2 cluster
  for k,v in similarity_matrix:
    if k[0] not in product1_selected and k[1] not in product2_selected:
      product1_selected[k[0]]=True
      product2_selected[k[1]]=True
      selected_pair.append(k)
  return selected_pair 

aspect_extractor,sent_classifier = get_models()
load_nlp = time.time()
nlp = init_spacy_lg()
loaded_nlp = time.time()
# st.write("Spacy loading time",loaded_nlp-load_nlp)
def get_aspects(reviews, aspects):
    review_list = reviews['reviews']
    review_text = list()

    ctr = 0
    for review in review_list:
        # if ctr > 2:
        #     break
        if review["reviewText"]:
          review_text.append(review["reviewText"])
        ctr += 1
    # st.write(review_text)
    with st.spinner('Extracting Aspects and Polarity'):
        aspect_extraction_start = time.time()
        result = aspect_polarity_extractor(review_text)
        data = [ r[0] for r in result ]
        data = [{'text':d['text'],'aspect':d['aspect'],'sentiment':d['sentiment']} for d in data]
        aspect_extraction_end = time.time()
        data = pd.DataFrame(data)
        # data.to_csv(".csv")
        # st.write(data)
    aspect_scoring_start = time.time()
    sentiment_score_mapping = {'Positive':1,'Neutral':0,'Negative':-1}
    aspect_mappings = {}
    for i, row in data.iterrows():
        for aspect, sentiment in zip(row['aspect'], row['sentiment']):
            aspect = aspect.strip()
            if aspect in aspect_mappings.keys():
                aspect_mappings[aspect].append(sentiment_score_mapping[sentiment])
            else:
                aspect_mappings[aspect] = []
                aspect_mappings[aspect].append(sentiment_score_mapping[sentiment])    
    unique_aspects = aspect_mappings.keys()
    aspect_review_count = {}
    aspect_score = {}
    for k in aspect_mappings:
        score = get_aspect_score(k,aspect_mappings[k])
        aspect_review_count[k] = len(aspect_mappings[k])
        aspect_score[k] = score
    aspect_review_count = dict(sorted(aspect_review_count.items(), key=lambda item: item[1],reverse=True))
    from collections import OrderedDict
    aspect_score = OrderedDict(list(sorted(aspect_score.items(), key=lambda item : item[1],reverse=True))) 
    aspect_scoring_end = time.time()
    clustering_start = time.time()
    algo = "DBSCAN"
    stopwords = nlp.Defaults.stop_words
    unique_aspects = [aspect for aspect in unique_aspects if (aspect not in stopwords) and (len(str(aspect))>1)]
    aspect_labels,cluster_centers_,asp_vectors = get_word_clusters(unique_aspects, nlp,algo)
    asp_to_cluster_map = dict(zip(unique_aspects, aspect_labels))
    index_aspect_mapping = {}
    for i,a in enumerate(list(unique_aspects)):
      index_aspect_mapping[i]=a
    clustering_end = time.time()
    cluster_title= {}
    if algo=="kmeans":
      closest, _ = pairwise_distances_argmin_min(cluster_centers_, asp_vectors)
      print(closest)
      for i,p in enumerate(closest):
        cluster_title[i] = index_aspect_mapping[p]
      st.write(cluster_title)
    label_aspect_list = {}
    for aspect in asp_to_cluster_map:
      # st.write(aspect,asp_to_cluster_map[aspect])
      if algo=="kmeans":
        label = cluster_title[int(asp_to_cluster_map[aspect])]
      else:
        label = int(asp_to_cluster_map[aspect])
      if label in label_aspect_list:
        label_aspect_list[label].append(aspect)
      else:
        label_aspect_list[label] = []
        label_aspect_list[label].append(aspect)
    # st.write(label_aspect_list)              
    if algo=="DBSCAN":
      for k,v in label_aspect_list.items():
        if k == -1:
          continue
        cluster_title[k]=get_highest_count_aspect(v,aspect_review_count)
      label_aspect_list_db = {}
      for k,v in label_aspect_list.items():
        if k == -1:
          continue
        label_aspect_list_db[cluster_title[k]] = v
      label_aspect_list = label_aspect_list_db
    # st.write(cluster_title)
    st.write(label_aspect_list)
    st.write("Aspect Scoring time",aspect_scoring_end-aspect_scoring_start)
    st.write("Clustering time",clustering_end-clustering_start)
    st.write("Aspect polarity extraction time",aspect_extraction_end-aspect_extraction_start)
    return label_aspect_list
def collect_aspects(aspects, aspect_list):
    # collection = dict()
    # for single_asp in aspect_list:
    #     collection[single_asp] = {
    #         'attribute': list(),
    #         'perc': list()
    #     }

    # for asp in aspects["aspects"]:
    #     for single_asp in aspect_list:
    #         asp_entry = asp[single_asp]
    #         for i in range(0, asp_entry["num_entries"]):
    #             value_attr = asp_entry['attr_text'][i] + ' ' + asp_entry['attr_key'][i]
    #             collection[single_asp]['attribute'].append(value_attr)
    #             collection[single_asp]['perc'].append(asp_entry['perc'])

    collection = {
        'price':{
            'attribute':['abc','xyz'],
            'perc':[80,90]
        },
        'size':{
            'attribute':['mnq','def'],
            'perc':[70,90]
        }
    }

    return collection
