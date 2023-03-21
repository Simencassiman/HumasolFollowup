/**
 * Allow a form submission without reloading the page.
 *
 * @param endpoint to which to submit the form
 * @param form  id of the html element
 * @param inputs list of input names (attribute name) from which to collect
 *      the data
 * @param func function to execute on success
 * @param types optionally specify types of inputs (e.g., input or select)
 */
function changeFormSubmit(endpoint, form, inputs, func, types=null) {
    $(document).on('submit', "#" + form, function(e) {
        e.preventDefault();
        $.ajax({
            type: 'POST',
            url: endpoint,
            data: types
                ? Object.fromEntries(
                    inputs.map(
                        (x, i) => [x, $(types[i] + "#" + x).val()]
                    )
                )
                : Object.fromEntries(
                inputs.map( x => [x, $("input#" + x).val()])
            ),
            success: func
        })
    });
}

function defer(fn) {
    if (window.jQuery) {
        fn();
    } else {
        setTimeout(() => defer(fn) , 50);
    }
}

function loadContent(url, container) {
    defer(() => {
        $("#loader").toggleClass("hidden");
        $.get(url, function( data ) {
            $("#loader").toggleClass("hidden");
            $(container).html( data );
        })
    })
}
