""" wrapper class for webui policies and events
"""
import calendar
import logging
import os
import platform as pf
import time
import json
import yaml
from json.decoder import JSONDecodeError
from pylclient.secrets.secret import Secret
from webapi import WebAPI
from webapi.auth import Authentication
from webapi.policy import RTPolicy, ConstraintsProfiles
from webapi.skopeit import SkopeIT
from webui_v2_apis.skopeit.skopeit import SkopeIT as SkopeIT2
from webapi.policy.dlp_profiles import DlpProfiles
from ..utils import policy_config as pc
from ..utils import constants
from pylclient.remoteexecute import remoteexecute_rpc as rexec

LOGGER = logging.getLogger(__name__)
event_details_common_tags = {'user', 'app', 'alert', 'activity', 'instance_id',
                             'from_user', 'object_type', 'action'}
event_details_file_tags = {'object', 'file_size', 'file_type'}
event_details_dlp_tags = {''}
PROXY_VAULT = "tests/connectortests/proxy_creds"

app_names_hippo = {
    "Google Gemini": "Google Bard",
    "Workday": "Workday Human Capital Management",
    "Webex by Cisco": "Cisco Webex Teams and Meet",
    "X (formerly Twitter)": "Twitter",
    "ShareFile": "Citrix ShareFile",
    "Workplace by Facebook": "Facebook at Work",
    "Atlassian Jira Software": "Atlassian - JIRA",
    "Amazon Relational Database Service": "Amazon RDS",
    "Amazon Lambda": "AWS Lambda",
    "GCP Storage": "Google Cloud Storage",
    "GCP Storage for Firebase": "Google Firebase Storage",
    "Google Accounts": "Google App Suite",
    "Atlassian Bitbucket": "Bitbucket",
    "Atlassian Accounts": "Atlassian App Suite",
    "Yahoo Accounts": "Yahoo App Suite",
    "Amazon Web Services Console": "Amazon Web Services",
    "YouTube": "Youtube",
    "LinkedIn": "Linkedin",
    "Microsoft Accounts": "Microsoft Office 365 Suite",
    "Microsoft Live Accounts": "Microsoft Live Suite",
    "Microsoft Live Outlook.com": "Microsoft Live Outlook",
    "Microsoft Office 365 Sharepoint Online": "Microsoft Office 365 Sharepoint Sites",
    "Microsoft Power BI": "Power BI",
    "Microsoft Viva Engage": "Yammer"
 }

def get_exp_non_dlp_event_details(test_details, app_details,
                                  file_details):
    """ initialising expected values from test, app and file details
        Parameters
        ----------
        test_details: test_details
        app_details: application details from app accounts yml file
        file details: file details from file info yml
    """
    if "ignore_tag" not in test_details.keys():
        test_details["ignore_tag"] = []
    exp_event = {
        'user': os.environ['NSUser'],
        'app': test_details["policy_data"]["app_name"],
        'alert': "yes" if test_details["policy_enabled"] else "no",
        'activity': test_details["policy_data"]["activities"],
        'from_user': app_details['from_user'] if app_details else None,
        'object_type': test_details['object_type'] if "object_type" in test_details else None,
        'action': test_details['policy_data']['action']['action_name'],
        'os': pf.system() + " " + pf.release(),
        'os_version': pf.system() + " " + pf.release(),
        'device': pf.system() + " Device"
    }
    if "instance_id" in app_details:
        exp_event['instance_id'] = app_details['instance_id'] if app_details else None
    if "Darwin" in pf.system():
        exp_event['os'] = "Catalina"
        exp_event['os_version'] = "Catalina"
        exp_event['device'] = "Mac Device"

    if "app_type" in test_details:
        if test_details["app_type"] == "iOS":
            exp_event.update({
                'os': "iOS",
                'os_version': "iOS",
                'device': ["iOS Device", "iPad"]
            })
            if os.environ['NSUser'] == str(None):
                exp_event.pop('user')

    update_file_details_in_expected_event(exp_event, file_details, test_details)
    try:
        if 'to_user' in test_details['test_method']['args']:
            exp_to = ""
            separator = ","
            if 'to_user_separator' in test_details['test_method']['args']:
                separator = test_details['test_method']['args']['to_user_separator']
            for usr in test_details['test_method']['args']['to_user']:
                exp_to = exp_to + usr + separator
            if separator == ",":
                exp_to = exp_to[:-1]
            exp_event.update({
                'to_user': exp_to
            })
    except KeyError:
        LOGGER.debug("args not present in test_method")
    if 'to_storage' in test_details['test_method']:
        exp_event.update({
            'to_storage': test_details['test_method']['to_storage']
        })
    if 'from_storage' in test_details['test_method']:
        exp_event.update({
            'from_storage': test_details['test_method']['from_storage']
        })
    return exp_event


def update_file_details_in_expected_event(exp_event, file_details, test_details):
    """ initialising expected values from test, app and file details
        Parameters
        ----------
        test_details: test_details
        exp_event: application details from app accounts yml file
        file_details: file details from file info yml
    """
    LOGGER.info("Finding if the object under test is file or message")
    file_object = True
    if file_details:
        if isinstance(file_details, list) and "message" in file_details[0].keys():
            file_object = False
        elif isinstance(file_details, dict) and "message" in file_details.keys():
            file_object = False

    LOGGER.info("Object under test is a %s", ('file' if file_object else 'message'))

    if file_details and exp_event["object_type"] == "File" and file_object:
        if "object" not in test_details["ignore_tag"]:
            exp_event.update({'object': file_details['name'] if isinstance(file_details, dict)
                                                             else [idx['name'] for idx in file_details]})
        if "file_size" not in test_details["ignore_tag"]:
            exp_event.update({'file_size': file_details['file_size'] if isinstance(file_details, dict)
                                                             else [idx['file_size'] for idx in file_details]})
        if "file_type" not in test_details["ignore_tag"]:
            exp_event.update({'file_type': file_details['file_type'] if isinstance(file_details, dict)
                                                             else [idx['file_type'] for idx in file_details]})
        if "md5" not in test_details["ignore_tag"]:
            exp_event.update({'md5': file_details['file_md5'] if isinstance(file_details, dict)
                                                             else [idx['file_md5'] for idx in file_details]})


def validate_event_details(events, test_details, app_details,
                           file_details):
    """validates the event details against exp values from test and app
            details.

        Parameters
        ----------
        events: events blob from webui api
        test_details : test_details, optional
            test details from test json (default is None)
        app_details : app_details, optional
            application account details from app yml file (default is None)
        file_details : file_details, optional
            file details from file_info yml file (default is None)
        Returns
        ------
        Boolean
            True if all details are matching false if not
    """
    exp_non_dlp_event_details = get_exp_non_dlp_event_details(
        test_details, app_details, file_details)

    is_detail_matching = True
    non_dlp_event = []
    dlp_event = []
    ignoretag = {}
    for event in events:
        if "justification_type" not in event.keys():
            if test_details["policy_data"]["action"]["action_name"] == "encrypt":
                non_dlp_event.append(event)
                dlp_event.append(event)
            else:
                if test_details['policy_enabled'] and event.get('alert_type', '') == 'DLP':
                    dlp_event.append(event)
                else:
                    non_dlp_event.append(event)
    print(json.dumps(non_dlp_event, indent=4))
    # updating md5 and file_size ignore tags for rar and zip files
    if file_details and not isinstance(file_details, list):
        if "name" in file_details:
            if ".rar" in file_details['name'].lower() or ".zip" in file_details['name']:
                test_details['ignore_tag'] = test_details.get("ignore_tag", [])
                test_details['ignore_tag'].extend(['md5', 'file_size', 'file_type'])
    if "ignore_tag" in test_details:
        ignoretag = set(test_details["ignore_tag"])
    # if missing_tags:   #kept for reference
    #     logging.error("missing keys in event tag::%s", missing_tags)
    #     if ignoretag != missing_tags:
    #         is_detail_matching = False
    check_for_tags = exp_non_dlp_event_details.keys()
    dlp_tags = {'dlp_profile', 'dlp_rule', 'dlp_rule_count', 'dlp_rule_severity'}
    try:
        check_for_tags = check_for_tags - ignoretag
        dlp_tags -= ignoretag
    except TypeError:
        pass

    LOGGER.info("Validating the attributes of Non-DLP events")
    is_detail_matching = validate_event_attributes(non_dlp_event, exp_non_dlp_event_details, check_for_tags)
    if not is_detail_matching:
        LOGGER.error("Non-DLP validation failed")
        return is_detail_matching

    if dlp_event:
        LOGGER.info("Validating the attributes of DLP events")
        dlp_flag_value = True
        if "dlp" in ignoretag:
            LOGGER.info("DLP validation is set to false via ignore_tag")
            dlp_flag_value = False
        is_detail_matching = validate_event_attributes(dlp_event, exp_non_dlp_event_details, check_for_tags,
                                                       file_info=file_details, dlp_flag=dlp_flag_value,
                                                       dlp_tags=dlp_tags)
        if not is_detail_matching:
            LOGGER.error("DLP validation failed")
    return is_detail_matching


