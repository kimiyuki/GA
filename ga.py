import argparse, re, os
from dotenv import load_dotenv

from googleapiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
CLIENT_SECRETS_PATH = 'secrets.json'  # Path to client_secrets.json file.
load_dotenv()
VIEW_ID = str(os.environ.get('VIEW_ID')) 


def initialize_analyticsreporting():
    """Initializes the analyticsreporting service object.

  Returns:
    analytics an authorized analyticsreporting service object.
  """
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    flags = parser.parse_args([])

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH,
        scope=SCOPES,
        message=tools.message_if_missing(CLIENT_SECRETS_PATH))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storage = file.Storage('analyticsreporting.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())

    # Build the service object.
    analytics = build('analytics',
                      'v4',
                      http=http,
                      discoveryServiceUrl=DISCOVERY_URI)

    return analytics


def get_report(analytics, sdate, edate):
    # Use the Analytics Service Object to query the Analytics Reporting API V4.
    return analytics.reports().batchGet(
        body={
            'reportRequests': [{
                'viewId': VIEW_ID,
                'dateRanges': [{ 'startDate': sdate, 'endDate': edate }],
                'metrics': [{ 'expression': 'ga:'+ mt} for mt in ['users', 'sessions'] ],
                "dimensions": [{'name':'ga:'+dim} for dim in ['date', 'deviceCategory', 'medium']] 
            }]
        }).execute()


def parse_response(response):
    """Parses and prints the Analytics Reporting API V4 response"""
    data = []
    report = response.get("reports", [])[0] 
    columnHeader = report.get('columnHeader', {})
    headers = columnHeader.get('dimensions', []) + \
              [x['name'] for x in columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])]
    data.append([re.sub('ga:', '', x) for x in headers])

    for row in report.get('data', {}).get('rows', []):
        data.append(row.get('dimensions', []) + \
                    [int(x) for x in row.get('metrics', {})[0].get('values', [])])

    return data

#if __name__ == "__main__":
analytics = initialize_analyticsreporting()
response = get_report(analytics, '2021-01-10', "2021-01-11")
data = parse_response(response)
with open('out.csv', "w") as f:
  f.writelines(map(lambda x: ','.join([str(z) for z in x]) + "\n", data))


#print(response)
#print_response(response)
  #main()