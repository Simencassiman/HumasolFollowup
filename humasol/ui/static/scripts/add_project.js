const MAX_STUDENTS = 4;
const MAX_ENTRIES = 10;


/******************
 Project specifics
*******************/

function setProjectSpecifics(content) {

    if ($("#project-specific").hasClass("hidden")) {
        $("#project-specific").removeClass("hidden")
    }

    $("#specifics-content").html(content)
}

function toggleEnergyComponent(checkbox) {
    var row = $(checkbox).parent().parent().parent().parent().children()


    row.each((idx, item) => {
        if (idx > 0) {
            item = $(item)

            if (checkbox.checked && item.hasClass("hidden")){
                item.removeClass("hidden")
            } else if (!checkbox.checkbox && !item.hasClass("hidden")) {
                item.addClass("hidden")
            }
        }
    });

    checkMultipleEnergySources();
}

function checkMultipleEnergySources() {
    var sources = 0
    var components = $(".energy-component")

    components.each((idx, item) => {
        var checkbox = $($(item).children()[0]).find("input")[0]
        console.log(checkbox);

        if(checkbox.checked) {
            sources++
        }
    })

    components.each((idx, item) => {
        var checkbox = $($(item).children()[0]).find("input")[0]

        var row = $($(item).children()[1])

        if (checkbox.checked){
            if (sources > 1 && row.hasClass("hidden")) {
                row.removeClass("hidden")
            } else if (sources <= 1 && !row.hasClass("hidden")) {
                row.addClass("hidden")
            }
        } else {
            if (!row.hasClass("hidden")) {
                row.addClass("hidden")
            }
        }
    })
}


/******************
 Field Lists
*******************/

function popLabels(listId, labels) {
    // Remove labels with no corresponding input
    if (listId == '#partners') {
        labels.splice( 5, 1)
    } else if (listId == '#tasks') {
        labels.splice( 9, 1)
        labels.splice( 3, 1)
    } else if (listId == '#subscriptions') {
        labels.splice( 7, 1)
        labels.splice( 1, 1)
    }

    return labels;
}

function isNumeric(str) {
    // Only process strings
    if (typeof str != "string") {
      return false
    }

    return !isNaN(str) && // use type coercion to parse the _entirety_ of the string (`parseFloat` alone does not do this)...
            !isNaN(parseFloat(str)) // ...and ensure strings of whitespace fail
}

function insertIndex(index, inputs, labels, check, reverse=false) {
    inputs.each((idx, item) => {
        // Convert item from DOM element to jquery object
        item = $(item)

        var name = item.attr('name').split('-');

        // If number in name, substitute it by the current card index
        var found = false
        if (reverse) {  // Used for nested lists (e.g., periods of a task)
            for(var part = name.length - 1; part >= 0; part--) {
                if (check(name[part])) {
                    found = true
                    name[part] = index
                    break
                }
            }
        } else {
            for (var part in name) {
                if (check(name[part])) {
                    found = true
                    name[part] = index
                    break
                }
            }
        }

        // Only the card with a name matching 'check' will need to be updated
        if (found) {
            // Recombine the split and updated name
            name = name.join('-');

            // Labels have a for attribute referencing the id of an input
            labels.eq(idx).attr('for', name);
            item.attr('id', name);
            // Inputs have a name and id attribute that should be updated
            item.attr('name', name);
        }
    })
}

function renumberPeriods(grid, elementIdentifier) {
    grid.children().each((idx, period) => {
        // Convert item from DOM element to jquery object
        period = $(period)

        // Get all the input fields in the period
        var labels = period.find('label')
        var inputs = period.find('input, select, textarea')

        // Update the index contained in the name attribute
        // Traverse name in reverse to find the second number first
        insertIndex(idx, inputs, labels, elementIdentifier, true)
    });
}

function renumberElements(listId, elementIdentifier) {
    // Get all cards in the provided list
    var items = $(listId).children();

    items.each((index, item) => {
        // Convert item from DOM element to jquery object
        item = $(item)

        // Get all the input fields in the card
        var labels = item.find('label')
        var inputs = item.find('input, select, textarea')

        // Remove extra labels
        // (e.g. for Partner, the organization label has no corresponding input)
        labels = popLabels(listId, labels)

        // Update the index contained in the name attribute
        insertIndex(index, inputs, labels, elementIdentifier)

        // If it's follow-up work then also the periods need to be renamed appropriately
        if (listId == '#tasks' || listId == '#subscriptions') {
            console.log('Renumbering periods');
            renumberPeriods(item.find('.form-grid'), elementIdentifier)
        }
    })
}

