$(document).ready(function () {
    let all_ticket_filters = $('div.all-tickets .header .filters input:checkbox');
    all_ticket_filters.change(function () {
        let selections = [];

        $.each(all_ticket_filters, (i, filter) => {
            if (filter.checked) selections.push(filter.name)
        })

        $(`.all-tickets .request-card-container .request-card`).each(function (i, card) {
            let req_status = $(card).find(`input[name="request_status"]`).val();

            if (selections.includes(req_status)) $(card).show();
            else $(card).hide();
        })
    });
});