import boto3
import os
import json
import hashlib
import random
import string
from datetime import datetime
from flask_restx import Namespace, Resource
from flask import request, render_template, Blueprint, abort

from CTFd.plugins.challenges import BaseChallenge
from CTFd.utils.user import get_current_user, get_current_team, is_admin, get_ip
from CTFd.utils.uploads import delete_file
from CTFd.utils.dates import unix_time
from CTFd.utils.decorators import authed_only, admins_only
from CTFd.utils.decorators.visibility import check_challenge_visibility
from CTFd.plugins import register_plugin_assets_directory
from CTFd.api import CTFd_API_v1
from CTFd.models import (
    db,
    Challenges,
    Fails,
    Solves,
    ChallengeFiles,
    Tags,
    Hints,
    Flags,
    Users,
)

from .models import EC2Config, EC2ChallengeTracker, EC2Challenge, EC2History
from .forms import EC2ConfigForm


def define_ec2_admin(app):
    """Define EC2 admin configuration routes"""
    print("DEBUG: Registering EC2 admin blueprint")
    admin_ec2_config = Blueprint(
        "admin_ec2_config",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )

    @admin_ec2_config.route("/admin/ec2_config", methods=["GET", "POST"])
    # @admins_only  # Temporarily disabled for debugging
    def ec2_config_admin():
        print(f"DEBUG: EC2 config admin route hit - Method: {request.method}")
        print(f"DEBUG: Request URL: {request.url}")
        print(f"DEBUG: Request headers: {dict(request.headers)}")
        
        # Manual admin check
        if not is_admin():
            print("DEBUG: User is not admin, returning 403")
            abort(403)
        
        print("DEBUG: User is admin, proceeding")
        ec2 = EC2Config.query.filter_by(id=1).first()
        # form = EC2ConfigForm()  # Temporarily disabled

        # If no EC2 config exists, create one
        if ec2 is None:
            ec2 = EC2Config(id=1)
            db.session.add(ec2)
            db.session.commit()

        if request.method == "POST":
            print("DEBUG: Processing POST request")
            print(f"DEBUG: Form data: {dict(request.form)}")
            try:
                ec2.aws_access_key_id = request.form.get("aws_access_key_id") or None
                ec2.aws_secret_access_key = request.form.get("aws_secret_access_key") or None
                ec2.region = request.form.get("region")
                ec2.default_instance_type = request.form.get("default_instance_type")
                ec2.default_security_group = request.form.get("default_security_group")
                ec2.default_key_name = request.form.get("default_key_name")
                # ec2.default_subnet_id = request.form.get("default_subnet_id")  # Temporarily disabled
                
                max_time = request.form.get("max_instance_time")
                if max_time:
                    ec2.max_instance_time = int(max_time)
                
                ec2.auto_stop_enabled = request.form.get("auto_stop_enabled") == "on"

                db.session.add(ec2)
                db.session.commit()
                ec2 = EC2Config.query.filter_by(id=1).first()
                
                print("DEBUG: Configuration saved successfully")
                
                # Redirect to prevent duplicate form submission
                from flask import redirect, url_for, flash
                flash("EC2 configuration saved successfully!", "success")
                return redirect(url_for("admin_ec2_config.ec2_config_admin"))
                
            except Exception as e:
                print(f"Error saving EC2 config: {e}")
                import traceback
                traceback.print_exc()
                from flask import flash
                flash(f"Error saving configuration: {str(e)}", "error")

        # Create a simple form object for template rendering
        form = type('Form', (), {})()
        return render_template("admin_ec2_config.html", form=form, ec2_config=ec2)

    print("DEBUG: Registering EC2 admin blueprint with app")
    app.register_blueprint(admin_ec2_config)


