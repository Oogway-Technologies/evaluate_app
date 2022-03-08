from src.walmart_config import (KEY_VERSION, KEY_PATH, CONSUMER_ID)
from WIOpy import WalmartIO
import streamlit as st
glb_wiopy = WalmartIO(
        private_key_version=KEY_VERSION,
        private_key_filename=KEY_PATH,
        consumer_id=CONSUMER_ID)


def search_by_id(prod_id):
    data = glb_wiopy.product_lookup(prod_id)[0]
    return data


def search_prod(prod, sort='', order=''):
    if sort and order:
        data = glb_wiopy.search(prod, sort=sort, order=order)
        return data
    if sort:
        data = glb_wiopy.search(prod, sort=sort)
        return data
    if order:
        data = glb_wiopy.search(prod, order=order)
        return data
    data = glb_wiopy.search(prod)
    return data


def search_prod_in_category(prod, cat, sort='price', order='ascending'):
    data = glb_wiopy.search(prod, categoryId=cat, sort=sort, order=order)
    return data


def search_prod_and_filter(prod, prod_filter):
    # prod_filter example: 'brand:Samsung'
    data = glb_wiopy.search(prod, filter=prod_filter)


def get_recommendations(prod_id):
    data = glb_wiopy.product_recommendation(prod_id)
    return data
def get_reviews(prod_id,nextPage=''):
    # data = glb_wiopy.reviews(prod_id,**{'nextPage':nextPage})
    data = glb_wiopy.reviews(prod_id, nextPage=nextPage)

    return data

# def get_reviews(prod_id):
#     data = glb_wiopy.reviews(prod_id)
#     return data 
#   
# 
def split_categoryPath(categoryPath):
    categoryPath = categoryPath.replace(" ", "-")
    return categoryPath.split("/")


def get_all_reviews(prod_id,num_reviews=2):
    nextPage = "/reviews/"+prod_id+"?page=1"
    res = get_reviews(prod_id=prod_id,nextPage=nextPage)
    # st.write(res)
    categoryPath = res.categoryPath
    categoryPath = split_categoryPath(categoryPath)
    review_text = []
    for review in res.reviews:
        r = { 'reviewText':review["reviewText"],

                }
        review_text.append(r)    
    for i in range(1,num_reviews):
        try:
            if res.nextPage:
                print("nextPage",res.nextPage)
                res = get_reviews(prod_id=prod_id,nextPage=res.nextPage)
                # print(type((res.reviews[0])))
                
                # print(res.reviews[0]['reviewText'])
                for review in res.reviews:
                    print(type(review))
                    r = {
                        'reviewText':review["reviewText"]
                    }
                    review_text.append(r)
        except Exception as e:
            print(e)
    data = {

        'itemId':res.itemId,
        'name':res.name,
        'categoryPath':categoryPath,
        'reviews':review_text
    }
    return data


def get_taxonomy():
    data = glb_wiopy.taxonomy()
    return data


def get_trends():
    data = glb_wiopy.trending()
    return data
