""" module to handle http archive files actions"""
import hashlib
import json
import logging
import os

from json.decoder import JSONDecodeError

import requests

LOGGER = logging.getLogger(__name__)


def get_req_hash_code(time_stamp, method, url):
    """
    generating request id using time stamp, method name and url
    time_stamp: string
    method: string
    url: string
    """
    return hashlib.md5(hashlib.md5(str(time_stamp).encode('utf-8')).digest()
                + hashlib.md5(str(method).encode('utf-8')).digest()
                + hashlib.md5(str(url).encode('utf-8')).digest()).hexdigest()


def har_to_json_obj(har_file_abs_path):
    """
    reading har file and storing in json file
    har_file_abs_path: string path to har file
    """
    har_json_obj = None
    try:
        with open(har_file_abs_path, encoding='utf-8') as f:
            har_json_obj = json.load(f)
    except JSONDecodeError:
        with open(har_file_abs_path, encoding='utf-8-sig') as f:
            har_json_obj = json.load(f)
    except FileNotFoundError:
        LOGGER.error("%s file not found", har_file_abs_path)

    return har_json_obj


class HARWrapper():
    """
    class to upload and download files to MinIO Server.
    """
    session_object = None
    har_file_path = None

    def __init__(self, har_file_path):
        self.har_file_path = har_file_path

    def replay_har_content(self):
        """ method to replay har content"""
        request_objects = self.read_har_file_requests()
        if not request_objects:
            return
        for request_object in request_objects:
            response = None
            http_method = request_object['method'].lower()
            req_url = request_object['url'].replace("https", "http")
            req_hdrs = request_object['headers']
            req_date = request_object['data']
            req_params = request_object['params']
            try:
                session_object = requests.Session()
                if http_method == "connect":
                    continue
                response = getattr(session_object, http_method) \
                    (url=req_url, headers=req_hdrs, data=req_date, params=req_params, verify=False)

                server = "not_mock_server"
                if 'x-is-mock-server' in response.headers:
                    server = "mock_server"
                else:
                    LOGGER.debug('Chekc this')

                LOGGER.info("%s | %s | %s", server, str(response.status_code), request_object['url'])

            except Exception as exp:  # pylint: disable=broad-except
                LOGGER.error("%s ::Exception %s", request_object['url'], exp)

    def read_har_file_requests(self):
        """ method to read har files"""
        request_objects = []
        har_file_abs_path = os.path.abspath(self.har_file_path)
        har_json_obj = har_to_json_obj(har_file_abs_path)
        file_name = os.path.basename(har_file_abs_path)

        for entry in har_json_obj['log']['entries']:
            request_info = {}
            packet_request = entry['request']
            method = packet_request['method']
            url = packet_request['url']
            params = None
            data = None

            request_id = get_req_hash_code(entry['startedDateTime'], method, url)

            if 'postData' in packet_request:
                if 'text' in packet_request['postData']:
                    data = str(packet_request['postData']['text']).encode('utf-8')
                elif 'params' in packet_request['postData']:
                    params = {}
                    for param in packet_request['postData']['params']:
                        if not param['name']:
                            data = str(param['value']).encode('utf-8')
                        else:
                            params[str(param['name']).encode('utf-8')] = str(param['value']).encode('utf-8')
            data = data or None
            headers = dict(
                (d['name'], d['value']) for d in packet_request['headers'])
            headers['requestid'] = request_id
            headers['harfile'] = file_name
            if "Content-Length" in headers:
                headers.pop("Content-Length")

            request_info['method'] = method
            request_info['url'] = url
            request_info['headers'] = headers if headers else None
            request_info['data'] = data if data else None
            request_info['params'] = params if params else []
            request_objects.append(request_info)

        return request_objects
