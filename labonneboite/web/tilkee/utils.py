import os

import requests

from labonneboite.conf import settings


TILKEE_HTTP_TIMEOUT_SECONDS = 20
AWS_HTTP_TIMEOUT_SECONDS = 40

# FIXME duplicate code from tilkee.js
ALLOWED_FILE_EXTENSIONS = (
    '.doc',
    '.docx',
    '.jpeg',
    '.jpg',
    '.mov',
    '.mp4',
    '.pdf',
    '.png',
)


def process(files, company, user):
    """
    Create a Tilkee project with the user files.

    Return: an HTTP url that points to the user project on Tilkee.
    """
    # 1. Upload files
    document_s3_urls = [upload_file(fobj) for fobj in files]

    # 2. Create Tilkee project https://tilkee.readme.io/docs/wrapper
    # Note: we added 'v2' prefix to address upstream 500 errors
    documents = [{
        'name': fobj.filename,
        's3_url': s3_url,
        'signable': False,
        'downloadable': True,
    } for fobj, s3_url in zip(files, document_s3_urls)]
    response = post('/v2/wrapper/token_from_files', json={
        'project': {
            'name': u'{} / {}'.format(company.name, company.siret)
        },
        'person': {
            # The user ID will be used to find the project among existing
            # Tilkee projects. It's an anonymous data.
            'name': 'user-{}'.format(user.id)
        },
        'documents': documents
    }).json()
    project_url = response['token']['link']
    project_id = response['project']['id']

    # 3. Notify Tilkee to associate user email address to project
    # (undocumented feature)
    post('/v2/notifications', json={
        'company_id': settings.TILKEE_COMPANY_ID,
        'project_id': project_id,
        'rule': 'connexion_ended',
        'url': user.email,
        'custom_output': 'pole_emploi_lbb',
        'target': 'Email',
    })

    return project_url


def upload_file(fobj):
    """
    Upload a file to Tilkee's S3 bucket.

    Return: an HTTP url that points to the user file.
    """
    # Get upload url
    # https://tilkee.readme.io/docs/what-is-it-3
    response = get('/direct_upload_data/').json()
    upload_url = response['s3_endpoint']
    key = response['key'].replace('${filename}', fobj.filename)
    data = {
        'key': key,
        'acl': 'public-read',
        'policy': response['policy'],
        'Signature': response['signature'],
        'AWSAccessKeyId': response['AWSAccessKeyId'],
        'success_action_status': '201',
    }

    # Upload file to S3
    try:
        response = requests.post(upload_url, data=data, files={'file': fobj},
                                 timeout=AWS_HTTP_TIMEOUT_SECONDS)
    except requests.ReadTimeout:
        fobj.seek(0, 2) # seek to end of file
        file_size_megabytes = fobj.tell() / (1024*1024.)
        message = u'AWS upload timeout: filesize={} Mb"'.format(file_size_megabytes)
        raise TilkeeError(message)

    if response.status_code != 201:
        message = u'Upload failed: data={data} status={response.status_code} content="{response.content}"'.format(
            data=data, response=response
        )
        raise TilkeeError(message)

    return upload_url + '/' + key


def get(endpoint, **kwargs):
    return request(endpoint, 'GET', **kwargs)


def post(endpoint, **kwargs):
    return request(endpoint, 'POST', **kwargs)


def request(endpoint, method, **kwargs):
    """
    HTTP request with proper error catching.

    Args:
        endpoint (str): endpoint from the Tilkee API
        method: 'GET' or 'POST'
        kwargs: additional arguments to be passed to requests

    Return: a Response object for which 200 <= status_code < 400.
    """
    func = {
        'GET': requests.get,
        'POST': requests.post,
    }[method]

    url = settings.TILKEE_API_BASE_URL + endpoint
    headers = {
        'Authorization': 'Bearer {}'.format(settings.TILKEE_ACCESS_TOKEN),
        'x-tilk-ref': settings.TILKEE_X_REF,
        'Content-Type': 'application/json',
    }
    try:
        response = func(url, headers=headers, verify=settings.TILKEE_VERIFY_SSL,
                        timeout=TILKEE_HTTP_TIMEOUT_SECONDS, **kwargs)
    except requests.ReadTimeout:
        message = 'HTTP timeout url={url} method={method}'.format(
            url=url, method=method
        )
        raise TilkeeError(message)

    if response.status_code >= 400:
        message = 'HTTP error url={url} method={method} status={response.status_code} content="{response.content}"'.format(
            url=url, method=method, response=response
        )
        raise TilkeeError(message)

    return response


def is_allowed(filename):
    """
    Check whether a filename is supported by Tilkee.
    """
    return os.path.splitext(filename).lower() in ALLOWED_FILE_EXTENSIONS


class TilkeeError(Exception):
    pass
