"""
Interaction with the Docker Registry

Imported from https://github.com/jupyterhub/binderhub/blob/055a33df308d450bddf2f1bfa6007b8b0ef537b8/binderhub/registry.py
"""
import base64
import json
import os
import requests
import requests.auth
from urllib.parse import urlparse

def parse_www_authenticate(www_authenticate):
    """
    Bad, partial parser for www-authenticate responses

    Bad and insecure code. Someone should read the HTTP spec
    and replace this with something legit.
    """
    parsed = {}
    # Strip out first word
    www_authenticate = ' '.join(www_authenticate.split(' ')[1:])
    # FIXME: If the content contains a ,, this is so fucked!
    parts = www_authenticate.split(',')
    for p in parts:
        k, v = p.split('=')
        parsed[k] = v.strip('"')
    return parsed



def get_image_manifest(registry, image, tag):
    """
    Fetch image manifest from a docker v2 registry.

    No authentication supported yet.
    """
    manifest_url = '{}/v2/{}/manifests/{}'.format(registry, image, tag)
    resp = requests.get(manifest_url)

    if resp.status_code == 401:
        # We need to grab a token
        # Info for where to grab it is in the WWW-Authenticate header
        www_authenticate = parse_www_authenticate(resp.headers.get('Www-Authenticate'))

        auth_resp = requests.get(
            www_authenticate.pop('realm'),
            params=www_authenticate,
        )

        token = auth_resp.json()['token']

        resp = requests.get(
            '{}/v2/{}/manifests/{}'.format(registry, image, tag),
            headers={'Authorization': 'Bearer {}'.format(token)},
        )

        if resp.status_code == 404:
            # 404 means it doesn't exist
            return None
        return resp.json()
    elif resp.status_code == 200:
        return resp.json()
    else:
        resp.raise_for_status()
