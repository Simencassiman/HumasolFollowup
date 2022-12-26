const MAX_STUDENTS = 4;
const MAX_ENTRIES = 10;

const SCRIPT_SUFFIX = '-script'


/******************
 Project specifics
*******************/

function projectSpecifics(category) {
    let elements = $(category).find("input")

    let selected
    for(let i in elements) {
        if(elements[i].checked) {
            selected = elements[i].value
            break;
        }
    }

    if (selected in templates_specifics) {
        setProjectSpecifics(templates_specifics[selected]['base']);

        if ('js' in templates_specifics[selected]) {
            addScript(
                selected.toLowerCase() + SCRIPT_SUFFIX,
                templates_specifics[selected]['js']
            )
        }

    } else {
        setProjectSpecifics(templates_specifics['default']['base']);
    }
}

function setProjectSpecifics(content) {

    let ps = $("#project-specific")

    if (ps.hasClass("hidden")) {
        ps.removeClass("hidden")
    }

    ps.html(content)
}


/******************
 Add list elements
*******************/
function addStudent() {
    addElementToList('#students', templates['student']);
}

function addSupervisor() {
    addElementToList('#supervisors', templates['supervisor']);
}

function addPartner() {
    addElementToList('#partners', templates['partner']);
}

function selectPartnerType(selector, type) {
    // Create a reference to the fields of that same partner
    let id = $(selector).attr('id').split('-')

    // Correct the id to partners-x-organization-country (x being the index)
    id[id.length - 1] = 'organization';
    id.push('country');
    id = id.join('-');

    // Retrieve label and input fields
    let label = $('label[for="' + id + '"]')
    let input = $('#' + id)

    // Toggle visibility of both the country label and input
    if (type == 'bp' && !input.hasClass("hidden")) {
        label.addClass("hidden");
        input.addClass("hidden");
    } else if (type == 'sp' && input.hasClass("hidden")) {
        label.removeClass("hidden");
        input.removeClass("hidden");
    }
}

function addTask() {
    addElementToList('#tasks', templates['task']);
}

function addSubscription() {
    addElementToList('#subscriptions', templates['subscription']);
}

function taskSubscriberType(selector, origin) {
    switch(selector.value) {
        case "stu":
            replaceSubscriber(selector, templates['task-student']);
            break;
        case "sup":
            replaceSubscriber(selector, templates['task-supervisor']);
            break;
        case "par":
            replaceSubscriber(
                selector,
                templates['task-partner'],
                true
            );
            break;
        default:
            break;
    }
}

function subscriptionSubscriberType(selector, origin) {
    switch(selector.value) {
        case "stu":
            replaceSubscriber(selector, templates['subscription-student']);
            break;
        case "sup":
            replaceSubscriber(selector, templates['subscription-supervisor']);
            break;
        case "par":
            replaceSubscriber(
                selector,
                templates['subscriber-partner'],
                true
            );
            break;
        default:
            break;
    }
}

function addPeriod(elem, prefix) {
    addPeriodToList(elem, templates['period'], prefix);
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

function renumberPeriods(grid, elementIdentifier) {
    grid.children().each((idx, period) => {
        // Convert item from DOM element to jquery object
        period = $(period)

        // Get all the input fields in the period
        let labels = period.find('label')
        let inputs = period.find('input, select, textarea')

        // Update the index contained in the name attribute
        // Traverse name in reverse to find the second number first
        insertIndex(idx, inputs, labels, elementIdentifier, true)
    });
}

function toggleButton(listId) {
    // Create ID reference to the button in question
    // Buttons corresponding to a list with ID lid are named lid-button
    let buttonId = listId + '-button'; // listId includes # for jquery

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

function addPeriodToList(btn, period, prefix) {
    let list = $(btn).parent().parent().parent().find('.form-grid')

    period = $(period)

    // Get all the input fields in the card
    let labels = period.find('label')
    let inputs = period.find('input, select, textarea')

    inputs.each((idx, item) => {
        let name = $(item).attr('name').split('-')
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
    let grid = $(btn).parent().parent().parent()

    $(btn).parent().parent().remove()
    renumberPeriods(grid, (n) => { return isNumeric(n) })
}

function showFollowup() {
    // Show followup section
    $("#project-followup").removeClass("hidden");
    // Hide button for followup (so it can't be pressed again, useless anyway)
    $("#btn-followup").addClass("hidden");
}

/**************
  Follow-up
***************/
function replaceSubscriber(selector, content, isPartner=false) {

    // Convert arguments to jQuery objects
    selector = $(selector);
    let sub = $(content);

    // Find task or subscription index from select element
    let idx = getIndex(selector);

    // Get all the input fields in the new subscriber card
    let labels = sub.find('label');
    let inputs = sub.find('input, select, textarea');

    if (isPartner) {
        labels = popLabels('#partners', labels);
    }

    // Set correct index in names and attributes so the form
    // gets parsed correctly
    insertIndex(idx, inputs, labels, (n) => { return n == 'x' })

    // Insert new subscriber in html
    let subSection = selector.parent().parent().parent().children()[1];
    subSection = $(subSection)
    // Remove old card
    subSection.children()[1].remove();
    // Insert new card
    subSection.append(sub);

}
