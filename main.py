#!/usr/bin/env python

import glob
import json
import os
import boto3
import datetime

from botocore.client import ClientError


def handler(event, context):
    # get req body data
    print("Req Body -", event["body"]) # Print Request Body
    reqBody = json.loads(event["body"])

    # check all the required fields are present in req body , if not return error
    if "video_source_url" not in reqBody or "destination_bucket" not in reqBody or "destination_bucket_region" not in reqBody or "uniqueId" not in reqBody:
        return {
            'statusCode': 400,
            'body': json.dumps('Error: Required fields are missing in request body'),
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        }

    # Initialize the job metadata
    video_source_url = reqBody["video_source_url"]
    destination_bucket_name = reqBody["destination_bucket"]
    destination_bucket_region = reqBody["destination_bucket_region"]
    uniqueId = str(reqBody["uniqueId"])  

    sourceS3Basename = os.path.splitext(os.path.basename(video_source_url))[0]
    destinationS3 = 's3://' + destination_bucket_name
    currentTime_in_string = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # AWS MediaConvert role value from environment variable 
    mediaConvertRole = os.environ['MediaConvertRole']
    region = os.environ['AWS_DEFAULT_REGION']
    statusCode = 200

    # Use MediaConvert SDK UserMetadata to tag jobs with the assetID
    # Events from MediaConvert will have the assetID in UserMedata
    jobMetadata = {'assetID': uniqueId}

    try:
        # Job settings are in the lambda zip file in the current working directory
        with open('job.json') as json_data:
            jobSettings = json.load(json_data)

        # get the account-specific mediaconvert endpoint for this region
        mc_client = boto3.client('mediaconvert', region_name=region)
        endpoints = mc_client.describe_endpoints()

        # add the account-specific endpoint to the client session
        client = boto3.client('mediaconvert', region_name=region,
                              endpoint_url=endpoints['Endpoints'][0]['Url'], verify=False)

        # Update the job settings with the source video from the S3 event and destination
        # paths for converted videos
        jobSettings['Inputs'][0]['FileInput'] = video_source_url

        # generate S3 keys for the HLS segments
        video_S3Key = f"/public/{uniqueId}/{currentTime_in_string}/HLS/{sourceS3Basename}"

        jobSettings['OutputGroups'][0]['OutputGroupSettings']['HlsGroupSettings']['Destination'] \
            = destinationS3 + video_S3Key


        # Convert the video using AWS Elemental MediaConvert
        job = client.create_job(Role=mediaConvertRole,
                                UserMetadata=jobMetadata, Settings=jobSettings)
        outputData = {}
        outputData['final_video_url'] = jobSettings['OutputGroups'][0]['OutputGroupSettings']['HlsGroupSettings']['Destination']
        outputData["thumbnail_url"] = ""
        outputData["video_s3_key"] = video_S3Key
        outputData["video_s3_path"] = destinationS3 + video_S3Key
        outputData["final_video_hls_url"] = f"https://{destination_bucket_name}.s3.{destination_bucket_region}.amazonaws.com{video_S3Key}.m3u8"

    except Exception as e:
        print('Exception: %s' % e)
        statusCode = 500
        raise

    finally:
        return {
            'statusCode': statusCode,
            'body': json.dumps(outputData),
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        }