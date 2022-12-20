const LABEL = 'ENERGY'
function addEnergySource(element) {
    console.log("Add source")
    console.log(templates[LABEL]['source'])
}

function addEnergyStorage(element) {
    console.log("Add storage")
}

function addEnergyLoad(element) {
    console.log("Add load")
}

function toggleEnergyComponent(checkbox) {
    let row = $(checkbox).parent().parent().parent().parent().children()


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
    let sources = 0
    let components = $(".energy-component")

    components.each((idx, item) => {
        let checkbox = $($(item).children()[0]).find("input")[0]
        console.log(checkbox);

        if(checkbox.checked) {
            sources++
        }
    })

    components.each((idx, item) => {
        let checkbox = $($(item).children()[0]).find("input")[0]

        let row = $($(item).children()[1])

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
