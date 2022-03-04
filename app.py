import json
import streamlit as st
from src.walmart_api import *
from src.service import get_aspects, collect_aspects,get_similar_clusters

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




st.button('Restart', on_click=clear_state)


def average_list(lst):
    if len(lst) == 0:
        return 0.0
    return sum(lst) / len(lst)


def run_compare():
    global item_1
    global item_2

    # Input aspects
    st.markdown('Specify comma-separated aspects to compare')
    aspects = st.text_input("Aspects: ", key="aspects")
    if aspects:
        # Get reviews for the two products
        item_1_rev = get_all_reviews(item_1,20)
        # st.write(item_1_rev)
        item_2_rev = get_all_reviews(item_2,20)

        # Run the API on the reviews and aspects
        aspects = [asp.strip() for asp in aspects.split(',')]
        st.write("Getting Product 1 Aspects")
        aspects_item_1 = get_aspects(item_1_rev, aspects)
        st.write("Getting Product 2 Aspects")
        aspects_item_2 = get_aspects(item_2_rev, aspects)
        
        selected_pair = get_similar_clusters(list(aspects_item_1.keys()),list(aspects_item_2.keys()))
        st.write("Common Aspects")
        st.write(selected_pair)
        # aspects_item_1 = collect_aspects(aspects_item_1, aspects)
        # aspects_item_2 = collect_aspects(aspects_item_2, aspects)

        # for i in range(0, len(aspects)):
        #     cols = st.columns(2)
        #     cols[0].subheader("Aspect: " + aspects[i])
        #     single_aspect_1 = aspects_item_1[aspects[i]]
        #     attr_list_1 = single_aspect_1["attribute"]
        #     perc_1 = average_list(single_aspect_1["perc"])
        #     cols[0].text(", ".join(attr_list_1))
        #     cols[0].markdown('Rating: ' + str(perc_1))

        #     cols[1].subheader("Aspect: " + aspects[i])
        #     single_aspect_2 = aspects_item_2[aspects[i]]
        #     attr_list_2 = single_aspect_2["attribute"]
        #     perc_2 = average_list(single_aspect_2["perc"])
        #     cols[1].text(", ".join(attr_list_2))
        #     cols[1].markdown('Rating: ' + str(perc_2))


def run():
    global prod
    if not input_prod:
        return
    if item_1 and item_2:
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
