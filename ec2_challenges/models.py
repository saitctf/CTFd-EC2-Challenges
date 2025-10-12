from CTFd.models import db, Challenges


class EC2Config(db.Model):
    """
    EC2 Config Model. This model stores the config for AWS connections and EC2 instance config.
    """
    __tablename__ = "ec2_config"

    id = db.Column(db.Integer, primary_key=True)
    
    # AWS Configuration
    aws_access_key_id = db.Column("aws_access_key_id", db.String(20))
    aws_secret_access_key = db.Column("aws_secret_access_key", db.String(40))
    region = db.Column("region", db.String(32))
    
    # Instance Configuration
    default_instance_type = db.Column("default_instance_type", db.String(32))
    default_security_group = db.Column("default_security_group", db.String(128))
    default_key_name = db.Column("default_key_name", db.String(128))
    # default_subnet_id = db.Column("default_subnet_id", db.String(128))  # Temporarily disabled
    
    # Challenge Configuration
    max_instance_time = db.Column("max_instance_time", db.Integer, default=1800)  # 30 minutes
    auto_stop_enabled = db.Column("auto_stop_enabled", db.Boolean(), default=True)


class EC2ChallengeTracker(db.Model):
    """
    EC2 Instance Tracker. This model stores the users/teams active EC2 instances.
    """
    __tablename__ = "ec2_challenge_tracker"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column("owner_id", db.String(64), index=True)
    challenge_id = db.Column("challenge_id", db.Integer, index=True)
    instance_id = db.Column("instance_id", db.String(128), index=True)
    timestamp = db.Column("timestamp", db.Integer, index=True)
    revert_time = db.Column("revert_time", db.Integer, index=True)
    host = db.Column("host", db.String(128), index=True)
    flag = db.Column("flag", db.String(128), index=True)


class EC2Challenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "ec2"}
    __tablename__ = "ec2_challenge"
    id = db.Column(None, db.ForeignKey("challenges.id"), primary_key=True)
    
    # AMI Configuration
    ami_id = db.Column(db.String(128), index=True)
    instance_type = db.Column(db.String(32))
    security_group = db.Column(db.String(128))
    key_name = db.Column(db.String(128))
    subnet_id = db.Column(db.String(128))
    
    # Challenge Configuration
    setup_script = db.Column(db.Text, default="")
    guide = db.Column(db.Text, default="")
    
    # Connection Configuration
    scheme = db.Column(db.String(10), default="")  # http, https, ssh, etc.
    port = db.Column(db.String(10), default="")    # port number
    
    # Instance Management
    auto_stop_time = db.Column(db.Integer, default=1800)  # 30 minutes


class EC2History(db.Model):
    __tablename__ = "ec2_history"
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer)
    instance_id = db.Column(db.String(128))
    challenge_id = db.Column(db.Integer)
    start_time = db.Column(db.Integer)
    end_time = db.Column(db.Integer)
    solved = db.Column(db.Boolean(), default=False)
