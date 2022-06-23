$(document).ready(function () {
    let all_ticket_filters = $('.header_controls .filters input:checkbox');
    let all_tickets = $(`.all-tickets .request-card-container .request-card-envelop`);

    // show/hide tickets from filters
    all_ticket_filters.change(function () {
        let selections = [];

        $.each(all_ticket_filters, (i, filter) => {
            if (filter.checked) selections.push(filter.name)
        })

        all_tickets.each(function (i, card) {
            let req_status = $(card).find(`input[name="request_status"]`).val();

            if (selections.includes(req_status)) $(card).show();
            else {
                $(card).find('input[name="selection"]').prop('checked', false);
                $(card).hide();
            }
        })
    });

    // for making checkbox work for clicks to tickets
    all_tickets.on('click', function (event) {
        if (
            (event.target.name === "selection") ||
            (event.target.name === "do_review") ||
            ($(event.target).parent()[0].name === "do_review") ||
            event.target.classList.contains("contact-phone") ||
            $(event.target).parent()[0].classList.contains("contact-phone")
        ) return

        $(this).find('input[type="checkbox"]').click();
    });

    // actions: mark-delivered for tickets
    $('#ticket-actions .mark:not(.disabled)').on('click', function () {
        console.log('mark requested');
        do_mark_connect_requests('mark-confirmed-tickets-delivered');
    });

    // actions: connect tickets
    let connect_button = $('#ticket-actions .connect');
    connect_button.on('click', function () {
        if (connect_button.hasClass('disabled')) return;
        console.log('connect requested');
        do_mark_connect_requests('connect-open-requests');
    });

    // ui adjustments for connecting requests
    $(all_tickets).find('input[type="checkbox"]').on('change', function () {
        let checked_boxes = $(all_tickets).find('input[type="checkbox"]:checked');

        if (checked_boxes.length === 2) {
            // flags assume conditions
            let has_donate = false;
            let has_receive = false;
            let is_all_created_type = true;

            checked_boxes.each(function (i, cb_element) {
                console.log(cb_element);
                if ($(cb_element).parents('.request-card').find('input[name="request_type"]').val()==1)
                    has_donate = true;
                else
                    has_receive = true;

                if ($(cb_element).parents('.request-card').find('input[name="request_status"]').val() != "created")
                    is_all_created_type = false;
            })

            // check flags
            if (has_donate && has_receive && is_all_created_type) {
                $('#ticket-actions .connect').removeClass('disabled');
                return
            }
        }

        $('#ticket-actions .connect').addClass('disabled');
    });

    // OnClick for Do_Review button in cards
    $(`button[name="do_review"]`).on('click', function () {
        let req_id = $(this).parent().parent().parent().parent().find('input[name="request_id"]').val();
        $('#full-popup').addClass('active');
        $('#full-popup #feedback-form').addClass('active');
        $('#full-popup #feedback-form input[name="req_id"]').val(req_id);

        $('#feedback-form textarea').val('');
        $('#feedback-form input[type="radio"]').prop('checked', false);
    })

    // feedback popup submit click handler
    $('#feedback-form').submit(function (e) {
        // perform input validation
        if (!($('#feedback-form input[name="rating_value"]:checked').val() && $('#feedback-form textarea').val())) {
            e.preventDefault();
            alert('please choose a rating and provide review to continue');
        }
    });
});

function do_mark_connect_requests(task) {
    let marked_ids = $('.all-tickets .request-card input[type="checkbox"]:checked')
        .parents('.request-card').find('input[name="request_id"]');

    let marked_ids_list = [];
    marked_ids.each(function (i, id_element) {
        // console.log(id_element);
        marked_ids_list.push($(id_element).val());
    });

    console.log(marked_ids_list);

    $.ajax({
        type: 'POST',
        url: window.location.pathname,
        data: JSON.stringify ({
            'task': task,
            'payload': marked_ids_list
        }),
        success: (data) => {
            console.log(data);
            if (data.success) window.location.reload();
        },
        contentType: "application/json",
        dataType: 'json'
    });
}
