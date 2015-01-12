# coding: utf-8
"""
Advanced search functions for Kata CKAN extension.
"""


def extract_search_params(data_dict):
    """
    Extracts parameters beginning with ``ext_`` from `data_dict['extras']`
    for advanced search.

    :param data_dict: contains all parameters from search.html
    :rtype: unordered lists extra_terms and extra_ops, dict extra_dates
    """
    extra_terms = []
    extra_ops = []
    extra_advanced_search = False
    # Extract parameters
    for (param, value) in data_dict['extras'].items():
        if len(value):
            # Extract search operators
            if param.startswith('ext_operator'):
                extra_ops.append((param, value))
            elif param.startswith('ext_advanced-search'):
                if value:
                    extra_advanced_search = True
            else:  # Extract search terms
                extra_terms.append((param, value))
    return extra_terms, extra_ops, extra_advanced_search


def parse_search_terms(c, data_dict, extra_terms, extra_ops):
    """
    Parse extra terms and operators into query q into data_dict:
    `data_dict['q']: ((author:*onstabl*) OR (title:*edliest jok* AND
    tags:*somekeyword*) OR (title:sometitle NOT tags:*otherkeyword*))`
    Note that all ANDs and NOTs are enclosed in parenthesis by ORs.
    Outer parenthesis are for date limits to work correctly.

    :param data_dict: full data_dict from package:search
    :param extra_terms: `[(ext_organization-2, u'someOrg'), ...]`
    :param extra_ops: `[(ext_operator-2, u'AND'), ...]`
    """
    def extras_cmp(a, b):
        a = a.split("-")[-1]
        b = b.split("-")[-1]
        if a <= b:
            if a < b:
                return -1
            else:
                return 0
        else:
            return 1

    extra_terms.sort(cmp=extras_cmp, key=lambda tpl: tpl[0])
    extra_ops.sort(cmp=extras_cmp, key=lambda tpl: tpl[0])
    c.current_search_rows = []
    # Handle first search term row
    (param, value) = extra_terms[0]
    p_no_index = param.split("-")[0]
    data_dict['q'] += ' ((%s:%s' % (p_no_index[4:], value)  # Add field search to query q
    c.current_search_rows.append({'field': p_no_index, 'text': value})

    n = min(len(extra_terms)-1, len(extra_ops))
    for i1 in range(0, n):
        (oparam, ovalue) = extra_ops[i1]
        (param, value) = extra_terms[i1+1]
        p_no_index = param.split("-")[0]
        if ovalue in ['AND', 'NOT']:
            data_dict['q'] += ' %s' % ovalue  # Add operator (AND / NOT)
            data_dict['q'] += ' %s:%s' % (p_no_index[4:], value)  # Add field search to query q
        elif ovalue == 'OR':
            data_dict['q'] += ') %s (' % ovalue  # Add operator OR
            data_dict['q'] += ' %s:%s' % (p_no_index[4:], value)  # Add field search to query q
        c.current_search_rows.append(
            {'field':p_no_index, 'text':value, 'operator':ovalue})
    data_dict['q'] += '))'


def constrain_by_temporal_coverage(c, extras):
    """
    Add temporal coverage constraint to Solr query if fields are given in extras

    -(-temporal_coverage_begin:[* TO 2100-01-01T00:00:00Z] AND temporal_coverage_begin:[* TO *]) AND
    -(-temporal_coverage_end:[1600-01-01T00:00:00Z TO *] AND temporal_coverage_end:[* TO *])
    --------------------------

    :param extras: data_dict['extras']
    :returns: Solr query that constrains by temporal coverage
    :rtype : str
    """
    START_FIELD = 'temporal_coverage_begin'
    END_FIELD = 'temporal_coverage_end'
    EXTRAS_START_FIELD = 'ext_' + START_FIELD
    EXTRAS_END_FIELD = 'ext_' + END_FIELD

    if not c.current_search_limiters:
        c.current_search_limiters = {}

    start_date = extras.get(EXTRAS_START_FIELD)
    end_date = extras.get(EXTRAS_END_FIELD)

    query = ''

    if start_date or end_date:
        if start_date:
            c.current_search_limiters[START_FIELD] = extras.pop(EXTRAS_START_FIELD)
        if end_date:
            c.current_search_limiters[END_FIELD] = extras.pop(EXTRAS_END_FIELD)

        start_date = start_date + '-01-01T00:00:00Z' if start_date else '*'
        end_date = end_date + '-12-31T23:59:59.999Z' if end_date else '*'

        query = ('-(-{sf}:[* TO {e}] AND {sf}:[* TO *]) AND '
                 '-(-{ef}:[{s} TO *] AND {ef}:[* TO *])').\
            format(s=start_date, e=end_date, sf=START_FIELD, ef=END_FIELD)

    return query

