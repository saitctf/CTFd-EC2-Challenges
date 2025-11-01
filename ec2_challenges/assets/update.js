CTFd.plugin.run((_CTFd) => {
    const $ = _CTFd.lib.$
    
    $(document).ready(function () {
        // Get current values from the template
        const currentAmiId = typeof EC2_AMI_ID !== 'undefined' ? EC2_AMI_ID : '';
        const currentSubnetId = typeof EC2_SUBNET_ID !== 'undefined' ? EC2_SUBNET_ID : '';
        const currentSecurityGroup = typeof EC2_SECURITY_GROUP !== 'undefined' ? EC2_SECURITY_GROUP : '';
        
        // Load available AMIs, subnets, and security groups
        $.getJSON("/api/v1/ec2_config", function (result) {
            if (result.success) {
                // Load AMIs
                $.each(result['data']['amis'], function (i, item) {
                    const option = $("<option />").val(item['value']).text(item['name'] + ` (${item['value']})`);
                    if (item['value'] === currentAmiId) {
                        option.attr('selected', 'selected');
                    }
                    $("#ami_id_select").append(option);
                });
                
                // Load Subnets
                $.each(result['data']['subnets'], function (i, item) {
                    const option = $("<option />").val(item['value']).text(item['value'] + (item['name'] ? ` [${item['name']}]` : ""));
                    if (item['value'] === currentSubnetId) {
                        option.attr('selected', 'selected');
                    }
                    $("#subnet_id_select").append(option);
                });
                
                // Load Security Groups
                $.each(result['data']['security_groups'], function (i, item) {
                    const option = $("<option />").val(item['value']).text(item['value'] + (item['name'] ? ` [${item['name']}]` : ""));
                    if (item['value'] === currentSecurityGroup) {
                        option.attr('selected', 'selected');
                    }
                    $("#security_group_select").append(option);
                });
            } else {
                console.error('Failed to load EC2 configuration:', result);
                showError('Failed to load EC2 configuration. Please check your AWS settings.');
            }
        }).fail(function() {
            console.error('Error loading EC2 configuration');
            showError('Error loading EC2 configuration. Please check your AWS settings.');
        });
    });
});

function showError(message) {
    const container = document.querySelector('.form-group');
    if (container) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.textContent = message;
        container.insertBefore(alert, container.firstChild);
    }
}