def define_ec2_status(app):
    """Define EC2 admin status routes"""
    admin_ec2_status = Blueprint(
        "admin_ec2_status",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )

    @admin_ec2_status.route("/admin/ec2_status", methods=["GET", "POST"])
    @admins_only
    def ec2_admin():
        ec2_tasks = EC2ChallengeTracker.query.all()
        id_name_map = {}
        for i in ec2_tasks:
            name = Users.query.filter_by(id=i.owner_id).first()
            id_name_map[i.owner_id] = name.name if name else "[User Removed]"
        return render_template(
            "admin_ec2_status.html", tasks=ec2_tasks, id_name_map=id_name_map
        )

    app.register_blueprint(admin_ec2_status)


def load(app):
    print("DEBUG: Loading EC2 plugin")
    upgrade(plugin_name="ec2_challenges")
    
    # Register the EC2 challenge type
    from CTFd.plugins.challenges import CHALLENGE_CLASSES
    CHALLENGE_CLASSES["ec2"] = EC2ChallengeType
    
    # Register assets
    register_plugin_assets_directory(app, base_path="/plugins/ec2_challenges/assets")
    
    # Register admin routes
    print("DEBUG: Defining EC2 admin routes")
    define_ec2_admin(app)
    define_ec2_status(app)
    
    # Register API namespaces
    CTFd_API_v1.add_namespace(instance_namespace, "/instance")
    CTFd_API_v1.add_namespace(instance_status_namespace, "/instance_status")
    CTFd_API_v1.add_namespace(active_ec2_namespace, "/ec2")
    CTFd_API_v1.add_namespace(ec2_config_namespace, "/ec2_config")
    
    print("DEBUG: EC2 plugin loaded successfully")
    
    # Initialize EC2 configuration from environment variables
    try:
        ec2 = EC2Config.query.filter_by(id=1).first()
        
        if ec2 is None:
            ec2 = EC2Config(id=1)
        
        # Set configuration from environment variables if available
        if "AWS_ACCESS_KEY_ID" in os.environ:
            ec2.aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        
        if "AWS_SECRET_ACCESS_KEY" in os.environ:
            ec2.aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        
        if "AWS_REGION" in os.environ:
            ec2.region = os.environ["AWS_REGION"]
        
        if "AWS_DEFAULT_INSTANCE_TYPE" in os.environ:
            ec2.default_instance_type = os.environ["AWS_DEFAULT_INSTANCE_TYPE"]
        
        if "AWS_DEFAULT_SECURITY_GROUP" in os.environ:
            ec2.default_security_group = os.environ["AWS_DEFAULT_SECURITY_GROUP"]
        
        if "AWS_DEFAULT_KEY_NAME" in os.environ:
            ec2.default_key_name = os.environ["AWS_DEFAULT_KEY_NAME"]
        
        if "AWS_MAX_INSTANCE_TIME" in os.environ:
            ec2.max_instance_time = int(os.environ["AWS_MAX_INSTANCE_TIME"])
        
        if "AWS_AUTO_STOP_ENABLED" in os.environ:
            ec2.auto_stop_enabled = os.environ["AWS_AUTO_STOP_ENABLED"].lower() in ["true", "1", "yes"]
        
        db.session.add(ec2)
        db.session.commit()
    except Exception as e:
        # This can fail due to database migrations not yet applied, so we should fail out gracefully
        print(f"Warning: Could not initialize EC2 configuration from environment variables: {e}")
        pass


def upgrade(plugin_name):
    """
    Upgrade function for the plugin
    """
    from CTFd.plugins.migrations import upgrade
    upgrade(plugin_name=plugin_name)


