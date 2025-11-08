# AWS Video to HLS Converter - Lambda Function

A serverless AWS Lambda function that converts MP4 videos to HLS (HTTP Live Streaming) format using AWS MediaConvert. This solution enables adaptive bitrate streaming with multiple quality levels.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup & Deployment](#setup--deployment)
- [API Reference](#api-reference)
- [Output Structure](#output-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This Lambda function:
1. Receives a POST request with an S3 video URL and destination details
2. Triggers AWS MediaConvert to transcode the video into HLS format
3. Generates multiple quality variants (2160p, 1080p, 720p, 540p)
4. Returns the HLS manifest URL and metadata

**Use Cases:**
- Video streaming platforms
- On-demand video services
- Adaptive bitrate video delivery
- Mobile and web video playback

---

## ✨ Features

- **Multi-Quality Output**: Generates 4 quality levels (4K, 1080p, 720p, 540p)
- **Adaptive Bitrate**: Enables HLS adaptive streaming
- **H.264 Encoding**: Compatible with most devices and browsers
- **AAC Audio**: Standard audio codec at 64kbps
- **Organized Storage**: Timestamped folder structure
- **CORS Enabled**: Ready for web applications

---

## 🏗️ Architecture

```
Input (MP4 on S3) → Lambda Function → AWS MediaConvert → Output (HLS on S3)
```

**Flow:**
1. Client sends POST request with video details
2. Lambda validates request and prepares job settings
3. MediaConvert processes video into HLS segments
4. Output stored in organized S3 structure
5. Lambda returns HLS manifest URL

---

## 📦 Prerequisites

### AWS Services Required:
- **AWS Lambda**: For running the function
- **AWS MediaConvert**: For video transcoding
- **AWS S3**: For storing source and output videos
- **IAM Role**: With appropriate permissions

### IAM Permissions:
The Lambda execution role needs:
- `mediaconvert:CreateJob`
- `mediaconvert:DescribeEndpoints`
- `s3:GetObject` (source bucket)
- `s3:PutObject` (destination bucket)

### Files Required:
- `main.py` - Lambda handler code
- `job.json` - MediaConvert job settings template

---

## 🚀 Setup & Deployment

### Step 1: Create IAM Role for MediaConvert

```bash
# Create a trust policy for MediaConvert
cat > mediaconvert-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "mediaconvert.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create the role
aws iam create-role \
  --role-name MediaConvertRole \
  --assume-role-policy-document file://mediaconvert-trust-policy.json

# Attach S3 access policy
aws iam attach-role-policy \
  --role-name MediaConvertRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Step 2: Package Lambda Function

```bash
# Create deployment package
zip -r function.zip main.py job.json

# Or if you have dependencies:
pip install -r requirements.txt -t .
zip -r function.zip .
```

### Step 3: Create Lambda Function

```bash
# Create Lambda execution role (separate from MediaConvert role)
aws iam create-role \
  --role-name LambdaMediaConvertRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach necessary policies
aws iam attach-role-policy \
  --role-name LambdaMediaConvertRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name LambdaMediaConvertRole \
  --policy-arn arn:aws:iam::aws:policy/AWSElementalMediaConvertFullAccess

# Create the Lambda function
aws lambda create-function \
  --function-name VideoToHLSConverter \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/LambdaMediaConvertRole \
  --handler main.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables={
    MediaConvertRole=arn:aws:iam::YOUR_ACCOUNT_ID:role/MediaConvertRole,
    AWS_DEFAULT_REGION=us-east-1
  }
```

### Step 4: Create API Gateway (Optional)

```bash
# Create REST API
aws apigateway create-rest-api \
  --name VideoConverter \
  --description "Video to HLS conversion API"

# Configure POST method and integrate with Lambda
# (Full API Gateway setup via CLI is complex - consider using AWS Console)
```

### Step 5: Configure S3 Buckets

```bash
# Ensure destination bucket has CORS enabled
aws s3api put-bucket-cors \
  --bucket YOUR_DESTINATION_BUCKET \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"]
    }]
  }'
