CTFd._internal.challenge.data = undefined

CTFd._internal.challenge.renderer = null;

CTFd._internal.challenge.preRender = function () { }

CTFd._internal.challenge.render = null;

CTFd._internal.challenge.postRender = function () { }

CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val())
    var submission = CTFd.lib.$('#challenge-input').val()

    var body = {
        challenge_id: challenge_id,
        submission: submission,
    }
    var params = {}
    if (preview) {
        params['preview'] = true
    }

    return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
        setTimeout(() => get_ec2_status(challenge_id), 100);
        if (response.status === 429) {
            // User was ratelimited but process response
            return response
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response
        }
        return response
    });
};

function get_ec2_status(challenge) {
    fetch("/api/v1/ec2").then(result => result.json()).then(result => {
        if (!result['data'].some((item, i) => {
            if (item.challenge_id == challenge) {
                document.querySelector('#ec2_container').innerHTML = `<div class="mt-2" id="${String(item.instance_id).replaceAll(":", "_").replaceAll("/", "_")}_revert_container"></div><div class="mt-2" id="${String(item.instance_id).replaceAll(":", "_").replaceAll("/", "_")}_connect_to_container"></div>`;
                let running = false;

                let revert_section = document.querySelector("#" + String(item.instance_id).replaceAll(":", "_").replaceAll("/", "_") + "_revert_container");
                let connect_section = document.querySelector("#" + String(item.instance_id).replaceAll(":", "_").replaceAll("/", "_") + "_connect_to_container");

                let initSecond = Math.floor(new Date().getTime() / 1000);

                let status_check_interval = setInterval(function () {
                    let currentSecond = Math.floor(new Date().getTime() / 1000);
                    let deltaSecond = Math.floor((currentSecond - initSecond) / 5);
                    let funny_words = [
                        'Provisioning VM challenge...',
                        'Getting stuff ready...',
                        'Injecting stuff...',
                        'Downloading viruses to your computer...',
                        'Almost ready...',
                        'Need coffee...',
                        'Killing time...',
                        'Killing in the name of...'
                    ]

                    if (!running) {
                        fetch(`/api/v1/instance_status?${new URLSearchParams({ instanceId: item.instance_id })}`).then(result => result.json()).then(result => {
                            if (result['success']) {
                                if (result['data']['running']) {
                                    running = true;
                                    const publicIP = result['public_ip'] || 'N/A';
                                    connect_section.innerHTML = `<span class="text-success"><strong>IP: ${publicIP}</strong></span>`;
                                    clearInterval(status_check_interval);
                                    revert_section.innerHTML = `<a onclick="start_instance('${item.challenge_id}');" class='btn btn-danger'><small style='color:white;'><i style='margin-right: 5px;' class="fas fa-redo"></i>Reset Challenge</small></a>`;
                                } else {
                                    connect_section.innerHTML = `<span>Your instance is starting, this shouldn't take longer than a minute and a half</span><br><br><br><span>${funny_words[deltaSecond % funny_words.length]}</span>`;
                                }
                            }
                        });
                    }
                }, 1000);
                return true;
            };
        })) {
            // No existing challenge, inject the start button
            document.querySelector('#ec2_container').innerHTML = `<span>
                <a onclick="start_instance('${CTFd.lib.$('#challenge-id').val()}');" class='btn btn-success'>
                    <small style='color:white;'><i style='margin-right: 5px;' class="fas fa-play"></i>Start Challenge</small>
                </a>
            </span>`
        }
    });
};

function start_instance(challenge) {
    running = false;
    document.querySelector('#ec2_container').innerHTML = '<div class="text-center"><i class="fas fa-circle-notch fa-spin fa-1x"></i><br><small>Starting challenge...</small></div>';
    fetch(`/api/v1/instance?${new URLSearchParams({ 'id': challenge })}`).then(result => result.json()).then(result => {
        if (!result.success) {
            if (result.data[0].indexOf("running") > 0) {
                ezq({ title: "Challenge already running", body: `You already have a challenge already running (${result.data[1]})<br><br>Would you like to stop that challenge and start this one?` }).then(() => {
                    stop_instance(result.data[2], result.data[3], false);
                    setTimeout(() => {
                        start_instance(challenge);
                    }, 250);
                })
            } else {
                ezal({ title: "Failed to start challenge", body: result.data[0], button: "Dismiss" });
            }
        } else {
            // Instance started successfully, now wait for IP
            wait_for_ip_and_show_status(challenge);
        }
    });
}

