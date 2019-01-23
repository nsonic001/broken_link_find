import csv
import subprocess
import time, psutil

import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
import botocore
import os

class EmailSender(object):
    def __init__(self, region_name='us-east-1'):
        boto3.setup_default_session(profile_name='devops')
        self.client = boto3.client('ses', region_name=region_name)

    @staticmethod
    def sendRawEmail(subject, to_addresses, from_address='',
                     body_plain='', body_html='',
                     attachment_file_name=None, attachment_file_path=None):
        msg = MIMEMultipart()
        msg['Subject'] = subject
        if body_plain:
            part = MIMEText(body_plain, 'plain')
            msg.attach(part)
        if body_html:
            part = MIMEText(body_html, 'html')
            msg.attach(part)

        if attachment_file_path:
            part = MIMEApplication(open(attachment_file_path, 'rb').read())
            part.add_header('Content-Disposition', 'attachment', filename=attachment_file_name)
            msg.attach(part)
        try:
            return EmailSender().client.send_raw_email(RawMessage={'Data': msg.as_string()},
                                                       Source=from_address,
                                                       Destinations=to_addresses)
        except botocore.exceptions.ClientError:
            print("send_email_alert", subject, to_addresses)


def run_link_checker(host, from_address, to_address):
    # host =  host"https://help.moengage.com" #sys.argv()[1]
    # ignore_urls = ["https://help.moengage.com/hc/en-us/articles/.\*/subscription.\*",
                   # "https://help.moengage.com/hc/en-us/sections/.\*/subscription.\*"]
    ignore_urls = []
    exec_command = "linkchecker " + host
    if ignore_urls:
        exec_command += " --ignore-url " + " --ignore-url ".join(ignore_urls)
    exec_command += " -F csv/home/ubuntu/brokenlink-out.csv"
    run_p = subprocess.Popen([exec_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # while True:
    #     nextline = run_p.stdout.readline()
    #     if nextline == '' and run_p.poll() is not None:
    #         break
    #     sys.stdout.write(nextline)
    #     sys.stdout.flush()

    TIMEOUT = 2 * 60 * 60  # 15 min

    p = psutil.Process(run_p.pid)
    print "process started with pid ", run_p.pid
    while 1:
        # # Poll process for new output until finished
        nextline = run_p.stdout.readline()
        if nextline == '' and run_p.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()
        # kill after given time
        if (time.time() - p.create_time()) > TIMEOUT:
            p.kill()
            # subprocess.Popen(["sed -i -e 1,4d linkchecker-out.csv"], shell=True, stdout=subprocess.PIPE,
            #                  stderr=subprocess.STDOUT)
            reader = csv.reader(open("/home/ubuntu/brokenlink-out.csv", "rU"), delimiter=';')
            writer = csv.writer(open("/home/ubuntu/brokenlink-out-final.csv", 'w'), delimiter=',')
            next(reader)
            next(reader)
            next(reader)
            next(reader)
            writer.writerows(reader)
            pwd = os.getcwd()
            EmailSender().sendRawEmail('Alert | Broken URL', [to_address], from_address=from_address, attachment_file_name='broken-link.csv', attachment_file_path='/home/ubuntu/brokenlink-out-final.csv')
            raise RuntimeError('timeout')
            # time.sleep(30)
            # 
            # 
if __name__ == '__main__':
    host = sys.argv[1]
    from_address = sys.argv[2]
    to_address = sys.argv[3]
    run_link_checker(host, from_address, to_address)

