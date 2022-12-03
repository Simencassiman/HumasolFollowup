
function scalePersonInfo() {
    var threshold = 130;
    var info = $('.person-info > p');

    info.each((idx, elem) => {
        var item = $(elem), fs = parseInt(item.css('font-size'));
        console.log(elem);
        console.log(idx);
        console.log(item.width() > threshold);

        while (item.width() > threshold) { /* while height is more than threshold */
            item.css({'font-size': fs-- }); /* reduce the font-size */
        }
    });
}

scalePersonInfo();
