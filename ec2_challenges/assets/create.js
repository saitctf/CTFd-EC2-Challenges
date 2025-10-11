CTFd.plugin.run((_CTFd) => {
    const $ = _CTFd.lib.$
    const md = _CTFd.lib.markdown()
    
    $(document).ready(function () {
        // Load available AMIs, subnets, and security groups
        $.getJSON("/api/v1/ec2_config", function (result) {
            if (result.success) {
                // Load AMIs
                $.each(result['data']['amis'], function (i, item) {
                    $("#ami_id_select").append($("<option />").val(item['value']).text(item['name'] + ` (${item['value']})`));
                });
                
                // Load Subnets
                $.each(result['data']['subnets'], function (i, item) {
                    $("#subnet_id_select").append($("<option />").val(item['value']).text(item['value'] + (item['name'] ? ` [${item['name']}]` : "")));
                });
                
                // Load Security Groups
                $.each(result['data']['security_groups'], function (i, item) {
                    $("#security_group_select").append($("<option />").val(item['value']).text(item['value'] + (item['name'] ? ` [${item['name']}]` : "")));
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