```

---

## 📡 API Reference

### Endpoint
```
POST /convert
```

### Request Body

```json
{
  "video_source_url": "s3://source-bucket/path/to/video.mp4",
  "destination_bucket": "output-bucket-name",
  "destination_bucket_region": "us-east-1",
  "uniqueId": "user123-video456"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_source_url` | string | ✅ | Full S3 URL of source MP4 video |
| `destination_bucket` | string | ✅ | Name of S3 bucket for HLS output |
| `destination_bucket_region` | string | ✅ | AWS region of destination bucket |
| `uniqueId` | string/number | ✅ | Unique identifier for organizing output |

### Response

#### Success (200)
```json
{
  "final_video_url": "s3://output-bucket/public/user123-video456/20251108143022/HLS/video",
  "thumbnail_url": "",
  "video_s3_key": "/public/user123-video456/20251108143022/HLS/video",
  "video_s3_path": "s3://output-bucket/public/user123-video456/20251108143022/HLS/video",
  "final_video_hls_url": "https://output-bucket.s3.us-east-1.amazonaws.com/public/user123-video456/20251108143022/HLS/video.m3u8"
}
```

#### Error (400)
```json
{
  "error": "Required fields are missing in request body"
}
```

#### Error (500)
```json
{
  "error": "Internal server error - check CloudWatch logs"
}
```

---

## 📂 Output Structure

### S3 Output Directory
```
s3://output-bucket/
└── public/
    └── {uniqueId}/
        └── {timestamp}/
            └── HLS/
                ├── {video}.m3u8          # Master playlist
                ├── {video}_2160.m3u8     # 4K variant playlist
                ├── {video}_1080.m3u8     # 1080p variant playlist
                ├── {video}_720.m3u8      # 720p variant playlist
                ├── {video}_540.m3u8      # 540p variant playlist
                └── {video}_*.ts          # Video segments
```

### Quality Variants

| Resolution | Bitrate | Codec | Audio |
|------------|---------|-------|-------|
| 3840x2160 (4K) | 8 Mbps | H.264 | AAC 64kbps |
| 1920x1080 (FHD) | 4 Mbps | H.264 | AAC 64kbps |
| 1280x720 (HD) | 2.5 Mbps | H.264 | AAC 64kbps |
| 960x540 (qHD) | 1.2 Mbps | H.264 | AAC 64kbps |

---

## ⚙️ Configuration

### Environment Variables

Set these in Lambda configuration:

| Variable | Description | Example |
|----------|-------------|---------|
| `MediaConvertRole` | ARN of IAM role for MediaConvert | `arn:aws:iam::123456789:role/MediaConvertRole` |
| `AWS_DEFAULT_REGION` | AWS region for MediaConvert | `us-east-1` |

### Customizing job.json

The `job.json` file contains MediaConvert job settings. You can modify:

**Video Settings:**
- Resolutions and bitrates
- Codec settings (H.264 parameters)
- GOP size and structure

**Audio Settings:**
- Bitrate (currently 64kbps)
- Sample rate (currently 48kHz)
- Codec profile

**HLS Settings:**
- Segment length (currently 10 seconds)
- Playlist type
- Directory structure

**Example: Change segment length**
```json
"HlsGroupSettings": {
  "SegmentLength": 6,  // Change from 10 to 6 seconds
  ...
}
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Required fields are missing in request body"
**Cause:** Missing required parameters in POST request  
**Solution:** Ensure all 4 required fields are present: `video_source_url`, `destination_bucket`, `destination_bucket_region`, `uniqueId`

#### 2. "Access Denied" errors
**Cause:** Insufficient IAM permissions  
**Solution:** 
- Verify MediaConvertRole has S3 read/write permissions
- Check Lambda execution role has MediaConvert permissions
- Ensure S3 bucket policies allow access

#### 3. MediaConvert job fails
**Cause:** Various - check MediaConvert console  
**Solution:**
- Verify source video is valid MP4
- Check source S3 URL is accessible
- Review CloudWatch logs for detailed error
- Ensure destination bucket exists

#### 4. CORS errors when playing video
**Cause:** S3 bucket CORS not configured  
**Solution:** Add CORS configuration to destination bucket (see Step 5 above)

### Viewing Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/VideoToHLSConverter --follow

# View MediaConvert jobs
aws mediaconvert list-jobs --status COMPLETE --max-results 10
```

### Testing Locally

You can test the handler logic:

```python
# test_event.json
{
  "body": "{\"video_source_url\":\"s3://bucket/video.mp4\",\"destination_bucket\":\"output\",\"destination_bucket_region\":\"us-east-1\",\"uniqueId\":\"test123\"}"
}

# Run test
python -c "
import json
from main import lambda_handler
with open('test_event.json') as f:
    event = json.load(f)
result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

---

## 📝 Code Overview

### Main Components

**`lambda_handler(event, context)`**
- Entry point for Lambda function
- Validates request body
- Configures MediaConvert job
- Returns output URLs

**Key Variables:**
- `video_source_url`: Input S3 URL
- `destinationS3`: Output bucket path
- `video_S3Key`: Organized output path with timestamp
- `jobMetadata`: Tracking metadata for MediaConvert

**Job Configuration:**
1. Loads `job.json` template
2. Gets MediaConvert endpoint
3. Updates input/output paths
4. Submits job to MediaConvert

---

## 🎥 Usage Example

### Using cURL

```bash
curl -X POST https://your-api-gateway-url/convert \
  -H "Content-Type: application/json" \
  -d '{
    "video_source_url": "s3://my-bucket/videos/sample.mp4",
    "destination_bucket": "my-output-bucket",
    "destination_bucket_region": "us-east-1",
    "uniqueId": "user-12345"
  }'
```

### Using Python

```python
import requests
import json

url = "https://your-api-gateway-url/convert"
payload = {
    "video_source_url": "s3://my-bucket/videos/sample.mp4",
    "destination_bucket": "my-output-bucket",
    "destination_bucket_region": "us-east-1",
    "uniqueId": "user-12345"
}

response = requests.post(url, json=payload)
result = response.json()

print(f"HLS URL: {result['final_video_hls_url']}")
```

### Playing HLS Video

Use the returned `final_video_hls_url` in any HLS-compatible player:

**HTML5 with hls.js:**
```html
<video id="video" controls></video>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
  const video = document.getElementById('video');
  const hls = new Hls();
  hls.loadSource('https://output-bucket.s3.us-east-1.amazonaws.com/public/user-12345/20251108143022/HLS/video.m3u8');
  hls.attachMedia(video);
</script>
```

---

## 💰 Cost Considerations

- **MediaConvert**: ~$0.015 per minute of output (varies by region)
- **Lambda**: First 1M requests/month free, then $0.20 per 1M
- **S3 Storage**: ~$0.023 per GB/month
- **Data Transfer**: Free to AWS services, ~$0.09/GB to internet

**Example:** Converting a 10-minute video:
- MediaConvert: ~$0.15 (10 min × $0.015)
- Lambda: Negligible for occasional use
- S3: Depends on retention period

---

## 🔒 Security Best Practices

1. **Use VPC**: Deploy Lambda in VPC for enhanced security
2. **Least Privilege**: Grant minimal IAM permissions
3. **Encrypt S3**: Enable S3 bucket encryption
4. **API Authentication**: Add API Gateway authentication
5. **Input Validation**: Validate S3 URLs to prevent injection
6. **Rate Limiting**: Implement API throttling

---

## 📚 Additional Resources

- [AWS MediaConvert Documentation](https://docs.aws.amazon.com/mediaconvert/)
- [HLS Specification](https://datatracker.ietf.org/doc/html/rfc8216)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Video.js HLS Player](https://videojs.com/)

---

## 📄 License

This project is available for use under your organization's licensing terms.

---

## 🤝 Contributing

For questions or improvements, contact the development team or submit a pull request.

---

**Last Updated:** November 8, 2025