function wait_for_ip_and_show_status(challenge) {
    let attempts = 0;
    const maxAttempts = 60; // 60 seconds timeout
    const checkInterval = 1000; // Check every second
    
    const checkForIP = () => {
        attempts++;
        
        // Update spinner message
        const statusMessages = [
            'Provisioning VM challenge...',
            'Doing stuff and things...',
            'Injecting stuff...',
            'Downloading viruses to your computer...',
            'Almost ready...',
            'Need coffee...',
            'Killing time...',
            'Killing in the name of...'
        ];
        const messageIndex = Math.min(Math.floor(attempts / 10), statusMessages.length - 1);
        document.querySelector('#ec2_container').innerHTML = 
            `<div class="text-center"><i class="fas fa-circle-notch fa-spin fa-1x"></i><br><small>${statusMessages[messageIndex]}</small></div>`;
        
        // Check if instance is running and get status
        fetch("/api/v1/ec2").then(result => result.json()).then(result => {
            const taskItem = result['data'].find(item => item.challenge_id == challenge);
            
            if (taskItem) {
                // Instance exists, check its status
                fetch(`/api/v1/instance_status?${new URLSearchParams({ instanceId: taskItem.instance_id })}`)
                    .then(result => result.json())
                    .then(statusResult => {
                        if (statusResult['success']) {
                            if (statusResult['data']['running']) {
                                // Instance is running, check if we have an IP
                                if (statusResult['public_ip'] && statusResult['public_ip'].trim() !== '') {
                                    // We have an IP! Show the final status
                                    show_final_status(challenge, taskItem, statusResult['public_ip']);
                                    return;
                                }
                            }
                        }
                        
                        // No IP yet, continue checking
                        if (attempts < maxAttempts) {
                            setTimeout(checkForIP, checkInterval);
                        } else {
                            // Timeout - show error
                            document.querySelector('#ec2_container').innerHTML = 
                                '<div class="text-center text-danger"><i class="fas fa-exclamation-triangle"></i><br><small>Timeout waiting for IP address</small></div>';
                        }
                    })
                    .catch(error => {
                        console.error('Error checking instance status:', error);
                        if (attempts < maxAttempts) {
                            setTimeout(checkForIP, checkInterval);
                        } else {
                            document.querySelector('#ec2_container').innerHTML = 
                                '<div class="text-center text-danger"><i class="fas fa-exclamation-triangle"></i><br><small>Error retrieving IP address</small></div>';
                        }
                    });
            } else {
                // Instance not found yet, continue checking
                if (attempts < maxAttempts) {
                    setTimeout(checkForIP, checkInterval);
                } else {
                    // Timeout - show error
                    document.querySelector('#ec2_container').innerHTML = 
                        '<div class="text-center text-danger"><i class="fas fa-exclamation-triangle"></i><br><small>Timeout waiting for instance to start</small></div>';
                }
            }
        })
        .catch(error => {
            console.error('Error checking EC2 status:', error);
            if (attempts < maxAttempts) {
                setTimeout(checkForIP, checkInterval);
            } else {
                document.querySelector('#ec2_container').innerHTML = 
                    '<div class="text-center text-danger"><i class="fas fa-exclamation-triangle"></i><br><small>Error checking instance status</small></div>';
            }
        });
    };
    
    // Start checking
    checkForIP();
}

function show_final_status(challenge, taskItem, publicIP) {
    // Create the final status display
    const containerId = String(taskItem.instance_id).replaceAll(":", "_").replaceAll("/", "_");
    document.querySelector('#ec2_container').innerHTML = 
        `<div class="mt-2" id="${containerId}_revert_container"></div><div class="mt-2" id="${containerId}_connect_to_container"></div>`;
    
    const revert_section = document.querySelector(`#${containerId}_revert_container`);
    const connect_section = document.querySelector(`#${containerId}_connect_to_container`);
    
    // Show the IP and reset button
    connect_section.innerHTML = `<span class="text-success"><strong>IP: ${publicIP}</strong></span>`;
    revert_section.innerHTML = `<a onclick="start_instance('${challenge}');" class='btn btn-danger'><small style='color:white;'><i style='margin-right: 5px;' class="fas fa-redo"></i>Reset Challenge</small></a>`;
}

