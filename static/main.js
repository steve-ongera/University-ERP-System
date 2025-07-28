const menuitems = document.querySelectorAll('.menu-link .menu_sub'),
    activeState = document.querySelector('.menu-link.active'),
    activeMenu = sessionStorage.getItem('activeMenu'),
    activeSubMenu = sessionStorage.getItem('activeSubMenu'),
    menuTop = document.querySelector('.menu-top'),
    sideNav = document.querySelector('.sidenav'),
    main = document.querySelector('main'),
    imgBrand = document.querySelector('img.navbar-brand'),
    mq = window.matchMedia("(max-width: 992px)")
    


const removeActiveSubMenu = () => {
    const activeOpenMenu = document.querySelector('ul.open li.active');
    if (activeOpenMenu)
        activeOpenMenu.classList.remove('active')
}


if (activeMenu) {
    if (activeState) {
        activeState.classList.remove('active')
    }
    const elem = document.querySelector(`#${activeMenu}`);
    if (elem) {
        elem.classList.add('active')
    }
    const subOpenMenu = document.querySelector(`#${activeMenu} ul`);
    const subMenus = document.querySelector('ul.open');
    if (subOpenMenu) {
        if(subMenus)
            subMenus.classList.remove()
        subOpenMenu.classList.add('open')
    }
}

const subMenuItems = document.querySelectorAll('ul.open li.sub-item a')
const activeStateSub = document.querySelector('.menu-link ul.open')
if (activeSubMenu) {
    removeActiveSubMenu()
    const subMenu = document.querySelector(`#${activeSubMenu}`)
    if (subMenu)
        subMenu.classList.add('active')
}

menuitems.forEach(item => {
    item.addEventListener('click',
        () => {
             
            const activeMenu = document.querySelector('.menu-link.active');
            const activeOpenMenu = document.querySelector('.menu-link ul.open');
            if (activeOpenMenu)
                activeOpenMenu.classList.remove('open')
            if (activeMenu) {
                activeMenu.classList.remove('active')
            }
            item.parentElement.classList.add('active')
            const activeId = item.parentElement.getAttribute('id')
            const openMenu = document.querySelector(`#${activeId} ul`)
            if (openMenu) {
                openMenu.classList.add('open')
            }
            sessionStorage.setItem('activeMenu', activeId)
            sessionStorage.removeItem('tabPaneActive'),
            sessionStorage.removeItem('navTabActive')
        }
    )
})

if (subMenuItems) {
    subMenuItems.forEach(item => {
        item.addEventListener('click', () => {
             
            removeActiveSubMenu()
            item.classList.add('active')
            sessionStorage.setItem('activeSubMenu', item.getAttribute('id'))
            sessionStorage.removeItem('tabPaneActive'),
            sessionStorage.removeItem('navTabActive')
        })
    })
}

//toggle top menu
menuTop.addEventListener('click', () => {
    const menuClose = document.querySelector('.sidenav.close'),
    menuTopLeftAlign = document.querySelector('.menu-top.left-pos')
    if (menuClose) {
        sideNav.classList.remove('close')
        if (!mq.matches)
            main.classList.remove('open')
        if (menuTopLeftAlign && !mq.matches) {
            menuTop.classList.remove('left-pos')
            imgBrand.classList.remove('close')
        }
    }
    else {
        sideNav.classList.add('close')
        main.classList.add('open')
        menuTop.classList.add('left-pos')
        imgBrand.classList.add('close')
    }
})


//media query
if (mq.matches) {
    sideNav.classList.add('close')
    main.classList.add('open')
    menuTop.classList.add('left-pos')
    document.querySelector('.navbar-nav').classList.add('mobile')
    imgBrand.classList.add('close')
}
else {
    sideNav.classList.remove('close')
    main.classList.remove('open')
    menuTop.classList.remove('left-pos')
    document.querySelector('.navbar-nav').classList.remove('mobile')
    imgBrand.classList.remove('close')
}

//academic evaluations
const startTrigger = document.querySelectorAll('.start-eval'),
    evalStart = document.querySelector('.eval-start'),
    evalProg = document.querySelector('.eval-prog'),
    evalFill = sessionStorage.getItem('evalFill')
if (evalFill) {
    evalStart.classList.add('hide');
    evalProg.classList.add('show');
}
if (startTrigger) {
    startTrigger.forEach(trig => {
        trig.addEventListener("click", () => {
            evalStart.classList.add('hide');
            evalProg.classList.add('show');
            sessionStorage.setItem('evalFill',true)
        })
    })
}


//tooltips
 
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
if (tooltipTriggerList)
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

