import rdflib
from rdflib.graph import Graph as _Graph
from rdflib.namespace import Namespace, RDF, RDFS, XSD, ClosedNamespace
from rdflib.term import URIRef, Literal, BNode, Node

rdflib.plugin.register('sparql', rdflib.query.Processor,
                       'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result,
                       'rdfextras.sparql.query', 'SPARQLQueryResult')

DC = ClosedNamespace(uri="http://purl.org/dc/terms/",
                     terms=[
                            'abstract','accessRights','accrualMethod',
                            'accrualPeriodicity', 'accrualPolicy', 'alternative',
                            'audience', 'available','bibliographicCitation',
                            'conformsTo','contributor','coverage', 'created',
                            'creator','date', 'dateAccepted', 'dateCopyrighted',
                            'dateSubmitted', 'description', 'educationLevel',
                            'extent', 'format', 'hasFormat', 'hasPart',
                            'hasVersion', 'identifier', 'instructionalMethod',
                            'isFormatOf', 'isPartOf', 'isReferencedBy',
                            'isReplacedBy', 'isRequiredBy', 'issued',
                            'isVersionOf', 'language', 'license', 'mediator',
                            'medium', 'modified', 'provenance', 'publisher',
                            'references', 'relation', 'replaces', 'requires',
                            'rights', 'rightsHolder', 'source', 'spatial',
                            'subject', 'tableOfContents', 'temporal', 'title',
                            'type', 'valid'
                            ]
                     )
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCES = Namespace("http://purl.org/dc/elements/1.1/")
FOAF = ClosedNamespace(uri="http://xmlns.com/foaf/0.1/",
                       terms="""account , accountName , accountServiceHomepage , 
                              age , aimChatID , based_near , birthday , 
                              currentProject , depiction , depicts , 
                              dnaChecksum, familyName, family_name, firstName, focus , fundedBy , geekcode , gender , givenName , givenname , holdsAccount , homepage , icqChatID , img , interest , isPrimaryTopicOf , jabberID , knows , lastName , logo , made , maker , mbox , mbox_sha1sum , member , membershipClass , msnChatID , myersBriggs , name , nick , openid , page , pastProject , phone , plan , primaryTopic , publications , schoolHomepage , sha1 , skypeID , status , surname , theme , thumbnail , tipjar , title , topic , topic_interest , weblog , workInfoHomepage , workplaceHomepage , yahooChatID, Agent , Document , Group , Image , LabelProperty , OnlineAccount , OnlineChatAccount , OnlineEcommerceAccount , OnlineGamingAccount , Organization , Person , PersonalProfileDocument , Project""".split(' , '))
LICENSES = Namespace("http://purl.org/okfn/licenses/")
LOCAL = Namespace("http://opendatasearch.org/schema#")
OPMV = Namespace("http://purl.org/net/opmv/ns#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
REV = Namespace("http://purl.org/stuff/rev#")
SCOVO = Namespace("http://purl.org/NET/scovo#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
VOID = Namespace("http://rdfs.org/ns/void#")
UUID = Namespace("urn:uuid:")
TIME = Namespace("http://www.w3.org/2006/time#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

namespaces = {
    "rdf": RDF,
    "rdfs": RDFS,
    "owl": OWL,
    "dc": DC,
    "foaf": FOAF,
    "opmv": OPMV,
    "skos": SKOS,
    "time": TIME,
    "void": VOID,
    "dcat": DCAT,
    "vcard": VCARD,
    "local": LOCAL,
    "rev": REV,
    "scovo": SCOVO,
    "licenses": LICENSES
}

def bind_ns(g):
    """
    Given an :class:`~rdflib.graph.Graph`, bind the namespaces present in
    the dictionary in this module to it for more readable serialisations.

    :param g: an instance of :class:`rdflib.graph.Graph`.
    """
    try:
        [g.bind(*x) for x in namespaces.items()]
    except: 
        pass

from rdflib import plugin, exceptions, query
def __query(self, query_object, processor='sparql', result='sparql',
        initBindings={}):
    if not isinstance(processor, query.Processor):
        processor = plugin.get(processor, query.Processor)(self)
    if not isinstance(result, query.Result):
        result = plugin.get(result, query.Result)
    return result(processor.query(query_object, initBindings, namespaces))


def Graph(*a, **kw):
    _Graph.bound_query = __query
    graph = _Graph(*a, **kw)
    bind_ns(graph)
    return graph


