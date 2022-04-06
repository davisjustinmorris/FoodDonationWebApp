$(document).ready(function () {
    $(`.full-popup`).on('click', function (event) {
        console.log(event.target.id);
        console.log(event);
        if (event.target.id === 'full-popup')
            $(`.full-popup`).removeClass('active')
    });
})