from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class EC2ConfigForm(FlaskForm):
    """Form for EC2 configuration"""
    
    # AWS Configuration
    aws_access_key_id = StringField(
        "AWS Access Key ID",
        validators=[DataRequired(), Length(min=16, max=20)],
        description="Your AWS Access Key ID"
    )
    
    aws_secret_access_key = StringField(
        "AWS Secret Access Key",
        validators=[DataRequired(), Length(min=40, max=40)],
        description="Your AWS Secret Access Key"
    )
    
    region = SelectField(
        "AWS Region",
        validators=[DataRequired()],
        choices=[
            ("us-east-1", "US East (N. Virginia)"),
            ("us-east-2", "US East (Ohio)"),
            ("us-west-1", "US West (N. California)"),
            ("us-west-2", "US West (Oregon)"),
            ("eu-west-1", "Europe (Ireland)"),
            ("eu-west-2", "Europe (London)"),
            ("eu-central-1", "Europe (Frankfurt)"),
            ("ap-southeast-1", "Asia Pacific (Singapore)"),
            ("ap-southeast-2", "Asia Pacific (Sydney)"),
            ("ap-northeast-1", "Asia Pacific (Tokyo)"),
        ],
        description="AWS region where your EC2 instances are located"
    )
    
    # Instance Configuration
    default_instance_type = SelectField(
        "Default Instance Type",
        validators=[DataRequired()],
        choices=[
            ("t2.micro", "t2.micro - 1 vCPU, 1 GB RAM"),
            ("t2.small", "t2.small - 1 vCPU, 2 GB RAM"),
            ("t2.medium", "t2.medium - 2 vCPU, 4 GB RAM"),
            ("t3.micro", "t3.micro - 2 vCPU, 1 GB RAM"),
            ("t3.small", "t3.small - 2 vCPU, 2 GB RAM"),
            ("t3.medium", "t3.medium - 2 vCPU, 4 GB RAM"),
        ],
        description="Default EC2 instance type for challenges"
    )
    
    # default_subnet_id = StringField(
    #     "Default Subnet ID",
    #     validators=[DataRequired()],
    #     description="Default subnet ID for EC2 instances"
    # )
    
    default_security_group = StringField(
        "Default Security Group",
        validators=[DataRequired()],
        description="Default security group ID for EC2 instances"
    )
    
    default_key_name = StringField(
        "Default Key Pair Name",
        validators=[DataRequired()],
        description="Default EC2 key pair name for SSH access"
    )
    
    # Challenge Configuration
    max_instance_time = IntegerField(
        "Maximum Instance Time (seconds)",
        validators=[DataRequired(), NumberRange(min=300, max=7200)],
        default=1800,
        description="Maximum time an instance can run (300-7200 seconds)"
    )
    
    auto_stop_enabled = BooleanField(
        "Auto-stop Enabled",
        default=True,
        description="Automatically stop instances after maximum time"
    )
    
    submit = SubmitField("Save Configuration")
