import elasticsearch


class ConnectionPool(object):
    ELASTICSEARCH_INSTANCE = None


def Elasticsearch():
    """
    Elasticsearch client singleton. All connections to ES should go through
    this client, so that we can reuse ES connections and not flood ES with new
    connections.
    """
    if ConnectionPool.ELASTICSEARCH_INSTANCE is None:
        ConnectionPool.ELASTICSEARCH_INSTANCE = elasticsearch.Elasticsearch()
    return ConnectionPool.ELASTICSEARCH_INSTANCE
