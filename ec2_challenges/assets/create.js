// EC2 Challenge Creation JavaScript

// Load available AMIs and subnets when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadAvailableAMIs();
    loadAvailableSubnets();
});

function loadAvailableAMIs() {
    fetch('/api/v1/ec2_config')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data.available_amis) {
                const select = document.getElementById('ami_id_select');
                select.innerHTML = '<option value="">Select an AMI...</option>';
                
                data.data.available_amis.forEach(ami => {
                    const option = document.createElement('option');
                    option.value = ami.id;
                    option.textContent = `${ami.name} (${ami.id}) - ${ami.architecture}`;
                    select.appendChild(option);
                });
            } else {
                console.error('Failed to load available AMIs:', data);
                showError('Failed to load available AMIs. Please check your AWS configuration.');
            }
        })
        .catch(error => {
            console.error('Error loading AMIs:', error);
            showError('Error loading available AMIs. Please check your AWS configuration.');
        });
}

function loadAvailableSubnets() {
    fetch('/api/v1/ec2_config')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data.available_subnets) {
                const select = document.getElementById('subnet_id_select');
                select.innerHTML = '<option value="">Select a subnet...</option>';
                
                data.data.available_subnets.forEach(subnet => {
                    const option = document.createElement('option');
                    option.value = subnet.id;
                    option.textContent = `${subnet.id} (${subnet.availability_zone}) - ${subnet.cidr_block}`;
                    select.appendChild(option);
                });
            } else {
                console.error('Failed to load available subnets:', data);
                showError('Failed to load available subnets. Please check your AWS configuration.');
            }
        })
        .catch(error => {
            console.error('Error loading subnets:', error);
            showError('Error loading available subnets. Please check your AWS configuration.');
        });
}

function showError(message) {
    const container = document.querySelector('.form-group');
    if (container) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.textContent = message;
        container.insertBefore(alert, container.firstChild);
    }
}
