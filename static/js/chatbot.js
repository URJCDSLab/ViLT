let eventSource = null;

// Function to handle SSE and update the response div
function setupSSE() {
    if (eventSource) {
        eventSource.close();
    }

    let email = document.getElementById("email_hidden").value;
    let career = document.getElementById("career_hidden").value;
    let subject = document.getElementById("subject_hidden").value;
    eventSource = new EventSource("/stream?email=" + email + "&career=" + career + "&subject=" + subject);

    eventSource.onmessage = function(event) {
        let data = JSON.parse(event.data);
        let type = data.type;
        let content = data.content;

        // Append the message to the response div based on the role
        if (type === "token") {
            $('#response .robot').last().append(content);
        }
        else if (type === "error") {
            console.log(content);
        }

        // Scroll to the bottom of the output container
        let outputContainer = document.getElementById("response");
        outputContainer.scrollTop = outputContainer.scrollHeight;
    };

    eventSource.onopen = function(event) {
        console.log("SSE connection opened.");
    };

    // Handle errors
    eventSource.onerror = function(event) {
        console.error("EventSource failed:", event);
        eventSource.close();
    };

    // Close the EventSource when the page is unloaded
    window.onbeforeunload = function() {
        console.error("SSE connection closed.");
        eventSource.close();
    };
}

// Call the setupSSE function when the page is ready
$(document).ready(function() {
    setupSSE();

    $('#prompt').keypress(function(event) {
        if (event.keyCode === 13 && !event.shiftKey) {
            event.preventDefault();
            $('#textform').submit();
        }
    });

    $('#textform').on('submit', function(event) {
        event.preventDefault();
        // get the CSRF token from the cookie
        var csrftoken = Cookies.get('csrftoken');

        // set the CSRF token in the AJAX headers
        $.ajaxSetup({headers: {'X-CSRFToken': csrftoken}});

        // Get the prompt
        let prompt = $('#prompt').val();
        var dateTime = new Date();
        var time = dateTime.toLocaleTimeString();
        var email = $('#email_hidden').val()
        var career = $('#career_hidden').val()
        var subject = $('#subject_hidden').val()


        // Append the prompt to the response div
        if (prompt !== "") {
            $('#response').append('<p id="GFG1" class="human">(' + time + ') <i class="bi bi-person"></i>: ' + prompt + '</p>');
        }
        // Clear the prompt
        $('#prompt').val('');
        $.ajax({
            url: '/chat',
            type: 'POST',
            data: {
                prompt: prompt,
                email: email,
                career: career,
                subject: subject
                },
                dataType: 'json',
                success: function(data) {
                    if (data.status === 'success' && prompt !=="") {
                        // Append the response to the response div
                        $('#response').append('<span id="GFG2" class="robot">('+ time + ') <i class="bi bi-robot"></i>: </span>');
                    }
                }
        });
    });
});

window.addEventListener('beforeunload', (event) => {
    chatbot_cleanup()
    event.preventDefault();
    event.returnValue = '';
});

function chatbot_cleanup() {
    var email = document.getElementById("email_hidden").value;
    var career = document.getElementById("career_hidden").value;
    var subject = document.getElementById("subject_hidden").value;
    var_url = "/chatbot-cleanup?email=" + email + "&career=" + career + "&subject=" + subject;
    jQuery.ajax({
        url: var_url,
        success: function () {
            pass;
        }
    });
}