var currentCalendarYear;
var switch_table;
var row_id;
var switch_action; //'add' or 'edit'
$(window).load(function() {

    $('#myModal').on('hide.bs.modal', function (e) {
       if (document.activeElement.id == 'close_modal') {
            if(switch_action=='add') {
                $.getJSON(Flask.url_for('overview.add_switch',
                    {'name': $('#switch_name').val(),
                    'location':$('#switch_location').val()}),
                    function(data) {
                        if(data.status) {
                            load_switch_table();
                        } else {
                            alert('Fout: kan schakelaar niet toevoegen');
                        }
                    }
                );
            } else {
                $.getJSON(Flask.url_for('overview.edit_switch',
                    {'id': row_id,
                    'name': $('#switch_name').val(),
                    'location':$('#switch_location').val()}),
                    function(data) {
                        if(data.status) {
                            load_switch_table();
                        } else {
                            alert('Fout: kan schakelaar niet aanpassen');
                        }
                    }
                );
            }
       }
    });

    var currentDate = new Date();
    $('#calendar').calendar(
        {style:'border',
        enableRangeSelection:true,
        language:'nl',
        customDayRenderer: function(element, date) {
            if (date.getDate() == currentDate.getDate() && date.getMonth() == currentDate.getMonth() && date.getYear() == currentDate.getYear()) {
                $(element).css('font-weight', 'bold');
                $(element).css('font-size', '15px');
                $(element).css('color', 'blue');
            }
        },
        renderEnd: function(e) {
            if (e.currentYear != currentCalendarYear) {
                currentCalendarYear = e.currentYear;
                get_calendar_data();
            }
        }
    });
    currentCalendarYear = $('#calendar').data('calendar').getYear();

    //Configure switches table
    switch_table = $('#switches_table').DataTable({
        'ordering': false,
        serverSide: true,
        stateSave: true,
        dom : 't',
        ajax: {
            url: Flask.url_for('{{"overview.switches_data"}}'),
            type: 'POST'
        },
        "columns": [
            {name: 'Locatie', data: 'location'},
            {name: 'Aan/uit', data: 'status'},
            {name: 'Status', data: 'get_status'},
            {name: 'Naam', data: 'name'},
            {name: 'IP', data: 'get_ip'},
        ],
        "language" : {"url" : "//cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/Dutch.json"}
    });


    //right click on an item in the table.  A menu pops up to execute an action on the selected row/item
    var i = document.getElementById("menu").style;
    document.getElementById("switches_table").addEventListener('contextmenu', function(e) {
        var posX = e.clientX;
        var posY = e.clientY;
        menu(posX, posY);
        e.preventDefault();
        row_id = $(e.target).closest('tr').prop('id');
    }, false);
    document.addEventListener('click', function(e) {
        i.opacity = "0";
        setTimeout(function() {i.visibility = "hidden";}, 1);
    }, false);

    function menu(x, y) {
      i.top = y + "px";
      i.left = x + "px";
      i.width = "200px";
      i.visibility = "visible";
      i.opacity = "1";
    }

    get_settings();

    setTimeout(function() {
        check_switch_hb_status();
    }, 1000);
    setInterval(check_switch_hb_status, 5000);

});

function check_switch_hb_status() {
    $.getJSON(Flask.url_for('overview.check_switch_hb_status'), function(data) {
        $.each( data.switch_list, function(index, val ) {
            hb_color = val.hb ? "palegreen" : "salmon";
            $('#' + val.id).css("background-color", hb_color);
            status_text = val.status ? "AAN" : "UIT"
            $('#get_status' + val.id).text(status_text);
            $('#get_ip' + val.id).text(val.ip);
        });
    });
}


function load_switch_table() {
    switch_table.ajax.reload();
}

//Before deleting, a confirm-box is shown.
function confirm_before_delete(message, fn) {
    bootbox.confirm(message, function(result) {
        if (result) {
            fn();
        }
    });
}

$('#calendar').clickDay(function(e) {
    if(e.events.length > 0) {
        $.getJSON(Flask.url_for('overview.delete_event', {'id': e.events[0].id}), function(data) {
            if(data.status) {
                get_calendar_data();
            } else {
                alert('Fout: kan datum niet wissen');
            }
        });
    } else {
        $.getJSON(Flask.url_for('overview.add_event', {'date_string': e.date}), function(data) {
            if(data.status) {
                get_calendar_data();
            } else {
                alert('Fout: kan datum niet bewaren');
            }
        });

    }

});

