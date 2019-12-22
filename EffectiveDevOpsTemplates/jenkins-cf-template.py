"""Generating CloudFormation template."""

from ipaddress import ip_network

from ipify import get_ip

from troposphere import (
        Base64,
        ec2,
        GetAtt,
        Join,
        Output,
        Parameter,
        Ref,
        Template,
        )

from troposphere.iam import (
        InstanceProfile,
        PolicyType as IAMPolicy,
        Role,
        )

from awacs.aws import (
        Action,
        Allow,
        Policy,
        Principal,
        Statement,
        )

from awacs.sts import AssumeRole

ApplicationPort = "8080"
ApplicationName = "jenkins"

GithubAccount = "ibrolord"
GithubAnsibleURL = "https://github.com/{}/ansible".format(GithubAccount)

AnsiblePullCmd = \
    "/usr/local/bin/ansible-pull -U {} {}.yml -i localhost".format(
            GithubAnsibleURL,
            ApplicationName
            )

PublicCidrIp = str(ip_network(get_ip()))

t = Template()
t.add_description("Effective DevOps in AWS: HelloWord web application")

t.add_parameter(Parameter(
    "KeyPair",
    Description="Name of an existing EC2 KeyPair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="Must be the name of an existing EC2 KeyPair.",
    ))

t.add_resource(ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp=PublicCidrIp,
            ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
            ),
        ],
))


#'''
ud = Base64(Join('\n', [
    "#!/bin/bash",
    "sudo yum -y update",
    "sudo yum install --enablerepo=epel -y git",
    "pip install ansible",
    "sudo yum install -y java-1.8.0",
    "sudo yum remove java-1.7.0-openjdk -y",
    "sudo wget -O /etc/yum.repos.d/jenkins.repo http://pkg.jenkins-ci.org/redhat/jenkins.repo",
    "sudo rpm --import http://pkg.jenkins-ci.org/redhat/jenkins-ci.org.key",
    "sudo yum install -y jenkins",
    "sudo chkconfig --add jenkins",
    "sudo service jenkins start",
    "pip install jenkins",
    AnsiblePullCmd,
    "echo '*/10 * * * * {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)
#    "wget http://bit.ly/2vESNuc -O /home/ec2-user/helloworld.js",
#    "wget http://bit.ly/2vVvT18 -O /etc/init/helloworld.conf",
#    "start helloworld"
]))
#'''

t.add_resource(IAMPolicy("Policy",
    PolicyName="AllowCodePipeline",
    PolicyDocument=Policy(
        Statement=[
            Statement(Effect=Allow,
                Action=[Action("codepipeline", "*")],
                Resource=["*"])
            ]
        ),
    Roles=[Ref("Role")]
    ))

t.add_resource(Role(
    "Role",
    AssumeRolePolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["ec2.amazonaws.com"])
                )
            ]
        )
    ))

t.add_resource(InstanceProfile(
    "InstanceProfile",
    Path="/",
    Roles=[Ref("Role")]
    ))

t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-0ff8a91507f77f867",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud,
    IamInstanceProfile=Ref("InstanceProfile"),
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our instance.",
    Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt("instance", "PublicDnsName"), ":", ApplicationPort
        ]),
))

print t.to_json()