def validate_event_attributes(event_list, expected_values, tags, file_info=None, dlp_flag=False, dlp_tags=None):
    """validates the event details against exp values from test and app
            details.

        Parameters
        ----------
        event_list: List of events
        expected_values : Expected value of attributes
        tags: Attributes to be checked
        file_info : DLP file info, optional (default is None)
        dlp_flag : Flag to indicate the type of event, optional (default is False)
        dlp_tags: Attributes related to DLP event

        Returns
        ------
        Boolean
            True if all details are matching false if not
    """
    LOGGER.debug(event_list)
    LOGGER.debug(expected_values)
    dlp_validation = True
    non_dlp_validation = True
    if not event_list:
        dlp_validation = False
        non_dlp_validation = False
    for event in event_list:
        for key in tags:
            if key == 'instance_id':
                event[key] = event[key].lower()
                expected_values[key] = expected_values[key].lower()
            if key == "os_version" and not constants.REVERSE_PROXY:
                event[key] = event[key].split()[0]+" "+ str(int(float(event[key].split()[-1])))
            if not compare_keys(event[key], expected_values[key]):
                msg = f"{key} is not matching in event details. exp value is " \
                        f"{expected_values[key]} and actual value is {event[key]}"
                LOGGER.error(msg)
                constants.message += "\n" + msg
                non_dlp_validation = False

    if dlp_flag:
        LOGGER.info("Verifying the DLP attributes")
        LOGGER.info("File attributes: \n%s", file_info)
        LOGGER.info("DLP Events: \n%s", event_list)

        LOGGER.info("Consolidate DLP events by capturing only the needed attributes before comparison")
        dlp_consolidated = consolidate_dlp_from_result(event_list, dlp_tags)
        file_data_consolidated = consolidate_file_info(file_info, dlp_tags)
        LOGGER.info(f"DLP Consolidated: {dlp_consolidated}, File Data Consolidated: {file_data_consolidated}")
        dlp_tags = {'dlp_profile'}
        for key in dlp_tags:
            if not compare_keys(dlp_consolidated[key], file_data_consolidated[key]):
                msg = f"{key} is not matching in event details. exp value is {file_data_consolidated[key]} and " \
                      f"actual value is {dlp_consolidated[key]}"
                LOGGER.error(msg)
                constants.message += "\n" + msg
                dlp_validation = False

    return dlp_validation and non_dlp_validation


def consolidate_dlp_from_result(dlp_event, dlp_tags):
    """ Consolidating the DLP information obtained from WebUI

            Parameters
            ----------
            dlp_event : list
            Events hit by the DLP rule

            dlp_tags : list
            List of attributes which are considered for comparison

            Returns
            ------
            Dictionary
                Consolidated result
    """
    dlp_consolidated = {attribute: [event[attribute] for event in dlp_event] for attribute in dlp_tags}
    dlp_consolidated["dlp_profile"] = list(set(dlp_consolidated["dlp_profile"]))
    return dlp_consolidated


def consolidate_file_info(file_details, dlp_tags):
    """ Consolidating the DLP information obtained from "files_info.yml"/"messages_info.yml" into a dictionary for
    further comparison

            Parameters
            ----------
            file_details : dictionary
            Information of message/file in the form of dictionary

            dlp_tags : list
            List of attributes which are considered for comparison

            Returns
            ------
            Dictionary
                Consolidated result
    """
    file_data_consolidated = {"dlp_profile": [], "dlp_rule": [], "dlp_rule_count": [], "dlp_rule_severity": []}
    if isinstance(file_details, list):
        for attribute in dlp_tags:
            for file_info in file_details:
                if attribute == "dlp_profile":
                    file_data_consolidated[attribute].append(file_info[attribute])
                else:
                    file_data_consolidated[attribute].extend(file_info[attribute])
        file_data_consolidated["dlp_profile"] = list(set(file_data_consolidated["dlp_profile"]))
    elif isinstance(file_details, dict):
        file_data_consolidated = {attribute: file_details[attribute] for attribute in dlp_tags}
        file_data_consolidated["dlp_profile"] = list(file_data_consolidated["dlp_profile"].split())

    return file_data_consolidated


def compare_keys(exp_value, actual_value):
    """ comparing two values by value or existing if its an array

            Parameters
            ----------
            exp_value : exp_value
                exp value for comparison
            actual_value : actual_value, optional
                Actual value for comparison

            Returns
            ------
            Boolean
                True if all details are matching false if not
    """
    is_matching = False
    try:
        if exp_value == actual_value:
            is_matching = True
        elif exp_value in actual_value:
            is_matching = True
        elif isinstance(exp_value, list):
            if exp_value[0] in actual_value:
                is_matching = True
        elif isinstance(actual_value[0], list):
            if any(exp_value in sublist for sublist in actual_value):
                is_matching = True
        elif sorted(exp_value) == sorted(actual_value):
            is_matching = True
    except TypeError as error:
        LOGGER.error("Exp Value %s, actual value %s, error:: %s", exp_value, actual_value, error)
    return is_matching