def get_available_amis(ec2_config):
    """
    Get list of available AMIs that can be used for challenges
    """
    if not ec2_config:
        return []
    
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )
        
        # Get AMIs that are available for challenges
        response = ec2_client.describe_images(
            Owners=['self'],  # Only AMIs owned by the account
            Filters=[
                {'Name': 'tag:ctfd-challenge', 'Values': ['true']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        amis = []
        for image in response['Images']:
            amis.append({
                'id': image['ImageId'],
                'name': image.get('Name', image['ImageId']),
                'description': image.get('Description', ''),
                'architecture': image.get('Architecture', 'x86_64'),
                'creation_date': image.get('CreationDate', '')
            })
        
        return amis
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: Failed to get available AMIs: {error_msg}")
        
        # Return a special error indicator instead of empty list
        if "UnauthorizedOperation" in error_msg or "not authorized" in error_msg.lower():
            return [{"error": "permission_denied", "message": "Missing ec2:DescribeImages permission"}]
        else:
            return [{"error": "api_error", "message": error_msg}]


def get_available_subnets(ec2_config):
    """
    Get available subnets in the VPC
    """
    if not ec2_config:
        return []
    
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )
        
        response = ec2_client.describe_subnets(
            Filters=[{'Name': 'state', 'Values': ['available']}]
        )
        
        subnets = []
        for subnet in response['Subnets']:
            subnets.append({
                'id': subnet['SubnetId'],
                'vpc_id': subnet['VpcId'],
                'availability_zone': subnet['AvailabilityZone'],
                'cidr_block': subnet['CidrBlock']
            })
        
        return subnets
    except Exception as e:
        print(f"ERROR: Failed to get available subnets: {str(e)}")
        return []


def get_security_groups(ec2_config, vpc_id):
    """
    Get security groups for a VPC
    """
    if not ec2_config:
        return []
    
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )
        
        response = ec2_client.describe_security_groups(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        return [sg['GroupId'] for sg in response['SecurityGroups']]
    except Exception as e:
        print(f"ERROR: Failed to get security groups: {str(e)}")
        return []


def get_instance_public_ip(ec2_config, instance_id):
    """
    Get the public IP address of an EC2 instance
    """
    if not ec2_config:
        return None
        
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )
        
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if response['Reservations']:
            instance = response['Reservations'][0]['Instances'][0]
            return instance.get('PublicIpAddress')
        
        return None
    except Exception as e:
        print(f"ERROR: Failed to get instance IP: {str(e)}")
        return None


def get_available_security_groups(ec2_config):
    """
    Get available security groups
    """
    if not ec2_config:
        return []
    
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )
        
        response = ec2_client.describe_security_groups()
        
        security_groups = []
        for sg in response['SecurityGroups']:
            security_groups.append({
                'id': sg['GroupId'],
                'name': sg['GroupName'],
                'description': sg.get('Description', ''),
                'vpc_id': sg['VpcId']
            })
        
        return security_groups
    except Exception as e:
        print(f"ERROR: Failed to get available security groups: {str(e)}")
        return []


def launch_instance_from_ami(ec2_config, ami_id, instance_type, security_group, key_name, subnet_id, user_script=None):
    """
    Launch a new EC2 instance from an AMI
    """
    if not ec2_config:
        return False, ["EC2 configuration not found!"]
    
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )
        
        # Prepare launch parameters
        launch_params = {
            'ImageId': ami_id,
            'MinCount': 1,
            'MaxCount': 1,
            'InstanceType': instance_type,
            'SecurityGroupIds': [security_group],
            'SubnetId': subnet_id,
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'ctfd-challenge', 'Value': 'true'},
                        {'Key': 'ctfd-managed', 'Value': 'true'},
                        {'Key': 'Name', 'Value': f'ctfd-challenge-{int(datetime.utcnow().timestamp())}'}
                    ]
                }
            ]
        }
        
        # Add key pair if specified
        if key_name:
            launch_params['KeyName'] = key_name
        
        # Add user data if specified
        if user_script:
            launch_params['UserData'] = user_script
        
        # Launch the instance
        response = ec2_client.run_instances(**launch_params)
        
        instance_id = response['Instances'][0]['InstanceId']
        
        # Wait for instance to be running
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        return True, {'instance_id': instance_id, 'response': response}
    except Exception as e:
        return False, [f"AWS error: {str(e)}"]


