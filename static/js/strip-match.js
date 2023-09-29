/* Atualização automática do strip-match */
var timeOutId = 0;
var requestMatchupESPN = function () {
    var this_weekday = parseInt(document.getElementById('weekday').value)
    var this_hour = parseInt(document.getElementById('hour').value)

    if (((this_weekday < 2) || (this_weekday == 2 && this_hour < 3)) || (((this_weekday > 4) || (this_weekday == 4 && this_hour > 21)))) {
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
    } else {
        timeOutId = setTimeout(requestMatchupESPN, 30000);
    }
}
/* Chama pela primeira vez assim que a página é carregada */
requestMatchupESPN();