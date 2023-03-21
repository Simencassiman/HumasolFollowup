
function scalePersonInfo() {
    let threshold = 130;
    let info = $('.person-info > p');

    info.each((idx, elem) => {
        let item = $(elem), fs = parseInt(item.css('font-size'));
        console.log(elem);
        console.log(idx);
        console.log(item.width() > threshold);

        while (item.width() > threshold) { /* while height is more than threshold */
            item.css({'font-size': fs-- }); /* reduce the font-size */
        }
    });
}

scalePersonInfo();