def terminate_instance(ec2_config, instance_id):
    """
    Terminate an EC2 instance
    """
    if not ec2_config:
        return False, ["EC2 configuration not found!"]
    
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )
        
        response = ec2_client.terminate_instances(InstanceIds=[instance_id])
        return True, response
    except Exception as e:
        return False, [f"AWS error: {str(e)}"]


def create_instance_challenge(ec2_config, challenge_id, random_flag):
    """
    Create a challenge instance by launching a new EC2 instance from AMI with flags
    """
    if not ec2_config:
        return False, ["EC2 configuration not found!"]
    
    # Validate required AWS settings
    if not ec2_config.region:
        return False, ["AWS region not configured. Please configure AWS settings first."]
    
    try:
        ec2_client = boto3.client(
            "ec2",
            region_name=ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )

        session = get_current_user()
        challenge = EC2Challenge.query.filter_by(id=challenge_id).first()

        # Check if user already has a running instance
        if not is_admin():
            if len(EC2ChallengeTracker.query.filter_by(owner_id=session.id).all()):
                tracker = EC2ChallengeTracker.query.filter_by(owner_id=session.id).first()
                challenge = EC2Challenge.query.filter_by(id=tracker.challenge_id).first()
                return False, [
                    "You already have a running instance!",
                    challenge.name,
                    tracker.challenge_id,
                    tracker.instance_id,
                ]

        # Get the flags on the challenge
        flags = Flags.query.filter_by(challenge_id=challenge_id).all()
        
        # Create user data script with flags
        user_script = f"""#!/bin/bash
# CTF Challenge Setup Script
echo "Setting up challenge environment..."

# Set flags as environment variables
"""
        
        for i, flag in enumerate(flags):
            user_script += f'echo "export FLAG_{i}={flag.content}" >> /etc/environment\n'
        
        user_script += f"""
# Additional challenge setup
{challenge.setup_script or ""}

# Log completion
echo "Challenge setup completed at $(date)" >> /var/log/ctf-setup.log
"""

        # Launch the instance from AMI
        success, result = launch_instance_from_ami(
            ec2_config,
            challenge.ami_id,
            challenge.instance_type,
            challenge.security_group,
            challenge.key_name,
            challenge.subnet_id,
            user_script
        )
        
        if success:
            instance_id = result['instance_id']
            
            # Create tracker entry
            entry = EC2ChallengeTracker(
                owner_id=session.id,
                challenge_id=challenge.id,
                instance_id=instance_id,
                timestamp=unix_time(datetime.utcnow()),
                revert_time=unix_time(datetime.utcnow()) + challenge.auto_stop_time,
                flag=random_flag,
            )
            
            db.session.add(entry)
            db.session.commit()
            
            return True, result
        else:
            return False, result
            
    except Exception as e:
        return False, [f"AWS error: {str(e)}"]


