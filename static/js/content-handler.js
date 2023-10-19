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
function changeTabs(tab, nth, year, table_format='group', param='Seed') {
    console.log(tab+", "+nth+", "+year+", "+table_format)
    if (document.getElementById('cur_param') != null) {
        cur_param = document.getElementById('cur_param').value
    } else {
        cur_param = param
    }
    if (document.getElementById('cur_ascending') != null) {
        cur_ascending = document.getElementById('cur_ascending').value
    } else {
        cur_ascending = 'False'
    }
    console.log(cur_param)
    console.log(cur_ascending)
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
            cur_param: cur_param,
            cur_ascending: cur_ascending,
            param: param,
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