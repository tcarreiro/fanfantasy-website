/* Atualização automática do strip-match */
var timeOutId = 0;
var requestMatchupESPN = function () {
    $.ajax({
        type: "POST",
        url: "/update_match_strip",
        data: {
            current_week: $('#week').val(),
            weekday: $('#weekday').val(),
            current_year: $('#year').val(),
            hour: $('#hour').val(),
        },
        success: function (response) {
            $('div#strip-match').empty().append(response.data)
            /* Chamar a função 30 s após o término da chamada atual */
            timeOutId = setTimeout(requestMatchupESPN, 30000);
        },
        error: function (response) {
            timeOutId = setTimeout(requestMatchupESPN, 30000);
        }
    });
}
/* Chama pela primeira vez assim que a página é carregada */
requestMatchupESPN();

/* Tabs */
function changeTabs(tab, nth, year, table_format='group') {
    console.log(tab+", "+nth+", "+year+", "+table_format)
    links = document.querySelectorAll('header nav li')
    links.forEach(link => {
        link.classList.remove('active')
    });
    links[nth].classList.add('active')
    $.ajax({
        type: "POST",
        url: tab,
        data: {
            tab: tab, // ???
            nth: nth, // ???
            table_format: table_format,
            year: year,
        },
        success: function (response) {
            $('div#main-content').empty().append(response.data)
        },
        error: function (response) {
            //$('div#main-content').empty().append(response.data) // TODO Colocar HTML com msg de erro
        }
    });
}

function changeStandingTableOrder(table_format, year, param, order) {
    links = document.querySelectorAll('header nav li')
    console.log(links)
    $.ajax({
        type: "POST",
        url: "/classificacao",
        data: {
            table_format: table_format,
            year: year,
            param: param,
            order: order,
        },
        success: function (response) {
            $('div#main-content').empty().append(response.data)
        },
        error: function (response) {
            //$('div#main-content').empty().append(response.data) // TODO Colocar HTML com msg de erro
        }
    });
}