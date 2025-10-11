// EC2 Challenge Update JavaScript

// Load available EC2 instances when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadAvailableInstances();
});

function loadAvailableInstances() {
    fetch('/api/v1/ec2_config')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data.available_instances) {
                const select = document.getElementById('instance_id_select');
                const currentValue = EC2_INSTANCE_ID;
                
                select.innerHTML = '<option value="">Select an EC2 instance...</option>';
                
                data.data.available_instances.forEach(instance => {
                    const option = document.createElement('option');
                    option.value = instance.id;
                    option.textContent = `${instance.name} (${instance.id}) - ${instance.type}`;
                    if (instance.id === currentValue) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            } else {
                console.error('Failed to load available instances:', data);
                showError('Failed to load available EC2 instances. Please check your AWS configuration.');
            }
        })
        .catch(error => {
            console.error('Error loading instances:', error);
            showError('Error loading available EC2 instances. Please check your AWS configuration.');
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

// Update instance type when instance is selected
document.getElementById('instance_id_select').addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    if (selectedOption.value) {
        // Extract instance type from the option text
        const typeMatch = selectedOption.textContent.match(/\(([^)]+)\)/);
        if (typeMatch) {
            const instanceType = typeMatch[1];
            const typeSelect = document.getElementById('instance_type_select');
            typeSelect.value = instanceType;
        }
    }
});
