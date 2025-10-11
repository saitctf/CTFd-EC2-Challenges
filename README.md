# CTFd EC2 Challenges Plugin

A CTFd plugin that allows creating challenges using AWS EC2 instances. This plugin is inspired by the ECS Challenges plugin and provides similar functionality for EC2 instances.

## Features

- **AMI-Based Instance Launching**: Launch fresh EC2 instances from AMIs for each challenge
- **Dynamic IP Display**: Automatically retrieve and display public IP addresses
- **User Scripts**: Run custom setup scripts when instances start
- **Auto-termination**: Automatically terminate instances after a configurable time
- **Admin Interface**: Configure AWS credentials and instance settings
- **Challenge Tracking**: Track active instances per user/team

## Installation

1. Copy the `ec2_challenges` folder to your CTFd `plugins` directory
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Restart CTFd
4. Configure AWS credentials in the admin panel (or use environment variables)

### Environment Variables

You can configure the plugin using environment variables instead of the web interface:

- `AWS_ACCESS_KEY_ID`: AWS Access Key ID (optional if using IAM role)
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key (optional if using IAM role)
- `AWS_REGION`: AWS region (required)
- `AWS_DEFAULT_INSTANCE_TYPE`: Default instance type (e.g., t2.micro)
- `AWS_DEFAULT_SECURITY_GROUP`: Default security group ID
- `AWS_DEFAULT_KEY_NAME`: Default key pair name
- `AWS_MAX_INSTANCE_TIME`: Maximum instance runtime in seconds (default: 1800)
- `AWS_AUTO_STOP_ENABLED`: Enable auto-stop (true/false, default: true)

## Configuration

### AWS Setup

#### Option 1: IAM Role (Recommended for AWS deployments)

If running CTFd on AWS (EC2, ECS, etc.), you can use an IAM role instead of hardcoded credentials:

1. Create an IAM role with the following permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "ec2:DescribeInstances",
                   "ec2:RunInstances",
                   "ec2:TerminateInstances",
                   "ec2:DescribeImages",
                   "ec2:DescribeSecurityGroups",
                   "ec2:DescribeKeyPairs",
                   "ec2:DescribeSubnets",
                   "ec2:DescribeVpcs",
                   "ec2:DescribeNetworkInterfaces",
                   "ec2:CreateTags",
                   "ec2:DescribeTags",
                   "ec2:DescribeImageAttribute"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

2. Attach the role to your CTFd instance/task
3. Configure AWS settings in the CTFd admin panel (credentials can be left blank)

#### Option 2: IAM User (For non-AWS deployments)

1. Create an AWS IAM user with the permissions listed above
2. Configure AWS credentials in the CTFd admin panel:
   - Go to Admin → EC2 Config
   - Enter your AWS Access Key ID and Secret Access Key
   - Select your AWS region
   - Configure default instance settings

### EC2 Instance Setup

1. Create AMIs for your challenges:
   - Build and configure your challenge environments
   - Create AMIs from your configured instances
   - Tag AMIs with `ctfd-challenge=true`
   - Ensure AMIs are in "available" state

2. Configure networking:
   - Set up VPCs and subnets
   - Configure security groups for challenge access
   - Ensure subnets have internet access for public IPs

## Usage

### Creating Challenges

1. Go to Admin → Challenges → Create
2. Select "EC2" as the challenge type
3. Choose an AMI from the dropdown
4. Select a subnet for the instance
5. Configure instance settings (type, security group, key pair)
6. Add a setup script if needed
7. Set auto-termination time (default: 30 minutes)
8. Save the challenge

### User Experience

1. Users click "Start Challenge" to launch a new EC2 instance from AMI
2. A spinner shows while the instance launches
3. Once running, the public IP is displayed
4. Users can SSH into the instance to solve the challenge
5. Instances automatically terminate after the configured time

## API Endpoints

- `GET /api/v1/ec2` - Get active instances for current user
- `GET /api/v1/instance?id=<challenge_id>` - Start an instance for a challenge
- `GET /api/v1/instance_status?instanceId=<instance_id>` - Get instance status and IP
- `GET /api/v1/ec2_config` - Get EC2 configuration (admin only)
- `GET /api/v1/ec2_config/status` - Get configuration status (admin only)

## Database Schema

### EC2Config
- AWS credentials and region
- Default instance settings
- Challenge configuration

### EC2ChallengeTracker
- Tracks active instances per user
- Stores instance metadata
- Manages auto-stop timing

### EC2Challenge
- Challenge-specific instance settings
- Setup scripts and guides
- Auto-stop configuration

### EC2History
- Instance usage history
- Performance tracking

## Security Considerations

- AWS credentials are stored in the database (consider using IAM roles)
- Instances should be properly secured with security groups
- Consider using VPCs for network isolation
- Monitor instance usage to prevent abuse

## Troubleshooting

### Common Issues

1. **No instances available**: Check that instances are tagged and stopped
2. **IP not displaying**: Verify security groups allow necessary access
3. **Instance won't start**: Check AWS permissions and instance state
4. **Setup script not running**: Ensure script is valid bash and has proper permissions

### Debug Mode

Enable debug logging by adding print statements to the Python code. Check CTFd logs for detailed error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This plugin is released under the same license as CTFd.
