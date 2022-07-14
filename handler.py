from datetime import datetime
import json
import uuid
from saral_utils.extractor.dynamo import DynamoDB
from saral_utils.utils.env import get_env_var
import warnings

# TODO: [SAR-114] include lambda-put-event and lambda-welcome-email in same service lambda-register-users


def register_user(event, context):
    data = event['queryStringParameters']

    # check for required values in passed post request
    if 'emailId' not in data:
        raise Exception("Couldn't register without emailId.")
    # TODO: [SAR-115] correctly parse timezone value from frontend
    if 'emailSendTime' not in data or 'emailSendTimeZone' not in data:
        warnings.warn('Time related information is not provided, using default values of 9AM GMT')
        email_send_time = '0900'
        email_send_time_zone = '+530'
    else:
        email_send_time = data['emailSendTime']
        email_send_time_zone = data['emailSendTimeZone']

    email_id = data['emailId']

    env = get_env_var('MY_ENV')
    region = get_env_var('MY_REGION')
    table = f'registered-users-{env}'
    db = DynamoDB(table=table, env=env, region=region)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # check if emailId exist in db
    # if email exist, update with new values else create a new record
    try:
        record = db.get_item(key={'emailId': {'S': email_id}})
        print('Record already exists so updating')
        created_at = record['createdAt']['S']
        updated_at = timestamp
    except Exception as error:
        print(error)
        print('record doesnt exist')
        created_at = timestamp
        updated_at = timestamp

    item = {
        'id': {'S': str(uuid.uuid4())},
        'emailId': {'S': email_id},
        'emailSendTime': {'S': email_send_time},
        'emailSendTimeZone': {'S': email_send_time_zone},
        'createdAt': {'S': created_at},
        'updatedAt': {'S': updated_at}
    }

    # write the todo to the database
    resp = db.put_item(payload=item)
    print(f'record created/updated for emailId: {email_id}')

    response = {
        "statusCode": 200,
        "body": json.dumps(item),
        "headers": {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-type',
            'Acess-Control-Allow-Methods': 'GET'
        }
    }

    return response
