import sys
import time
from os import environ

from huawei_lte_api.Client import Client
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.Connection import Connection
from huawei_lte_api.api.User import User
from huawei_lte_api.enums.sms import BoxTypeEnum, TextModeEnum
from huawei_lte_api.enums.user import LoginStateEnum
import huawei_lte_api.exceptions

try:
    HUAWEI_ROUTER_IP_ADDRESS = environ['HUAWEI_ROUTER_IP_ADDRESS']
    HUAWEI_ROUTER_ACCOUNT = environ['HUAWEI_ROUTER_ACCOUNT']
    HUAWEI_ROUTER_PASSWORD = environ['HUAWEI_ROUTER_PASSWORD']
    TARGET_PHONE_NUMBERS = environ['TARGET_PHONE_NUMBERS'].split(',')
    DELAY_LOOP_SECONDS = int(environ.get('DELAY_LOOP_SECONDS', "1"))
    DELAY_WAIT_SECONDS = int(environ.get('DELAY_WAIT_SECONDS', "15"))
except:
    print('Please provide the required environment variables.')
    sys.exit(1)

connection = None
client = None

# Use infinite loop to check SMS
while True:
    try:
        # Establish a connection with authorized
        connection = AuthorizedConnection('http://{}:{}@{}/'.format(HUAWEI_ROUTER_ACCOUNT, HUAWEI_ROUTER_PASSWORD, HUAWEI_ROUTER_IP_ADDRESS))
        client = Client(connection)

        # get first SMS (unread priority)
        sms_list = client.sms.get_sms_list(1, BoxTypeEnum.LOCAL_INBOX, 1, 0, 1, 1)

        # Skip this loop if no messages
        if sms_list['Messages'] == None:
            client.user.logout()
            time.sleep(DELAY_WAIT_SECONDS)
            continue

        # Skip this loop if the SMS was read
        if int(sms_list['Messages']['Message']['Smstat']) == 1:
            client.user.logout()
            time.sleep(DELAY_WAIT_SECONDS)
            continue

        sms = sms_list['Messages']['Message']

        # Found a new SMS
        print('{Date} Found a new SMS ID:{Message_Index} From:{Phone_Number}'.format(Date=sms['Date'], Message_Index=sms['Index'], Phone_Number=sms['Phone']))
        print('Details: {}'.format(sms))

        # Skip if SMS is an acknowledgment 
        if sms['SmsType'] != '7':

            # Forward to target numbers
            sent_sms = client.sms.send_sms(
                phone_numbers=TARGET_PHONE_NUMBERS,
                message=sms.get('Content', ''),
                sca=sms.get('Sca', ''),
            )

        # Set SMS as read
        client.sms.set_read(sms['Index'])

        # Logout
        client.user.logout()
        time.sleep(DELAY_LOOP_SECONDS)
    except huawei_lte_api.exceptions.ResponseErrorLoginRequiredException as e:
        pass
    except KeyboardInterrupt:
        # Force logout on exit
        client.user.logout()
        print('Exitting...')
        sys.exit(0)
    except Exception as e:
        print('Router connection failed! Please check the settings. \nError message:\n{error_msg}'.format(error_msg=e))
        # Force logout on exit
        client.user.logout()
        print('Exitting...')
        sys.exit(1)