function toggleButton(listId) {
    // Create ID reference to the button in question
    // Buttons corresponding to a list with ID lid are named lid-button
    var buttonId = listId + '-button'; // listId includes # for jquery

    // Less students are allowed than for the other categories
    if (listId == '#students' && $(listId).children().length >= MAX_STUDENTS
          || $(listId).children().length >= MAX_ENTRIES) {
              $(buttonId).addClass("hidden");
    }else if ((listId != '#students' && $(listId).children().length < MAX_ENTRIES
          || $(listId).children().length < MAX_STUDENTS) &&
        $(buttonId).hasClass("hidden") > -1) {
        $(buttonId).removeClass("hidden");
    }
}

function addElementToList(listId, element) {
    // Add element
    $(listId).append( element );

    // Check if max elements reached and deactivate button if necessary
    toggleButton(listId);

    // Number the new element correctly so the form parser will work
    renumberElements(listId, (n) => { return n == 'x' });
}

function deleteElement(element, levels=2) {
    // Get a reference to the card that contains the clicked cross and remove it
    // Also get a reference to the list containing it
    var card = $(element)
    for(var l = 0; l < levels; l++) {
        card = card.parent()
    }

    var list = card.parent();
    card.remove()
    var listId = '#' + list.attr('id');

    // Reactivate the button if it had been deactivated
    toggleButton(listId);
    // Renumber the element in the list so the form parser will work
    renumberElements(listId, (n) => { return isNumeric(n) });
}

function addPeriodToList(btn, period, prefix) {
    var list = $(btn).parent().parent().parent().find('.form-grid')

    period = $(period)

    // Get all the input fields in the card
    var labels = period.find('label')
    var inputs = period.find('input, select, textarea')

    inputs.each((idx, item) => {
        var name = $(item).attr('name').split('-')
        name[0] = prefix
        name = name.join('-')

        // Labels have a for attribute referencing the id of an input
        labels.eq(idx).attr('for', name);
        $(item).attr('id', name);
        // Inputs have a name and id attribute that should be updated
        $(item).attr('name', name);
    })

    list.append(period)
    renumberElements('#' + prefix, (n) => { return n == 'x' }); // Actually too much work... but easy
}

function deletePeriod(btn) {
    var grid = $(btn).parent().parent().parent()

    $(btn).parent().parent().remove()
    renumberPeriods(grid, (n) => { return isNumeric(n) })
}

function showFollowup() {
    // Show followup section
    $("#project-followup").removeClass("hidden");
    // Hide button for followup (so it can't be pressed again, useless anyway)
    $("#btn-followup").addClass("hidden");
}

function selectPartnerType(selector, type) {
    // Create a reference to the fields of that same partner
    var id = $(selector).attr('id').split('-')

    // Correct the id to partners-x-organization-country (x being the index)
    id[id.length - 1] = 'organization';
    id.push('country');
    id = id.join('-');

    // Retrieve label and input fields
    var label = $('label[for="' + id + '"]')
    var input = $('#' + id)

    // Toggle visibility of both the country label and input
    if (type == 'bp' && !input.hasClass("hidden")) {
        label.addClass("hidden");
        input.addClass("hidden");
    } else if (type == 'sp' && input.hasClass("hidden")) {
        label.removeClass("hidden");
        input.removeClass("hidden");
    }
}


/**************
  Follow-up
***************/

function getIndex(item) {
    var name = item.attr('name').split('-');
    var idx;

    for (var part in name) {
        if (isNumeric(name[part])) {
            idx = name[part];
            break;
        }
    }

    return idx
}

function replaceSubscriber(selector, content, isPartner=false) {

    // Convert arguments to jQuery objects
    selector = $(selector);
    var sub = $(content);

    // Find task or subscription index from select element
    var idx = getIndex(selector);

    // Get all the input fields in the new subscriber card
    var labels = sub.find('label');
    var inputs = sub.find('input, select, textarea');

    if (isPartner) {
        labels = popLabels('#partners', labels);
    }

    // Set correct index in names and attributes so the form
    // gets parsed correctly
    insertIndex(idx, inputs, labels, (n) => { return n == 'x' })

    // Insert new subscriber in html
    var subSection = selector.parent().parent().parent().children()[1];
    subSection = $(subSection)
    // Remove old card
    subSection.children()[1].remove();
    // Insert new card
    subSection.append(sub);

}