function stop_instance(challenge, instance_id, refresh = true) {
    console.log('DEBUG: stop_instance called with challenge:', challenge, 'instance_id:', instance_id);
    running = false;
    document.querySelector('#ec2_container').innerHTML = '<div class="text-center"><i class="fas fa-circle-notch fa-spin fa-1x"></i></div>';
    const url = `/api/v1/ec2_nuke?${new URLSearchParams({ 'instance': instance_id })}`;
    console.log('DEBUG: Calling endpoint:', url);
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
        .then(result => {
            if (!result.ok) {
                // If response is not OK, try to get error message
                return result.text().then(text => {
                    try {
                        return JSON.parse(text);
                    } catch {
                        throw new Error(`HTTP ${result.status}: ${text.substring(0, 100)}`);
                    }
                });
            }
            return result.json();
        })
        .then(data => {
            if (data.success) {
                if (refresh) {
                    get_ec2_status(challenge);
                }
            } else {
                console.error('Failed to stop instance:', data.error || 'Unknown error');
                alert('Failed to stop instance: ' + (data.error || 'Unknown error'));
                if (refresh) {
                    get_ec2_status(challenge);
                }
            }
        })
        .catch(error => {
            console.error('Error stopping instance:', error);
            alert('Error stopping instance: ' + error.message);
            if (refresh) {
                get_ec2_status(challenge);
            }
        });
}

var modal =
    '<div class="modal fade" tabindex="-1" role="dialog">' +
    '  <div class="modal-dialog" role="document">' +
    '    <div class="modal-content">' +
    '      <div class="modal-header">' +
    '        <h5 class="modal-title">{0}</h5>' +
    '        <button type="button" class="close btn-close" data-dismiss="modal" data-bs-dismiss="modal" aria-label="Close">' +
    "        </button>" +
    "      </div>" +
    '      <div class="modal-body">' +
    "        <p>{1}</p>" +
    "      </div>" +
    '      <div class="modal-footer">' +
    "      </div>" +
    "    </div>" +
    "  </div>" +
    "</div>";

function ezq(args) {
    let $ = CTFd.lib.$;
    String.prototype.format = function () { return [...arguments].reduce((acc, c, ci) => acc.replace(`{${ci}}`, c), this) };
    return new Promise((resolve, reject) => {
        var res = modal.format(args.title, args.body);
        var obj = $(res);
        var deny =
            $('<button type="button" class="btn btn-danger" data-dismiss="modal" data-bs-dismiss="modal">No</button>');
        var confirm = $(
            '<button type="button" class="btn btn-primary" data-dismiss="modal" data-bs-dismiss="modal">Yes</button>'
        );

        obj.find(".modal-footer").append(deny);
        obj.find(".modal-footer").append(confirm);

        if (!window.Modal) {
            obj.find(".close").append($("<span aria-hidden='true'>&times;</span>"));
        }

        $("main").append(obj);

        $(obj).on("hidden.bs.modal", function (e) {
            $(this).modal("dispose");
        });

        $(confirm).on("click", function () {
            resolve();
        });

        obj.modal('show');
    });
}

function ezal(args) {
    let $ = CTFd.lib.$;
    String.prototype.format = function () { return [...arguments].reduce((acc, c, ci) => acc.replace(`{${ci}}`, c), this) };

    var res = modal.format(args.title, args.body);
    var obj = $(res);
    var button = '<button type="button" class="btn btn-primary" data-dismiss="modal" data-bs-dismiss="modal">{0}</button>'.format(
        args.button
    );

    obj.find(".modal-footer").append(button);

    if (!window.Modal) {
        obj.find(".close").append($("<span aria-hidden='true'>&times;</span>"));
    }

    $("main").append(obj);

    obj.modal("show");

    $(obj).on("hidden.bs.modal", function (e) {
        $(this).modal("dispose");
    });

    return obj;
}

// Inject the bootstrap Modal plugin if window.Modal is set.
if (window.Modal) {
    let plugin = window.Modal
    let $ = CTFd.lib.$;
    const name = plugin.NAME;
    const JQUERY_NO_CONFLICT = $.fn[name];
    $.fn[name] = plugin.jQueryInterface;
    $.fn[name].Constructor = plugin;
    $.fn[name].noConflict = () => {
        $.fn[name] = JQUERY_NO_CONFLICT;
    };
}

setTimeout(() => get_ec2_status(CTFd.lib.$("#challenge-id").val()), 100);
