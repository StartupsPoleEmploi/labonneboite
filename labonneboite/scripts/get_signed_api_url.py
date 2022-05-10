import collections
import datetime
import hashlib
import hmac
import os
import sys
from operator import itemgetter
from urllib import parse

import click

from typing import Dict, AnyStr, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from urllib.parse import SplitResult
else:
    SplitResult = any

ParseQuery = Dict[str, List[str]]

def parse_url(url: str) -> Tuple[SplitResult, ParseQuery]:
    parsed_url = parse.urlsplit(url)
    parsed_query = parse.parse_qs(parsed_url.query)
    return parsed_url, parsed_query

def pop_signature_from_query(query: ParseQuery):
    query.pop('signature', '')
    query.pop('timestamp', '')
    query.pop('user', '')

def add_signature_to_query(api_user: str, api_key: str, query: ParseQuery) -> ParseQuery:
    pop_signature_from_query(query)

    # E.g.: '2017-05-11T10:06:20'
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    # (alphabetical) order of parameters is important.
    params = collections.OrderedDict(sorted([
        *query.items(),
        ('timestamp', [timestamp]),
        ('user', [api_user]),
    ], key=itemgetter(0)))

    # URL encode ordered parameters.
    # E.g.: 'latitude=48.866667&longitude=2.333333&rome_codes=A1501&timestamp=2017-05-11T10%3A06%3A20&user=YOUR_API_USER'
    urlencoded_params_string = parse.urlencode(params, doseq=True)

    # Generate a signature with the md5 algo.
    signature = hmac.new(api_key.encode(), urlencoded_params_string.encode(), hashlib.md5).hexdigest()
    params['signature'] = [signature]

    return params

def encode_query(query: ParseQuery) -> str:
    encoded_query = parse.urlencode(query, doseq=True)
    return encoded_query

def get_url_for_split_url_and_encoded_query(parsed_url: SplitResult, encoded_query: str) -> str:
    new_split_url = parsed_url._replace(query=encoded_query)
    url = new_split_url.geturl()
    return url

def get_url_for_split_url_and_query(parsed_url: SplitResult, query: ParseQuery) -> str:
    encoded_query = encode_query(query)
    url = get_url_for_split_url_and_encoded_query(parsed_url, encoded_query)
    return url

@click.command()
@click.option('--api-user', help="Might be env var LBB_API_USER (default: labonneboite)", default='labonneboite')
@click.option('--api-key', help="Might be env var LBB_API_KEY (if unset the key will be ask)", prompt=True, hide_input=True)
@click.argument('url')
def get_url(api_user: str, api_key: str, url: str):
    """
    Generate an url with the signature for a given url, api user and api key

    url example: https://labonneboite.beta.pole-emploi.fr/api/v1/company/\?departments\=33\&rome_codes_keyword_search\=informatique
    """
    parsed_url, parsed_query = parse_url(url)
    
    query_with_signature = add_signature_to_query(api_user, api_key, parsed_query)
    
    url = get_url_for_split_url_and_query(parsed_url, query_with_signature)

    click.secho(url, fg="green")

if __name__ == '__main__':
    get_url(auto_envvar_prefix='LBB')
