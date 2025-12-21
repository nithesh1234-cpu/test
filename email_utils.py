import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from json.decoder import JSONDecodeError
import win32com.client
from pylclient.secrets.secret import Secret


def generate_report_mail_body(pod_summary, run_name=None, run_id=None, team_info="app_connector"):
    mail_content = ""
    overall_stats = ""
    each_pod_cont = '''
                    <table style="width:100%" border=1>
                      <tr align="center" style="background-color: #FF8C00;">
                        <th>POD</th>
                        <th>Total TC's</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Untested</th>
                        <th>Pass %</th>
                        <th>Fail %</th>
                        <th>Untested %</th>
                      </tr>
                      {}
                    </table>
            '''
    summary_row_content = """
                        <tr align="center">
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                      </tr>"""

   # Skipping the ALL PODS summary in the repor as it's applicable only for connetors and not applicable for Reverseproxy
    if team_info == "app_connector":
        overall_stats += summary_row_content.format(
            "All PODS", pod_summary["total_summary"]["total"], pod_summary["total_summary"]["passed"],
            pod_summary["total_summary"]["failed"], pod_summary["total_summary"]["untested"],
            pod_summary["total_summary"]["pass_percent"], pod_summary["total_summary"]["failed_percent"],
            pod_summary["total_summary"]["untested_percent"])

    for each_pod, each_pod_summary in pod_summary.items():
        if "total_summary" in each_pod: continue
        app_wise_table = ""
        overall_stats += summary_row_content.format(each_pod, each_pod_summary["total"],
                                                     each_pod_summary["passed"], each_pod_summary["failed"],
                           each_pod_summary["untested"], each_pod_summary["pass_percent"],
                           each_pod_summary["failed_percent"], each_pod_summary["untested_percent"])

        for app_details in each_pod_summary.get("apps", []):
            style = ""
            if (app_details["details"]["pass_percent"] + app_details["details"]["known_failed_percent"]) < 70:
                style = "style=""background-color:#ff0000;color:#ffffff"""
            str_table = '''<tr align="center"" {}>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                          </tr>'''
            app_wise_table += str_table.format(style, app_details["app_name"], app_details["details"]["total"], app_details[
                "details"]["passed"], app_details["details"]["failed"],
                                               app_details["details"]["untested"], app_details["details"][
                                                   "pass_percent"], app_details["details"]["failed_percent"],
                                               app_details["details"]["untested_percent"], app_details["app_owner"])

        appwise_summary = """
                        <p>
                        <h2>{}</h2>
                        <table style="width:100%" border=1>
                          <tr align="center" style="background-color: #FF8C00;">
                            <th>Name</th>
                            <th>Total TC's</th>
                            <th>Passed</th>
                            <th>Failed</th>
                            <th>Untested</th>
                            <th>Pass %</th>
                            <th>Fail %</th>
                            <th>Untested %</th>
                            <th>QA Owner</th>
                          </tr>
                          {}
                        </table>
                     <p>""".format(each_pod, app_wise_table)

        mail_content = mail_content + appwise_summary

    mail_cont = """
    <html>
        <head></head>
        <body>
            <h1> Overall Execution Summary </h1>
            <p> {} </p>
            <p> {} </p>
            <p>
                <strong>TestRun link :</strong> <a href="https://netskope.testrail.io/index.php?/runs/view/{}"> {} </a>
            </p>
            <footer>
              <p><strong>Note:</strong> App name is as per the event details. Not based on the app you are
              accessing. eg: O365 excel download case is counted under Microsoft Office 365 OneDrive for Business <br>
            </footer>
        </body>
        </html>
    """.format(each_pod_cont.format(overall_stats), mail_content, run_id, run_name)
    return mail_cont


def get_report_mailing_list (pod_summary):
    cc_list = set()
    to_list = set()
    for each_pod, each_pod_summary in pod_summary.items():
        if "total_summary" in each_pod: continue
        to_list.add(each_pod_summary["manager"])
        cc_list.update(each_pod_summary["dev"])
        for app_details in each_pod_summary["apps"]:
            cc_list.add(app_details["app_owner"])

    # for dev in pod_summary["dev"]:
    #     cc_list.add(dev)
    cc_list.add("awadh@netskope.com")
    print(cc_list)
    print(to_list)
    return {"To": to_list, "CC": cc_list}


def sendemailutil_report(pod_summary, run_name=None,run_id=None, team_info="app_connector"):
    '''
    Method to snd the email with attachetn
    :param toAddr: To Address
    :param filename: file to be attached
    :return:
    '''
    secret = Secret("tests/connectortests/app_accounts")
    user_credentials = secret.get("appconnectornotify")
    username = user_credentials['username']
    password = user_credentials['apppassword']
    sender = username

    mail_body = generate_report_mail_body(pod_summary, run_name, run_id, team_info)
    distribution_list = get_report_mailing_list(pod_summary)

    # Uncomment below lines if using GMail server
    message = MIMEMultipart()
    message['From'] = sender
    additional_receivers = list()
    # message['To'] = ",".join(distribution_list["To"])
    if team_info == "app_connector":
        additional_receivers = ["dkundu@netskope.com"]
        message['To'] = "eng-app-connector-all@netskope.com"
    else:
        message['To'] = "eng-reverse-proxy-all@netskope.com"
        distribution_list['To'].add("eng-reverse-proxy-all@netskope.com")

    # message['CC'] = ",".join(distribution_list["CC"])
    receivers = list(distribution_list["To"])+list(distribution_list["CC"])
    print(receivers)
    if additional_receivers:
        receivers.extend(additional_receivers)
    # message['Subject'] = 'Connector Automation Execution Summary Report - {}'.format(pod_summary["pod_name"])
    message['Subject'] = '{} : Execution Summary Report'.format(run_name)

    message.attach(MIMEText(mail_body, 'html'))
    # Open PDF file in binary mode
    # Add attachment to message and convert message to string
    text = message.as_string()

    try:
        smtpObj = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtpObj.login(username, password)
        smtpObj.sendmail(sender, receivers, text)
        print("Successfully sent email")
    except Exception as e:
        print(e)
        print("Error: unable to send email")

    # Sends mail via MS Outlook native app installed locally on machine
    # outlook = win32com.client.Dispatch('outlook.application')
    # mail = outlook.CreateItem(0)
    # mail.To = distribution_list["To"]
    # mail.Subject = 'Connector Automation Execution Summary Report - {}'.format(pod_summary["pod_name"])
    # mail.HTMLBody = mail_body
    # mail.CC = distribution_list["CC"]
    # mail.Send()


