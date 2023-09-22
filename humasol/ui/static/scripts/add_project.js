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

    // Set project specifics content
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

    // Adjust options for script pipline managers
    updateManagers(selected)
}

function selectPartnerType(selector, type) {
    // Create a reference to the fields of that same partner
    let id = $(selector).attr('id').split('-')

    // Correct the id to partners-x-organization-country (x being the index)
    id[id.length - 1] = 'organization';
    id.push('country');
    id = id.join('-');

    // Retrieve label and input fields
    let field = $('#' + id).parent()

    // Toggle visibility of both the country label and input
    if (type == 'bp' && !field.hasClass("hidden")) {
        field.addClass("hidden");
    } else if (type == 'sp' && field.hasClass("hidden")) {
        field.removeClass("hidden");
    }
}

function setProjectSpecifics(content) {

    let ps = $("#specifics-content")

    if (ps.hasClass("hidden")) {
        ps.removeClass("hidden")
    }

    ps.html(content)
}

function updateManager(category, manager) {
    if (manager.attr('disabled')) {
        manager.removeAttr('disabled')
    }

    manager.children().each((idx, item) => {
        item = $(item)
        if (item.attr('label').toUpperCase() == category.toUpperCase()
                && item.attr('disabled')) {
            item.removeAttr('disabled')
        } else if (item.attr('label').toUpperCase() != category.toUpperCase()
                && !item.attr('disabled')) {
            item.attr('disabled', '')
        }
    })
}

function updateManagers(category) {
    updateManager(category, $('#api-manager'))
    updateManager(category, $('#data-manager'))
    updateManager(category, $('#report-manager'))
}


/******************
 Add list elements
*******************/

function addPartner() {
    addElementToList('#partners', templates['partner'], 'partners-x')
    toggleButton('#partners')
}

function addPeriod(elem) {
    elem = $(elem)

    let card = elem.parent()
    while(!(card.attr('id')
        && card.attr('id').match(/[a-z]+-[0-9]+(-[a-z\-0-9]+){0,1}/i)
    )) {
        card = card.parent()
    }

    let parenID = card.attr('id')
    let template = $(templates['period'])
    template.attr('id', parenID + template.attr('id'))

    addElementToList(
        '#' + parenID + '-periods',
        template[0],
        parenID + '-periods-x'
    )
}

function addStudent() {
    addElementToList('#students', templates['student'], 'students-x')

    // Check if max elements reached and deactivate button if necessary
    toggleButton('#students', MAX_STUDENTS);
}

function addSubscription() {
    addElementToList('#subscriptions', templates['subscription'], 'subscriptions-x')
    let subs = $('#subscriptions').children()

    // Renumber period IDs
    $('#' + subs[subs.length - 1].id + '-periods').children().each(
        (idx, item) => {
            item = $(item)
            item.attr(
                'id',
                insertIndex(item.attr('id'), idx, n => {return n == 'x'})
            )
        }
    )

    toggleButton('#subscriptions')
}

function addSupervisor() {
    addElementToList('#supervisors', templates['supervisor'], 'supervisors-x')
    toggleButton('#supervisors')
}

function addTask() {
    addElementToList('#tasks', templates['task'], 'tasks-x')
    let tasks = $('#tasks').children()

    // Renumber period IDs
    $('#' + tasks[tasks.length - 1].id + '-periods').children().each(
        (idx, item) => {
            item = $(item)
            item.attr(
                'id',
                insertIndex(item.attr('id'), idx, n => {return n == 'x'})
            )
        }
    )

    toggleButton('#tasks')
}


/******************
 Field Lists
*******************/

function deleteListElement(element, depth=0) {
    let listId = deleteElement(element, depth)

    // Reactivate the button if it had been deactivated
    toggleButton(listId);
}

function toggleButton(listId, max_entries=MAX_ENTRIES) {
    // Create ID reference to the button in question
    // Buttons corresponding to a list with ID lid are named lid-button
    let list = $(listId)
    let buttonId = listId + '-button' // listId includes # for jquery
    let button = $(buttonId)

    if(!button) {return}

    if (list.children().length >= max_entries && !button.hasClass("hidden")) {
        button.addClass("hidden")
    }
    if (list.children().length < max_entries && button.hasClass("hidden")) {
        button.removeClass("hidden")
    }
}

/**************
  Follow-up
***************/
function replaceSubscriber(selector, content, prefix) {
    const isPartner = selector.value == 'partner';

    // Convert arguments to jQuery objects
    selector = $(selector);
    let sub = insertPrefix($(content), prefix);

    // Find task or subscription index from select element
    let idx = prefix.split('-')[1];

    // Insert correct index
    renumberElement(sub, idx, n => { return n == 'x' })

    // Insert new subscriber in html
    let subSection = selector.parent();
    subSection = $(subSection)
    // Remove old card
    subSection.children()[2].remove();
    // Insert new card
    subSection.append(sub);

}

function showFollowup() {
    // Show followup section
    $("#project-followup").removeClass("hidden");
    // Hide button for followup (so it can't be pressed again, useless anyway)
    $("#btn-followup").addClass("hidden");
}

function subscriptionSubscriberType(selector) {
    const templateKey = selector.value + '-nondelete';
    const prefix = $(selector).attr('name').match(/(.+)-element_type/)[1]

    replaceSubscriber(selector, templates[templateKey], prefix);
}

function taskSubscriberType(selector) {
    const templateKey = selector.value + '-nondelete';
    const prefix = $(selector).attr('name').match(/(.+)-element_type/)[1]

    replaceSubscriber(selector, templates[templateKey], prefix);
}