class EC2ChallengeType(BaseChallenge):
    id = "ec2"
    name = "ec2"
    templates = {
        "create": "/plugins/ec2_challenges/assets/create.html",
        "update": "/plugins/ec2_challenges/assets/update.html",
        "view": "/plugins/ec2_challenges/assets/view.html",
    }
    scripts = {
        "create": "/plugins/ec2_challenges/assets/create.js",
        "update": "/plugins/ec2_challenges/assets/update.js",
        "view": "/plugins/ec2_challenges/assets/view.js",
    }
    route = "/plugins/ec2_challenges/assets"
    blueprint = Blueprint(
        "ec2_challenges",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )

    @staticmethod
    def update(challenge, request):
        """
        This method is used to update the information associated with a challenge.
        """
        data = request.form or request.get_json()
        
        challenge = EC2Challenge.query.filter_by(id=challenge.id).first()
        for attr, value in data.items():
            if hasattr(challenge, attr):
                setattr(challenge, attr, value)
        
        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        EC2Challenge.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()

    @staticmethod
    def read(challenge):
        """
        This method is used to read the information associated with a challenge.
        """
        challenge = EC2Challenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "instance_id": challenge.instance_id,
            "setup_script": challenge.setup_script,
            "guide": challenge.guide,
            "type_data": {
                "id": EC2ChallengeType.id,
                "name": EC2ChallengeType.name,
                "templates": EC2ChallengeType.templates,
                "scripts": EC2ChallengeType.scripts,
            },
        }
        return data

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.
        """
        data = request.form or request.get_json()
        
        challenge = EC2Challenge(**data)
        db.session.add(challenge)
        db.session.commit()
        return challenge

    @staticmethod
    def attempt(challenge, request):
        """
        This method is used to check whether a given input is right or wrong.
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        flags = Flags.query.filter_by(challenge_id=challenge.id).all()

        for flag in flags:
            if flag.content == submission:
                return True, "Correct!"

        return False, "Incorrect!"

    @staticmethod
    def solve(user, team, challenge, request):
        """
        This method is used to insert Solves for the admin panel.
        """
        challenge = EC2Challenge.query.filter_by(id=challenge.id).first()
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        solve = Solves(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(req=request),
            provided=submission,
        )
        db.session.add(solve)

        # Terminate the instance when solved
        ec2_config = EC2Config.query.filter_by(id=1).first()
        tracker = EC2ChallengeTracker.query.filter_by(
            challenge_id=challenge.id, owner_id=user.id
        ).first()
        
        if tracker:
            terminate_instance(ec2_config, tracker.instance_id)
            EC2ChallengeTracker.query.filter_by(instance_id=tracker.instance_id).delete()

        db.session.commit()

    @staticmethod
    def fail(user, team, challenge, request):
        """
        This method is used to insert Fails for the admin panel.
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        wrong = Fails(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(req=request),
            provided=submission,
        )
        db.session.add(wrong)
        db.session.commit()


# API Endpoints
instance_namespace = Namespace("instance", description="Endpoint to interact with EC2 instances")


@instance_namespace.route("", methods=["POST", "GET"])
class InstanceAPI(Resource):
    @authed_only
    def get(self):
        challenge_id = request.args.get("id")
        challenge = EC2Challenge.query.filter_by(id=challenge_id).first()
        if challenge is None:
            return abort(403)
        
        ec2_config = EC2Config.query.filter_by(id=1).first()
        session = get_current_user()

        # Check if user already has a running instance
        check = (
            EC2ChallengeTracker.query.filter_by(owner_id=session.id)
            .filter_by(challenge_id=challenge.id)
            .first()
        )

        if check is not None:
            return abort(403)

        flag = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
        success, result = create_instance_challenge(
            ec2_config,
            challenge_id,
            flag,
        )

        if success:
            return {"success": True, "data": []}
        else:
            return {"success": False, "data": result}


instance_status_namespace = Namespace(
    "instance_status",
    description="Get the status of an EC2 instance.",
)


@instance_status_namespace.route("", methods=["GET"])
class InstanceStatus(Resource):
    @authed_only
    def get(self):
        ec2_config = EC2Config.query.filter_by(id=1).first()
        
        if not ec2_config:
            return {"success": False, "data": [], "error": "No EC2 configuration found"}

        ec2_client = boto3.client(
            "ec2",
            ec2_config.region,
            aws_access_key_id=ec2_config.aws_access_key_id,
            aws_secret_access_key=ec2_config.aws_secret_access_key,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        )

        instance_id = request.args.get("instanceId")
        
        # URL decode the instance ID if it's encoded
        if instance_id:
            import urllib.parse
            instance_id = urllib.parse.unquote(instance_id)

        session = get_current_user()

        challenge_tracker = EC2ChallengeTracker.query.filter_by(
            instance_id=instance_id
        ).first()

        if not challenge_tracker:
            print(f"DEBUG: No challenge tracker found for instanceId: {instance_id}")
            return {"success": False, "data": [], "error": "No challenge tracker found"}

        # Check for owner match with type conversion
        owner_match = False
        try:
            # Try string comparison
            if str(challenge_tracker.owner_id) == str(session.id):
                owner_match = True
            # Try integer comparison
            elif int(challenge_tracker.owner_id) == int(session.id):
                owner_match = True
        except (ValueError, TypeError):
            pass
            
        if not owner_match:
            print(f"DEBUG: Owner mismatch - tracker owner: {challenge_tracker.owner_id}, session id: {session.id}")
            
            # Allow admins to access any instance
            if is_admin():
                print(f"DEBUG: Admin override - allowing access to instance owned by {challenge_tracker.owner_id}")
            else:
                return {"success": False, "data": [], "error": "Owner mismatch"}

        challenge = EC2Challenge.query.filter_by(
            id=challenge_tracker.challenge_id
        ).first()

        if not challenge:
            return {"success": False, "data": [], "error": "Challenge not found"}

        try:
            # Get instance status
            response = ec2_client.describe_instances(InstanceIds=[instance_id])
            
            if not response['Reservations']:
                return {"success": False, "data": [], "error": "Instance not found"}
            
            instance = response['Reservations'][0]['Instances'][0]
            state = instance['State']['Name']
            public_ip = instance.get('PublicIpAddress', '')
            
            # Update the host field in the tracker if we got an IP and it's different
            if public_ip and challenge_tracker.host != public_ip:
                print(f"DEBUG: Updating host field from '{challenge_tracker.host}' to '{public_ip}'")
                challenge_tracker.host = public_ip
                db.session.commit()
            
            is_running = state == 'running'
            
            return {
                "success": True,
                "data": {"running": is_running, "state": state},
                "public_ip": public_ip,
            }
            
        except Exception as e:
            print(f"DEBUG: Error getting instance status: {e}")
            return {"success": False, "data": [], "error": str(e)}


active_ec2_namespace = Namespace(
    "ec2", description="Endpoint to retrieve User EC2 Instance Status"
)


@active_ec2_namespace.route("", methods=["POST", "GET"])
class EC2Status(Resource):
    """
    The Purpose of this API is to retrieve a public JSON string of all EC2 instances
    in use by the current team/user.
    """

    @authed_only
    def get(self):
        ec2_config = EC2Config.query.first()

        session = get_current_user()
        tracker = EC2ChallengeTracker.query.filter_by(owner_id=session.id)
        data = list()
        for i in tracker:
            challenge = EC2Challenge.query.filter_by(id=i.challenge_id).first()

            # Skip if challenge doesn't exist (might have been deleted)
            if challenge is None:
                continue

            data.append(
                {
                    "id": i.id,
                    "owner_id": i.owner_id,
                    "challenge_id": i.challenge_id,
                    "timestamp": i.timestamp,
                    "revert_time": i.revert_time,
                    "instance_id": i.instance_id,
                }
            )
        return {"success": True, "data": data}


ec2_config_namespace = Namespace("ec2_config", description="Endpoint to manage EC2 configuration")


@ec2_config_namespace.route("", methods=["GET"])
class EC2ConfigAPI(Resource):
    @admins_only
    def get(self):
        ec2_config = EC2Config.query.filter_by(id=1).first()
        
        if not ec2_config:
            return {"success": False, "data": {}, "error": "No EC2 configuration found"}

        return {
            "success": True,
            "data": {
                "region": ec2_config.region,
                "aws_access_key_id": ec2_config.aws_access_key_id,
                "aws_secret_access_key": ec2_config.aws_secret_access_key,
                "available_amis": get_available_amis(ec2_config),
                "available_subnets": get_available_subnets(ec2_config),
                "available_security_groups": get_available_security_groups(ec2_config),
            }
        }


@ec2_config_namespace.route("/status", methods=["GET"])
class EC2ConfigStatusAPI(Resource):
    @admins_only
    def get(self):
        ec2_config = EC2Config.query.filter_by(id=1).first()
        
        return {
            "success": True,
            "data": {
                "config_valid": bool(ec2_config),
                "has_credentials": bool(ec2_config and (ec2_config.aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")))
            }
        }


