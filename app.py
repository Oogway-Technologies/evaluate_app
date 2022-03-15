from distutils.log import debug
import enum
import json
from logging import exception
import streamlit as st
from src.walmart_api import *
from src.service import get_aspects,get_similar_clusters,get_review_list,get_pro_con
from utils import print_pros,print_cons,print_aspects,list_to_text,get_summaries,print_summaries
DEV_MODE = False
import pathlib
import os
config_path  = os.path.join(pathlib.Path(__file__).parent.resolve(),'config.json')
query_params = st.experimental_get_query_params()
try:
    if query_params['user'][0]=='admin':
        with open(config_path,'r') as f:
            config_param = json.loads(f.read())
        eps = config_param['eps']
        min_samples = config_param['min_samples']
        number_of_reviews = config_param['number_of_reviews']
        # debug = config_param['debug']

    st.sidebar.write("Admin Panel")
    reviews_options = range(10,51,10)
    index = reviews_options.index(number_of_reviews)
    number_of_reviews = st.sidebar.selectbox('Number of Reviews?',reviews_options,index=index)
    eps = st.sidebar.slider('DBSCAN eps ?', min_value=1.0, max_value=10.0, value=eps, step=0.5)
    min_samples = st.sidebar.slider('DBSCAN min_samples ?', 1, 10, min_samples)
    # debug = st.sidebar.checkbox("Debug",value=debug)
    update = st.sidebar.button("Update")
    if update:
        d = {'number_of_reviews':number_of_reviews,'eps':eps,'min_samples':min_samples}
        # d = {'number_of_reviews':number_of_reviews,'eps':eps,'min_samples':min_samples,'debug':debug}
        if update:
            with open(config_path,'w') as f:
                f.write(json.dumps(d))
except Exception as e:
    
    pass  

try:
    with open(config_path,'r') as f:
        config_param = json.loads(f.read())
    number_of_reviews = int(config_param['number_of_reviews']/10)
except Exception as e:
    st.write(e)
    number_of_reviews = 1

def clear_state():
    st.session_state["prod"] = ""
    st.session_state["item_1"] = ""
    st.session_state["item_2"] = ""


# App title
st.title("Evaluate")

# Search bar is always at the top of the page after the title
st.write("Please type in items like shoes, tv, phones, headphones you would like to compare. ")
input_prod = st.text_input("Search", key="prod")
search = st.button('Search')
# st.markdown("Select two items to compare")
st.write("Copy/Paste the item id's from the search results you want to compare. ")
item_1 = st.text_input("First item id: ", key="item_1")
item_2 = st.text_input("Second item id: ", key="item_2")
prod = None

# st.subheader('Select comparison features:')
st.write("Select one or more features decision matrix, pro/cons and summary and hit evaluate button")
decision_matrix = st.checkbox('Decision Matrix (~60-90 seconds)')
summaries = st.checkbox('Summaries (~5-10 seconds)')
pros_cons = st.checkbox('Pros Cons (~5-10 seconds)')

cols = st.columns(2)
eval_button = cols[0].button('Evaluate')
cols[1].button('Restart', on_click=clear_state)


def average_list(lst):
    if len(lst) == 0:
        return 0.0
    return sum(lst) / len(lst)


def run_compare():
    global item_1 
    global item_2

    # Input aspects
    # st.markdown('Specify comma-separated aspects to compare')
    # aspects = st.text_input("Aspects: ", key="aspects")
    # if aspects:
    # Get reviews for the two products
    item_1_rev = get_all_reviews(item_1,number_of_reviews)
    # st.write(item_1_rev)
    item_2_rev = get_all_reviews(item_2,number_of_reviews)

    # Run the API on the reviews and aspects
    # aspects = [asp.strip() for asp in aspects.split(',')]
    # st.write("Getting Product 1 Aspects")
    review_list_1 = get_review_list(item_1_rev['reviews'])
    review_list_2 = get_review_list(item_2_rev['reviews'])


    
    if pros_cons:
        body = {
            'text':list_to_text(review_list_1),
            'category':item_1_rev['categoryPath'],
            'default_category':'tv'
        }
        pros_list_1,cons_list_1 = get_pro_con(body)
        pros_list_1 = list(set(pros_list_1))
        cons_list_1 = list(set(cons_list_1))
        body = {
            'text':list_to_text(review_list_2),
            'category':item_2_rev['categoryPath'],
            'default_category':'tv'
        }
        pros_list_2,cons_list_2 = get_pro_con(body)
        pros_list_2 = list(set(pros_list_2))
        cons_list_2 = list(set(cons_list_2))
        st.header('Pros Cons:')
        print_pros(pros_list_1,pros_list_2,item_1,item_2) 
        print_cons(cons_list_1,cons_list_2,item_1,item_2)  
    if decision_matrix:
        st.header('Decision Matrix:')
        aspects_item_1 = {}
        aspects_item_2 = {}
        if len(review_list_1)==0 or len(review_list_2)==0:
            st.write("Not enough data for decision matrix")
        else:
            aspects_item_1,cluster_scores_1 = get_aspects(review_list_1)
            aspects_item_2,cluster_scores_2 = get_aspects(review_list_2)
            selected_pair = get_similar_clusters(list(aspects_item_1.keys()),list(aspects_item_2.keys()))
            
            print_aspects(selected_pair,item_1,item_2,cluster_scores_1,cluster_scores_2)
    if summaries:
        sum_1 = get_summaries(review_list_1)
        sum_2 = get_summaries(review_list_2)
        print_summaries(sum_1,sum_2,item_1,item_2)

def run():
    global prod
    # if not input_prod:
    #     return
    if item_1 and item_2 and eval_button:
        run_compare()
        return

    # Read in taxonomy
    with open('src/taxonomy.json') as json_file:
        data = json.load(json_file)

    # Get product list
    if DEV_MODE:
        with open('sample_data.json') as json_file:
            prod = json.load(json_file)
    # elif not prod:
    elif search:
        prod = search_prod(prod=input_prod)

    if not prod:
        return

    st.markdown('Total results: 10 of ' + str(prod['totalResults']))

    for i in range(0, 5):
        try:
            item_a = prod['items'][2*i]
            item_b = prod['items'][2*i+1]
            item_a_numReviews = item_a['numReviews']
            item_b_numReviews = item_b['numReviews']
            cols = st.columns(2)
            # st.write(item_a)

            cols[0].subheader("Item id: " + str(item_a['itemId']))
            cols[0].text(item_a['name'])
            cols[0].text("Price: $" + str(item_a['salePrice']))
            cols[0].text("Reviews: " + str(item_a_numReviews))
            cols[0].image(item_a['mediumImage'], use_column_width=True)

            cols[1].subheader("Item id: " + str(item_b['itemId']))
            cols[1].text(item_b['name'])
            cols[1].text("Price: $" + str(item_b['salePrice']))
            cols[1].text("Reviews: " + str(item_b_numReviews))
            cols[1].image(item_b['mediumImage'], use_column_width=True)
        except Exception as e:
            continue


if __name__ == "__main__":
    run()
