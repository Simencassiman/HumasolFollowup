
function addElementToList(listId, element) {
    // Add element
    $(listId).append( element );

    // Check if max elements reached and deactivate button if necessary
    toggleButton(listId);

    // Number the new element correctly so the form parser will work
    renumberElements(listId, (n) => { return n == 'x' });
}

function addScript(id, src) {
    if ($( "#" + id ).length ) return

    let newScript = document.createElement("script");
    newScript.setAttribute("id", id);
    newScript.setAttribute("src", src);
    document.body.appendChild(newScript);
    //newScript.addEventListener("load", scriptLoaded, false);
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

function isNumeric(str) {
    // Only process strings
    if (typeof str != "string") {
      return false
    }

    return !isNaN(str) && // use type coercion to parse the _entirety_ of the string (`parseFloat` alone does not do this)...
            !isNaN(parseFloat(str)) // ...and ensure strings of whitespace fail
}
