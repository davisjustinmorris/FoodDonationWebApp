$(document).ready(function () {
    $('.log_sign').on('click', toggle_log_sign);

    setTimeout(
        () => $('#refresh_message').text(""),
        5000,
    );

})

function toggle_log_sign() {
    $(`#login, #signup`).toggleClass('active');
}
