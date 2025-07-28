$(document).ready(function () {
    $(".multiSelect").chosen();

    //logo upload
    $(".iconClick").click(function () {
        $(".inputFile").trigger('click');
    });

    $('.inputFile').on('change', function () {
        var src = URL.createObjectURL(this.files[0])
        document.getElementById('settingsLogo').src = src;
        $('#logoUpload').removeClass('inputFile');

    });

    $("#logoUpload").click(function () {
        $('#logoUpload').addClass('inputFile');
        var formData = new FormData();
        formData.append('file', $('.inputFile')[0].files[0]);

        $.ajax({
            url: "/SystemSettings/UploadLogo/",
            type: "POST",
            dataType: "json",
            data: formData,
            contentType: false,
            processData: false,
            success: function (data) {
                if (data !== "Sorry no file is selected") {
                    if (data = "upload success") {
                        toastr.success("Uploaded successfully");

                    } else {
                        toastr.error(data);
                    }
                }
            },
            error: function (data) {
                toastr.error(data);

            }
        })
    });

    //profile upload
    $(".profIconClick").click(function () {
        $(".profileInputFile").trigger('click');
    });

    $('.profileInputFile').on('change', function () {
        var profSrc = URL.createObjectURL(this.files[0])
        document.getElementById('profilePicture').src = profSrc;
        $('#profileUpload').removeClass('profileInputFile');

    });

    $("#profileUpload").click(function () {
        $('#profileUpload').addClass('profileInputFile');
        var formData = new FormData();
        formData.append('file', $('.profileInputFile')[0].files[0]);

        $.ajax({
            url: "/Account/UploadProfile/",
            type: "POST",
            dataType: "json",
            data: formData,
            contentType: false,
            processData: false,
            success: function (data) {
                if (data !== "Sorry no file is selected") {
                    if (data = "upload success") {
                        toastr.success("Profile updated successfully");
                    } else {
                        toastr.error(data);
                    }
                }
            },
            error: function (data) {
                toastr.error(data);
            }
        })
    });


    //class status
    $('.classStatus').on('change', function (e) {
        var name = e.target.id.replace('_', ' ');
        var isChecked = e.target.checked;
        var classInput = $('#ClassStatus').val();
        var array = [];
        if (classInput) {
            array = classInput.split(",");
        }
        if (isChecked)
        {
            array.push(name);
        }
        else
        {
            const index = array.indexOf(name);
            if (index > -1) {
                array.splice(index, 1); 
            }
        }
        document.getElementById('ClassStatus').value = array;
    });
    //Report status
    $('.reportStatus').on('change', function (e) {
        var name = e.target.id.replace('_', ' ');
        var isChecked = e.target.checked;
        var classInput = $('#ReportStatus').val();
        var array = [];
        if (classInput) {
            array = classInput.split(",");
        }
        if (isChecked)
        {
            array.push(name);
        }
        else
        {
            const index = array.indexOf(name);
            if (index > -1) {
                array.splice(index, 1); 
            }
        }
        document.getElementById('ReportStatus').value = array;
    });
    //privileges
    $('.groupPrivilege').on('change', function (e) {
       
        var name = e.target.id;
        var isChecked = e.target.checked;
        var privileges = $('#groupPrivileges').val();
        var array = [];
        if (privileges) {
            array = privileges.split(",");
        }
        if (isChecked) {
            array.push(name);
        }
        else {
            const index = array.indexOf(name);
            if (index > -1) {
                array.splice(index, 1);
            }
        }
        document.getElementById('groupPrivileges').value = array;
    });




    $('#groupRole').on('change', function () {
        var e = document.getElementById("groupRole");
        var value = e.value;
   
        $('.privDivClass').attr("hidden", true);
        var id = ('privDiv-' + value);
        var allId = ('privDiv-' + 9);
        $('.' + id).removeAttr('hidden');
        $('.' + allId).removeAttr('hidden');





        //$.ajax({
        //    type: "POST",
        //    url: "/UserManagement/getUserPrivileges?role=" + value,
        //    success: function (result) {
        //        $('#userPriv').html('');
        //        for (let i = 0; i < result.length; i++) {
        //            var options = '';
        //            options +=
        //                '<div class="col-md-6">'
        //                + '<div class="md-form mb-4">'
        //                + '<div class="form-check form-switch">'
        //                + '<label class="form-check-label ml-4" for="flexCheckDefault">'
        //                + result[i].privilegeName +
        //                '</label>'
        //                +
        //                '<input class="form-check-input  form-custom-check-input groupPrivilege shadow-none border" type="checkbox"/>' +
        //                '</div>' +
        //                '</div>' +
        //                '</div>'
        //            $('#userPriv').append(options);
        //        }


        //    },
        //    error: function (data) {
        //        alert(data);
        //    }
        //});


    });
    var setText = $('.editorText');
    setText.each(function(index, element){
        var cont = "";
        var child = element.children;
        for (let i = 0; i < child.length; i++)
        {
        cont = cont + child[i].outerText;
        }
        var set = "";
        if (cont.split(/\s+/).length > 20) {
            set = cont.split(/\s+/).slice(0, 20).join(" ") + "...";
        } else {
            set = cont.split(/\s+/).slice(0, 20).join(" ");
        }
        element.textContent = set;
    });


    $('#TargetGroupsList').on('change', function () {
        debugger
        var groups = $("#TargetGroupsList").val();
        var array = groups.join(",");
        //groups.each(function (index, element) {
        //    array.push(element);
        //})

        $.ajax({
            url: "/Socials/checkIsStudSelected?array=" + array,
            type: "POST",
            dataType: "json",
            contentType: false,
            processData: false,
            success: function (data) {
                debugger
                if (data === "succeed") {
                    $(".toggleStudentInfo").attr("hidden", false)
                    $(".chosen-container").removeAttr("style")
                } else {
                    $(".toggleStudentInfo").attr("hidden", true)
                }
            },
            error: function (data) {
                toastr.error(data);

            }
        })

    });


    //SMS
    $('#TargetGroup').on('change', function () {
        debugger
        var selGroup = $("#TargetGroup").val();
        if (selGroup) {
            if (selGroup == "Staff") {
                $(".staffCatHidden").attr("hidden", false);
                $(".studentCatHidden").attr("hidden", true);
                $(".toggleStudentInfo").attr("hidden", true);
            } else if (selGroup == "Student") {
                $(".staffCatHidden").attr("hidden", true);
                $(".studentCatHidden").attr("hidden", false);
                $(".toggleStudentInfo").attr("hidden", true);
            } else {
                $(".staffCatHidden").attr("hidden", true);
                $(".studentCatHidden").attr("hidden", true);
                $(".toggleStudentInfo").attr("hidden", true);
            }
        } else {
            $(".staffCatHidden").attr("hidden", true);
            $(".studentCatHidden").attr("hidden", true);
            $(".toggleStudentInfo").attr("hidden", true);
        }
    });

    $('#StaffTargetCat').on('change', function () {
        var selectedCat = $("#StaffTargetCat").val();
        if (selectedCat && selectedCat == "Per Campus") {
            $(".staffCampus").attr("hidden", false);
            $(".staffDepartment").attr("hidden", true);
            $(".studentCatHidden").attr("hidden", true);
            $(".toggleStudentInfo").attr("hidden", true);
        } else if (selectedCat && selectedCat == "Per Department") {
            $(".staffCampus").attr("hidden", true);
            $(".staffDepartment").attr("hidden", false);
            $(".studentCatHidden").attr("hidden", true);
            $(".toggleStudentInfo").attr("hidden", true);

        } else {
            $(".staffCampus").attr("hidden", true);
            $(".staffDepartment").attr("hidden", true);
            $(".studentCatHidden").attr("hidden", true);
            $(".toggleStudentInfo").attr("hidden", true);

        }
    });

    $('#studentGroupIselected').on('change', function () {
        debugger
        var group = $("#studentGroupIselected").val();
        if (group && group == "Not All") {
            $(".toggleStudentInfo").attr("hidden", false);
            $(".chosen-container").removeAttr("style");
        } else {
            $(".toggleStudentInfo").attr("hidden", true);
        }
    });







    $('#hostelSelect').on('change', function () {
        debugger
        var hostel = $("#hostelSelect").val().replaceAll(/ /g, "-").replaceAll("'", "-").replaceAll(",", "-").replaceAll(".", "-");
        $('#gridHostel tbody tr').attr("hidden", true);
        $("." + hostel).attr("hidden", false)

    });

    $('#needApproval').on('click', function () {
        document.getElementById("Approval").value = "true";
        $("form").submit();
    });
    $('#publicationType').on('change', function () {
        var prv = $('#prevselected').val();
        if (prv) {
            $('.' + prv).attr("hidden", true);
        }
        var typ = $("#publicationType").val();
        var selectedType = typ.replace(/[ ,]+/g, "-");
        $('.' + selectedType).attr("hidden", false);
        document.getElementById("prevselected").value = selectedType;



    });

    //Clearance
    $('#badgebtn').click(function () {
        if (document.getElementById('badgebtn').textContent === "I want to type") {
            $('#Reason').attr("hidden", true);
            $('#TypedReason').attr("hidden", false);
            document.getElementById('badgebtn').textContent = "I want to select";
        } else {
            $('#Reason').attr("hidden", false);
            $('#TypedReason').attr("hidden", true);
            document.getElementById('badgebtn').textContent = "I want to type";
        }
    });


















})