function clear_calendar() {
    $.getJSON(Flask.url_for('overview.clear_calendar', {'year': currentCalendarYear}), function(data) {
        if(data.status) {
            get_calendar_data();
        } else {
            alert('Fout: kan kalender niet wissen');
        }
    });
}

function load_calendar() {
    $.getJSON(Flask.url_for('overview.load_calendar', {'year': currentCalendarYear}), function(data) {
        if(data.status) {
            get_calendar_data();
        } else {
            alert('Fout: kan kalender niet laden');
        }
    });
}

function get_calendar_data() {
    $.getJSON(Flask.url_for('overview.get_calendar_data', {'year': currentCalendarYear}), function(data) {
        //var dataSource = $('#calendar').data('calendar').getDataSource();
        var dataSource = [];
        $.each( data.calendar, function(index, val ) {
            //$('#timer_' + key).html(val);
            var event = {
                id: val.id,
                name: val.name,
                color: val.color,
                location: val.location,
                startDate: new Date(val.startDate),
                endDate: new Date(val.endDate)
            }
            dataSource.push(event);
        });
        $('#calendar').data('calendar').setDataSource(dataSource);
    });
}

function toggle_switch(id) {
    $.getJSON(Flask.url_for('overview.toggle_switch', {'id': id}), function(data) {
        if(data.status) {
            setTimeout(function() {
                check_switch_hb_status();
            }, 1000);
        } else {
            alert('Fout: kan status van de schakelaar niet veranderen');
        }
    });
}

function add_switch() {
    switch_action = 'add';
    $('#switch_name').val('');
    $('#switch_ip').val('');
    $('#switch_location').val('');
    $('#modal_title').html('Nieuwe schakelaar');
    $('#myModal').modal();
}

function handle_floating_menu(menu_id) {
    if(menu_id=='edit') {
        //alert('edit an entry ' + row_id);
        $.getJSON(Flask.url_for('overview.switch_data', {'id': row_id}), function(data) {
            if(data.status) {
                switch_action = 'edit';
                $('#switch_name').val(data.switch.name);
                $('#switch_ip').val(data.switch.ip);
                $('#switch_location').val(data.switch.location);
                $('#modal_title').html('Schakelaar aanpassen')
                $('#myModal').modal();
            } else {
                alert('Fout: kan schakelaar niet aanpassen');
            }
        });
    } else if (menu_id=='delete') {
        bootbox.confirm('Bent u zeker dat u deze schakelaar wilt wissen?', function(result) {
        if (result) {
            $.getJSON(Flask.url_for('overview.delete_switch', {'id': row_id}), function(data) {
                if(data.status) {
                    load_switch_table();
                } else {
                    alert('Fout: kan schakelaar niet wissen');
                }
            });

        }
    });
    }
}

function save_settings() {
    let settings = [];
    for(i=0; i < 3; i++) {
        let sched = {
                'start_time': $(`#start_time${i}`).val(),
                'stop_time': $(`#stop_time${i}`).val(),
                'stop_time_wednesday': $(`#stop_time_wednesday${i}`).val(),
                'auto_switch': document.getElementById(`auto_switch${i}`).checked
            }
        settings.push(sched);
    }
    $.getJSON(Flask.url_for('overview.save_settings', {'settings' : JSON.stringify(settings)}),
        function(data) {
            if(data.status) {
                alert('Instellingen zijn bewaard');
            } else if('message' in data) {
                alert(data.message)
            } else {
                alert('Fout: kan instellingen niet bewaren');
            }
        }
    );
}

function get_settings() {
    $.getJSON(Flask.url_for('overview.get_settings'), function(data) {
        if(data.status) {
            data.schedule.forEach((sched, i) => {
                $(`#start_time${i}`).val(sched.start_time);
                $(`#stop_time${i}`).val(sched.stop_time);
                $(`#stop_time_wednesday${i}`).val(sched.stop_time_wednesday);
                document.getElementById(`auto_switch${i}`).checked = sched.auto_switch

            });
            // $('#start_time').val(data.switch.start_time);
            // $('#stop_time').val(data.switch.stop_time);
            // $('#stop_time_wednesday').val(data.switch.stop_time_wednesday);
            // document.getElementById("auto_switch").checked = data.switch.auto_switch
        } else {
            alert('Fout: kan settings niet ophalen');
        }
    });
}