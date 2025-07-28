$(document).ready(function () {

    //password toggle
    $("#togglePassword,#toggleCPassword").on('click', function () {
        var inputs = $("#password,#cpassword");
        inputs.each(function (index, element) {
            element.getAttribute('type') === 'password' ? element.setAttribute('type', 'text') : element.setAttribute('type', 'password');
            this.classList.toggle("bi-eye");
        });
    });

    ////tabs state
    //$('a[data-toggle="tab"]').on('show.bs.tab', function (e) {
    //    sessionStorage.setItem('activeTab', $(e.target).attr('href'));
    //});
    //var activeTab = sessionStorage.getItem('activeTab');
    //if (activeTab) {
    //    $('#myTab a[href="' + activeTab + '"]').tab('show');
    //}

    $('input').addClass('shadow-none');
    $('input').toggleClass('border');
    $('input').addClass('shadow-none');

    //tooltip
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    //datatable
    const dataTable = $('table.display').DataTable({
        pagingType: 'full_numbers',
        lengthMenu: [
            [10, 25, 50, -1],
            [10, 25, 50, 'All'],
        ],
        responsive: true,
        "sDom": "lfrti",
        "dom": '<"top"if>rt<"bottom"lp><"">',
        oLanguage: {
            oPaginate: {
                sprev: '<span class="pagination-fa"><i class="fa-thin fa-angles-left"></i></span>',
                snext: '<span class="pagination-fa"><i class="fa-thin fa-angles-right"></i></span>'
            }
        },
        orderCellsTop: false,
    });

    const dataTableHostel = $('table.gridHostel').DataTable({
        responsive: true,
        "paging": false,
    });

    var headersArray = [];
    var headers = $('.social tr th').length;
    for (let i = 0; i < headers; i++) {
        headersArray.push(i);
    }

    const dataTableSocial = $('table.social').DataTable({
        pagingType: 'full_numbers',
        "odering": false,
        "columnDefs": [
            { "orderable": false, "targets": headersArray } // Applies the option to all columns
        ],
        lengthMenu: [
            [3, 5, 10, 25, 50, -1],
            [3, 5, 10, 25, 50, 'All'],
        ],
        responsive: true,
        "sDom": "lfrti",
        "dom": '<"top"if>rt<"bottom"lp><"">',
        oLanguage: {
            oPaginate: {
                sprev: '<span class="pagination-fa"><i class="fa-thin fa-angles-left"></i></span>',
                snext: '<span class="pagination-fa"><i class="fa-thin fa-angles-right"></i></span>'
            }
        },
        orderCellsTop: false,
    });

    var socialtable = $('.social');
    console.log(socialtable);
    $('.social tr').addClass('noborder');
    $('.social tr th').removeClass('sorting_asc');
    $('.tOpinion tr').removeClass('noborder');
    $('.tMemo tr').removeClass('noborder');
    $('.tPublication tr').removeClass('noborder');

    $('#searchdata').keyup(function () {
        dataTable.search($(this).val()).draw();
        dataTableSocial.search($(this).val()).draw();
        dataTableHostel.search($(this).val()).draw();
    });

    $('#gridleave_info,#gridIn_first,#gridleave_filter,#gridIn_last,#eventGrid_first,#eventGrid_last,.dataTables_info,.dataTables_filter').hide();
    $('.bottom').addClass('row d-flex flex-row p-2 mt-3');
    $('.dataTables_length,.dataTables_paginate').addClass('col mt-2');
    $('.pagination').addClass('col-md-12');

    //ck editor 
    ClassicEditor
        .create(document.querySelector('#editor'))
        .then(editor => {
            //console.log(editor);
        })
        .catch(error => {
            // console.error(error);
        });

    ClassicEditor
        .create(document.querySelector('#editornote'))
        .then(editor => {
            //console.log(editor);
        })
        .catch(error => {
            //console.error(error);
        });



    //printer
    function printDocument() {
        var divToPrint = document.getElementById('div_print');
        var newWin = window.open('', 'Print-Window');
        newWin.document.open();
        newWin.document.write('<html><body onload="window.print()">' + divToPrint.innerHTML + '</body></html>');
        newWin.document.close();
        setTimeout(function () { newWin.close(); }, 10);
    }
   
});