class WebUIWrapper:
    """WebuiWrapper class for policy and event manipulation"""

    def __init__(self, hostname, webui_credentials, variables):
        self.webapi = WebAPI(hostname=hostname, username=webui_credentials.get('username'),
                             password=webui_credentials.get('password'))
        self.auth = Authentication(self.webapi)
        self.user_policy_name_pre = ''.join(
            ''.join(
                e for e in os.environ['NSUser'].split('@')[0] if e.isalnum()))
        self.user_policy_name_fmt = self.user_policy_name_pre + "_policy_{}"
        self.user_policy_name = ""
        if "default" in variables:
            if not variables["default"]["profileuser"]:
                self.user_policy_name_fmt = variables["default"]["device_name"].replace(":", "_") + "_policy"
                os.environ['NSUser'] = str(None)
            else:
                self.user_policy_name_fmt = (variables["default"]["profileuser"].split("@")[0] + "_policy").replace(".", "")
                os.environ['NSUser'] = variables["default"]["profileuser"]
        proxy_dict = variables['proxy_creds']
        self.ip_addr = proxy_dict['proxy_ip']
        self.tid = proxy_dict['tenant_id']
        secret = Secret(PROXY_VAULT)
        self.proxy_credentials = secret.get(proxy_dict["account_name"])
        feature_flags = {'is_synthetic': variables['is_synthetic'], 'is_multiuser': variables['is_multiuser'],\
                         'fp_disable': variables['fp_disable']}
        self.feature_flags = feature_flags

    def wait_for_policy_push(self, policy_name):
        """
        Method to check the policy pushed to DB
        will return success if policy is pushed with in the configured time
        :return:
        """
        LOGGER.debug('Method : _waitforpolicypush ')
        tenantpath = "/opt/ns/tenant/{}/".format(self.tid)
        outputfilepath = tenantpath + policy_name + "_out.txt"
        decodedfilepath = tenantpath + policy_name + "decode"
        decode_cmd = " base64 -d {} > {}".format(tenantpath + "dp_user_info.db", decodedfilepath)
        dump_cmd = "sqlite3 {} .dump > {}".format(decodedfilepath, outputfilepath)
        search_cmd = " cat {} | grep {}".format(outputfilepath, policy_name)
        del_cmd = " rm {} {}".format(outputfilepath, decodedfilepath)
        status = False
        # t_end = time.time() + 60 * 3
        t_end = time.time() + 30
        LOGGER.debug(decode_cmd)
        LOGGER.debug(dump_cmd)
        LOGGER.debug(search_cmd)
        while not status:
            rexec.run(del_cmd, self.ip_addr, self.proxy_credentials['username'],
                      self.proxy_credentials['password'])
            rexec.run(decode_cmd, self.ip_addr, self.proxy_credentials['username'],
                                 self.proxy_credentials['password'])
            rexec.run(dump_cmd, self.ip_addr, self.proxy_credentials['username'],
                                 self.proxy_credentials['password'])
            response = rexec.run(search_cmd, self.ip_addr, self.proxy_credentials['username'],
                                 self.proxy_credentials['password'])
            LOGGER.info("Checking the policy {} in proxy {}".format(policy_name, self.ip_addr))
            LOGGER.info(response.result)
            if "rulename" in response.result and policy_name in response.result:
                LOGGER.info("Policy Pushed to DB")
                return True
            if time.time() > t_end:
                LOGGER.info("Policy is not reached Proxy: Exiting the TestCase")
                assert False
            time.sleep(2) #Sleeping for 2 seconds befoe checking again
        return status

    def _setproxylogs(self):
        '''
        Method to set the proxy logs
        :return:
        '''
        # pylint: disable=unused-variable
        LOGGER.debug('Method : _setproxylogs ')
        commandlog = 'sudo nswatson.sh -p 3214 -c "set log  tenantid {}" -c "set log level all 0 ' \
                     'cfg 1" '.format(self.tid)
        LOGGER.info("Set proxy logs")
        rexec.run(commandlog, self.ip_addr, self.proxy_credentials['username'],
                  self.proxy_credentials['password'])


    def _proxyrestart(self):
        '''
        Method to restart the proxy
        :return:
        '''
        # pylint: disable=unused-variable
        LOGGER.debug('Method : _proxyrestart ')
        restart_cmd = "sudo supervisorctl restart mtnsproxy"
        LOGGER.info("proxy restarting")
        rexec.run(restart_cmd, self.ip_addr, self.proxy_credentials['username'],
                  self.proxy_credentials['password'])
        time.sleep(160)


    def _clearredis_syntheticbrowser(self, username):
        '''
        Method to clear the redis for the user for synthetic testing
        :return:
        '''
        # pylint: disable=unused-variable
        redis_host = "redis01.hippo.local"
        LOGGER.debug('Method : _clearredis_syntheticbrowser ')
        symbol = '"$"'
        clear_cmd = "redis-cli keys '*{}*' | xargs -L1 -I '$' echo '{}' | xargs redis-cli DEL".format(username, symbol)
        LOGGER.info("Clearning redis  command : {}".format(clear_cmd))
        rexec.run(clear_cmd, redis_host, self.proxy_credentials['username'],
                  self.proxy_credentials['password'])

    def _clearredis_awskey(self):
        '''
        Method to clear the redis for the AWS key  for synthetic testing
        :return:
        '''
        # pylint: disable=unused-variable
        LOGGER.debug('Method : _clearredis_awskey')
        redis_host = "redis01.hippo.local"
        clear_cmd = "redis-cli keys '*nsproxy*:acces*:*{}*' | xargs redis-cli DEL".format(self.tid)
        LOGGER.info("Clearning redis  command : {}".format(clear_cmd))
        rexec.run(clear_cmd, redis_host, self.proxy_credentials['username'],
                  self.proxy_credentials['password'])



    def get_application_events(self, test_details, num_events=100):
        """ Returns list of application events """
        LOGGER.debug("Collecting application events within the given timerange")
        self.login_to_webapi()
        retry_count = 5

        events = list()
        for each_iteration in range(retry_count):
            query = 'policy eq {} and  user eq {}  and activity eq \'{}\''.format(
                test_details["policy_name"], os.environ["NSUser"],
                    "".join(test_details["policy_data"].get("activities", ["Browse"])))

            start_time = test_details["start_time"]
            if not test_details.get("end_time"):
                end_time = int(time.mktime(time.localtime())) + 60
            else:
                end_time = test_details["end_time"]

            LOGGER.debug("query to fetch the event ::: %s", query)
            skopeit_events = SkopeIT(self.webapi)
            result_key = "data"
            try:
                event_details = skopeit_events.get_alerts(
                    starttime=start_time, endtime=end_time, query=query,  limit=num_events)
            except Exception as err:
                if "This API has been deprecated" in str(err):  # If V1 API is deprecated using V2 API Calls.
                    skopeit_events = SkopeIT2(self.webapi)
                    event_details = skopeit_events.get_alerts(
                        starttime=start_time, endtime=end_time, query=query, limit=num_events)
                    result_key = "result"
                else:
                    raise
            if result_key in event_details and event_details[result_key]:
                events.extend(event_details[result_key])
                LOGGER.info("Events are fetched: %s" % len(events))
                break
            else:
                time.sleep(1)
                end_time += 1
        else:
            LOGGER.debug("No events are available")

        self.logout_from_webapi()
        return events

    def validate_event(self, test_details=None, app_details=None, file_details=None, loop_count=10):
        """validates the event details against exp values from test and app
        details.

            Parameters
            ----------
            test_details : test_details, optional
                test details from test json (default is None)
            app_details : app_details, optional
                application account details from app yml file (default is None)
            file_details : file_details, optional
                file details from file_info yml file (default is None)
            Returns
            ------
            Boolean
                True if all details are matching false if not
        """
        self.login_to_webapi()
        is_event_populated = False
        events = []
        if "proxy" in self.ip_addr and test_details["policy_data"]["app_name"] in app_names_hippo.keys():
            test_details["policy_data"]["app_name"] = app_names_hippo[test_details["policy_data"]["app_name"]]

        for iterator in range(loop_count):
            start_time = test_details['start_time']
            end_time = int(time.mktime(time.localtime())) + 60
            if self.feature_flags['is_multiuser']:
                query = 'user eq {} and activity eq \'{}\' and app eq \'{}\' and from_user eq \'{}\'' \
                    .format(os.environ["NSUser"],
                            "".join(test_details["policy_data"]["activities"]),
                            test_details["policy_data"]["app_name"], app_details['from_user'])
            else:
                query = 'user eq {} and activity eq \'{}\' and app eq \'{}\'' \
                    .format(os.environ["NSUser"],
                            "".join(test_details["policy_data"]["activities"]),
                            test_details["policy_data"]["app_name"])
                if test_details["policy_enabled"]:
                    query = query + " and policy eq {}".format(self.user_policy_name)

            if os.environ["NSUser"] == str(None):
                query = 'policy eq {} and activity eq \'{}\' and app eq \'{}\'' \
                    .format(self.user_policy_name,
                            "".join(test_details["policy_data"]["activities"]),
                            test_details["policy_data"]["app_name"])
            LOGGER.debug("query to fetch the event ::: %s", query)
            skopeit_events = SkopeIT(self.webapi)
            result_key = "data"
            if test_details['policy_enabled']:
                try:
                    event_details = skopeit_events.get_alerts(
                    starttime=start_time, endtime=end_time, query=query)
                except Exception as err:
                    if "This API has been deprecated" in str(err): # If V1 API is deprecated using V2 API Calls.
                        skopeit_events = SkopeIT2(self.webapi)
                        event_details = skopeit_events.get_alerts(
                            starttime=start_time, endtime=end_time, query=query)
                        result_key = "result"
                    else:
                        raise
            else:
                try:
                    test_details['ignore_tag'].append('file_type')
                except KeyError:
                    test_details['ignore_tag'] = ['file_type']
                try:
                    event_details = skopeit_events.get_events(starttime=start_time, endtime=end_time, query=query)
                except Exception as err:
                    if "This API has been deprecated" in str(err):  # If V1 API is deprecated using V2 API Calls.
                        skopeit_events = SkopeIT2(self.webapi)
                        event_details = skopeit_events.get_events(starttime=start_time, endtime=end_time, query=query)
                        result_key = "result"
                    else:
                        raise

            LOGGER.debug('Event details are ::: {}'.format(json.dumps(event_details, indent=2, sort_keys=True)))
            if result_key in event_details:
                if event_details[result_key]:
                    events = event_details[result_key]
                    is_event_populated = True
                    if isinstance(event_details[result_key], list):
                        for count, event in enumerate(event_details[result_key]):
                            if count < 6:
                                constants.message += "\n\n\n" + json.dumps(event, indent=4)
                    else:
                        constants.message += "\n\n\n" + json.dumps(event_details[result_key], indent=4)
                    break

            LOGGER.debug("event not found retrying. Iteration::%s", iterator + 1)
            time.sleep(3)

        test_details['start_time'] = int(time.mktime(time.localtime()))
        self.logout_from_webapi()

        if not is_event_populated:
            activity_found = self.failure_analysis_applicationevent(start_time, end_time, test_details, app_details, file_details)
            if not activity_found:
                # Activity is not in application events - test must fail
                # is_event_populated is already False, which will cause test to fail
                LOGGER.error(f"Activity {test_details['policy_data']['activities'][0]} is not in the application events. Test must fail.")
        if is_event_populated:
            is_event_populated = validate_event_details(events,
                                                        test_details,
                                                        app_details,
                                                        file_details)

        fp_status = self._check_fp_events(start_time, end_time, test_details)
        try:
            if "fp_disable" in test_details["ignore_tag"]:
                self.feature_flags['fp_disable'] = True
        except KeyError:
            pass

        if not self.feature_flags['fp_disable']:
            return is_event_populated and fp_status
        return is_event_populated

    def login_to_webapi(self):
        """
        Method to Login to webapi
        """
        # Before establishing tenant api session closing existing sessions
        try:
            self.logout_from_webapi()
        except Exception as err:
            LOGGER.error("logout error before login: {}".format(str(err)))

        retry_count = 3
        while retry_count >= 0:
            try:
                self.auth.login()
                break
            except (JSONDecodeError, AttributeError) as exp:
                LOGGER.debug(exp)
                break
            except Exception as err:
                LOGGER.error(err)
                retry_count -= 1
                time.sleep(60)
                LOGGER.info("Retrying for web api connection")
        else:
            raise "WebApi Connection failed after multiple retries"

    def logout_from_webapi(self):
        """
        Method to logout from the webapi.
        """
        try:
            self.auth.logout()
        except (JSONDecodeError, AttributeError) as exp:
            LOGGER.debug(exp)

    def failure_analysis_applicationevent(self,start_time,end_time,test_details,app_details,file_details):
        '''
        Do the analysis since Alert Event is not g
        '''
        if "proxy" in self.ip_addr and test_details["policy_data"]["app_name"] in app_names_hippo.keys():
            test_details["policy_data"]["app_name"] = app_names_hippo[test_details["policy_data"]["app_name"]]
        skopeit_events = SkopeIT(self.webapi)
        result_key = "data"
        query = 'user eq {}  and app eq \'{}\'' \
            .format(os.environ["NSUser"],
                    test_details["policy_data"]["app_name"])
        try:
            event_details = skopeit_events.get_events(starttime=start_time, endtime=end_time, query=query)
        except Exception as err:
            if "This API has been deprecated" in str(err):  # If V1 API is deprecated using V2 API Calls.
                skopeit_events = SkopeIT2(self.webapi)
                event_details = skopeit_events.get_events(starttime=start_time, endtime=end_time, query=query)
                result_key = "result"
            else:
                raise
        actual_json_blob_fp = event_details[result_key]
        for events in actual_json_blob_fp:
            if test_details['policy_data']['activities'][0] in events["activity"]:
                msg = "Activity {} is present in the application event, TC failed because  policy is not hit ".format(
                    test_details['policy_data']['activities'][0])
                LOGGER.info(msg)
                constants.message = "\n" + msg
                out = json.dumps(events, indent=4)
                LOGGER.info("Application Event disaplayed below")
                print(json.dumps(events, indent=4))
                return True
        msg =  f"Activity {test_details['policy_data']['activities'][0]} is not in the application events , potential Traffic change "
        constants.message += msg
        LOGGER.info(msg)
        return False

    def _check_fp_events(self, start_time, end_time, test_details):
        '''
        Method to check the FP events during the TC time frame
        '''
        if self.feature_flags['fp_disable']:
            return
        skopeit_events = SkopeIT(self.webapi)
        result_key = "data"
        query = 'user eq {}' \
            .format(os.environ["NSUser"])
        LOGGER.debug("looking for FP Events")
        try:
            event_details = skopeit_events.get_events(
                starttime=start_time, endtime=end_time, query=query)
        except Exception as err:
            if "This API has been deprecated" in str(err):  # If V1 API is deprecated using V2 API Calls.
                skopeit_events = SkopeIT2(self.webapi)
                event_details = skopeit_events.get_events(
                    starttime=start_time, endtime=end_time, query=query)
                result_key = "result"
            else:
                raise
        if event_details.get('status', '') == 'success' or event_details.get('ok') == '1':
            actual_json_blob_fp = event_details[result_key]
            dup_count = 0
            fp_count = 0
            for events in actual_json_blob_fp:
                if not "justification_type" in events:
                    if "web_universal_connector" in events or "universal_connector" in events:
                        LOGGER.info('Suspected FP events are ::: %s', json.dumps(events, indent=2, sort_keys=True))
                        if isinstance(events, list):
                            for count, event in enumerate(events):
                                if count < 2:
                                    constants.message += "\n\n" + json.dumps(event, indent=4)
                        else:
                            constants.message += "\n\n" + json.dumps(events, indent=4)
                        return False
                    if 'fp_check_skip' not in test_details.keys():
                        dup_count += self.duplicate_event_check(events, test_details)
                        fp_count += self.false_positive_event_check(events, test_details)
                    else:
                        if 'FP' not in test_details['fp_check_skip']:
                            fp_count += self.false_positive_event_check(events, test_details)
                        if 'DUP' not in test_details['fp_check_skip']:
                            dup_count += self.duplicate_event_check(events, test_details)
            if dup_count > 1:
                msg = "\nDuplicate event has been caught during validation."
                constants.message += msg
                return False
            if fp_count > 0:
                msg = "\nFalse positive event has been caught during validation."
                constants.message += msg
                return False
        return True

    def false_positive_event_check(self, events, test_details):
        """ Method to validate for false positive events
            Parameters
            ----------
            events: events detail
            test_details: test json
            -----------------------
            returns false positive events count
        """
        fp_event_count = 0
        if events['app'].lower() == (test_details['policy_data']['app_name']).lower():
            if (events['activity'].lower() != test_details['policy_data']['activities'][0].lower() and
                    events['activity'].lower() != 'view all' and events['activity'].lower() != 'view'):
                LOGGER.info('False Positive event detected are ::: %s',
                            json.dumps(events, indent=2, sort_keys=True))
                msg = "\nFP event has been caught during validation. Possible FP event is: " \
                      + events['activity']
                constants.message += msg
                fp_event_count += 1
        return fp_event_count

    def duplicate_event_check(self, events, test_details):
        """ Method to validate for duplicate events
            Parameters
            ----------
            events: events detail
            test_details: test json
            -----------------------
            returns duplicate events count
        """
        activity_count = 0
        if events['app'].lower() == (test_details['policy_data']['app_name']).lower():
            if (events['activity']).lower() == test_details['policy_data']['activities'][0].lower():
                if 'alert_type' in events.keys():
                    if (events['alert_type']).lower() != 'dlp':
                        activity_count += 1
                else:
                    activity_count += 1
        return activity_count

    def delete_policy(self, policy_name=None):
        """ returns the policy matching the name policy_name

            Parameters
            ----------
            policy_name : str, optional
            Name of the policy default value is none
            """
        if constants.NO_POLICY:
            return

        self.login_to_webapi()

        user_policy_name_pre_delete = ''.join(
            ''.join(
                e for e in os.environ['NSUser'].split('@')[0] if e.isalnum()))
        user_policy_name_for_delete = user_policy_name_pre_delete + "_policy"
        real_time_policy = RTPolicy(self.webapi, version=3.0)
        try:
            LOGGER.info("Deleting all policies in the tenant with name starting : "+user_policy_name_for_delete)
            policies = real_time_policy.get_policy()
            if policies.get("data"):
                for rdata in policies.get("data"):
                    if user_policy_name_for_delete in rdata["rule_name"]:
                        real_time_policy.delete_policy(rdata["rule_name"])
            real_time_policy.apply_config_changes()
        except Exception as err:
            if "Error while applying config changes" in str(err):
                time.sleep(30)
                real_time_policy.apply_config_changes()
            else:
                raise err




        self.logout_from_webapi()

    def get_policy(self, policy_name):
        """ returns the policy matching the name policy_name

            Parameters
            ----------
            policy_name : str
            Name of the policy

            Return
            ------
            Dict
                Policy details dictionary
            """
        self.login_to_webapi()
        real_time_policy = RTPolicy(self.webapi)
        policy_details = real_time_policy.get_policy_by_name(policy_name)
        self.logout_from_webapi()
        return policy_details

    def create_policy(self, test_details, app_account_details=None, policy_name=None):
        """
        :param test_details: test details for policy data
        :app_account_details : account details for instance and from_user data
        :param policy_name: optional policy name. if no name provided then name
        will be generated from environment variable NSUser
        :return:
        """
        if test_details == {}:
            return

        # Check and create required DLP profiles
        if "dlp_profile" in test_details.get("policy_data", {}):
            if "DLP_Message_Profile" == test_details["policy_data"]["dlp_profile"][0]:
                self.create_message_dlp_profile("DLP Message Rule", "DLP_Message_Profile")
            if "DLP_Message_Link_Profile" == test_details["policy_data"]["dlp_profile"][0]:
                self.create_message_dlp_profile("DLP Message Link Rule", "DLP_Message_Link_Profile")
        # test_details['start_time'] = int(time.mktime(time.localtime()))
        if self.feature_flags['is_synthetic']:
            self._clearredis_awskey()
            self._clearredis_syntheticbrowser(os.environ['NSUser'])
            time.sleep(5)
            self._proxyrestart()

        if not test_details['policy_enabled']:
            test_details['start_time'] = int(time.mktime(time.localtime()))
            LOGGER.info("Policy flag is disabled, policy creation is skipped.")
            return
        add_policy_post_data = pc.add_policy_post_data_template.copy()

        if not policy_name:
            self.user_policy_name = self.user_policy_name_fmt.format(str(calendar.timegm(time.gmtime())))
            policy_name = self.user_policy_name
            add_policy_post_data["name"] = policy_name

        add_policy_post_data["enabled"] = 1
        policy_dict = {
            'app': test_details["policy_data"]["app_name"],

            'action': test_details["policy_data"]["action"]
        }

        if "activities" in test_details["policy_data"]:
            test_details["policy_data"]["activity"] = ','.join(test_details["policy_data"]["activities"])


        add_policy_post_data["match_criteria_action"] = {}
        self.update_policy_action_data(policy_dict, add_policy_post_data)

        self.update_dlp_profile_policy_config(add_policy_post_data, policy_dict, test_details)

        self.update_file_type_size_policy_data(test_details, add_policy_post_data)

        if os.environ['NSUser'] != str(None):
            add_policy_post_data["users"] = [os.environ['NSUser']]

        self.login_to_webapi()

        real_time_policy = RTPolicy(self.webapi, version=3.0)
        if real_time_policy.get_policy_by_name(policy_name):
            LOGGER.info("Deleting policy which is already present")
            real_time_policy.delete_policy(policy_name)

        if app_account_details:
            self.update_user_constraint_profile(app_account_details, policy_dict, test_details, add_policy_post_data)
        else:
            self.update_app_activity_policy_config(add_policy_post_data, app_account_details, [],
                                                   policy_dict,
                                                   test_details)
        if "object_type" in test_details["policy_data"]:
            add_policy_post_data["object_type"]=test_details["policy_data"]["object_type"]

        if "instance" == test_details["policy_data"]["app_or_category"] or "category" == test_details["policy_data"]["app_or_category"]:
            add_policy_post_data.pop("apps")

        #updating policy configuration with policy group value 1 (Header group)
        add_policy_post_data["groupId"] = real_time_policy.get_group_id()

        LOGGER.debug("Creating policy with data %s", add_policy_post_data)
        try:
            real_time_policy.create_policy(policy_name, policy_hash=add_policy_post_data)
        except ConnectionError as err:
            LOGGER.error(str(err))
            time.sleep(25)
            real_time_policy.create_policy(policy_name, policy_hash=add_policy_post_data)
            real_time_policy.apply_config_changes()
        except Exception as err:
            if "Error while applying config changes" in str(err):
                time.sleep(30)
                LOGGER.error("Failed to apply config changes: %s" % str(err))
                real_time_policy.apply_config_changes()
            else:
                raise err

        # real_time_policy.rearrange_policy(name=policy_name, rpolicy="")
        if "goskope" in self.ip_addr:
            time.sleep(30)  # manual wait for policy push
        elif ("proxy11" or "proxy01" or "proxy04") in self.ip_addr:
            time.sleep(15)
        else:
            # temporarily suppressing exception. Need to fix and remove exception
            try:
                self.wait_for_policy_push(policy_name)
            except: pass
        user_policy_data = real_time_policy.get_policy_by_name(policy_name)
        test_details['start_time'] = int(time.mktime(time.localtime()))
        if user_policy_data:
            LOGGER.info("Policy created successfully with data:")
            LOGGER.info("Policy created at : " + str(test_details['start_time']))
            LOGGER.info(user_policy_data)
        else:
            LOGGER.error("Failed to create a policy")

        if constants.POPUP_VALIDATION:
            if "proxy" in self.ip_addr or ".stg." in self.ip_addr:
                if "block" == policy_dict['action']['action_name'] or "useralert" == policy_dict['action']['action_name']:
                    LOGGER.info("Disabling the NSClient agent")
                    os.system(r'"C:\\Program Files (x86)\\Netskope\\STAgent\\nsdiag.exe" -t disable')
                    LOGGER.info("Enabling the NSClient agent")
                    os.system(r'"C:\\Program Files (x86)\\Netskope\\STAgent\\nsdiag.exe" -t enable')
                    time.sleep(30)

        self.logout_from_webapi()

    def create_all_category_based_policy(self, test_details, app_account_details=None, policy_name=None):
        """ Creates a policy with All categories and given Activity.
        By default, Creates for Browse activity and Block Action.
        """
        LOGGER.debug("Adding policy with all categories")
        policy_template = pc.post_data_template_to_add_policy_with_all_categories.copy()
        if not policy_name:
            self.user_policy_name = self.user_policy_name_fmt.format(str(calendar.timegm(time.gmtime())))
            policy_name = self.user_policy_name
        policy_template["name"] = policy_name
        self.login_to_webapi()
        real_time_policy = RTPolicy(self.webapi, version=3.0)
        all_categories = real_time_policy.get_all_categories()
        all_categories = all_categories["data"]
        category_section = {
            "appCategory": "",
            "category": [],
            "activities": [
                {
                    "activity": "Browse",
                    "list_of_constraints": []
                }
            ]
        }
        categories_data_list = list()
        for each_category in all_categories:
            category_data = category_section.copy()
            category_data["appCategory"] = each_category.get("category_name")
            category_data["category"] = [each_category.get("category_id")]
            categories_data_list.append(category_data)

        policy_template["categories"] = categories_data_list
        policy_template["match_criteria_action"] = {
            "action_name": "block",
            "template": "block_page.html"
        }
        if os.environ['NSUser'] != str(None):
            policy_template["users"] = [os.environ['NSUser']]

        LOGGER.debug("Creating policy with data %s", policy_template)
        real_time_policy.create_policy(policy_name, policy_hash=policy_template)
        time.sleep(30)
        user_policy_data = real_time_policy.get_policy_by_name(policy_name)
        test_details['start_time'] = int(time.mktime(time.localtime()))
        if user_policy_data:
            LOGGER.info("Policy created successfully with data:")
            LOGGER.info("Policy created at : " + str(test_details['start_time']))
            LOGGER.info(user_policy_data)
        else:
            LOGGER.error("Failed to create a policy")
        self.logout_from_webapi()

    def delete_additional_policy(self):
        LOGGER.info("Deleting additional policies...")
        if constants.NO_POLICY:
            return
        real_time_policy = RTPolicy(self.webapi, version=3.0)
        count = 0
        while count < 10:
            policy_name = self.user_policy_name + "_" + str(count)
            if real_time_policy.get_policy_by_name(policy_name):
                real_time_policy.delete_policy(policy_name)
            count = count + 1
        real_time_policy.apply_config_changes()

    def create_additional_policy(self, test_details, app_account_details=None, policy_name=None):
        if test_details == {}:
            return
        #test_details['start_time'] = int(time.mktime(time.localtime()))
        if self.feature_flags['is_synthetic']:
            self._clearredis_awskey()
            self._clearredis_syntheticbrowser(os.environ['NSUser'])
            time.sleep(5)
            self._proxyrestart()

        if not test_details['policy_enabled']:
            LOGGER.info("Policy flag is disabled, policy creation is skipped.")
            return
        for index, policy_data in enumerate(test_details["additional_policy_data"]):
            add_policy_post_data = pc.add_policy_post_data_template.copy()

            policy_name = self.user_policy_name_fmt.format(str(calendar.timegm(time.gmtime()))) + "_" + str(index)
            add_policy_post_data["name"] = policy_name

            add_policy_post_data["enabled"] = 1
            if "rule_position" in policy_data:
                add_policy_post_data["position"] = policy_data["rule_position"]
            else:
                add_policy_post_data["position"] = "2"
            policy_dict = {
                'app': policy_data["app_name"],

                'action': policy_data["action"]
            }

            if "activities" in policy_data:
                policy_data["activity"] = ','.join(policy_data["activities"])

            add_policy_post_data["match_criteria_action"] = {}
            self.update_policy_action_data(policy_dict, add_policy_post_data)

            self.update_dlp_profile_policy_config_additional_data(add_policy_post_data, policy_dict, policy_data)

            self.update_file_type_size_policy_additional_data(policy_data, add_policy_post_data)

            if os.environ['NSUser'] != str(None):
                add_policy_post_data["users"] = [os.environ['NSUser']]

            self.login_to_webapi()

            real_time_policy = RTPolicy(self.webapi, version=3.0)
            if real_time_policy.get_policy_by_name(policy_name):
                LOGGER.info("Deleting policy which is already present")
                real_time_policy.delete_policy(policy_name)

            if app_account_details:
                self.update_user_constraint_additional_profile(app_account_details, policy_dict, test_details,
                                                               policy_data, add_policy_post_data, index)
            else:
                self.update_app_activity_additional_policy_config(add_policy_post_data, app_account_details, [],
                                                       policy_dict,
                                                       policy_data)
            if "object_type" in policy_data:
                add_policy_post_data["object_type"] = policy_data["object_type"]

            if "instance" == policy_data["app_or_category"] or "category" == policy_data["app_or_category"]:
                add_policy_post_data.pop("apps")

            add_policy_post_data["groupId"] = real_time_policy.get_group_id()

            LOGGER.debug("Creating policy with data %s", add_policy_post_data)
            try:
                real_time_policy.create_policy(policy_name, policy_hash=add_policy_post_data)
            except ConnectionError as err:
                LOGGER.error(str(err))
                time.sleep(25)
                real_time_policy.create_policy(policy_name, policy_hash=add_policy_post_data)
                real_time_policy.apply_config_changes()
            except Exception as err:
                if "Error while applying config changes" in str(err):
                    time.sleep(30)
                    LOGGER.error("Failed to apply config changes: %s" % str(err))
                    real_time_policy.apply_config_changes()
                else:
                    raise err
            if "goskope" in self.ip_addr:
                time.sleep(30)  # manual wait for policy push
            elif ("proxy11" or "proxy01" or "proxy04") in self.ip_addr:
                time.sleep(15)
            else:
                # temporarily suppressing exception. Need to fix and remove exception
                try:
                    self.wait_for_policy_push(policy_name)
                except:
                    pass
            user_policy_data = real_time_policy.get_policy_by_name(policy_name)
            test_details['start_time'] = int(time.mktime(time.localtime()))
            if user_policy_data:
                LOGGER.info("Policy created successfully with data:")
                LOGGER.info("Policy created at : " + str(test_details['start_time']))
                LOGGER.info(user_policy_data)
            else:
                LOGGER.error("Failed to create a policy")
            self.logout_from_webapi()

    def update_dlp_profile_policy_config_additional_data(self, add_policy_post_data, policy_dict, policy_data):
        """ updating policy data for dlp profile

            Parameters
            ----------
            test_details : dict
            add_policy_post_data : dict
            policy_dict
            Return
            ------
            None
        """
        LOGGER.debug("Adding DLP Profile config for policy : %s",self.user_policy_name)
        if "dlp_profile" in policy_data:
            del add_policy_post_data['match_criteria_action']
            if policy_dict["action"]['action_name'] == "block" or policy_dict["action"]['action_name'] == "useralert":
                add_policy_post_data['dlp_actions'] = [
                    {
                        "dlp_profile": policy_data["dlp_profile"][0],
                        "actions": [
                            {
                                "action_name": policy_dict['action']["action_name"],
                                "template": policy_dict['action']["template"]
                            }
                        ]
                    }
                ]
            else:
                add_policy_post_data['dlp_actions'] = [
                    {
                        "dlp_profile": policy_data["dlp_profile"][0],
                        "actions": [
                            {
                                "action_name": policy_dict['action']["action_name"]
                            }
                        ]
                    }
                ]
            add_policy_post_data['dlp_profile'] = policy_data["dlp_profile"]

    def update_file_type_size_policy_additional_data(self, policy_data, add_policy_post_data):
        """ updating policy data for file_size and file_type

            Parameters
            ----------
            test_details : dict
            add_policy_post_data : dict

            Return
            ------
            None
        """
        LOGGER.debug("Updating policy: %s for file size and file type", self.user_policy_name)
        if "file_size" in policy_data:
            add_policy_post_data["file_size"] = [
                {
                    "operator": policy_data["file_size"]["operator"],
                    "size": policy_data["file_size"]["size"],
                    "unit": policy_data["file_size"]["unit"]
                }
            ]
        if "file_types" in policy_data:
            if isinstance(policy_data["file_types"][0], str):
                add_policy_post_data["b_negate_file_types"] = "false"
                add_policy_post_data["file_types"] = policy_data["file_types"]
            elif isinstance(policy_data["file_types"][0], dict):
                add_policy_post_data["b_negate_filefilter_profiles"] = False
                categories = []
                for category in policy_data["file_types"][0]["categories"]:
                    categories.append(pc.file_filter_category[category])
                policy_data["file_types"][0]["categories"] = categories
                add_policy_post_data["filefilter_fileTypes"] = policy_data["file_types"][0]

    def update_user_constraint_additional_profile(self, app_account_details, policy_dict, test_details, policy_data,
                                                  add_policy_post_data, index):
        """ updating user costraint profile to policy configuration
            Parameters
            ----------
            app_account_details : contains app specific instance and from_user details
            policy_dict : dictionary code policy dict
            test_details : dictionary containing test json
            add_policy_post_data : policy payload json
            Return
            ------
            None
        """
        constraint_list = []
        if "list_of_constraints" in policy_data.keys() and policy_data["list_of_constraints"] is not None:
            if "from_user" in policy_data["list_of_constraints"]:
                if "app_type" in test_details:
                    if test_details["app_type"] == "iOS":
                        from_user_profile_name = add_policy_post_data["name"].split("_")[2] + "_{}_".format(index) + \
                                                 "from_user_profile"
                else:
                    from_user_profile_name = add_policy_post_data["name"].split("_")[0] + "_{}_".format(index) + \
                                             "from_user_profile"
                from_user_profile_id = self.create_user_constraint_profile(from_user_profile_name,
                                                                           [app_account_details["from_user"]])
                constraint_list.append({"constraints_type": "from_user",
                                        "constraints_profile": "{}".format(from_user_profile_id)
                                        })
            if "to_user" in policy_data["list_of_constraints"]:
                if "app_type" in test_details:
                    if test_details["app_type"] == "iOS":
                        to_user_profile_name = add_policy_post_data["name"].split("_")[2] + "_{}_".format(index) + \
                                               "to_user_profile"
                else:
                    to_user_profile_name = add_policy_post_data["name"].split("_")[0] + "_{}_".format(index) + \
                                           "to_user_profile"
                to_user_profile_id = self.create_user_constraint_profile(to_user_profile_name,
                                                                         test_details['test_method']['args']['to_user'])
                constraint_list.append({"constraints_type": "to_user",
                                        "constraints_profile": "{}".format(to_user_profile_id)
                                        })

        self.update_app_activity_additional_policy_config(add_policy_post_data, app_account_details, constraint_list,
                                                          policy_dict, policy_data)


    def update_app_activity_additional_policy_config(self, add_policy_post_data, app_account_details, constraint_list,
                                                     policy_dict, policy_data):
        """ updating user app and app-instance to policy configuration
            Parameters
            ----------
            app_account_details : contains app specific instance and from_user details
            policy_dict : dictionary code policy dict
            test_details : dictionary containing test json
            add_policy_post_data : policy payload json
            Return
            ------
            None
        """
        if "category" in policy_data["app_or_category"]:
            add_policy_post_data['categories'] = [
                {
                    "appCategory": pc.app_categories[policy_dict['app']]["category"],
                }
            ]
            add_policy_post_data['categories'][0]['category'] = pc.app_categories[policy_dict['app']]["id"],
            if "activity" in policy_data:
                add_policy_post_data["categories"][0]["activities"] = [
                    {
                        "activity": policy_data['activity'],
                        "list_of_constraints": constraint_list
                    }
                ]
        elif "app" in policy_data["app_or_category"]:
            add_policy_post_data['apps'] = [
                {
                    "appName": policy_dict['app'],
                }
            ]
            if "activity" in policy_data:
                add_policy_post_data["apps"][0]["activities"] = [
                            {
                                "activity": policy_data['activity'],
                                "list_of_constraints": constraint_list
                            }
                        ]
        elif "instance" in policy_data["app_or_category"]:
            self.create_app_instance({"appName": policy_dict["app"],
                                      "instanceName": self._remove_special_chars(policy_dict["app"]).lower() +
                                                      self._remove_special_chars(app_account_details["instance_id"]),
                                      "instanceId": app_account_details["instance_id"]})
            add_policy_post_data['appInstances'] = [
                {
                    "appInstanceName": policy_dict['app'],
                    "instanceName": self._remove_special_chars(policy_dict["app"]).lower() +
                                    self._remove_special_chars(app_account_details["instance_id"]),
                    "activities": [
                        {
                            "activity": policy_data['activity'],
                            "list_of_constraints": []
                        }
                    ]
                }
            ]
            add_policy_post_data["appInstances"][0]["activities"][0]["list_of_constraints"] = constraint_list

    def update_dlp_profile_policy_config(self, add_policy_post_data, policy_dict, test_details):
        """ updating policy data for dlp profile

            Parameters
            ----------
            test_details : dict
            add_policy_post_data : dict
            policy_dict
            Return
            ------
            None
        """
        LOGGER.debug("Adding DLP Profile config for policy : %s",self.user_policy_name)
        if "dlp_profile" in test_details["policy_data"]:

            del add_policy_post_data['match_criteria_action']
            if policy_dict["action"]['action_name'] == "block" or policy_dict["action"]['action_name'] == "useralert":
                add_policy_post_data['dlp_actions'] = [
                    {
                        "dlp_profile": test_details["policy_data"]["dlp_profile"][0],
                        "actions": [
                            {
                                "action_name": policy_dict['action']["action_name"],
                                "template": policy_dict['action']["template"]
                            }
                        ]
                    }
                ]
            else:
                add_policy_post_data['dlp_actions'] = [
                    {
                        "dlp_profile": test_details["policy_data"]["dlp_profile"][0],
                        "actions": [
                            {
                                "action_name": policy_dict['action']["action_name"]
                            }
                        ]
                    }
                ]
            add_policy_post_data['dlp_profile'] = test_details["policy_data"]["dlp_profile"]

    def update_user_constraint_profile(self, app_account_details, policy_dict, test_details, add_policy_post_data):
        """ updating user costraint profile to policy configuration
            Parameters
            ----------
            app_account_details : contains app specific instance and from_user details
            policy_dict : dictionary code policy dict
            test_details : dictionary containing test json
            add_policy_post_data : policy payload json
            Return
            ------
            None
        """
        constraint_list = []
        if "list_of_constraints" in test_details["policy_data"].keys() and \
            test_details["policy_data"]["list_of_constraints"] is not None:
            if "from_user" in test_details["policy_data"]["list_of_constraints"]:
                if "app_type" in test_details:
                    if test_details["app_type"] == "iOS":
                        from_user_profile_name = add_policy_post_data["name"].split("_")[2] + "_" + "from_user_profile"
                else:
                    from_user_profile_name = add_policy_post_data["name"].split("_")[0] + "_"+ add_policy_post_data["name"].split("_")[2] + "_" + "from_user_profile"
                from_user_profile_id = self.create_user_constraint_profile(from_user_profile_name,
                                                                           [app_account_details["from_user"]])
                constraint_list.append({"constraints_type": "from_user",
                                        "constraints_profile": "{}".format(from_user_profile_id)
                                        })
            if "to_user" in test_details["policy_data"]["list_of_constraints"]:
                if "app_type" in test_details:
                    if test_details["app_type"] == "iOS":
                        to_user_profile_name = add_policy_post_data["name"].split("_")[2] + "_" + "to_user_profile"
                else:
                    to_user_profile_name = add_policy_post_data["name"].split("_")[0] + "_"+ add_policy_post_data["name"].split("_")[2] + "_" + "to_user_profile"
                to_user_profile_id = self.create_user_constraint_profile(to_user_profile_name,
                                                                         test_details['test_method']['args']['to_user'])
                constraint_list.append({"constraints_type": "to_user",
                                        "constraints_profile": "{}".format(to_user_profile_id)
                                        })

        self.update_app_activity_policy_config(add_policy_post_data, app_account_details, constraint_list, policy_dict,
                                               test_details)


    def update_app_activity_policy_config(self, add_policy_post_data, app_account_details, constraint_list, policy_dict,
                                          test_details):
        """ updating user app and app-instance to policy configuration
            Parameters
            ----------
            app_account_details : contains app specific instance and from_user details
            policy_dict : dictionary code policy dict
            test_details : dictionary containing test json
            add_policy_post_data : policy payload json
            Return
            ------
            None
        """
        if "category" in test_details["policy_data"]["app_or_category"]:
            add_policy_post_data['categories'] = [
                {
                    "appCategory": pc.app_categories[policy_dict['app']]["category"],
                }
            ]
            add_policy_post_data['categories'][0]['category'] = pc.app_categories[policy_dict['app']]["id"],
            if "activity" in test_details["policy_data"]:
                add_policy_post_data["categories"][0]["activities"] = [
                    {
                        "activity": test_details["policy_data"]['activity'],
                        "list_of_constraints": constraint_list
                    }
                ]
        elif "app" in test_details["policy_data"]["app_or_category"]:
            add_policy_post_data['apps'] = [
                {
                    "appName": policy_dict['app'],
                }
            ]
            if "activity" in test_details["policy_data"]:
                add_policy_post_data["apps"][0]["activities"] = [
                            {
                                "activity": test_details["policy_data"]['activity'],
                                "list_of_constraints": constraint_list
                            }
                        ]
        elif "instance" in test_details["policy_data"]["app_or_category"]:
            self.create_app_instance({"appName": policy_dict["app"],
                                      "instanceName": self._remove_special_chars(policy_dict["app"]).lower() +
                                                      self._remove_special_chars(app_account_details["instance_id"]),
                                      "instanceId": app_account_details["instance_id"]})
            add_policy_post_data['appInstances'] = [
                {
                    "appInstanceName": policy_dict['app'],
                    "instanceName": self._remove_special_chars(policy_dict["app"]).lower() +
                                    self._remove_special_chars(app_account_details["instance_id"]),
                    "activities": [
                        {
                            "activity": test_details["policy_data"]['activity'],
                            "list_of_constraints": []
                        }
                    ]
                }
            ]
            add_policy_post_data["appInstances"][0]["activities"][0]["list_of_constraints"] = constraint_list

    def update_file_type_size_policy_data(self, test_details, add_policy_post_data):
        """ updating policy data for file_size and file_type

            Parameters
            ----------
            test_details : dict
            add_policy_post_data : dict

            Return
            ------
            None
        """
        LOGGER.debug("Updating policy: %s for file size and file type", self.user_policy_name)
        if "file_size" in test_details["policy_data"]:
            add_policy_post_data["file_size"] = [
                {
                    "operator": test_details["policy_data"]["file_size"]["operator"],
                    "size": test_details["policy_data"]["file_size"]["size"],
                    "unit": test_details["policy_data"]["file_size"]["unit"]
                }
            ]
        if "file_types" in test_details["policy_data"]:
            if isinstance(test_details["policy_data"]["file_types"][0], str):
                add_policy_post_data["b_negate_file_types"] = "false"
                add_policy_post_data["file_types"] = test_details["policy_data"]["file_types"]
            elif isinstance(test_details["policy_data"]["file_types"][0], dict):
                add_policy_post_data["b_negate_filefilter_profiles"] = False
                categories = []
                for category in test_details["policy_data"]["file_types"][0]["categories"]:
                    categories.append(pc.file_filter_category[category])
                test_details["policy_data"]["file_types"][0]["categories"] = categories
                add_policy_post_data["filefilter_fileTypes"] = test_details["policy_data"]["file_types"][0]

    def update_policy_action_data(self, policy_dict, add_policy_post_data):
        """ updating policy action details

            Parameters
            ----------
            policy_dict : dict
            add_policy_post_data : dict

            Return
            ------
            None
        """
        LOGGER.debug("Updating policy: %s for policy action data", self.user_policy_name)
        if policy_dict["action"]['action_name'] == "block":
            if "template" in policy_dict["action"]:
                template_map_value = self.get_popup_template_name("block", policy_dict["action"]['template'])
                del policy_dict["action"]
                policy_dict["action"] = {
                    "action_name": "block",
                    "template": template_map_value
                }
            else:
                del policy_dict["action"]
                policy_dict["action"] = {
                    "action_name": "block",
                    "template": "block_page.html"
                }
            add_policy_post_data["match_criteria_action"]["action_name"] = policy_dict['action']["action_name"]
            add_policy_post_data["match_criteria_action"]["template"] = policy_dict['action']["template"]

        elif policy_dict["action"]['action_name'] == "useralert":
            if "template" in policy_dict["action"]:
                template_map_value = self.get_popup_template_name("useralert", policy_dict["action"]['template'])
                del policy_dict["action"]
                policy_dict["action"] = {
                    "action_name": "useralert",
                    "template": template_map_value
                }
            else:
                del policy_dict["action"]
                policy_dict["action"] = {
                    "action_name": "useralert",
                    "template": "useralert_justify.html"
                }
            add_policy_post_data["match_criteria_action"]["action_name"] = policy_dict['action']["action_name"]
            add_policy_post_data["match_criteria_action"]["template"] = policy_dict['action']["template"]
        else:
            add_policy_post_data["match_criteria_action"]["action_name"] = policy_dict['action']["action_name"]

    def wait_until_policy_name_exists(self, ssh, policy_name, cmds):
        """ wait until policy name appears in decoded policy dump

            Parameters
            ----------
            ssh : object ssh session for proxy machine
            policy_name : str policy_name to search for
            cmds: list  commands array for dumping, decoding and searching policies

            Return
            ------
            bool
            returning policy exists or not
        """
        # pylint: disable=unused-variable
        LOGGER.debug("Searching for  policy: %s", self.user_policy_name)
        status = False
        t_end = time.time() + 60 * 5
        while not status:
            ssh.exec_command(cmds[0])
            ssh.exec_command(cmds[1])
            stdin, stdout, stderr = ssh.exec_command(cmds[2])
            out = stdout.readlines()
            LOGGER.debug("out_string: %s", out)
            LOGGER.debug("Searching for Policyname in DB")
            if out:
                for ele in out:
                    ele = ele.strip(" ").strip("\n")
                    LOGGER.debug(ele)
                    if "rulename" in ele and policy_name in ele:
                        LOGGER.info("Policy Name Found in DB")
                        status = True
                        break
            if time.time() > t_end:
                LOGGER.info("Time out reached breaking from loop")
                break
        return status

    def create_user_constraint_profile(self, profile_name=None, user_list=None):
        """ Create user constrain profile
            Parameters
            ----------
            profile_name : str profile name to search for
            user_list : list of user email to be included in constraint profile
            Return
            ------
            bool
            returning constraint profile id
        """
        constraint_list = []
        for user_email in user_list:
            constraint_list.append({"email_address": user_email, "negate": "false"})
        prof_hash = {"id": None, "name": profile_name,
                     "entries": constraint_list,
                     "variable": "user"}
        constraint_profile = ConstraintsProfiles(self.webapi)
        if constraint_profile.get_constraint_profile_by_name(profile_name):
            constraint_profile.delete_constraint_profile(profile_name)
            time.sleep(10)  # for constraint profile to sync
        constraint_profile.create_and_apply_profiles(name=profile_name, profile_hash=prof_hash)
        time.sleep(10)  # for constraint profile to sync
        return constraint_profile.get_constraint_profile_id(profile_name)

    def create_app_instance(self, instance_hash):
        """ Create application instance
            Parameters
            ----------
            instance_hash : dictionary to get instance details for app
            Return
            ------
            bool
            returning constraint profile id
            {"appName":"Google Gmail","instanceName":"sqaskope","instanceId":"sqaskope.com"}
        """
        skopeit = SkopeIT(self.webapi)
        try:
            if not(instance_hash['instanceId'], instance_hash['instanceName']) in \
                  skopeit.get_application_instances()["raw_data"]["data"][instance_hash["appName"]].items():
                skopeit.create_application_instance_from_hash(instance_hash)
        except KeyError:
            skopeit.create_application_instance_from_hash(instance_hash)

    @staticmethod
    def _remove_special_chars(app_name):
        '''
        remove special charecters from string
        :return: str
        '''
        return ''.join(char for char in app_name if char.isalnum())

    @staticmethod
    def get_popup_template_name(action, template_name):
        with open("config/environment/dynamic.local.yml") as tenant:
            tenant_data = yaml.full_load(tenant)
        tenant_name = tenant_data["webui_hostname"]
        with open("config/environment/popup_template_map.yml") as popup_template:
            popup_template_data = yaml.full_load(popup_template)
        try:
            return popup_template_data[tenant_name][action][template_name]
        except:
            LOGGER.error("Key not found")

    def handle_client_notification(self, test_info, app_account_details, data=None):
        """Handle client notification"""
        if (not test_info['policy_enabled']):
            uj_options = test_info['uj_options']
            if uj_options:
                if uj_options.lower() == "ok" or test_info['uj_options'].lower() == "cancel":
                    if test_info['assert_result']:
                        test_info['assert_result'] = False
                    else:
                        test_info['assert_result'] = True
            return
        else:
            from connector_tests_v2.common.utils import native_windows
            try:
                if not constants.POPUP_VALIDATION:
                    if str(test_info['uj_options']).lower() == "proceed":
                        if test_info['assert_result']:
                            test_info['assert_result'] = False
                        else:
                            test_info['assert_result'] = True
                else:
                    native_windows.handle_client_notification_templates(test_info["uj_options"])
            except AssertionError:
                if constants.POPUP_VALIDATION:
                    self.validate_event(test_info, app_account_details, file_details=data)
                    raise RuntimeError("Client pop up window not found")

    def create_message_dlp_profile(self, rule_name, profile_name):
        """Handle creation of  DLP Profile"""
        dlp_profile_page = DlpProfiles(self.webapi)
        if not dlp_profile_page.get_rule_id(rule_name):
            pc.message_dlp_rule_data["rule_name"] = rule_name
            response = dlp_profile_page.create_dlp_rule(pc.message_dlp_rule_data)
            dlp_profile_page.apply_pending_changes(feature="dlp")
            LOGGER.info(response)
        else:
            LOGGER.info("DLP Rule {} already present".format(rule_name))

        if not dlp_profile_page.get_dlp_profile(profile_name):
            response = dlp_profile_page.create_dlp_profile(profile_name,[dlp_profile_page.get_rule_id(rule_name)])
            dlp_profile_page.apply_pending_changes(feature="dlp")
            LOGGER.info(response)
        else:
            LOGGER.info("DLP Profile {} already present".format(profile_name))
