$(document).on('click','.slider_hidden',function(){
    //$('.slider').css('height',0)
    $('html,body').animate({scrollTop: window.innerHeight},500);
})