//tab state
const navTabActive = document.querySelector('.nav-tabs .nav-link.active'),
        navTabs = document.querySelectorAll('.nav-tabs .nav-link'),
        tabPaneActive = document.querySelector(".tab-pane.show.active"),
        activeTabPane = sessionStorage.getItem('tabPaneActive'),
        activeNavTab = sessionStorage.getItem('navTabActive')

navTabs.forEach(nav => {
    nav.addEventListener('click', () => {
         
        const tabPaneId = nav.getAttribute('data-bs-target').substring(1);
        sessionStorage.setItem('navTabActive', nav.getAttribute('id'))
        sessionStorage.setItem('tabPaneActive', tabPaneId)
    })
})
 
if (activeNavTab && activeTabPane) {
    const sett = document.getElementById('settingsToggle')
    sett.addEventListener('click', () => {
        sessionStorage.removeItem('navTabActive')
        sessionStorage.removeItem('tabPaneActive')
    })
    if (navTabActive)
        navTabActive.classList.remove('active')
    if (tabPaneActive)
        tabPaneActive.classList.remove('show', 'active')
    const activePane = document.getElementById(activeTabPane),
        activeTab = document.getElementById(activeNavTab)
    if (activeTab)
        activeTab.classList.add('active')
    if (activePane)
        activePane.classList.add('show', 'active')
    
}



//scroll position 
 
const scrollSideY = sessionStorage.getItem('scrollSideY'),
    scrollMainY = sessionStorage.getItem('scrollMainY'),
    sideNavArea = document.querySelector('.sidenav')

if (scrollSideY)
    sideNavArea.scrollTop = scrollSideY
if (scrollMainY)
    document.documentElement.scrollTop = scrollMainY

sideNavArea.addEventListener('scroll', () => {
     
    sessionStorage.setItem('scrollSideY', sideNavArea.scrollTop)
})

window.addEventListener('scroll', () => {
     
    sessionStorage.setItem('scrollMainY', document.documentElement.scrollTop)
})


////stepper online survey
//var current_fs, next_fs, previous_fs; //fieldsets
//var left, opacity, scale; //fieldset properties which we will animate
//var animating; //flag to prevent quick multi-click glitches

//$(".next").click(function () {
//    if (animating) return false;
//    animating = true;

//    current_fs = $(this).parent();
//    next_fs = $(this).parent().next();

//    //activate next step on progressbar using the index of next_fs
//    $("#progressbar li").eq($("fieldset").index(next_fs)).addClass("active");

//    //show the next fieldset
//    next_fs.show();
//    //hide the current fieldset with style
//    current_fs.animate({ opacity: 0 }, {
//        step: function (now, mx) {
//            //as the opacity of current_fs reduces to 0 - stored in "now"
//            //1. scale current_fs down to 80%
//            scale = 1 - (1 - now) * 0.2;
//            //2. bring next_fs from the right(50%)
//            left = (now * 50) + "%";
//            //3. increase opacity of next_fs to 1 as it moves in
//            opacity = 1 - now;

//            current_fs.hide();
//            next_fs.css({ 'opacity': opacity });
//        },
//        duration: 800,
//        complete: function () {
//            //current_fs.hide();
//            animating = false;
//        },
//        //this comes from the custom easing plugin
//        easing: 'easeInOutBack'
//    });
//});

//$(".previous").click(function () {
//    if (animating) return false;
//    animating = true;

//    current_fs = $(this).parent();
//    previous_fs = $(this).parent().prev();

//    //de-activate current step on progressbar
//    $("#progressbar li").eq($("fieldset").index(current_fs)).removeClass("active");

//    //show the previous fieldset
//    previous_fs.show();
//    //hide the current fieldset with style
//    current_fs.animate({ opacity: 0 }, {
//        step: function (now, mx) {
//            //as the opacity of current_fs reduces to 0 - stored in "now"
//            //1. scale previous_fs from 80% to 100%
//            scale = 0.8 + (1 - now) * 0.2;
//            //2. take current_fs to the right(50%) - from 0%
//            left = ((1 - now) * 50) + "%";
//            //3. increase opacity of previous_fs to 1 as it moves in
//            opacity = 1 - now;
//            //current_fs.css({ 'left': left });
//            current_fs.hide();
//            previous_fs.css({ 'opacity': opacity });
//        },
//        duration: 800,
//        complete: function () {
//            //current_fs.hide();
//            animating = false;
//        },
//        //this comes from the custom easing plugin
//        easing: 'easeInOutBack'
//    });
//});

//$(".submit").click(function () {
//    return false;
//})

