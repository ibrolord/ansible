import boto3
client = boto3.client('cloudwatch')

def alarm(event, context):
    instance = event['detail']['instance-id']
    state = event['detail']['state']
    if state == "running":
        warning = put_alarm(instance, 60, 'alert-email')
        critical = put_alarm(instance, 80, 'alert-sms')
        return warning, critical
    else:
      return delete_alarms(instance)

def put_alarm(instance, threshold, sns):
    sns_prefix = 'arn:aws:sns:us-east-1:256218820153:'
    response = client.put_metric_alarm(
      AlarmName='DiskSpaceUtilization-{}-{}'.format(instance, sns),
      MetricName='DiskSpaceUtilization',
      Namespace='System/Linux',
      Dimensions=[
          {
              "Name": "InstanceId",
              "Value": instance
              },
          {
              "Name": "Filesystem",
              "Value": "/dev/xvda1"
              },
          {
              "Name": "MountPath",
              "Value": "/"
              }
          ],
      Statistic='Average',
      Period=300,
      Unit='Percent',
      EvaluationPeriods=2,
      Threshold=threshold,
      ComparisonOperator='GreaterThanOrEqualToThreshold',
      TreatMissingData='missing',
      AlarmActions=[
          sns_prefix + sns,
          ],
      OKActions=[
          sns_prefix + sns,
          ]
      )
    return response

def delete_alarms(instance):
    names = [
      'DiskSpaceUtilization-{}-alert-email'.format(instance),
      'DiskSpaceUtilization-{}-alert-sms'.format(instance),
    ]
    return client.delete_alarms(AlarmNames=names)

