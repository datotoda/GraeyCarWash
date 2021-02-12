document.addEventListener('DOMContentLoaded', function(){
    let sideNav = M.Sidenav.init(document.querySelectorAll('.sidenav'), {});
    let instances = M.Collapsible.init(document.querySelectorAll('.collapsible'), {});
    var selects = M.FormSelect.init(document.querySelectorAll('select'), {});
    var darepicker = M.Datepicker.init(document.querySelectorAll('.datepicker'), {
        'format': 'dd/mm/yyyy'
    });
    var timepicker = M.Timepicker.init(document.querySelectorAll('.timepicker'), {});
})