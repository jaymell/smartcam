# smartcam

Use your stock webcam (can be either a local Linux device or an IP camera) as a security camera. It runs well in Docker on a Raspberry Pi 3. 
* Motion detection
* Stream video to Amazon S3 for long-term remote storage
* Pipe images to Kinesis for machine learning

Requires the following:
* Dynamo db
* Kinesis stream
* S3 bucket
* [This API](https://github.com/jaymell/smartcam-serve) running somehwere
* [This incredible client](https://github.com/jaymell/smartcam-client) running somewhere
* Optional: [This object detection tool](https://github.com/jaymell/pydetect-objects)
