$(document).ready(function () {
    $(`.full-popup`).on('click', function (event) {
        if (event.target.id === 'full-popup')
            $(`.full-popup`).removeClass('active').find(`> form`).removeClass('active');
    });
})

function show_request_form() {
    $('#request-form').addClass('active').parent().addClass('active');
}

function show_feedback_form(caller) {
    console.log(caller.value);
    $('#feedback-form').addClass('active').parent().addClass('active');
    $(`#feedback-form input[name='req_id']`).val(caller.value);
}   