import argparse
import csv
import json
import os
import yaml


def extract_data_from_precondition(precondition, activity):
    DLP = "NON_DLP"
    DLP_type = False
    file_size = False
    file_type = False
    uj_options = "ok"
    action = "block"
    policy_type = "app"
    list_of_constraints = ["from_user"]
    out = dict()

    precondition = precondition.replace(" ", "").lower()
    if "useralert" in precondition:
        action = "useralert"
        if "proceed" in precondition:
            uj_options = "proceed"
        else:
            uj_options = "cancel"
    elif "alert" in precondition:
        action = "alert"
        uj_options = False
    if "instance" in precondition:
        policy_type = "instance"

    if "touser" in precondition:
        list_of_constraints.append("to_user")

    if "nondlp" not in precondition or "dlp" not in precondition:
        DLP = "DLP"
        if "pii" in precondition:
            DLP_type = "PII"
        elif "pci" in precondition:
            DLP_type = "PCI"
        elif "phi" in precondition:
            DLP_type = "PHI"
        elif "profanity" in precondition:
            DLP_type = "Profanity"
        elif "sourcecode" in precondition:
            DLP_type = "Sourcecode"
        else:
            pass
    if "upload" in activity.lower() or "download" in activity.lower():
        if "large" in precondition.lower():
            file_size = "large"
        elif "medium" in precondition.lower():
            file_size = "medium"
        else:
            file_size = "small"

        if "csv" in precondition:
            file_type = "csv"
        elif "document" in precondition:
            file_type = "documents"
        elif "xlsx" in precondition:
            file_type = "xlsx"
        elif "zip" in precondition:
            file_type = "zip"
        elif "ppt" in precondition:
            file_type = "pptx"
        elif "mdb" in precondition:
            file_type = "mdb"
        elif "docx" in precondition:
            file_type = "docx"
        elif "image" in precondition:
            file_type = "image"
        elif "audio" in precondition:
            file_type = "audio"
        elif "video" in precondition:
            file_type = "video"
        elif "pdf" in precondition:
            file_type = "pdf"
        elif "xml" in precondition:
            file_type = "xml"
        elif "rar" in precondition:
            file_type = "rar"
        elif "sql" in precondition:
            file_type = "sql"
        else:
            file_type = "documents"

        if DLP_type:
            file_name = DLP.lower() + "_" + DLP_type.lower() + "_" + file_size + "_" + file_type
        else:
            file_name = DLP.lower() + "_" + file_size + "_" + file_type

        FILE_INFO_YML = "testdata/files/files_info.yml"
        with open(FILE_INFO_YML, 'r') as stream:
            data_loaded = yaml.safe_load(stream)

        for key, val in data_loaded.items():
            if file_name in key:
                out["filename"] = val['name']
                out["filetype"] = val['file_type']
                break
    out["DLP"] = DLP
    out["DLP_Type"] = DLP_type
    out["action"] = action
    out["uj_options"] = uj_options
    out["policy_type"] = policy_type
    out["list_of_constraints"] = list_of_constraints
    return out


def generate_testcases(input_file=None, output_folder=None):
    activity_list = ["login", "upload", "download", "post", "send", "share", "p2_activities"]

    login_dict = {"tests": []}
    upload_dict = {"tests": []}
    download_dict = {"tests": []}
    post_dict = {"tests": []}
    share_dict = {"tests": []}
    send_dict = {"tests": []}
    p2_activities_dict = {"tests": []}

    with open(input_file, 'r', encoding='utf-8-sig') as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)
        required_fields = ['Title', 'Case ID', 'SaaS App', 'Activity', 'Preconditions']

        # extracting field names through first row
        fields = next(csvreader)

        for item in required_fields:
            if item not in fields:
                raise ValueError(f"Missing {item} field in {filename}")

        title_index = fields.index('Title')
        caseid_index = fields.index('Case ID')
        app_name_index = fields.index('SaaS App')
        activity_index = fields.index('Activity')
        precondition_index = fields.index('Preconditions')


        # extracting each data row one by one
        for row in csvreader:
            activity = row[activity_index]
            app_name = row[app_name_index]
            title = row[title_index]
            caseid = row[caseid_index]
            precondition = row[precondition_index]

            out = extract_data_from_precondition(precondition, activity)

            dlp_profile = None
            if out["DLP"] == "DLP":
                dlp_profile = out["DLP_Type"]
            action = out["action"]
            uj_options = out["uj_options"]
            policy_type = out["policy_type"]
            list_of_constraints = out["list_of_constraints"]

            test_dict = dict()
            test_dict["app name"] = app_name
            test_dict["testrail_id"] = caseid
            test_dict["test_name"] = title
            test_dict["tags"] = ["regression"]
            test_dict["test_method"] = {"name": f"test_{activity.lower()}_from_navigation"}
            if activity.lower() == "upload" or activity.lower() == "download":
                file_type = False
                file_name = False
                try:
                    file_name = out["filename"]
                    file_type = out["filetype"]
                except (KeyError, NameError):
                    pass
                if file_name:
                    if "." in file_name:
                        test_dict["test_method"]["args"] = {"file": file_name.split(".")[0]}

            if activity.lower() == "post":
                if dlp_profile:
                    test_dict["test_method"]["args"] = {"msg": "DLP_" + dlp_profile}
                else:
                    test_dict["test_method"]["args"] = {"msg": "GEN_MSG"}

            if activity.lower() == "upload" or activity.lower() == "download":
                test_dict["object_type"] = "file"
            elif "log" in activity.lower():
                test_dict["object_type"] = "user"
            else:
                test_dict["object_type"] = "notes"
            test_dict["uj_options"] = uj_options
            test_dict["assert_result"] = True
            test_dict["policy_enabled"] = True

            policy_data = dict()
            policy_data["app_name"] = app_name
            policy_data["app_name"] = app_name
            policy_data["app_or_category"] = policy_type
            if activity.lower() == "send" or activity.lower() == "share":
                if "to_user" not in list_of_constraints:
                    list_of_constraints.append("to_user")
            policy_data["list_of_constraints"] = list_of_constraints
            if dlp_profile:
                policy_data["dlp_profile"] = list()
                policy_data["dlp_profile"].append("DLP-" + dlp_profile)
            if activity.lower() == "upload" or activity.lower() == "download":
                policy_data["file_size"] = dict()
                if file_type:
                    policy_data["file_types"] = [file_type]
                else:
                    policy_data["file_types"] = []
            policy_data["activities"] = list()
            policy_data["activities"].append(activity)
            policy_data["action"] = dict()
            policy_data["action"]["action_name"] = action
            test_dict["policy_data"] = policy_data

            p1_activity_list = ["upload", "download", "post", "send", "share"]

            if activity.lower() not in p1_activity_list and "log" not in activity.lower():
                p2_activities_dict["tests"].append(test_dict)
            elif "log" in activity.lower():
                login_dict["tests"].append(test_dict)
            else:
                eval(f"{activity.lower()}_dict[\"tests\"]").append(test_dict)

        activity_list = ["login", "upload", "download", "post", "send", "share", "p2_activities"]
        for activity in activity_list:
            if eval(f"{activity}_dict[\"tests\"]"):
                file_path = os.path.join(output_folder + f'/{activity}.json')
                with open(file_path, 'w', encoding='utf-8') as f:
                    print(f"Generated {file_path}")
                    json.dump(eval(f"{activity}_dict"), f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="input csv file")
    parser.add_argument("output_folder", help="output folder path")
    args = parser.parse_args()

    input_file = args.input_file
    output_folder = args.output_folder

    generate_testcases(input_file, output_folder)
