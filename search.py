import re, time
from whoosh import index, sorting
from whoosh.qparser import MultifieldParser


def main(search_string):
    start = time.time()
    ix = index.open_dir('indices', indexname='lore')
    end = time.time()
    duration = end - start
    print('Index open: {0:.2f}s'.format(duration))

    # define the parser to search across the three key fields
    qp = MultifieldParser(['name', 'subtitle', 'description'], schema=ix.schema)

    print(search_string)
    # correct casing on search operators AND, NOT, and OR
    operators = ['and', 'not', 'or']
    for operator in operators:
        operator_search = re.compile('({0})'.format(operator), re.IGNORECASE)
        search_string = operator_search.sub('{0}'.format(operator.upper()), search_string)

    print(search_string) # debugging

    q = qp.parse(u'{0}'.format(search_string))
    print(q) # debugging

    count = 0
    start = time.time()
    with ix.searcher() as s:
        multi_sort = sorting.MultiFacet()
        multi_sort.add_field('source')
        multi_sort.add_field('name')
        hits = s.search(q, limit=None, sortedby=multi_sort, terms=True)

        results = []
        for hit in hits:
            #print(dict(hit))
            hit_matches = hit.matched_terms()

            result = hit.fields()

            for hit_match in hit_matches:
                #print(hit_match)
                hit_field = hit_match[0]
                hit_term = hit_match[1].decode('utf8')

                if hit_field != 'source':

                    term_search = re.compile('({0})'.format(hit_term), re.IGNORECASE)

                    # print('{0} - {1}'.format(hit_field, hit_term)) # debugging

                    result[hit_field] = term_search.sub('**\\1**', result[hit_field])

            results.append(result)
            # print('{0} - {1}'.format(hit['type'].title(), hit['name'])) # debugging
            count += 1
    end = time.time()
    duration = end - start
    print('Duration: {0:.2f}s'.format(duration))
    print('Count of results: {0}'.format(count))

    response = {
        'search': search_string,
        'query': str(q),
        'duration': '{0:.2f}s'.format(duration),
        'results': results
    }

    #print(response)
    return response

#main('"king\'s fall"')