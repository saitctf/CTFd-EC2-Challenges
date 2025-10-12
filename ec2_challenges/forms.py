from CTFd.forms import BaseForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class EC2ConfigForm(BaseForm):
    """Form for EC2 configuration"""
    
    # AWS Configuration
    aws_access_key_id = StringField(
        "AWS Access Key ID (Optional)",
        validators=[Length(min=16, max=20)],
        description="Your AWS Access Key ID (leave blank if using IAM roles)"
    )
    
    aws_secret_access_key = StringField(
        "AWS Secret Access Key (Optional)",
        validators=[Length(min=40, max=40)],
        description="Your AWS Secret Access Key (leave blank if using IAM roles)"
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


class EC2ChallengeForm(BaseForm):
    """Form for EC2 challenge creation/editing"""
    
    # Basic Challenge Fields
    name = StringField(
        "Challenge Name",
        validators=[DataRequired(), Length(min=1, max=80)],
        description="Name of the challenge"
    )
    
    description = TextAreaField(
        "Description",
        validators=[DataRequired()],
        description="Challenge description and instructions"
    )
    
    value = IntegerField(
        "Points",
        validators=[DataRequired(), NumberRange(min=1)],
        description="Points awarded for solving this challenge"
    )
    
    category = StringField(
        "Category",
        validators=[DataRequired(), Length(min=1, max=80)],
        description="Challenge category"
    )
    
    # EC2 Configuration
    ami_id = SelectField(
        "AMI ID",
        validators=[DataRequired()],
        choices=[],  # Will be populated dynamically
        description="Amazon Machine Image to use for this challenge"
    )
    
    instance_type = SelectField(
        "Instance Type",
        validators=[DataRequired()],
        choices=[
            ("t2.micro", "t2.micro - 1 vCPU, 1 GB RAM"),
            ("t2.small", "t2.small - 1 vCPU, 2 GB RAM"),
            ("t2.medium", "t2.medium - 2 vCPU, 4 GB RAM"),
            ("t3.micro", "t3.micro - 2 vCPU, 1 GB RAM"),
            ("t3.small", "t3.small - 2 vCPU, 2 GB RAM"),
            ("t3.medium", "t3.medium - 2 vCPU, 4 GB RAM"),
        ],
        description="EC2 instance type"
    )
    
    subnet_id = SelectField(
        "Subnet ID",
        validators=[DataRequired()],
        choices=[],  # Will be populated dynamically
        description="Subnet where the instance will be launched"
    )
    
    security_group = SelectField(
        "Security Group",
        validators=[DataRequired()],
        choices=[],  # Will be populated dynamically
        description="Security group for the instance"
    )
    
    key_name = StringField(
        "Key Pair Name",
        validators=[DataRequired()],
        description="EC2 key pair for SSH access"
    )
    
    # Connection Configuration
    scheme = SelectField(
        "Connection Scheme (Optional)",
        choices=[
            ("", "None"),
            ("http", "HTTP"),
            ("https", "HTTPS"),
            ("ssh", "SSH"),
            ("ftp", "FTP"),
            ("sftp", "SFTP"),
        ],
        description="Protocol scheme to prepend to the IP address"
    )
    
    port = StringField(
        "Port (Optional)",
        validators=[Length(max=10)],
        description="Port number to append to the IP address (e.g., 3000, 8080)"
    )
    
    # Challenge Content
    setup_script = TextAreaField(
        "Setup Script (Optional)",
        description="Bash script to run on instance startup"
    )
    
    guide = TextAreaField(
        "Challenge Guide (Optional)",
        description="Additional instructions or hints for the challenge"
    )
    
    auto_stop_time = IntegerField(
        "Auto-stop Time (seconds)",
        validators=[NumberRange(min=300, max=7200)],
        default=1800,
        description="Time before instance automatically stops (300-7200 seconds)"
    )
    
    submit = SubmitField("Create Challenge")
