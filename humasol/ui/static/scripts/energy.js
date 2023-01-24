const LABEL = 'ENERGY'
const PREFIX = 'specifics-energy'

function addEnergySource() {
    console.log("Add source")
    addElementToList(
        '#energy-sources',
        insertPrefix(templates_specifics[LABEL]['source'], PREFIX + '-sources-x')
    );
}

function addEnergyStorage() {
    console.log("Add storage")
    addElementToList(
        '#energy-storages',
        insertPrefix(templates_specifics[LABEL]['storage'], PREFIX + '-storage-x')
    );
}

function addEnergyLoad() {
    console.log("Add load")
    addElementToList(
        '#energy-consumptions',
        insertPrefix(templates_specifics[LABEL]['consumption'], PREFIX + '-consumptions-x')
    );
}

function toggleOverheats(element) {
    const fields = ['overheating_time', 'cooldown_time']

    $(element).siblings()
        .filter(
            (_, e) =>
                fields.some(f => ($(e).attr('id') || $(e).attr('for')).includes(f))
        ).each((_, elem) => $(elem).toggle(element.checked))
}

function selectComponentType(selector, type) {
    // Create a reference to the fields of that same partner
    let card = $(selector).parent().parent()
    let component = card.find('#component')

    let selected = component.find('#' + type)

    console.log(selected.length)


    if (selected.length > 0){
        if (selected.hasClass("hidden")) {
            selected.toggleClass("hidden");
        }
    } else {
        component.append(
            insertPrefix(
                templates_specifics[LABEL][type],
                PREFIX + '-sources-x'
            )
        )
        // Renumber the element in the list so the form parser will work
        renumberListElements('#' + card.parent().attr('id'), (n) => { return n == 'x' });
    }

    component.children().each((idx, elem) => {
        let child = $(elem)

        if (child.attr('id') != type && !child.hasClass('hidden')) {
            child.toggleClass("hidden")
        }
    })
}
