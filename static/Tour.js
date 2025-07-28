// System tour
 
let systemSteps = [],
    dashboardSteps = [],
    studentdashboardSteps = [],
    staffdashboardSteps = []

const systemTour = document.querySelector('#systemTour'),
    appendSteps = (stepsArray, data) => {
        if (data) {
            for (let i = 0; i < data.length ; i++) {
                const elem = data[i];
                const elemDet = document.getElementById(elem.id)
                if (elemDet) {
                    stepsArray.push(elem)
                }
            }
        }
    },
    selectedModule = sessionStorage.getItem('moduleSelection')



fetch('/tour.json').then(
    res =>res.json())
    .then(data => {
        //system Walkthrough
        const moduleData = JSON.parse(JSON.stringify(data))
        appendSteps(systemSteps, moduleData.moduleTour)
      
       
        //Modules tour
        if (selectedModule) {
            if (selectedModule === 'dashboard') {
                 
                appendSteps(dashboardSteps, moduleData.dashboard)
                const dashTour = new Tour(dashboardSteps)
                dashTour.show()
            }
            if (selectedModule === 'staffdashboard') {
                appendSteps(staffdashboardSteps, moduleData.staffdashboard)
                const dashTour = new Tour(staffdashboardSteps)
                dashTour.show()
            }
            if (selectedModule === 'studentdashboard') {
                appendSteps(studentdashboardSteps, moduleData.studentdashboard)
                const dashTour = new Tour(studentdashboardSteps)
                dashTour.show()
            }
            sessionStorage.removeItem('moduleSelection')
        }


    })

//sys tour ***
var tourSys = new Tour(systemSteps);
if (systemTour) {
    systemTour.addEventListener('click', () => {
         
        const myModalEl = document.getElementById('tourModal2');
        const modal = bootstrap.Modal.getInstance(myModalEl)
        modal.hide();
        // system tour init
        tourSys.show()
    })

}
//end of sys tour ***

//module tour ***
const moduleSelection = document.querySelector('#moduleSelection')
if (moduleSelection) {
    moduleSelection.addEventListener('change', e => {
        const selVal = e.target.value;
        sessionStorage.setItem('moduleSelection', selVal)
        sessionStorage.setItem('activeMenu', selVal)
            if (selVal === 'dashboard') {
                location.href = '/home/index'
            }
            if (selVal === 'staffdashboard') {
                location.href = '/home/StaffDashboard'
            }
            if (selVal === 'studentdashboard') {
                location.href = '/home/StudentDashboard'
            }

        $('#tourModal3').modal('hide');
        sessionStorage.setItem('isModule',true)
    })
}

