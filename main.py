import json
from src.walmart_api import *


def save_result(res):
    out = dict()
    for key in res.keys():
        out[key] = res[key]

    with open('review_data.json', 'w') as outfile:
        json.dump(out, outfile)


if __name__ == '__main__':
    res = get_reviews(prod_id='561262765')
    # res = search_prod(prod='Shirt')
    print(res)

