# coding=utf-8
"""
Test data in unflattened package dictionary format.
"""

TEST_ORGANIZATION = {
    'title': u'Test Organization',
    'description': u'Description of an organization',
    'image_url': u'',
    'users': [{'capacity': 'admin', 'name': u'testsysadmin'}],
    'type': 'organization',
    'name': u'test-org'
}

TEST_ORGANIZATION_COMMON = {
    'title': u'Test Organization',
    'description': u'Description of an organization',
    'image_url': u'',
    'users': [
        {'capacity': 'admin', 'name': u'testsysadmin'},
        {'capacity': 'editor', 'name': u'tester'},
        {'capacity': 'member', 'name': u'joeadmin'}
    ],
    'type': 'organization',
    'name': u'test_org_common'
}

TEST_ORGANIZATION_SELENIUM = {
    'title': u'Kata Testing',
    'description': u'An organization for handling Kata\'s Selenium testing',
    'image_url': u'http://www.csc.fi/logo_en.gif',
    'users': [],
    'type': 'organization',
    'name': u'test_org_common'
}

TEST_RESOURCE = {'url': u'http://www.helsinki.fi',
                 'algorithm': u'SHA',
                 'format': u'CSV',
                 'hash': u'somehash',
                 'mimetype': u'application/csv',
                 'resource_type': 'file'}

TEST_DATADICT = {'access_application_new_form': u'False',
                 'accept-terms': u'yes',
                 'agent': [{'role': u'author',
                            'name': u'T. Tekijä',
                            'organisation': u'O-Org',
                            },
                           {'role': u'contributor',
                            'name': u'R. Runoilija',
                            'id': u'lhywrt8y08536tq3yq',
                            'organisation': u'Y-Yritys',
                            'URL': u'https://www.yyritys.kata.fi',
                            },
                           {'role': u'funder',
                            'name': u'R. Ahanen',
                            'organisation': u'CSC Oy',
                            'URL': u'http://www.csc.fi',
                            'fundingid': u'12345-ABCDE-$$$',
                            },
                           {'role': u'owner',
                            'organisation': u'CSC Oy',
                            'URL': u'http://www.csc.fi',
                            },
                           {'role': u'distributor',
                            'organisation': u'CSC Oy',
                            'URL': u'http://www.csc.fi',
                            },
                           {'role': u'contributor',
                            'name': u'A. Puri',
                            'organisation': u'CSC Oy',
                            }],

                 'algorithm': u'MD5',
                 'availability': u'direct_download',
                 'checksum': u'f60e586509d99944e2d62f31979a802f',
                 'contact': [{'name': u'Jali Jakelija',
                              'email': u'jali.jakelija@csc.fi',
                              'URL': u'http://www.tdata.fi',
                              'phone': u'05549583',
                              }],
                 'direct_download_URL': u'http://www.tdata.fi/kata',
                 'discipline': u'Tietojenkäsittely ja informaatiotieteet',
                 'format': u'CSV',
                 'geographic_coverage': u'Keilaniemi (populated place),Espoo (city)',
                 'langdis': 'False',
                 # 'langtitle': [
                 #     {'lang': u'fin', 'value': u'Test Data'},
                 #     {'lang': u'abk', 'value': u'Title 2'},
                 #     {'lang': u'swe', 'value': u'Title 3'},
                 #     {'lang': u'tlh', 'value': u'ᐼᑐᑤᑸᒌᒠᒴᓈᓜᓰᔄᔘᔬ'},
                 # ],
                 'language': u'eng, fin, swe',
                 'license_id': u'cc-by',
                 'license_URL': u'Not to be distributed outside the Milky Way galaxy',
                 'mimetype': u'application/csv',
                 'name': u'',
                 'langnotes': [
                    {'lang': u'fin', 'value': u'''This is a dataset used for testing Kata CKAN extension.
                    This is entirely fictional data and any resemblance to anything is purely coincidental.
                    No animals were harmed during this dataset creation.'''}
                 ],
                 'notes': u'',
                 'owner_org': '',
                 'event': [
                     {
                            u'when': u'2000-01-01',
                            u'who': u'T. Tekijä',
                            u'type': u'creation',
                            u'descr': u'Kerätty dataa'
                        },
                        {
                            u'when': u'2000-01-01',
                            u'who': u'J. Julkaisija',
                            u'type': u'published',
                            u'descr': u'Alustava julkaisu'
                        },
                        {
                            u'type': u'modified',
                            u'who': u'M. Muokkaaja',
                            u'when': u'2013-11-18',
                            u'descr': u'Lisätty dataa'
                        },
                 ],
                 'pids': [
                     {
                         'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_data_pid',
                         'type': u'data',
                     },
                     {
                         'provider': u'kata',
                         'id': u'urn:nbn:fi:csc-kata20140728095757755621',
                         'type': u'data',
                         'primary': u'True',
                     },
                     {
                         'provider': u'kata',
                         'id': u'kata_metadata_PID',
                         'type': u'metadata',
                     },
                     {
                         'provider': u'kata',
                         'id': u'kata_version_PID',
                         'type': u'version',
                     },
                 ],
                 'tag_string': u'Python,ohjelmoitunut solukuolema,programming',
                 'temporal_coverage_begin': u'2003-07-10T06:36:27-12:00',
                 'temporal_coverage_end': u'2010-04-15T03:24:47+12:45',
                 'title': u'{"fin": "Test Data", "abk": "Title 2", "swe": "Title 3", "tlh": "ᐼᑐᑤᑸᒌᒠᒴᓈᓜᓰᔄᔘᔬ"}',
                 'type': u'dataset',
                 'version': u'2013-11-18T12:25:53Z',
                 'private': False,  # Use Python boolean or fix _compare_datadicts() in tests to support 'True' == True
                 'xpaths': {
                     'xpath/path1': u'xpath_value',
                     'xpath/path2': u'xpath_value2',
                 },
                 }
