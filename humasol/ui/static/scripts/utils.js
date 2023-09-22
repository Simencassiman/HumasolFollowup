SEPARATOR = '-'


function addElementToList(listId, element, prefix=null, depth=0) {
    if (prefix) {
        // Add prefix to all labels and input items
        element = insertPrefix($(element), prefix)
    }

    // Add element
    const list = $(listId);
    list.append( element[0] );

    // Number the new element correctly so the form parser will work
    renumberListElements(listId, (n) => { return n == 'x' }, depth);
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

function changeTab(target) {
    let tabs = $('#sidebar')
    let panels = $('#panels')

    // Toggle tab display
    tabs.children('div')
        .each((idx, item) => {
            item = $(item)
            if (item.attr('id') == (target + '-tab') && !item.hasClass('visible')) {
                item.addClass('visible')
            } else if (item.attr('id') != (target + '-tab') && item.hasClass('visible')) {
                item.removeClass('visible')
            }
    })

    // Toggle panel display
    panels.children('div.panel')
        .each((idx, elem) => {
            elem = $(elem)
            if (elem.attr('id') == target && elem.hasClass('hidden')) {
                elem.removeClass('hidden')
            } else if (elem.attr('id') != target && !elem.hasClass('hidden')) {
                elem.addClass('hidden')
            }
    })

    const yOffset = -110;
    const element = document.getElementById('tabs-top');

    if (element != null) {
        const y = element.getBoundingClientRect().top + window.scrollY + yOffset;

        window.scrollTo({top: y, behavior: 'smooth'});
    }
}

function scriptLoaded() {
  console.log("Script is ready to rock and roll!");
}

/**
 * Deletes a card element containing the clicked element from its parent list.
 * The function assumes that the card to be deleted has and ID attribute and
 * that it is of the form [prefix-]listId-X, where x is the number indicating
 * the position in the list (zero indexed).
 *
 * @effect renumbers the list items in the parent list after the selected
 * element is deleted
 *
 * @param element clicked element that called this function
 * @param depth list depth, i.e. if it is a nested list and how many levels
 * precede it
 *
 * @return ID of the parent list from which the card has been deleted
 */
function deleteElement(element, depth=0) {
    // Get a reference to the card that contains the clicked cross and remove it
    // Also get a reference to the list containing it
    let card = $(element)
    let regex = /([a-z]+-)+[0-9]+(-[a-z\-0-9]+)*/i
    if (!(card.attr('id') && card.attr('id').match(regex))) {
        let cards = card.parents().filter(
            (i, e) => $(e).attr('id') && $(e).attr('id').match(regex)
        )

        if (cards.length == 0) {
            return
        }
        card = $(cards.get(0))
    }

    let list = card.parent();
    card.remove()
    let listId = '#' + list.attr('id');

    // Renumber the element in the list so the form parser will work
    renumberListElements(listId, (n) => { return isNumeric(n) }, depth);

    return listId
}

function getIndex(item) {
    let name = item.attr('name').split(SEPARATOR);
    let idx;

    for (var part in name) {
        if (isNumeric(name[part])) {
            idx = name[part];
            break;
        }
    }

    return idx
}

function insertIndex(tag, index, check, depth=0) {
    const name = tag.split(SEPARATOR);

    // If number in name, substitute it by the current card index
    let found_at = 0
    let part
    for (part in name) {
        if (check(name[part])) {
            if (found_at == depth) {
                name[part] = index
                break
            }
            found_at++
        }
    }

    return name.join(SEPARATOR)
}

function insertPrefix(element, prefix) {
    // Renumber inputs and labels
    if (element.is("label") && element.attr('for')) {
        // Renumber for
        element.attr(
            'for',
            prefix + '-' + element.attr('for')
        )
        return  // Will not have children
    } else if (element.is("input, select, textarea") && element.attr('name')) {
        // Insert index in ID
        element.attr(
            'id',
            prefix + '-' + element.attr('id')
        )
        // Renumber name
        element.attr(
            'name',
            prefix + '-' + element.attr('name')
        )
        return  // Will not have children
    }

    // Recurse
    element.children().each(
        (idx, item) => insertPrefix($(item), prefix)
    )

    return element
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

function renumberElement(element, index, elementIdentifier, depth=0) {
    // Renumber IDs
    if (element.attr('id')
        && element.attr('id').match(/[a-z]+-[0-9x]+(-[a-z\-0-9]+){0,1}/i)
    ) {
        // Insert index in ID
        element.attr(
            'id',
            insertIndex(element.attr('id'), index, elementIdentifier, depth)
        )
    }

    // Renumber inputs and labels
    if (element.is("label") && element.attr('for')) {
        // Renumber for
        element.attr(
            'for',
            insertIndex(element.attr('for'), index, elementIdentifier, depth)
        )
        return  // Will not have children
    } else if (element.is("input, select, textarea") && element.attr('name')) {
        // Renumber name
        element.attr(
            'name',
            insertIndex(element.attr('name'), index, elementIdentifier, depth)
        )
        return  // Will not have children
    }

    // Recurse
    element.children().each(
        (idx, item) => renumberElement($(item), index, elementIdentifier, depth)
    )
}

function renumberListElements(listId, elementIdentifier, depth=0) {
    // Get all cards in the provided list
    let items = $(listId).children();

    items.each((index, item) => {
        // Convert item from DOM element to jquery object
        item = $(item)

        // Renumber all elements down the hierarchy
        renumberElement(item, index, elementIdentifier, depth)
    })
}
