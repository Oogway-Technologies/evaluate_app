import enum
import json
import streamlit as st
from src.walmart_api import *
from src.service import get_aspects,get_similar_clusters,get_review_list,get_pro_con
from utils import print_pros,print_cons,print_aspects,list_to_text,get_summaries,print_summaries
DEV_MODE = False


def clear_state():
    st.session_state["prod"] = ""
    st.session_state["item_1"] = ""
    st.session_state["item_2"] = ""


# App title
st.title("Evaluate")

# Search bar is always at the top of the page after the title
input_prod = st.text_input("Search:", key="prod")

st.markdown("Select two items to compare")
item_1 = st.text_input("First item id: ", key="item_1")
item_2 = st.text_input("Second item id: ", key="item_2")
prod = None

st.subheader('Select comparison features:')
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
    item_1_rev = get_all_reviews(item_1,2)
    # st.write(item_1_rev)
    item_2_rev = get_all_reviews(item_2,2)

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
    if not input_prod:
        return
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
    elif not prod:
        prod = search_prod(prod=input_prod)

    if not prod:
        return

    st.markdown('Total results: 10 of ' + str(prod['totalResults']))

    for i in range(0, 5):
        item_a = prod['items'][2*i]
        item_b = prod['items'][2*i+1]
        cols = st.columns(2)

        cols[0].subheader("Item id: " + str(item_a['itemId']))
        cols[0].text(item_a['name'])
        cols[0].text("Price: $" + str(item_a['salePrice']))
        cols[0].image(item_a['mediumImage'], use_column_width=True)

        cols[1].subheader("Item id: " + str(item_b['itemId']))
        cols[1].text(item_b['name'])
        cols[1].text("Price: $" + str(item_b['salePrice']))
        cols[1].image(item_b['mediumImage'], use_column_width=True)


if __name__ == "__main__":
    run()
