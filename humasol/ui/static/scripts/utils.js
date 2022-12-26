
function addElementToList(listId, element) {
    // Add element
    $(listId).append( element );

    // Check if max elements reached and deactivate button if necessary
    toggleButton(listId);

    // Number the new element correctly so the form parser will work
    renumberElements(listId, (n) => { return n == 'x' });
}

function addScript(id, src, callback=null) {
    if ($( "#" + id ).length ) return

    let newScript = document.createElement("script");
    newScript.setAttribute("id", id);
    newScript.setAttribute("src", src);
    document.body.appendChild(newScript);

    if (callback) {
        newScript.addEventListener("load", callback, false);
    }
}

function scriptLoaded() {
  console.log("Script is ready to rock and roll!");
}

function deleteElement(element, levels=2) {
    // Get a reference to the card that contains the clicked cross and remove it
    // Also get a reference to the list containing it
    let card = $(element)
    for(let l = 0; l < levels; l++) {
        card = card.parent()
    }

    let list = card.parent();
    card.remove()
    let listId = '#' + list.attr('id');

    // Reactivate the button if it had been deactivated
    toggleButton(listId);
    // Renumber the element in the list so the form parser will work
    renumberElements(listId, (n) => { return isNumeric(n) });
}

function getIndex(item) {
    let name = item.attr('name').split('-');
    let idx;

    for (var part in name) {
        if (isNumeric(name[part])) {
            idx = name[part];
            break;
        }
    }

    return idx
}

function insertIndex(index, inputs, labels, check, reverse=false) {
    inputs.each((idx, item) => {
        // Convert item from DOM element to jquery object
        item = $(item)

        let name = item.attr('name').split('-');

        // If number in name, substitute it by the current card index
        let found = false
        if (reverse) {  // Used for nested lists (e.g., periods of a task)
            for(let part = name.length - 1; part >= 0; part--) {
                if (check(name[part])) {
                    found = true
                    name[part] = index
                    break
                }
            }
        } else {
            let part
            for (part in name) {
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

function insertPrefix(template, prefix) {
    // Convert item from DOM element to jquery object
    let item = $(template);

    // Get all the input fields in the card
    let labels = item.find('label')
    let inputs = item.find('input, select, textarea')

    labels.each((index, elem) => {
        // Convert item from DOM element to jquery object
        let label = $(elem)

        // Insert prefix
        let for_attr = prefix + '-' + label.attr('for');

        // Set new attribute
        label.attr('for', for_attr)
    })

    inputs.each((index, elem) => {
        // Convert item from DOM element to jquery object
        let input = $(elem)

        // Insert prefix
        let id = prefix + '-' + input.attr('id');
        let name = prefix + '-' + input.attr('name');

        // Set new attribute
        input.attr('id', id)
        input.attr('name', name)
    })

    return item.get()
}

function isNumeric(str) {
    // Only process strings
    if (typeof str != "string") {
      return false
    }

    return !isNaN(str) && // use type coercion to parse the _entirety_ of the string (`parseFloat` alone does not do this)...
            !isNaN(parseFloat(str)) // ...and ensure strings of whitespace fail
}

function onSliderChange(element) {
    let item = $(element)
    let label = $('label[for=' + item.attr('id') + ']')[0]

    label.innerHTML = label.innerHTML.replace(
        /\d{1,2}/,
        Math.round(item.val())
    )
}

function renumberElements(listId, elementIdentifier) {
    // Get all cards in the provided list
    let items = $(listId).children();

    items.each((index, item) => {
        // Convert item from DOM element to jquery object
        item = $(item)

        // Get all the input fields in the card
        let labels = item.find('label')
        let inputs = item.find('input, select, textarea')

        // Remove extra labels
        // (e.g. for Partner, the organization label has no corresponding input)
        labels = popLabels(listId, labels)

        // Update the index contained in the name attribute
        insertIndex(index, inputs, labels, elementIdentifier)

        // If it's follow-up work then also the periods need to be renamed appropriately
        if (listId == '#tasks' || listId == '#subscriptions') {
            renumberPeriods(item.find('.form-grid'), elementIdentifier)
        }
    })
}
