#!/usr/bin/env python3

import argparse
import boto3
import datetime
import json

parser = argparse.ArgumentParser()
parser.add_argument('--days', type=int, default=30)
parser.add_argument('--profiles', type=str, default='default')
parser.add_argument('--granularity', type=str, default='MONTHLY')
args = parser.parse_args()

profiles = args.profiles.split(',')
granularity = args.granularity

now = datetime.datetime.utcnow()
start = (now - datetime.timedelta(days=args.days)).strftime('%Y-%m-%d')
end = now.strftime('%Y-%m-%d')

# loop over profiles key=profile, value=results
profiles_results = {}
# remove any data below MIN_COST
filtered_results = {}
MIN_COST = 0.1

# to use a specific profile e.g. 'dev'
for profile in profiles:
    session = boto3.session.Session(profile_name=profile)
    cd = session.client('ce', 'us-east-1')

    results = []
    token = None
    while True:
        if token:
            kwargs = {'NextPageToken': token}
        else:
            kwargs = {}
        data = cd.get_cost_and_usage(TimePeriod={'Start': start, 'End':  end}, Granularity=granularity, Metrics=['UnblendedCost'], GroupBy=[{'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}, {'Type': 'DIMENSION', 'Key': 'SERVICE'}], **kwargs)
        results += data['ResultsByTime']
        token = data.get('NextPageToken')
        if not token:
            break
    
    filtered_results[profile] = []
    profiles_results[profile] = results
    for result_by_time in results:
        for group in result_by_time['Groups']:
            amount = group['Metrics']['UnblendedCost']['Amount']
            if float(amount) < MIN_COST:
                continue  
            unit = group['Metrics']['UnblendedCost']['Unit']
            filtered_results[profile].append([result_by_time['TimePeriod']['Start'], group['Keys'][0], group['Keys'][1], amount]) #, unit, result_by_time['Estimated']])

#print(profiles_results)
print(json.dumps(filtered_results))
