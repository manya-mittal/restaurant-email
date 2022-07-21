from pymongo import MongoClient
import requests
from pdf_mail import sendpdf
import cronitor

cronitor.api_key = 'f38ab01db8b54a3e8b2743f51a5a097d'
monitor = cronitor.Monitor('3XpGac')  # links to cronitor monitor
monitor.ping(state='run')

MONGO_URI = 'mongodb+srv://easyeatsadmin:easyeatsadmin%40%24%23*@easyeat-dev.eyl6j.mongodb.net/easyeats?retryWrites=true&w=majority'
client = MongoClient(MONGO_URI)
db = client['easyeats']
collection = db.restaurant_details

napi_base_url = 'https://napi-dev.easyeat.ai'
auth_token_api_endpoint = napi_base_url + '/api/auth/admin/verify'
eod_report_api_endpoint = napi_base_url + '/api/report/eod-report'

access_token_body = {
    "login_email": "api@easyeat.ai",
    "admin_cred": "1234",
    "role": "ee_admin"
}

token = ''
headers = {}
try:
    token = requests.post(auth_token_api_endpoint, json=access_token_body).json().get('token')  # sends a post request
    if token is None:
        raise Exception('post request failed, unable to get access token')
    headers = {'Authorization': 'Bearer ' + token, 'country-code': 'ID', 'accept-language': 'id-ID'}
except:
    print('Error: post request failed')
    monitor.ping(state='fail', message='Error: Could not get access token')

for restaurant in db.restaurant_details.find({"country_code": "ID"}):
    ID = str(restaurant.get('id'))
    name = restaurant.get('name')

    body = {
        "restaurant_id": ID,
        "date": "2022-06-15",
        "json": 0
    }

    link = ''
    try:
        link = requests.post(eod_report_api_endpoint, headers=headers, json=body).json().get('data')
        if link is None:
            raise Exception('post request failed')
        # gets link from post request
    except:
        print('Error: post request failed. Unable to get link')
        monitor.ping(state='fail', message='Error: Could not get pdf link')

    try:
        response = requests.get(link)
        with open('/Users/manyamittal/Dev/EasyEat/Workspace/restaurant-email/' + name + ' EOD.pdf', 'wb') as f:
            f.write(response.content)  # saves the pdf file
    except:
        monitor.ping(state='fail', message='Error: Could not open URL')

    sender_email_address = 'manya.mittal@easyeat.ai'
    receiver_email_address = 'manya.mittal@easyeat.ai'
    sender_email_password = 'jjmtehijgshxsddt'
    subject_of_email = name + ' EOD'
    body_of_email = 'Dear ' + name + ',\n\nHere is your EOD report. \n\nKind Regards, \nEasy Eat '
    filename = name + ' EOD'
    location_of_file = '/Users/manyamittal/Dev/EasyEat/Workspace/restaurant-email'

    emailInstance = sendpdf(sender_email_address,
                            receiver_email_address,
                            sender_email_password,
                            subject_of_email,
                            body_of_email,
                            filename,
                            location_of_file)

    # sending the email
    try:
        emailInstance.email_send()
    except:
        print('Could not send email for the first time. Retrying.')
        newEmailInstance = sendpdf(sender_email_address,
                                   receiver_email_address,
                                   sender_email_password,
                                   subject_of_email,
                                   body_of_email,
                                   filename,
                                   location_of_file)
        try:
            newEmailInstance.email_send()
        except:
            # if there was a second error, send email to indicate failure
            print('Error: Could not send email to ' + name)
            monitor.ping(state='fail', message='Email was not sent to ' + name)

        else:
            print('Email successfully sent to ' + name)
            monitor.ping(state='complete')
    else:
        print('Email successfully sent to ' + name)
        monitor.ping(state='complete')
